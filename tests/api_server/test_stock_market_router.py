#!/usr/bin/env python3
"""测试股票市场管理 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_START_DATE,
    TEST_END_DATE,
    assert_success_response
)


class TestStockMarketAPI:
    """股票市场管理 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    def test_sync_stock_list(self, client: TestClient) -> None:
        """测试同步股票列表"""
        response = client.post(
            "/api/v1/market/stock/sync",
            json={"force_update": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "task_id" in data["data"]
        assert data["data"]["sync_type"] == "stock"

    def test_get_stock_sync_status(self, client: TestClient) -> None:
        """测试获取股票同步状态"""
        response = client.get("/api/v1/market/stock/sync-status")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data

    def test_sync_kline(self, client: TestClient) -> None:
        """测试同步单股K线"""
        response = client.post(
            f"/api/v1/market/kline/sync/{TEST_STOCK_CODE}",
            json={
                "interval": "1d",
                "start_date": TEST_START_DATE,
                "end_date": TEST_END_DATE
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "task_id" in data["data"]
        assert data["data"]["sync_type"] == "kline"

    def test_sync_kline_data_structure(self, client: TestClient) -> None:
        """测试同步K线 - 数据结构"""
        response = client.post(
            f"/api/v1/market/kline/sync/{TEST_STOCK_CODE}",
            json={"interval": "1d"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"]["status"] == "pending"
        assert data["data"]["status"]["progress"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
