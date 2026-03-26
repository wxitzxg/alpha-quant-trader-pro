"""Other routers endpoint tests"""

import pytest


class TestFundflowEndpoints:
    """Test fundflow API endpoints"""

    def test_get_fundflow(self, client, default_stock):
        """Test GET /api/v1/fundflow/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/fundflow/{default_stock}",
            params={"page": 1, "page_size": 10}
        )

        # Accept 200 or handle gracefully if data not available
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # Data may be empty if external service not configured
            assert "success" in data

    def test_get_dragon_tiger(self, client, default_stock):
        """Test GET /api/v1/fundflow/dragon-tiger/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/fundflow/dragon-tiger/{default_stock}",
            params={"page": 1, "page_size": 10}
        )

        # Accept 200 or handle gracefully if data not available
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # Data may be empty if external service not configured
            assert "success" in data


class TestNewsEndpoints:
    """Test news API endpoints"""

    def test_get_news_list(self, client):
        """Test GET /api/v1/news/list endpoint"""
        response = client.get(
            "/api/v1/news/list",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_search_news(self, client):
        """Test GET /api/v1/news/search endpoint"""
        response = client.get(
            "/api/v1/news/search",
            params={"query": "股票", "page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestFinancialEndpoints:
    """Test financial API endpoints"""

    def test_get_financial_indicators(self, client, default_stock):
        """Test GET /api/v1/financial/indicators/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/financial/indicators/{default_stock}"
        )

        # Accept 200 or 404 if data not available
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
