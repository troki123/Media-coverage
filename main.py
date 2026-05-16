from fastapi import FastAPI
from pydantic import BaseModel
from news_summary.Gemini_AIsummary import GeminiSumarize

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.get("/summarize")
def summarize():
    summary = GeminiSumarize()
    return summary.get_summary()