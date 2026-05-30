import pytest
import sqlite3
from news_summary.Gemini_AIsummary import GeminiSumarize

@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch):
    """
    Sets up an isolated in-memory SQLite database for the test suite.
    Intercepts and overrides the app's database path to prevent modifications to live data.
    """


    conn = sqlite3.connect(":memory:")
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

    # 2. Store a reference to the real __init__ method
    original_init = GeminiSumarize.__init__

    # 3. Create a wrapper that runs the real init first, then injects the test DB path
    def mock_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)  # Runs your actual initialization
        self.db_path = ":memory:"             # Overrides the path safely

    # 4. Patch the class with our smart wrapper
    monkeypatch.setattr(GeminiSumarize, "__init__", mock_init)
