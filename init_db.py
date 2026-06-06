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
    media_name TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    content TEXT,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_date DATE
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
    print("Database initialized.")

if __name__ == "__main__":
    setup_database()
