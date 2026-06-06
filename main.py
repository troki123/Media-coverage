import requests
import os
import sqlite3
import random
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flasgger import Swagger
from news_summary.Gemini_AIsummary import GeminiSumarize
from core import setup_logging, register_error_handlers
from flask_cors import CORS
from init_db import setup_database

# === LOGGER INITIALIZATION ===
setup_logging()

setup_database()

# === LOAD ENVIRONMENT VARIABLES ===
load_dotenv()

# === API CONFIGURATION ===
app = Flask(__name__)

CORS(app)
swagger = Swagger(app)

# === GLOBAL EXCEPTION HANDLER ===
register_error_handlers(app) 


def fetch_news(query):
    """
    Fetches articles from NewsAPI based on the provided query parameter.
    Includes a custom User-Agent header to bypass local request restrictions.
    """
    url = "https://newsapi.org/v2/everything"
    
    # Securely retrieve the API key from environment variables
    api_key = os.getenv("NEWS_API_KEY")
    
    params = {
        "q": query,
        "pageSize": 3,
        "apiKey": api_key,
        "sortBy": "relevancy",
        "language": "en"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    app.logger.info(f"Sending request to NewsAPI for query: '{query}'")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        articles = data.get("articles", [])
        app.logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI.")
        return articles
    except Exception as e:
        app.logger.error(f"Error fetching from NewsAPI: {e}")
        return []


# ==================================== ENDPOINTS ===========================================

@app.route("/search", methods=["GET"])
def search():
    """
    Search for articles via NewsAPI, process descriptions using Gemini AI,
    and automatically store the results inside the SQLite media_news table.
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: false
        default: technology
        description: Keyword for fetching articles
    responses:
      200:
        description: Articles successfully fetched, analyzed, and persisted
      500:
        description: Internal Server error
    """
    query = request.args.get("q", "general")
    app.logger.info(f"Endpoint /search called with query parameter: '{query}'")

    # 1. Fetch raw articles from the external provider
    articles = fetch_news(query)

    # 2. Initialize the Gemini service instance
    try:
        ai_analyzer = GeminiSumarize()
    except Exception as e:
        app.logger.error(f"Failed to initialize Gemini Client: {e}")
        ai_analyzer = None

    processed_articles = []
    
    # Generate a unique search batch ID matching the format from news_search.py
    generated_search_id = random.randint(1000000000, 1999999999)

    # 3. Setup SQLite path and connection to intercept the web data stream
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "database", "app.db")
    db_connected = os.path.exists(db_path)
    
    if db_connected:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

    # 4. Iterate through articles, generate summaries, and cache them inside SQLite
    for idx, a in enumerate(articles):
        if not a.get("title") or a.get("title") == "[Removed]":
            continue

        title = a.get("title")
        raw_description = a.get("description", "No description available")
        
        # Prepare the structured text payload for the LLM
        content_to_analyze = f"Title: {title}\nDescription: {raw_description}"

        if ai_analyzer:
            app.logger.info(f"Sending article {idx+1} to Gemini for analysis...")
            ai_summary = ai_analyzer.get_summary(content_to_analyze)
        else:
            ai_summary = raw_description

        source_name = a.get("source", {}).get("name", "Unknown") if isinstance(a.get("source"), dict) else "Unknown"
        article_url = a.get("url", "#")

        # Automatically insert rows into media_news on behalf of the web user
        if db_connected:
            try:
                cursor.execute("""
                    INSERT INTO media_news (search_id, media_name, link, summary, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (generated_search_id, source_name, article_url, ai_summary, raw_description))
            except Exception as db_err:
                app.logger.error(f"Failed to auto-insert live web query into SQLite: {db_err}")

        # Map fields into the JSON structure required by the frontend application
        processed_articles.append({
            "title": title,
            "url": article_url,
            "description": ai_summary,  
            "source": source_name,
            "published_at": a.get("publishedAt", ""),
        })

    # Commit changes and clean up connection handles
    if db_connected:
        conn.commit()
        conn.close()
        app.logger.info(f"Successfully automated storage of logs for search batch #{generated_search_id}")

    return jsonify({
        "query": query,
        "articles": processed_articles
    })
    

# =========================== AI SUMMARY (SWAGGER ONLY) ===========================================
@app.route("/summary", methods=["GET"])
def news_summary():
    """
    Generate an isolated system summary using Gemini AI.
    ---
    parameters:
      - name: search_id
        in: query
        type: integer
        required: true
        description: The internal database search tracking ID to run batch summaries against

    responses:
      200:
        description: Successfully generated batch summaries
      400:
        description: Missing required search_id parameter

    """
    # Extract search_id safely from the incoming URL query string
    search_id_raw = request.args.get("search_id")

    if not search_id_raw:
        app.logger.warning("Endpoint /summary called without a search_id parameter.")
        return jsonify({"error": "Missing required parameter: search_id"}), 400

    try:
        search_id = int(search_id_raw)
    except ValueError:
        return jsonify({"error": "Parameter search_id must be an integer"}), 400


    app.logger.info("Endpoint /summary called. Initializing Gemini Summarization...")
    summary = GeminiSumarize()
    return summary.get_summary() 


# =========================== SQLITE API ENDPOINTS ===========================================

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """
    Fetches high-level metrics from the actual database/app.db file.
    """
    try:
        # Match the exact path structure: database/app.db
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "database", "app.db")
        
        # Safe fallback check if the database folder or file hasn't been generated yet
        if not os.path.exists(db_path):
            return jsonify({
                "total_searches": 0,
                "total_sources": 0,
                "status": "Database missing"
            }), 200

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Count unique search batches using DISTINCT search_id from media_news table
        cursor.execute("SELECT COUNT(DISTINCT search_id) FROM media_news")
        total_searches = cursor.fetchone()[0]
        
        # 2. Count total rows saved in the media_news table
        cursor.execute("SELECT COUNT(*) FROM media_news")
        total_sources = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "total_searches": total_searches,
            "total_sources": total_sources,
            "status": "Connected"
        }), 200
        
    except Exception as e:
        app.logger.error(f"Database error while fetching analytics: {e}")
        return jsonify({"error": "Failed to fetch analytics data", "details": str(e)}), 500


@app.route("/api/sources", methods=["GET"])
def get_sources():
    """
    Retrieves recent rows from the media_news table grouped by search_id.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "database", "app.db")
        
        if not os.path.exists(db_path):
            return jsonify([]), 200

        # check_same_thread=False is used for multi-threaded environment safety
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Get the 5 most recent distinct search IDs stored in the table
        cursor.execute("SELECT DISTINCT search_id FROM media_news ORDER BY id DESC LIMIT 5")
        distinct_ids = cursor.fetchall()
        
        history_payload = []
        for (s_id,) in distinct_ids:
            if s_id is None:
                continue
                
            # Fetch target logs belonging to this specific search batch
            cursor.execute("SELECT media_name, link, summary FROM media_news WHERE search_id = ?", (s_id,))
            rows = cursor.fetchall()
            
            history_payload.append({
                "id": s_id,
                "query": f"Search Batch #{s_id}", 
                "sources_count": len(rows),
                "articles": [{"title": f"[{row[0]}] {row[2][:60] if row[2] else 'Verified Connection'}", "url": row[1]} for row in rows]
            })
            
        conn.close()
        return jsonify(history_payload), 200
        
    except Exception as e:
        app.logger.error(f"Database error while fetching sources history: {e}")
        return jsonify({"error": "Failed to fetch source history", "details": str(e)}), 500
    
    
if __name__ == "__main__":
    app.run(debug=True)