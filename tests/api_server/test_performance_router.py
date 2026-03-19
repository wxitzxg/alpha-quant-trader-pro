#!/usr/bin/env python3
"""测试收益统计 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestPerformanceAPI:
    """收益统计 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 账户收益汇总测试 ==========
    @pytest.mark.asyncio
    async def test_get_account_performance_success(self, client):
        """测试账户收益汇总 - 成功"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "transaction_id": "t1",
                        "symbol": "600519",
                        "transaction_type": "BUY",
                        "amount": 10000,
                        "transaction_date": "2024-03-15"
                    },
                    {
                        "transaction_id": "t2",
                        "symbol": "600519",
                        "transaction_type": "SELL",
                        "amount": 11000,
                        "transaction_date": "2024-03-20"
                    }
                ]
            }

            mock_service.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {
                        "symbol": "000001",
                        "market_value": 50000,
                        "quantity": 100
                    }
                ]
            }

            response = client.get("/api/v1/performance/account/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "metrics" in data["data"]
            assert "transactions_count" in data["data"]
            assert data["data"]["transactions_count"] == 2

    @pytest.mark.asyncio
    async def test_get_account_performance_failure(self, client):
        """测试账户收益汇总 - 失败"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": False,
                "error": "Database error"
            }

            response = client.get("/api/v1/performance/account/summary")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 单股收益统计测试 ==========
    @pytest.mark.asyncio
    async def test_get_stock_performance_success(self, client):
        """测试单只股票收益统计 - 成功"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "transaction_id": "t1",
                        "symbol": "600519",
                        "transaction_type": "BUY",
                        "amount": 10000,
                        "price": 100,
                        "fee": 10,
                        "transaction_date": "2024-03-15"
                    },
                    {
                        "transaction_id": "t2",
                        "symbol": "600519",
                        "transaction_type": "SELL",
                        "amount": 11000,
                        "price": 110,
                        "fee": 10,
                        "transaction_date": "2024-03-20"
                    }
                ]
            }

            response = client.get("/api/v1/performance/stock/600519")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["profit"] > 0  # 应该盈利
            assert data["data"]["profit_rate"] > 0

    @pytest.mark.asyncio
    async def test_get_stock_performance_no_transactions(self, client):
        """测试单股收益统计 - 无交易记录"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": []
            }

            response = client.get("/api/v1/performance/stock/600519")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["profit"] == 0

    # ========== 历史收益曲线测试 ==========
    @pytest.mark.asyncio
    async def test_get_performance_history_daily(self, client):
        """测试历史收益曲线 - 日级"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "transaction_id": "t1",
                        "symbol": "600519",
                        "transaction_type": "BUY",
                        "amount": 10000,
                        "transaction_date": "2024-03-15"
                    },
                    {
                        "transaction_id": "t2",
                        "symbol": "600519",
                        "transaction_type": "SELL",
                        "amount": 11000,
                        "transaction_date": "2024-03-16"
                    }
                ]
            }

            response = client.get(
                "/api/v1/performance/history?period=daily"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "history" in data["data"]
            assert data["data"]["period"] == "daily"

    @pytest.mark.asyncio
    async def test_get_performance_history_monthly(self, client):
        """测试历史收益曲线 - 月级"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "transaction_id": "t1",
                        "symbol": "600519",
                        "transaction_type": "BUY",
                        "amount": 10000,
                        "transaction_date": "2024-03-15"
                    },
                    {
                        "transaction_id": "t2",
                        "symbol": "600519",
                        "transaction_type": "SELL",
                        "amount": 11000,
                        "transaction_date": "2024-04-15"
                    }
                ]
            }

            response = client.get(
                "/api/v1/performance/history?period=monthly"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["period"] == "monthly"

    # ========== 收益对比分析测试 ==========
    @pytest.mark.asyncio
    async def test_compare_performance_success(self, client):
        """测试收益对比分析 - 成功"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_account_summary.return_value = {
                "success": True,
                "data": {
                    "total_market_value": 100000,
                    "total_profit": 10000,
                    "cash_balance": 50000
                }
            }

            response = client.get("/api/v1/performance/compare")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "account_return" in data["data"]
            assert "benchmark_return" in data["data"]
            assert "alpha" in data["data"]
            assert data["data"]["benchmark"] == "沪深300 (模拟)"

    @pytest.mark.asyncio
    async def test_compare_performance_failure(self, client):
        """测试收益对比分析 - 失败"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_account_summary.return_value = {
                "success": False,
                "error": "Account not found"
            }

            response = client.get("/api/v1/performance/compare")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 边界测试 ==========
    @pytest.mark.asyncio
    async def test_get_performance_history_with_date_range(self, client):
        """测试历史收益曲线 - 带日期范围"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "transaction_id": "t1",
                        "symbol": "600519",
                        "transaction_type": "SELL",
                        "amount": 11000,
                        "transaction_date": "2024-03-20"
                    }
                ]
            }

            response = client.get(
                "/api/v1/performance/history?start_date=2024-03-01&end_date=2024-03-31&period=daily"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["start_date"] == "2024-03-01"
            assert data["data"]["end_date"] == "2024-03-31"

    # ========== 异常测试 ==========
    @pytest.mark.asyncio
    async def test_get_account_performance_exception(self, client):
        """测试账户收益汇总 - 异常"""
        with patch('api_server.routers.performance.portfolio_service') as mock_service:

            mock_service.get_transaction_history.side_effect = Exception("Unexpected error")

            response = client.get("/api/v1/performance/account/summary")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

