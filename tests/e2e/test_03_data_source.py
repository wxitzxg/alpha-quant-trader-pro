"""Data source endpoint tests"""

import pytest


class TestDataSourceEndpoints:
    """Test data source API endpoints"""

    def test_get_stock_list(self, client):
        """Test GET /api/v1/stock/list endpoint"""
        response = client.get("/api/v1/stock/list", params={"page": 1, "page_size": 20})

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Response should contain stocks or list field
        response_data = data.get("data", {})
        assert "stocks" in response_data or "list" in response_data

    def test_get_stock_info(self, client, default_stock):
        """Test GET /api/v1/stock/info/{stock_code} endpoint"""
        response = client.get(f"/api/v1/stock/info/{default_stock}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Response should contain symbol and name fields
        response_data = data.get("data", {})
        assert "symbol" in response_data or "code" in response_data
        assert "name" in response_data

    def test_get_realtime_quote(self, client, default_stock):
        """Test GET /api/v1/quote/realtime/{stock_code} endpoint"""
        response = client.get(f"/api/v1/quote/realtime/{default_stock}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Response should contain price and symbol fields
        response_data = data.get("data", {})
        assert "price" in response_data or "current_price" in response_data
        assert "symbol" in response_data or "code" in response_data

    def test_get_batch_quotes(self, client, test_stocks):
        """Test POST /api/v1/quote/batch endpoint"""
        response = client.post(
            "/api/v1/quote/batch",
            json={"symbols": test_stocks}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Response should contain quotes list
        response_data = data.get("data", {})
        assert "quotes" in response_data or "list" in response_data

    def test_get_kline(self, client, default_stock):
        """Test GET /api/v1/kline/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/kline/{default_stock}",
            params={"interval": "1d", "limit": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Response should contain klines list
        response_data = data.get("data", {})
        assert "klines" in response_data or "list" in response_data

    def test_get_kline_stats(self, client, default_stock):
        """Test GET /api/v1/kline/stats/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/kline/stats/{default_stock}",
            params={"period": "1y"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_financial_indicators(self, client, default_stock):
        """Test GET /api/v1/financial/indicators/{stock_code} endpoint"""
        response = client.get(f"/api/v1/financial/indicators/{default_stock}")

        # Accept 200 (success) or 404 (not available)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
