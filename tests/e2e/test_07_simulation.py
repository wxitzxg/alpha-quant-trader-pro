"""Simulation endpoint tests"""

import pytest
import uuid


class TestSimulationEndpoints:
    """Test simulation API endpoints"""

    # Class-level storage for account_id shared between tests
    account_id = None
    unique_account_name = f"test_account_{uuid.uuid4().hex[:8]}"

    def test_create_simulation_account(self, client):
        """Test POST /api/v1/simulation/account endpoint"""
        response = client.post(
            "/api/v1/simulation/account",
            json={
                "account_name": self.unique_account_name,
                "initial_capital": 100000.0,
                "commission_rate": 0.0003
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        # Store account_id for subsequent tests
        TestSimulationEndpoints.account_id = data["data"].get("account_id")
        assert TestSimulationEndpoints.account_id is not None

    def test_list_accounts(self, client):
        """Test GET /api/v1/simulation/accounts endpoint"""
        response = client.get("/api/v1/simulation/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify our account appears in the list
        accounts = data.get("data", [])
        account_ids = [acc.get("account_id") for acc in accounts]
        assert TestSimulationEndpoints.account_id in account_ids

    def test_get_account(self, client):
        """Test GET /api/v1/simulation/account/{account_id} endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.get(f"/api/v1/simulation/account/{TestSimulationEndpoints.account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert data["data"].get("account_id") == TestSimulationEndpoints.account_id

    def test_simulation_buy(self, client):
        """Test POST /api/v1/simulation/buy endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.post(
            "/api/v1/simulation/buy",
            json={
                "account_id": TestSimulationEndpoints.account_id,
                "symbol": "600011",
                "price": 10.0,
                "quantity": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_positions(self, client):
        """Test GET /api/v1/simulation/positions/{account_id} endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.get(f"/api/v1/simulation/positions/{TestSimulationEndpoints.account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify the position we just bought appears
        positions = data.get("data", [])
        symbols = [p.get("symbol") for p in positions]
        assert "600011" in symbols

    def test_simulation_sell(self, client):
        """Test POST /api/v1/simulation/sell endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.post(
            "/api/v1/simulation/sell",
            json={
                "account_id": TestSimulationEndpoints.account_id,
                "symbol": "600011",
                "price": 11.0,
                "quantity": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_trades(self, client):
        """Test GET /api/v1/simulation/trades/{account_id} endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.get(f"/api/v1/simulation/trades/{TestSimulationEndpoints.account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Verify trades include our buy/sell
        trades = data.get("data", [])
        assert len(trades) >= 2

    def test_delete_account(self, client):
        """Test DELETE /api/v1/simulation/account/{account_id} endpoint"""
        assert TestSimulationEndpoints.account_id is not None, "account_id not set from create test"

        response = client.delete(f"/api/v1/simulation/account/{TestSimulationEndpoints.account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
