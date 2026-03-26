"""Health check endpoint tests"""

import pytest


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_health(self, client):
        """Test GET /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # Accept either "status": "healthy" or similar health indicators
        assert "status" in data or "healthy" in str(data).lower()

    def test_api_v1_health(self, client):
        """Test GET /api/v1/health endpoint"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
