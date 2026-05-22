from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv
from flask import request # imports requests
from flasgger import Swagger
from news_summary.Gemini_AIsummary import GeminiSumarize


load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)

# Function retrieves news articles from newspapi based on user provided search query
# Requests are sent to newsapi endpoint and returns a list of matching articles
def fetch_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        # query tells newsapi to give articles related to this keyword
        "q": query,
        "pageSize": 10,
        "apiKey": os.getenv("NEWS_API_KEY")
    }

    # requests.get sends a request to newsapi server
    # server sends data back in JSON format
    # data only extracts title and url of the article
    response = requests.get(url, params=params)
    data = response.json()
    return data["articles"]

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
        query = request.args.get("q", "technology")  # default if empty

        articles = fetch_news(query)

        # jsonify converts python data into a JSON response
        # articles table extracts only the title and url of the article
        return jsonify({
            "articles": [
                {"title": a["title"], "url": a["url"]}
                for a in articles # loops through every article
            ],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
    summary = GeminiSumarize()
    return summary.get_summary()

    
if __name__ == "__main__":
    app.run(debug = True)