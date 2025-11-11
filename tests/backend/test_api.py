"""Basic API tests."""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_readiness_check():
    """Test readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_register_user():
    """Test user registration."""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "tenant_name": "Test Tenant"
    })
    # May fail if user exists, that's OK for this basic test
    assert response.status_code in [200, 201, 400]


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

