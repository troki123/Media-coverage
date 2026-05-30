import pytest
from unittest.mock import MagicMock, patch
from news_summary.Gemini_AIsummary import GeminiSumarize


@patch('news_summary.Gemini_AIsummary.sqlite3')  # Faking a database
@patch('news_summary.Gemini_AIsummary.genai')    # Faking Gemini API
def test_gemini_summary_success(mock_genai, mock_sqlite):
    """
    Tests successfull summary generation when database empty (Cache miss)
    """

    # 1. Setting up fake SQLite response (returns None -> not found in database)
    mock_cursor = mock_sqlite.connect().cursor()
    mock_cursor.fetchone.return_value = None

    # 2. Setting up fake Gemini API response
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client

    # Simulating response.text returning "ASCII FLOWER"
    mock_response = MagicMock()
    mock_response.text = "ASCII FLOWER"
    mock_client.models.generate_content.return_value = mock_response

    # 3. Running our code
    sumarizer = GeminiSumarize()
    result = sumarizer.get_summary(search_querry="test_querry")

    # 4. Assertions
    assert "ASCII FLOWER" in result
    # Checking if our code tried to connect to database and add new sumary
    assert mock_sqlite.connect.called
    assert mock_cursor.execute.called
