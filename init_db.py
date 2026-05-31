import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "app.db")

def ensure_database_tables():
    """Verifies that the database schema and required tables exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create searches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create media_news table
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
    print("Database initialized successfully.")

# Alias for backward compatibility with news_search.py
setup_database = ensure_database_tables

if __name__ == "__main__":
    ensure_database_tables()