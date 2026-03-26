"""Portfolio endpoint tests"""

import pytest


class TestPortfolioEndpoints:
    """Test portfolio API endpoints"""

    def test_get_account_summary(self, client):
        """Test GET /api/v1/portfolio/account/summary endpoint"""
        response = client.get("/api/v1/portfolio/account/summary")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_cash_balance(self, client):
        """Test GET /api/v1/portfolio/account/cash endpoint"""
        response = client.get("/api/v1/portfolio/account/cash")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_add_cash(self, client):
        """Test POST /api/v1/portfolio/account/cash/add endpoint"""
        response = client.post(
            "/api/v1/portfolio/account/cash/add",
            json={"amount": 100000.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_buy_stock(self, client):
        """Test POST /api/v1/portfolio/trade/buy endpoint"""
        response = client.post(
            "/api/v1/portfolio/trade/buy",
            json={"stock_code": "600011", "quantity": 100, "price": 10.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify trade details in response
        assert "data" in data
        trade_data = data["data"]
        assert trade_data is not None

    def test_get_positions(self, client):
        """Test GET /api/v1/portfolio/positions endpoint"""
        response = client.get("/api/v1/portfolio/positions")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify the position we just bought appears
        positions = data.get("data", [])
        stock_codes = [p.get("stock_code") for p in positions]
        assert "600011" in stock_codes

    def test_get_position_detail(self, client, default_stock):
        """Test GET /api/v1/portfolio/positions/{stock_code} endpoint"""
        response = client.get(f"/api/v1/portfolio/positions/{default_stock}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_sell_stock(self, client):
        """Test POST /api/v1/portfolio/trade/sell endpoint"""
        response = client.post(
            "/api/v1/portfolio/trade/sell",
            json={"stock_code": "600011", "quantity": 50, "price": 11.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_transactions(self, client):
        """Test GET /api/v1/portfolio/transactions endpoint"""
        response = client.get("/api/v1/portfolio/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify transactions include our buy/sell
        transactions = data.get("data", [])
        assert len(transactions) >= 2
        # Check that we have both buy and sell transactions
        types = [t.get("transaction_type") for t in transactions]
        assert "buy" in types
        assert "sell" in types

    def test_add_favorite(self, client):
        """Test POST /api/v1/portfolio/favorites/add endpoint"""
        response = client.post(
            "/api/v1/portfolio/favorites/add",
            json={"symbol": "600011"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_favorites(self, client):
        """Test GET /api/v1/portfolio/favorites endpoint"""
        response = client.get("/api/v1/portfolio/favorites")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_remove_favorite(self, client):
        """Test POST /api/v1/portfolio/favorites/remove endpoint"""
        response = client.post(
            "/api/v1/portfolio/favorites/remove",
            json={"symbol": "600011"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
