# init_db.py
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")