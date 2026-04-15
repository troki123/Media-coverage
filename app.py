import os
import requests
from dotenv import load_dotenv
from tavily import TavilyClient

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

tavily = TavilyClient(api_key=TAVILY_KEY)

# Using Gemini 2.5 Flash
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_KEY}"

def fetch_news(query):
    """Fetches news and filters out social media/video platforms."""
    print(f"🔍 Fetching textual sources for: {query}...")
    
    # Dodajemo 'exclude_domains' kako bi Tavily odmah preskočio uobičajene video/social platforme
    search = tavily.search(
        query=query, 
        search_depth="basic", 
        max_results=15, # Tražimo više da bi AI imao od čega filtrirati
        exclude_domains=["youtube.com", "instagram.com", "reddit.com", "tiktok.com", "facebook.com", "vimeo.com", "twitter.com", "x.com"]
    )
    
    context = ""
    for r in search['results']:
        context += f"TITLE: {r['title']} | URL: {r['url']}\n"
    return context

def ask_gemini(news_content, query):
    """Filters and formats only high-quality textual links."""
    print("🧠 AI is filtering and formatting text-only sources...")
    
    prompt_text = (
        f"You are a professional research librarian. I have a list of potential sources for '{query}'.\n\n"
        f"TASK:\n"
        f"1. Remove any links that point to YouTube, Instagram, Reddit, or any social media.\n"
        f"2. Provide a clean, numbered list of ONLY high-quality articles, news reports, and academic/official websites.\n"
        f"3. Format as: Title - Link.\n"
        f"4. Maximum 10 results. No summaries, no intros.\n\n"
        f"DATA:\n{news_content}"
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_text
            }]
        }]
    }
    
    response = requests.post(GEMINI_URL, json=payload)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"AI Server Error: {response.status_code} - {response.text}"

def main():
    user_query = input("Enter the topic for a text-only source list: ")
    
    try:
        news_data = fetch_news(user_query)
        if not news_data:
            print("No sources found.")
            return
            
        link_list = ask_gemini(news_data, user_query)
        
        print("\n" + "="*60)
        print(f" TEXT-ONLY SOURCES FOR: {user_query.upper()} ")
        print("="*60)
        print(link_list)
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()