"""Stock sync endpoint tests"""

import pytest

from .conftest import assert_success_response, assert_response_structure


class TestStockSyncEndpoints:
    """Test stock sync endpoints"""

    def test_sync_stock_list(self, client):
        """Test POST /api/v1/market/stock/sync endpoint"""
        response = client.post(
            "/api/v1/market/stock/sync",
            json={"force_update": True}
        )

        data = assert_success_response(response)
        assert "data" in data
        assert_response_structure(data["data"], ["task_id", "sync_type"])
        assert data["data"]["sync_type"] == "stock"

    def test_get_stock_sync_status(self, client):
        """Test GET /api/v1/market/stock/sync-status endpoint"""
        response = client.get("/api/v1/market/stock/sync-status")

        assert_success_response(response)

    def test_sync_kline(self, client, default_stock):
        """Test POST /api/v1/market/kline/sync/{stock_code} endpoint"""
        response = client.post(
            f"/api/v1/market/kline/sync/{default_stock}",
            json={"interval": "1d"}
        )

        data = assert_success_response(response)
        assert "data" in data
        assert_response_structure(data["data"], ["task_id", "sync_type"])
        assert data["data"]["sync_type"] == "kline"

    def test_sync_kline_second_stock(self, client, test_stocks):
        """Test POST /api/v1/market/kline/sync/{stock_code} with second stock"""
        second_stock = test_stocks[1]  # 601611
        response = client.post(
            f"/api/v1/market/kline/sync/{second_stock}",
            json={"interval": "1d"}
        )

        data = assert_success_response(response)
        assert "data" in data
        assert_response_structure(data["data"], ["task_id", "sync_type"])
        assert data["data"]["sync_type"] == "kline"
