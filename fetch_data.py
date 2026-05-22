from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
from flask import request # imports requests

load_dotenv()

app = Flask(__name__)

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
    response = requests.get(url, params=params)
    data = response.json()
    return data["articles"]

# Function defines flask api endpoint - handles incoming requests
# Reads query parameters, fetches articles using fetch_news() and returns JSON response
@app.route("/news-summary")
def news_summary():
    try:
        # this should read the query from the url
        query = request.args.get("q", "general")  # default if empty

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
                    "published_at": a.get("publishedAt", "")
                }

                for a in articles if a.get("title") and a.get("url")
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug = True)