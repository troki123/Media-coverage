from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import request # imports requests

load_dotenv()

app = Flask(__name__)

genai.configure(api_key = os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Code For Fetching News
def fetch_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        # query tells newsapi to give articles related to this keyword
        "q": query,
        "pageSize": 10,
        "apiKey": os.getenv("NEWS_API_KEY")
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data["articles"]

# API Endpoint
@app.route("/news-summary")
def news_summary():
    try:
        # this should read the query from the url
        query = request.args.get("q", "technology")  # default if empty

        articles = fetch_news(query)

        # sends a response to frontend
        return jsonify({
            "articles": [
                {"title": a["title"], "url": a["url"]}
                for a in articles
            ],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug = True)