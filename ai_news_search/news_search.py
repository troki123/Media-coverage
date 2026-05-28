import os
import requests
import time
import sqlite3
from dotenv import load_dotenv
from init_db import setup_database  

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
NEWS_KEY = os.getenv("NEWS_API_KEY") 

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_KEY}"

def fetch_news(query):
    """Dohvaća vijesti s NewsAPI-ja."""
    print(f"🔍 Fetching articles from NewsAPI for: {query}...")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": 30,  
        "apiKey": NEWS_KEY,
        "sortBy": "relevancy",
        "language": "en"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if response.status_code != 200 or "articles" not in data:
            print(f"⚠️ NewsAPI Error: {data.get('message', 'Unknown error')}")
            return ""

        # Pakiramo podatke u tekstualni kontekst za Gemini
        context = ""
        for a in data["articles"]:
            # Sigurno izvlačenje podataka 
            title = a.get("title")
            url_link = a.get("url")
            description = a.get("description", "No description available")
            
            if title and url_link:
                context += f"TITLE: {title}\nURL: {url_link}\nDESC: {description}\n---\n"
        
        return context

    except Exception as e:
        print(f"❌ Error fetching from NewsAPI: {e}")
        return ""

def ask_gemini(news_content, query):
    """Gemini kritički analizira NewsAPI podatke, odbacuje irelevantne kontroverze i traži bit."""
    print("🧠 AI is strictly filtering and verifying source relevance...")
    
    prompt_text = (
        f"You are an expert research librarian and fact-checker. Your task is to extract the most relevant sources for the user query: '{query}'.\n\n"
        f"STRICT FILTERING RULES:\n"
        f"1. Read the TITLE and DESCRIPTION of each article carefully.\n"
        f"2. If the article is just clickbait, political controversy, or mentions the query words only in passing without actually answering/addressing the topic '{query}', DO NOT INCLUDE IT.\n"
        f"3. Select ONLY the most high-quality, informative, and contextually accurate sources (up to 10).\n"
        f"4. Output Format: Title | URL (use the pipe symbol to separate them).\n"
        f"5. Do not include introductory text, bullet points, markdown formatting, or empty lines. Just the raw text lines.\n\n"
        f"DATA TO ANALYZE:\n{news_content}"
    )
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        response = requests.post(GEMINI_URL, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return f"AI Error: {response.status_code}"
    except Exception as e:
        return f"AI Connection Error: {e}"

def get_or_create_search_id(query):
    """Provjerava bazu i vraća stari ID ili kreira novi."""
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY,
            query_text TEXT UNIQUE
        )
    """)
    
    cursor.execute("SELECT id FROM searches WHERE LOWER(query_text) = LOWER(?)", (query.strip(),))
    row = cursor.fetchone()
    
    if row:
        search_id = row[0]
        print(f"♻️ Found existing search history for '{query}'. Reusing ID: {search_id}")
    else:
        search_id = int(time.time())
        cursor.execute("INSERT INTO searches (id, query_text) VALUES (?, ?)", (search_id, query.strip()))
        conn.commit()
        print(f"🆕 New topic detected. Generated brand new ID: {search_id}")
        
    conn.close()
    return search_id

def save_to_db(search_id, link_list_text):
    """Parsira tekst od Gemini-ja i sprema u bazu samo ako su naslov i link valjani."""
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()
    
    lines = link_list_text.strip().split('\n')
    count = 0
    for line in lines:
        if "|" in line:
            clean_line = line.split('.', 1)[-1] if '.' in line[:4] else line
            parts = clean_line.split("|")
            
            if len(parts) == 2:
                title = parts[0].strip()
                url = parts[1].strip()
                
                # DODATNA PROVJERA: Preskoči ako su naslov ili URL prazni
                if not title or not url:
                    continue
                
                # Provjera duplikata
                cursor.execute("""
                    SELECT 1 FROM media_news 
                    WHERE search_id = ? AND link = ?
                """, (search_id, url))
                
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO media_news (search_id, media_name, link) VALUES (?, ?, ?)",
                        (search_id, title, url)
                    )
                    count += 1  # Povećava se SAMO ako je stvarno spremljeno u bazu
    
    conn.commit()
    conn.close()
    return count

def main():
    setup_database()
    
    user_query = input("Enter the topic for a text-only source list: ")
    if not user_query.strip():
        print("Query cannot be empty.")
        return

    try:
        # 1. Uzmi ili kreiraj povijesni ID
        current_search_id = get_or_create_search_id(user_query)
        
        # 2. Povuci sirove vijesti s NewsAPI-ja (nema cenzure za osjetljive teme)
        news_data = fetch_news(user_query)
        if not news_data:
            print("No sources found from NewsAPI.")
            return
            
        # 3. Pošalji Gemini-ju da probrani materijal pretvori u top 10 linkova
        link_list = ask_gemini(news_data, user_query)
        
        if "AI Error" in link_list or "AI Connection Error" in link_list:
            print(f"❌ Gemini failed: {link_list}")
            return

        # 4. Spremi pročišćene rezultate u SQLite
        saved_count = save_to_db(current_search_id, link_list)
        
        print("\n" + "="*60)
        print(f" TEXT-ONLY SOURCES FOR: {user_query.upper()} (ID: {current_search_id}) ")
        print("="*60)
        print(link_list)
        print(f"\n✅ Successfully saved {saved_count} new sources to database/app.db")
        
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()