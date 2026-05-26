import os
import requests
from dotenv import load_dotenv
from tavily import TavilyClient

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

tavily = TavilyClient(api_key=TAVILY_KEY)

# Using the stable Gemini 2.5 Flash model found in your project
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_KEY}"

def fetch_news(query):
    """Searches the internet for the latest news and returns raw content."""
    print(f"🔍 Searching for news about: {query}...")
    # Advanced search to get better snippets for the AI to read
    search = tavily.search(query=query, search_depth="advanced", max_results=3)
    
    context = ""
    for r in search['results']:
        context += f"\nSOURCE: {r['url']}\nCONTENT: {r['content']}\n"
    return context

def ask_gemini(news_content, query):
    """Sends news data to Gemini 2.5 Flash and returns an English summary."""
    print("🧠 AI (Gemini 2.5 Flash) is analyzing the data...")
    
    prompt_text = (
        f"You are a professional news analyst. Based on the following news data, "
        f"write a comprehensive and objective report in English about '{query}':\n\n"
        f"{news_content}"
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
    user_query = input("Enter the topic for news search: ")
    
    try:
        news_data = fetch_news(user_query)
        if not news_data:
            print("No news found for this topic.")
            return
            
        report = ask_gemini(news_data, user_query)
        
        print("\n" + "="*40)
        print("        FINAL NEWS REPORT        ")
        print("="*40)
        print(report)
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()