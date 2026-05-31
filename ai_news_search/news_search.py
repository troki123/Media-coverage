import os
import requests
import time
import sqlite3
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
NEWS_KEY = os.getenv("NEWS_API_KEY")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_KEY}"

# Dinamički određujemo path do baze bez obzira odakle se modul importira
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, "database", "app.db")


def fetch_news(query):
    """Dohvaća vijesti s NewsAPI-ja."""
    print(f"🔍 Fetching articles from NewsAPI for: {query}...")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": 50,
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

        context = ""
        for a in data["articles"]:
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
    """Gemini kritički analizira NewsAPI podatke i vraća top 10 linkova."""
    print("🧠 AI is strictly filtering and verifying source relevance...")

    prompt_text = (
        f"You are an expert research librarian and fact-checker. Your task is to extract the most relevant sources for the user query: '{query}'.\n\n"
        f"STRICT FILTERING RULES:\n"
        f"1. Read the TITLE and DESCRIPTION of each article carefully.\n"
        f"2. Only exclude articles where the query topic is completely irrelevant or the article has no actual content about it.\n"
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
    conn = sqlite3.connect(DB_PATH)
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

                if not title or not url:
                    continue

                cursor.execute("""
                    SELECT 1 FROM media_news
                    WHERE search_id = ? AND link = ?
                """, (search_id, url))

                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO media_news (search_id, media_name, link) VALUES (?, ?, ?)",
                        (search_id, title, url)
                    )
                    count += 1

    conn.commit()
    conn.close()
    return count


def run_ai_search(query: str) -> dict:
    """
    Glavna funkcija koju poziva main.py — ne koristi input(), vraća dict.
    
    Returns:
        dict s ključevima: search_id, saved_count, sources (lista dicts), error (ako ima)
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty."}

    try:
        current_search_id = get_or_create_search_id(query)

        news_data = fetch_news(query)
        if not news_data:
            return {"error": "No sources found from NewsAPI.", "search_id": current_search_id}

        link_list = ask_gemini(news_data, query)

        if "AI Error" in link_list or "AI Connection Error" in link_list:
            return {"error": f"Gemini failed: {link_list}", "search_id": current_search_id}

        saved_count = save_to_db(current_search_id, link_list)

        # Parsiraj rezultate u strukturirani format za API odgovor
        sources = []
        for line in link_list.strip().split('\n'):
            if "|" in line:
                clean_line = line.split('.', 1)[-1] if '.' in line[:4] else line
                parts = clean_line.split("|")
                if len(parts) == 2:
                    title = parts[0].strip()
                    url = parts[1].strip()
                    if title and url:
                        sources.append({"title": title, "url": url})

        return {
            "search_id": current_search_id,
            "query": query,
            "saved_count": saved_count,
            "sources": sources,
        }

    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


# Zadržavamo standalone CLI način rada
def main():
    from init_db import setup_database
    setup_database()

    user_query = input("Enter the topic for a text-only source list: ")
    result = run_ai_search(user_query)

    if "error" in result:
        print(f"❌ {result['error']}")
        return

    print("\n" + "="*60)
    print(f" TEXT-ONLY SOURCES FOR: {user_query.upper()} (ID: {result['search_id']}) ")
    print("="*60)
    for s in result["sources"]:
        print(f"{s['title']} | {s['url']}")
    print(f"\n✅ Successfully saved {result['saved_count']} new sources to database")


if __name__ == "__main__":
    main()