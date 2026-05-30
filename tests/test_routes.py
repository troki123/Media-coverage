import pytest
from main import app

@pytest.fixture
def client():
    """
    This is fixture - a function that prepares an enviroment for the test.
    Creates a simulated client for sending Http request to our Flask.
    """

    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_search_endpoint_success(client):
    """
    Tests if route /search returns status code 200 and a valid JSON format.
    """
    # Sending a Simulated request to /search?q=technology
    response = client.get('/search?q=technology')

    # Checking if Http status code 200 (Ok)
    assert response.status_code == 200

    # Transforming resonse to JSON and checking structure
    data = response.get_json()
    assert "query" in data
    assert "articles" in data
    assert data['query'] in "technology"


