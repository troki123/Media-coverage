import requests
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flasgger import Swagger
from news_summary.Gemini_AIsummary import GeminiSumarize
from ai_news_search.news_search import run_ai_search   # <-- novi import
from core import setup_logging, register_error_handlers
from flask_cors import CORS
from init_db import setup_database


# === LOGGER ===
setup_logging()

setup_database()

load_dotenv()

# =============== API ===============
app = Flask(__name__)

CORS(app)
swagger = Swagger(app)

# === GLOBAL EXCEPTION HANDLER ===
register_error_handlers(app)


# Function retrieves news articles from NewsAPI based on user provided search query.
# Requests are sent to newsapi endpoint and returns a list of matching articles.
def fetch_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": 100,
        "apiKey": os.getenv("NEWS_API_KEY"),
        "sortBy": "relevancy",
        "language": "en"
    }

    app.logger.info(f"Sending request to NewsAPI for query: '{query}'")
    response = requests.get(url, params=params)
    data = response.json()
    articles = data.get("articles", [])
    app.logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI.")
    return articles


# ==================================== ENDPOINTS ===========================================

@app.route("/search", methods=["GET"])
def search():
    """
    Searching for articles with NewsAPI (raw results, no AI filtering)
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: false
        default: technology
        description: Key word for fetching articles
    responses:
      200:
        description: Articles successfully fetched
      500:
        description: Internal Server error
    """
    query = request.args.get("q", "general")
    app.logger.info(f"Endpoint /search called with query parameter: '{query}'")

    articles = fetch_news(query)

    return jsonify({
        "query": query,
        "articles": [
            {
                "title": a.get("title", "No title"),
                "url": a.get("url", "#"),
                "description": a.get("description", "No description available"),
                "source": a.get("source", {}).get("name", "Unknown"),
                "published_at": a.get("publishedAt", ""),
            }
            for a in articles if a.get("title") and a.get("url")
        ]
    })


# =========================== AI SEARCH ===========================================

@app.route("/ai-search", methods=["GET"])
def ai_search():
    """
    AI-filtered news search — fetches articles, filters with Gemini, saves to DB
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Topic to search and AI-filter
    responses:
      200:
        description: AI-filtered sources saved and returned
      400:
        description: Missing query parameter
      500:
        description: Internal Server error
    """
    query = request.args.get("q", "").strip()

    if not query:
        app.logger.warning("Endpoint /ai-search called without a 'q' parameter.")
        return jsonify({"error": "Missing required parameter: q"}), 400

    app.logger.info(f"Endpoint /ai-search called with query: '{query}'")

    result = run_ai_search(query)

    if "error" in result:
        app.logger.error(f"AI search failed: {result['error']}")
        return jsonify(result), 500

    app.logger.info(
        f"AI search complete for '{query}'. "
        f"search_id={result['search_id']}, saved={result['saved_count']}"
    )
    return jsonify(result)


# =========================== AI SUMMARY ===========================================

@app.route("/summary", methods=["GET"])
def news_summary():
    """
    Generating batch summaries with Gemini AI using a specific search tracking ID
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
    search_id_raw = request.args.get("search_id")

    if not search_id_raw:
        app.logger.warning("Endpoint /summary called without a search_id parameter.")
        return jsonify({"error": "Missing required parameter: search_id"}), 400

    try:
        search_id = int(search_id_raw)
    except ValueError:
        return jsonify({"error": "Parameter search_id must be an integer"}), 400

    app.logger.info("Endpoint /summary called. Initializing Gemini Summarization...")
    summarizer = GeminiSumarize()
    execution_result = summarizer.get_summary(search_id=search_id)
    return jsonify({"message": execution_result})


if __name__ == "__main__":
    app.run(debug=True)