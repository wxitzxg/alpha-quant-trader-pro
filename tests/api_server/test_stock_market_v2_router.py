#!/usr/bin/env python3
"""测试股票市场数据 API 路由器 v2"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


from api_server.main import app


class TestStockMarketV2API:
    """股票市场数据 API v2 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 同步股票列表测试 ==========
    def test_sync_stock_list_success(self, client):
        """测试同步股票列表 - 成功"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.sync_all_stocks.return_value = {
                "success": True,
                "count": 4000,
                "message": "同步成功"
            }

            response = client.post(
                "/api/v1/market/stock/sync",
                json={"force_update": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["count"] == 4000
            assert "Stock sync completed" in data["message"]

    def test_sync_stock_list_failed(self, client):
        """测试同步股票列表 - 失败"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.sync_all_stocks.return_value = {
                "success": False,
                "message": "同步失败"
            }

            response = client.post(
                "/api/v1/market/stock/sync",
                json={"force_update": True}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 获取股票列表测试 ==========
    def test_get_stock_list_success(self, client):
        """测试获取股票列表 - 成功"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_stock_list.return_value = {
                "success": True,
                "data": [
                    {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
                    {"symbol": "000858", "name": "五粮液", "exchange": "SZ"},
                ],
                "total": 4000,
                "page": 1,
                "page_size": 20,
                "total_pages": 200
            }

            response = client.get("/api/v1/market/stock/list?page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == 4000
            assert len(data["data"]["stocks"]) == 2

    def test_get_stock_list_pagination(self, client):
        """测试获取股票列表 - 分页"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_stock_list.return_value = {
                "success": True,
                "data": [{"symbol": "600519"}] * 10,
                "total": 100,
                "page": 2,
                "page_size": 10,
                "total_pages": 10
            }

            response = client.get("/api/v1/market/stock/list?page=2&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 10

    def test_get_stock_list_boundary(self, client):
        """测试获取股票列表 - 边界值"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_stock_list.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "page": 1,
                "page_size": 1,
                "total_pages": 0
            }

            response = client.get("/api/v1/market/stock/list?page_size=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # ========== 同步K线测试 ==========
    def test_sync_kline_success(self, client):
        """测试同步K线 - 成功"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.sync_single_kline.return_value = {
                "success": True,
                "count": 120,
                "message": "同步成功"
            }

            response = client.post(
                "/api/v1/market/kline/sync/600519",
                json={
                    "interval": "1d",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["count"] == 120
            assert "KLine sync completed" in data["message"]

    def test_sync_kline_failed(self, client):
        """测试同步K线 - 失败"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.sync_single_kline.return_value = {
                "success": False,
                "message": "同步失败"
            }

            response = client.post(
                "/api/v1/market/kline/sync/600519",
                json={"interval": "1d"}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 获取K线测试 ==========
    def test_get_kline_success(self, client):
        """测试获取K线 - 成功"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_kline_data.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2024-03-15",
                        "open": 100.0,
                        "high": 105.0,
                        "low": 95.0,
                        "close": 102.0,
                        "volume": 1000000
                    }
                ] * 30,
                "total": 30
            }

            response = client.get(
                "/api/v1/market/kline/600519?interval=1d&start_date=2024-02-01&end_date=2024-03-31&limit=120"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["symbol"] == "600519"
            assert data["data"]["interval"] == "1d"
            assert len(data["data"]["klines"]) == 30

    def test_get_kline_with_limit(self, client):
        """测试获取K线 - 限制条数"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_kline_data.return_value = {
                "success": True,
                "data": [],
                "total": 0
            }

            response = client.get("/api/v1/market/kline/600519?limit=50")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["symbol"] == "600519"

    def test_get_kline_boundary(self, client):
        """测试获取K线 - 边界值"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_kline_data.return_value = {
                "success": True,
                "data": [],
                "total": 0
            }

            response = client.get("/api/v1/market/kline/600519?limit=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # ========== 同步状态查询测试 ==========
    def test_get_stock_sync_status(self, client):
        """测试获取股票同步状态"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_sync_status.return_value = {
                "success": True,
                "data": {
                    "status": "idle",
                    "last_sync_time": None,
                    "progress": 0
                }
            }

            response = client.get("/api/v1/market/stock/sync-status")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_get_kline_sync_status(self, client):
        """测试获取K线同步状态"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_sync_status.return_value = {
                "success": True,
                "data": {
                    "status": "idle",
                    "last_sync_time": None
                }
            }

            response = client.get("/api/v1/market/kline/sync-status/600519")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    # ========== 异常测试 ==========
    def test_sync_stock_list_exception(self, client):
        """测试同步股票列表 - 异常"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.sync_all_stocks.side_effect = Exception("Sync error")

            response = client.post(
                "/api/v1/market/stock/sync",
                json={"force_update": True}
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_kline_exception(self, client):
        """测试获取K线 - 异常"""
        with patch('api_server.routers.stock_market_v2.service') as mock_service:
            mock_service.get_kline_data.side_effect = Exception("Data error")

            response = client.get("/api/v1/market/kline/600519")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
