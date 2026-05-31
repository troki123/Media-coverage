import os
import sqlite3
import sys
import warnings
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flasgger import Swagger
from flask_cors import CORS

# Import database utilities from init_db.py
from init_db import ensure_database_tables, DB_PATH

warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_news_search"))
try:
    from news_search import get_or_create_search_id
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from news_search import get_or_create_search_id

from news_summary.Gemini_AIsummary import GeminiSumarize
from core import setup_logging, register_error_handlers

setup_logging()
load_dotenv()

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)
register_error_handlers(app)


def fetch_news(query):
    """Retrieves standard articles matching the search criteria via NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    api_key = os.getenv("NEWS_API_KEY")
    
    params = {
        "q": query,
        "pageSize": 15,
        "apiKey": api_key,
        "sortBy": "relevancy",
        "language": "en"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        app.logger.error(f"Error fetching from NewsAPI: {e}")
        return []


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "general").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    ensure_database_tables()

    existing_search_id = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM searches WHERE LOWER(query_text) = LOWER(?)", (query,))
        row = cursor.fetchone()
        if row:
            existing_search_id = row[0]
        conn.close()
    except Exception as e:
        app.logger.error(f"Error checking existing searches: {e}")

    # Case 1: Cache hit - Load existing data from the database
    if existing_search_id:
        app.logger.info(f"Cache hit for '{query}' (ID: {existing_search_id})")
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT media_name, link, content, summary FROM media_news WHERE search_id = ?", (existing_search_id,))
            rows = cursor.fetchall()
            conn.close()

            if rows:
                processed_articles = []
                for r in rows:
                    processed_articles.append({
                        "title": r["content"] if r["content"] else "News Article",
                        "url": r["link"],
                        "description": r["summary"],
                        "source": r["media_name"],
                        "published_at": ""
                    })
                
                return jsonify({
                    "query": query.upper(),
                    "search_id": existing_search_id,
                    "articles": processed_articles,
                    "from_cache": True
                })
        except Exception as db_err:
            app.logger.error(f"Failed to load cached data: {db_err}")

    # Case 2: Cache miss - Execute pipeline and process with Gemini AI
    try:
        generated_search_id = get_or_create_search_id(query)
    except Exception as e:
        app.logger.error(f"Failed to get/create search ID: {e}")
        return jsonify({"error": "Database error generating search token"}), 500

    articles = fetch_news(query)
    processed_articles = []
    
    ai_analyzer = GeminiSumarize()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for a in articles:
            title = a.get("title")
            url = a.get("url", "#")
            description = a.get("description") or "No description available"
            source_name = a.get("source", {}).get("name", "Unknown") if isinstance(a.get("source"), dict) else "Unknown"

            if not title or title == "[Removed]":
                continue

            ai_summary = ai_analyzer.get_summary(description)
            
            if "IRRELEVANT_ARTICLE" in ai_summary:
                continue

            cursor.execute("SELECT 1 FROM media_news WHERE search_id = ? AND link = ?", (generated_search_id, url))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO media_news (search_id, media_name, link, content, summary)
                    VALUES (?, ?, ?, ?, ?)
                """, (generated_search_id, source_name, url, title, ai_summary))

            processed_articles.append({
                "title": title,
                "url": url,
                "description": ai_summary,
                "source": source_name,
                "published_at": a.get("publishedAt", "")
            })

        conn.commit()
        conn.close()
    except Exception as e:
        app.logger.error(f"Error during live search processing: {e}")

    return jsonify({
        "query": query.upper(),
        "search_id": generated_search_id,
        "articles": processed_articles,
        "from_cache": False
    })


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    ensure_database_tables()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM searches")
        total_searches = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM media_news")
        total_sources = cursor.fetchone()[0]
        conn.close()
        return jsonify({"total_searches": total_searches, "total_sources": total_sources, "status": "Connected"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sources", methods=["GET"])
def get_sources():
    ensure_database_tables()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        history_payload = []
        cursor.execute("SELECT id, query_text FROM searches ORDER BY id DESC LIMIT 5")
        searches = cursor.fetchall()
        
        for s in searches:
            s_id = s["id"]
            q_text = s["query_text"]
            
            cursor.execute("SELECT content, link FROM media_news WHERE search_id = ?", (s_id,))
            rows = cursor.fetchall()
            
            history_payload.append({
                "id": s_id,
                "query": f"Topic: {q_text.upper()}",  
                "sources_count": len(rows),
                "articles": [{"title": r['content'][:60] + "..." if r['content'] else "Link", "url": r['link']} for r in rows]
            })
            
        conn.close()
        return jsonify(history_payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    ensure_database_tables()
    app.run(debug=True)