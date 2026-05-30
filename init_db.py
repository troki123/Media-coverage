# init_db.py (UPDATED VERSION)
import sqlite3
import os

def setup_database():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_id INTEGER,
        media_name TEXT NOT NULL,
        link TEXT NOT NULL,
        content TEXT,
        summary TEXT,
        authors TEXT,              -- NEW: Article authors
        publish_date DATETIME,     -- NEW: Publication date
        top_image TEXT,            -- NEW: Main image URL
        keywords TEXT,             -- NEW: Extracted keywords
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY,
            query_text TEXT UNIQUE
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized with full article schema.")