"""Backtest endpoint tests"""

import pytest


class TestBacktestEndpoints:
    """Test backtest API endpoints"""

    def test_single_backtest(self, client, default_stock):
        """Test POST /api/v1/backtest/single endpoint"""
        response = client.post(
            "/api/v1/backtest/single",
            json={
                "symbol": default_stock,
                "strategy": "vcp",
                "config": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000.0
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert "task_id" in data["data"]

    def test_portfolio_backtest(self, client, test_stocks):
        """Test POST /api/v1/backtest/portfolio endpoint"""
        response = client.post(
            "/api/v1/backtest/portfolio",
            json={
                "symbols": test_stocks,
                "strategy": "vcp",
                "config": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000.0
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert "task_id" in data["data"]
        assert "results" in data["data"]

    def test_compare_strategies(self, client, default_stock):
        """Test POST /api/v1/backtest/compare endpoint"""
        response = client.post(
            "/api/v1/backtest/compare",
            json={
                "symbol": default_stock,
                "config": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000.0
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert "comparison" in data["data"]
        assert "best_strategy" in data["data"]

    def test_get_backtest_result_not_found(self, client):
        """Test GET /api/v1/backtest/result/{task_id} with non-existent task"""
        # Use a mock task_id that doesn't exist
        response = client.get("/api/v1/backtest/result/non_existent_task_id")

        # Should return 404 for non-existent task
        assert response.status_code == 404

    def test_get_backtest_result_after_single_backtest(self, client, default_stock):
        """Test GET /api/v1/backtest/result/{task_id} after running a backtest"""
        # First run a single backtest to get a valid task_id
        backtest_response = client.post(
            "/api/v1/backtest/single",
            json={
                "symbol": default_stock,
                "strategy": "vcp",
                "config": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000.0
                }
            }
        )

        assert backtest_response.status_code == 200
        backtest_data = backtest_response.json()
        task_id = backtest_data["data"]["task_id"]

        # Now get the result using the task_id
        response = client.get(f"/api/v1/backtest/result/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
