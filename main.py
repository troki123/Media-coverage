from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
from flask import request # imports requests
from flasgger import Swagger
from news_summary.Gemini_AIsummary import GeminiSumarize
import logging
from logging.config import dictConfig
from datetime import datetime, timezone


load_dotenv()

# =========================== LOGGER =========================
# Osiguranje foldera
if not os.path.exists("logs"):
    os.makedirs("logs")

date_str = datetime.now(timezone.utc).strftime("%d_%m_%Y_")

# Globalna konfiguracija logiranja za cijelu aplikaciju
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': f'logs/{date_str}app.log',
            'formatter': 'default',
            'level': 'DEBUG',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
        }
    },
    'loggers': {
        'httpcore': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'google': {
            'level': 'WARNING',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        
        'werkzeug': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
})

# =============== API ===============
app = Flask(__name__)
swagger = Swagger(app)


# Function retrieves news articles from newspapi based on user provided search query
# Requests are sent to newsapi endpoint and returns a list of matching articles
def fetch_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        # query tells newsapi to give articles related to this keyword
        "q": query,
        "pageSize": 100,
        "apiKey": os.getenv("NEWS_API_KEY"),
        "sortBy": "relevancy",
        "language": "en"
    }

    # requests.get sends a request to newsapi server
    # server sends data back in JSON format
    # data only extracts title and url of the article
    app.logger.info(f"Sending request to NewsAPI for query: '{query}'")

    response = requests.get(url, params=params)
    data = response.json()
    articles = data.get("articles", [])
    app.logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI.")
    return articles

# Function defines flask api endpoint - handles incoming requests
# Reads query parameters, fetches articles using fetch_news() and returns JSON response
@app.route("/search", methods=["GET"])
def search():
    # docstring for search route, required so we can see search endpoint in swagger
    """
    Searching for articles with NewsAPI
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
        description: Articles succesfully fetched
      500:
        description: Internal Server error
    """
    try:
        # this should read the query from the url
        query = request.args.get("q", "general")  # default if empty

        app.logger.info(f"Endpoint /search called with query parameter: '{query}'")

        articles = fetch_news(query)

        # jsonify converts python data into a JSON response
        # articles table extracts only the title and url of the article
        return jsonify({
            "query": query,
            "articles": [
                {
                    "title": a.get("title", "No title"),
                    "url": a.get("url", "#"),
                    "description": a.get("description", "No descritpion available"),
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "published_at": a.get("publishedAt", ""),
                }

                for a in articles if a.get("title") and a.get("url")
            ]
        })

    except Exception as e:
        app.logger.error(f"Error occurred in /search endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    

# =========================== AI SUMMARY ===========================================
@app.route("/summary", methods=["GET"])
def news_summary():
     # docstring for summary route, required so we can see summary endpoint in swagger
    """
    Generating summary with Gemini AI
    ---
    responses:
      200:
        description: Successfully generated summary
    """

    try:
        app.logger.info("Endpoint /summary called. Initializing Gemini Summarization...")
        summary = GeminiSumarize()
        return summary.get_summary() 
    except Exception as e:
        app.logger.error(f"Error occurred in /summary endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug = True)