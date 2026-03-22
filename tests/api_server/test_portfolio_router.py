#!/usr/bin/env python3
"""测试持仓管理 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api_server.main import app
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_NAME,
    TEST_QUANTITY,
    TEST_PRICE_COST,
    PAGE_SIZE_DEFAULT,
    assert_success_response,
    assert_error_response,
    assert_pagination_response
)


class TestPortfolioAPI:
    """持仓管理 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    # ========== 账户汇总测试 ==========
    def test_get_account_summary_success(self, client: TestClient) -> None:
        """测试获取账户汇总 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_account_summary.return_value = {
                "success": True,
                "data": {
                    "total_assets": 100000,
                    "total_market_value": 80000,
                    "total_cash": 20000,
                    "total_profit": 10000,
                    "total_profit_rate": 0.111,
                    "position_count": 5
                },
                "message": "账户汇总获取成功"
            }

            response = client.get("/api/v1/portfolio/account/summary")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["total_assets"] == 100000
            assert data["data"]["total_market_value"] == 80000
            assert data["data"]["total_cash"] == 20000

    def test_get_account_summary_failed(self, client: TestClient) -> None:
        """测试获取账户汇总 - 失败"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_account_summary.return_value = {
                "success": False,
                "message": "获取失败"
            }

            response = client.get("/api/v1/portfolio/account/summary")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 持仓列表测试 ==========
    def test_get_positions_success(self, client: TestClient) -> None:
        """测试获取持仓列表 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {
                        "symbol": TEST_STOCK_CODE,
                        "name": TEST_STOCK_NAME,
                        "quantity": TEST_QUANTITY,
                        "avg_cost": TEST_PRICE_COST,
                        "current_price": 1600,
                        "market_value": 160000,
                        "profit": 10000,
                        "profit_rate": 0.0667
                    }
                ],
                "total": 5,
                "page": 1,
                "page_size": PAGE_SIZE_DEFAULT,
                "total_pages": 1,
                "message": "持仓列表获取成功"
            }

            response = client.get(f"/api/v1/portfolio/positions?page=1&page_size={PAGE_SIZE_DEFAULT}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert_pagination_response(data, expected_total=5, expected_page=1)
            assert len(data["data"]["positions"]) == 1
            assert data["data"]["positions"][0]["symbol"] == TEST_STOCK_CODE

    def test_get_positions_pagination(self, client: TestClient) -> None:
        """测试获取持仓列表 - 分页"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_all_positions.return_value = {
                "success": True,
                "data": [{"symbol": TEST_STOCK_CODE}] * 10,
                "total": 50,
                "page": 2,
                "page_size": 10,
                "total_pages": 5
            }

            response = client.get("/api/v1/portfolio/positions?page=2&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 10
            assert data["data"]["total"] == 50

    def test_get_positions_boundary(self, client: TestClient) -> None:
        """测试获取持仓列表 - 边界值"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_all_positions.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "page": 1,
                "page_size": 1,
                "total_pages": 0
            }

            response = client.get("/api/v1/portfolio/positions?page_size=1")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 0

    # ========== 单只股票持仓测试 ==========
    def test_get_position_success(self, client: TestClient) -> None:
        """测试获取单只股票持仓 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_position.return_value = {
                "success": True,
                "data": {
                    "symbol": TEST_STOCK_CODE,
                    "name": TEST_STOCK_NAME,
                    "quantity": TEST_QUANTITY,
                    "avg_cost": TEST_PRICE_COST,
                    "current_price": 1600,
                    "market_value": 160000,
                    "profit": 10000,
                    "profit_rate": 0.0667
                },
                "message": "持仓信息获取成功"
            }

            response = client.get(f"/api/v1/portfolio/positions/{TEST_STOCK_CODE}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == TEST_STOCK_CODE
            assert data["data"]["profit"] == 10000

    def test_get_position_not_found(self, client: TestClient) -> None:
        """测试获取单只股票持仓 - 未找到"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_position.return_value = {
                "success": False,
                "message": "持仓不存在"
            }

            response = client.get("/api/v1/portfolio/positions/000000")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False

    # ========== 买入股票测试 ==========
    def test_buy_stock_success(self, client: TestClient) -> None:
        """测试买入股票 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.record_buy.return_value = {
                "success": True,
                "data": {
                    "symbol": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY,
                    "price": TEST_PRICE_COST,
                    "amount": 150000,
                    "transaction_date": "2024-03-15",
                    "transaction_id": "txn_123"
                },
                "message": "买入成功"
            }

            response = client.post(
                "/api/v1/portfolio/trade/buy",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY,
                    "price": TEST_PRICE_COST,
                    "transaction_date": "2024-03-15"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == TEST_STOCK_CODE
            assert data["data"]["amount"] == 150000

    def test_buy_stock_failed(self, client: TestClient) -> None:
        """测试买入股票 - 失败"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.record_buy.return_value = {
                "success": False,
                "message": "余额不足"
            }

            response = client.post(
                "/api/v1/portfolio/trade/buy",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY,
                    "price": TEST_PRICE_COST,
                    "transaction_date": "2024-03-15"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    # ========== 卖出股票测试 ==========
    def test_sell_stock_success(self, client: TestClient) -> None:
        """测试卖出股票 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.record_sell.return_value = {
                "success": True,
                "data": {
                    "symbol": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY // 2,
                    "price": 1600,
                    "amount": 80000,
                    "transaction_date": "2024-03-15",
                    "transaction_id": "txn_456"
                },
                "message": "卖出成功"
            }

            response = client.post(
                "/api/v1/portfolio/trade/sell",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY // 2,
                    "price": 1600,
                    "transaction_date": "2024-03-15"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["amount"] == 80000

    # ========== 现金管理测试 ==========
    def test_add_cash_success(self, client: TestClient) -> None:
        """测试充值 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.set_cash_balance.return_value = {
                "success": True,
                "message": "充值成功"
            }

            response = client.post(
                "/api/v1/portfolio/account/cash/add",
                json={"amount": 50000}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_cash_balance_success(self, client: TestClient) -> None:
        """测试获取现金余额 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_cash_balance.return_value = {
                "success": True,
                "data": {"cash_balance": 100000},
                "message": "现金余额获取成功"
            }

            response = client.get("/api/v1/portfolio/account/cash")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["cash_balance"] == 100000

    # ========== 交易历史测试 ==========
    def test_get_transactions_success(self, client: TestClient) -> None:
        """测试获取交易历史 - 成功"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {
                        "symbol": TEST_STOCK_CODE,
                        "type": "buy",
                        "quantity": TEST_QUANTITY,
                        "price": TEST_PRICE_COST,
                        "amount": 150000,
                        "transaction_date": "2024-03-15"
                    }
                ],
                "total": 10,
                "page": 1,
                "page_size": PAGE_SIZE_DEFAULT,
                "total_pages": 1,
                "message": "交易历史获取成功"
            }

            response = client.get(f"/api/v1/portfolio/transactions?page=1&page_size={PAGE_SIZE_DEFAULT}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert_pagination_response(data, expected_total=10, expected_page=1)
            assert len(data["data"]["transactions"]) == 1

    def test_get_transactions_with_filter(self, client: TestClient) -> None:
        """测试获取交易历史 - 带筛选条件"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "page": 1,
                "page_size": PAGE_SIZE_DEFAULT,
                "total_pages": 0
            }

            response = client.get(
                "/api/v1/portfolio/transactions"
                f"?stock_code={TEST_STOCK_CODE}&start_date=2024-01-01&end_date=2024-12-31"
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_transactions_pagination(self, client: TestClient) -> None:
        """测试获取交易历史 - 分页"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_transaction_history.return_value = {
                "success": True,
                "data": [{"symbol": TEST_STOCK_CODE}] * 15,
                "total": 100,
                "page": 3,
                "page_size": 15,
                "total_pages": 7
            }

            response = client.get(
                "/api/v1/portfolio/transactions?page=3&page_size=15"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 3
            assert data["data"]["page_size"] == 15

    # ========== 异常测试 ==========
    def test_buy_stock_exception(self, client: TestClient) -> None:
        """测试买入股票 - 异常"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.record_buy.side_effect = Exception("Transaction error")

            response = client.post(
                "/api/v1/portfolio/trade/buy",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY,
                    "price": TEST_PRICE_COST,
                    "transaction_date": "2024-03-15"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_positions_exception(self, client: TestClient) -> None:
        """测试获取持仓列表 - 异常"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.get_all_positions.side_effect = Exception("Database error")

            response = client.get(f"/api/v1/portfolio/positions?page=1&page_size={PAGE_SIZE_DEFAULT}")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
