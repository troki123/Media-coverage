import os
import pytest
import sqlite3
from unittest.mock import patch, MagicMock

# Set up dummy environment variables to prevent GeminiSumarize initialization from raising ValueError
os.environ["GOOGLE_API_KEY"] = "mock-google-key-123"
os.environ["NEWS_API_KEY"] = "mock-news-key-123"

from main import app


@pytest.fixture
def client():
    """Initializes the Flask test client with the TESTING flag enabled."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db(tmp_path):
    """
    Creates a temporary SQLite database in an isolated directory
    to safely test database endpoints without altering production data.
    """
    db_file = tmp_path / "app.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    # Create the required table schema so endpoints can execute queries successfully
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER,
            media_name TEXT,
            link TEXT,
            summary TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()
    return str(db_file)


## =================== 1. TESTS FOR THE /search ENDPOINT ===================

@patch("main.fetch_news")
@patch("main.GeminiSumarize")
@patch("os.path.exists")
@patch("sqlite3.connect")
def test_search_endpoint_success(mock_sql_connect, mock_exists, mock_gemini_cls, mock_fetch_news, client):
    """
    Tests a successful pipeline execution for the /search route.
    Mocks the external NewsAPI data stream, Gemini AI instance, and database actions.
    """
    # 1. Simulate that the database file path is valid and exists
    mock_exists.return_value = True
    
    # 2. Mock the NewsAPI response payload returning one valid article structure
    mock_fetch_news.return_value = [
        {
            "title": "Artificial Intelligence in 2026",
            "description": "A deep dive into upcoming LLM advancements.",
            "url": "https://example.com/ai-2026",
            "source": {"name": "TechNews"},
            "publishedAt": "2026-05-31"
        }
    ]
    
    # 3. Instantiate a fake Gemini client and mock its get_summary behavior
    mock_gemini_instance = MagicMock()
    mock_gemini_instance.get_summary.return_value = "Mocked AI summary text."
    mock_gemini_cls.return_value = mock_gemini_instance

    # 4. Mock the SQLite connection objects to intercept database write operations
    mock_conn = MagicMock()
    mock_sql_connect.return_value = mock_conn

    # Trigger the GET request via Flask test client
    response = client.get("/search?q=AI")
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Validate payload parameters and response schema integrity
    assert data["query"] == "AI"
    assert len(data["articles"]) == 1
    assert data["articles"][0]["title"] == "Artificial Intelligence in 2026"
    assert data["articles"][0]["description"] == "Mocked AI summary text."
    assert data["articles"][0]["source"] == "TechNews"


@patch("main.fetch_news")
def test_search_endpoint_filtered_removed(mock_fetch_news, client):
    """
    Verifies that articles labeled as '[Removed]' or missing a primary title
    are correctly skipped and omitted from the frontend response payload.
    """
    mock_fetch_news.return_value = [
        {"title": "[Removed]", "description": "Removed content", "url": "#"},
        {"title": "", "description": "Missing title", "url": "#"}
    ]

    response = client.get("/search?q=test")
    assert response.status_code == 200
    data = response.get_json()
    
    # The application must filter both invalid entries out, returning an empty list
    assert len(data["articles"]) == 0


## =================== 2. TESTS FOR THE /summary ENDPOINT ===================

@patch("main.GeminiSumarize")
def test_summary_isolated_endpoint(mock_gemini_cls, client):
    """Tests the isolated /summary endpoint mainly utilized for Swagger documentation."""
    mock_gemini_instance = MagicMock()
    mock_gemini_instance.get_summary.return_value = "Isolated System Status Summary."
    mock_gemini_cls.return_value = mock_gemini_instance

    response = client.get("/summary")
    assert response.status_code == 200
    assert response.data.decode("utf-8") == "Isolated System Status Summary."


## =================== 3. TESTS FOR SQLITE ENDPOINTS (ANALYTICS & SOURCES) ===================

def test_analytics_db_missing(client):
    """
    Ensures that /api/analytics returns 0 counts gracefully with a safe status string
    if the physical database file does not exist on disk yet.
    """
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/analytics")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_searches"] == 0
        assert data["total_sources"] == 0
        assert data["status"] == "Database missing"


def test_analytics_success(client, mock_db):
    """
    Verifies metric aggregations inside /api/analytics when rows exist.
    Confirms DISTINCT tracking behaves correctly under grouped entries.
    """
    # Insert test logs directly into the temporary isolated database fixture
    conn = sqlite3.connect(mock_db)
    cursor = conn.cursor()
    # Write two distinct source entries tied to the exact same batch ID
    cursor.execute("INSERT INTO media_news (search_id, media_name, link) VALUES (111222, 'Media A', 'http://a.com')")
    cursor.execute("INSERT INTO media_news (search_id, media_name, link) VALUES (111222, 'Media B', 'http://b.com')")
    conn.commit()
    conn.close()

    # Intercept system path resolutions to feed our custom test database instance
    with patch("main.os.path.abspath") as mock_path:
        mock_path.return_value = mock_db
        with patch("os.path.exists", return_value=True), patch("sqlite3.connect", return_value=sqlite3.connect(mock_db)):
            response = client.get("/api/analytics")
            assert response.status_code == 200
            data = response.get_json()
            
            # The calculation expects 1 unique query batch but 2 total parsed items
            assert data["total_searches"] == 1
            assert data["total_sources"] == 2
            assert data["status"] == "Connected"


def test_get_sources_history_empty(client):
    """Ensures /api/sources responds with an empty JSON array if no database file exists."""
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/sources")
        assert response.status_code == 200
        assert response.get_json() == []


def test_get_sources_success(client, mock_db):
    """
    Validates the structure of /api/sources payload history tracking.
    Ensures recent records are grouped correctly under their respective search_id context.
    """
    conn = sqlite3.connect(mock_db)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO media_news (id, search_id, media_name, link, summary) 
        VALUES (1, 555, 'BBC', 'http://bbc.com', 'AI is rising.')
    """)
    conn.commit()
    conn.close()

    with patch("os.path.exists", return_value=True), patch("sqlite3.connect", return_value=sqlite3.connect(mock_db)):
        response = client.get("/api/sources")
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 555
        assert data[0]["sources_count"] == 1
        assert data[0]["articles"][0]["url"] == "http://bbc.com"