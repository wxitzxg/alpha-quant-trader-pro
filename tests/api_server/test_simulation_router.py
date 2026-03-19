#!/usr/bin/env python3
"""测试模拟交易 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestSimulationAPI:
    """模拟交易 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    @pytest.fixture
    def mock_service(self):
        """创建模拟服务"""
        with patch('api_server.routers.simulation.SIMULATION_SERVICE') as mock:
            yield mock

    # ========== 账户管理测试 ==========
    def test_create_simulation_account_success(self, client, mock_service):
        """测试创建模拟账户 - 成功"""
        mock_account = MagicMock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "account_name": "测试账户",
            "initial_capital": 100000.0,
            "commission_rate": 0.003,
            "created_at": datetime.now().isoformat()
        }
        mock_service.create_account.return_value = mock_account

        response = client.post(
            "/api/v1/simulation/account",
            json={
                "account_name": "测试账户",
                "initial_capital": 100000,
                "commission_rate": 0.003
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["account_name"] == "测试账户"
        assert data["data"]["initial_capital"] == 100000.0

    def test_create_simulation_account_invalid_capital(self, client, mock_service):
        """测试创建模拟账户 - 无效资金"""
        mock_service.create_account.side_effect = ValueError("Initial capital must be positive")

        response = client.post(
            "/api/v1/simulation/account",
            json={
                "account_name": "测试账户",
                "initial_capital": -10000,
                "commission_rate": 0.003
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    # ========== 获取账户信息测试 ==========
    def test_get_simulation_account_success(self, client, mock_service):
        """测试获取模拟账户 - 成功"""
        mock_account = MagicMock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "account_name": "测试账户",
            "current_balance": 95000.0,
            "total_profit": -5000.0,
            "profit_rate": -0.05,
            "positions_count": 2
        }
        mock_service.get_account.return_value = mock_account
        mock_service.market_prices = {}

        response = client.get("/api/v1/simulation/account/acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["account_id"] == "acc_123"
        assert data["data"]["current_balance"] == 95000.0

    def test_get_simulation_account_not_found(self, client, mock_service):
        """测试获取模拟账户 - 未找到"""
        mock_service.get_account.side_effect = ValueError("Account not found")

        response = client.get("/api/v1/simulation/account/invalid_id")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    # ========== 列表账户测试 ==========
    def test_list_simulation_accounts_success(self, client, mock_service):
        """测试获取所有账户 - 成功"""
        mock_account1 = MagicMock()
        mock_account1.to_dict.return_value = {
            "account_id": "acc_1",
            "account_name": "账户1",
            "current_balance": 100000.0
        }
        mock_account2 = MagicMock()
        mock_account2.to_dict.return_value = {
            "account_id": "acc_2",
            "account_name": "账户2",
            "current_balance": 150000.0
        }
        mock_service.list_accounts.return_value = [mock_account1, mock_account2]
        mock_service.market_prices = {}

        response = client.get("/api/v1/simulation/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["account_name"] == "账户1"

    def test_list_simulation_accounts_empty(self, client, mock_service):
        """测试获取所有账户 - 空列表"""
        mock_service.list_accounts.return_value = []
        mock_service.market_prices = {}

        response = client.get("/api/v1/simulation/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    # ========== 买入股票测试 ==========
    def test_buy_stock_success(self, client, mock_service):
        """测试买入股票 - 成功"""
        mock_trade = MagicMock()
        mock_trade.trade_id = "trade_123"
        mock_trade.amount = 10000.0
        mock_trade.commission = 30.0
        mock_trade.timestamp = datetime.now()

        mock_account = MagicMock()
        mock_account.current_balance = 90000.0

        mock_service.buy.return_value = mock_trade
        mock_service.get_account.return_value = mock_account

        response = client.post(
            "/api/v1/simulation/buy",
            json={
                "account_id": "acc_123",
                "symbol": "600519",
                "price": 100.0,
                "quantity": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["action"] == "buy"
        assert data["data"]["symbol"] == "600519"
        assert data["data"]["total_cost"] == 10030.0
        assert data["data"]["account_balance"] == 90000.0

    def test_buy_stock_insufficient_balance(self, client, mock_service):
        """测试买入股票 - 余额不足"""
        mock_service.buy.side_effect = ValueError("Insufficient balance")

        response = client.post(
            "/api/v1/simulation/buy",
            json={
                "account_id": "acc_123",
                "symbol": "600519",
                "price": 1000.0,
                "quantity": 1000
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    # ========== 卖出股票测试 ==========
    def test_sell_stock_success(self, client, mock_service):
        """测试卖出股票 - 成功"""
        mock_trade = MagicMock()
        mock_trade.trade_id = "trade_456"
        mock_trade.amount = 10000.0
        mock_trade.commission = 30.0
        mock_trade.pnl = 500.0
        mock_trade.timestamp = datetime.now()

        mock_account = MagicMock()
        mock_account.current_balance = 105000.0

        mock_service.sell.return_value = mock_trade
        mock_service.get_account.return_value = mock_account

        response = client.post(
            "/api/v1/simulation/sell",
            json={
                "account_id": "acc_123",
                "symbol": "600519",
                "price": 110.0,
                "quantity": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["action"] == "sell"
        assert data["data"]["pnl"] == 500.0
        assert data["data"]["total_revenue"] == 9970.0

    # ========== 持仓管理测试 ==========
    def test_get_positions_success(self, client, mock_service):
        """测试获取持仓列表 - 成功"""
        mock_service.get_positions.return_value = {
            "positions": [
                {
                    "symbol": "600519",
                    "quantity": 100,
                    "cost_price": 100.0,
                    "current_price": 105.0,
                    "market_value": 10500.0,
                    "profit": 500.0,
                    "profit_rate": 0.05
                }
            ],
            "total_market_value": 10500.0,
            "total_profit": 500.0
        }

        response = client.get("/api/v1/simulation/positions/acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "positions" in data["data"]
        assert len(data["data"]["positions"]) == 1
        assert data["data"]["positions"][0]["symbol"] == "600519"

    def test_get_positions_empty(self, client, mock_service):
        """测试获取持仓列表 - 空持仓"""
        mock_service.get_positions.return_value = {
            "positions": [],
            "total_market_value": 0.0,
            "total_profit": 0.0
        }

        response = client.get("/api/v1/simulation/positions/acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["positions"]) == 0

    # ========== 交易历史测试 ==========
    def test_get_trades_success(self, client, mock_service):
        """测试获取交易历史 - 成功"""
        mock_service.get_trades.return_value = {
            "trades": [
                {
                    "trade_id": "trade_1",
                    "symbol": "600519",
                    "action": "buy",
                    "price": 100.0,
                    "quantity": 100,
                    "amount": 10000.0,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "total_count": 1,
            "limit": 20
        }

        response = client.get("/api/v1/simulation/trades/acc_123?limit=20")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "trades" in data["data"]
        assert len(data["data"]["trades"]) == 1

    def test_get_trades_with_limit(self, client, mock_service):
        """测试获取交易历史 - 带限制"""
        mock_service.get_trades.return_value = {
            "trades": [],
            "total_count": 0,
            "limit": 5
        }

        response = client.get("/api/v1/simulation/trades/acc_123?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["limit"] == 5

    # ========== 删除账户测试 ==========
    def test_delete_simulation_account_success(self, client, mock_service):
        """测试删除模拟账户 - 成功"""
        response = client.delete("/api/v1/simulation/account/acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["account_id"] == "acc_123"
        assert "deleted_at" in data["data"]

    # ========== 边界测试 ==========
    def test_create_account_with_minimum_capital(self, client, mock_service):
        """测试创建账户 - 最小资金"""
        mock_account = MagicMock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_min",
            "account_name": "最小资金账户",
            "initial_capital": 1.0,
            "commission_rate": 0.001
        }
        mock_service.create_account.return_value = mock_account

        response = client.post(
            "/api/v1/simulation/account",
            json={
                "account_name": "最小资金账户",
                "initial_capital": 1.0,
                "commission_rate": 0.001
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["initial_capital"] == 1.0

    # ========== 异常测试 ==========
    def test_get_account_with_exception(self, client, mock_service):
        """测试获取账户 - 异常"""
        mock_service.get_account.side_effect = Exception("Database error")

        response = client.get("/api/v1/simulation/account/acc_123")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    def test_buy_stock_with_exception(self, client, mock_service):
        """测试买入股票 - 异常"""
        mock_service.buy.side_effect = Exception("Trade execution error")

        response = client.post(
            "/api/v1/simulation/buy",
            json={
                "account_id": "acc_123",
                "symbol": "600519",
                "price": 100.0,
                "quantity": 100
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
