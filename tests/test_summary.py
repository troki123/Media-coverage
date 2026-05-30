import pytest
from unittest.mock import MagicMock, patch
from news_summary.Gemini_AIsummary import GeminiSumarize


@patch('news_summary.Gemini_AIsummary.genai')
def test_gemini_summary_success(mock_genai):
    """
    Tests successful content generation through GeminiSummarize 
    when the local database cache does not contain the requested text.
    """
    # Arrange: Mock the Gemini Client and its response structure
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "Sample ASCII Flower Output"
    mock_client.models.generate_content.return_value = mock_response

    # Act: Run the target method
    summarizer = GeminiSumarize()
    result = summarizer.get_summary(article_text="Test raw input data")

    # Assert: Verify output text and check that the client was called with correct models
    assert "Sample ASCII Flower Output" in result
    assert mock_client.models.generate_content.called
    
    # Ensure our fallback safety configurations remain intact
    called_model = mock_client.models.generate_content.call_args[1]['model']
    assert called_model in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
