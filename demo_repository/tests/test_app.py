import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Health check endpoint test."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"

def test_index_route(client):
    """Index root route test."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert "service" in data

def test_get_users(client):
    """Users endpoint test - will fail if DATABASE_URL configuration is missing."""
    response = client.get("/users/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)}"
    data = response.get_json()
    assert "users" in data
    assert len(data["users"]) > 0
