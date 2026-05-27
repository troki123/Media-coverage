import sqlite3
import os

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

conn.commit()
conn.close()