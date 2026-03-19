#!/usr/bin/env python3
"""测试持仓管理服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

from api_server.services.portfolio_service import PortfolioService


class TestPortfolioService:
    """持仓管理服务层测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return PortfolioService(db_url="postgresql://test:test@localhost/test_db")

    def test_get_account_summary_success(self, service):
        """测试获取账户汇总成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_summary = Mock()
            mock_summary.total_market_value = 100000.0
            mock_summary.stock_market_value = 80000.0
            mock_summary.cash = 20000.0
            mock_summary.total_floating_pl = 5000.0
            mock_summary.total_realized_pl = 3000.0
            mock_summary.positions_count = 5
            mock_account_service.get_account_summary.return_value = mock_summary
            mock_get_services.return_value = (Mock(), Mock(), Mock(), mock_account_service, Mock())

            result = service.get_account_summary()

            assert result["success"] is True
            assert result["data"]["total_market_value"] == 100000.0
            assert result["data"]["stock_market_value"] == 80000.0
            assert result["data"]["cash"] == 20000.0
            assert result["data"]["positions_count"] == 5

    def test_get_account_summary_failure(self, service):
        """测试获取账户汇总失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_account_summary()

            assert result["success"] is False
            assert "error" in result

    def test_get_position_success(self, service):
        """测试获取持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = Mock()
            mock_position.symbol = "600519"
            mock_position.quantity = 100
            mock_position.cost_price = 1500.0
            mock_position.current_price = 1700.0
            mock_position.market_value = 170000.0
            mock_position.cost_value = 150000.0
            mock_position.floating_pl = 20000.0
            mock_position.position_ratio = 0.0
            mock_position.last_updated = datetime.now()
            mock_position_service.get_position.return_value = mock_position
            mock_get_services.return_value = (Mock(), mock_position_service, Mock(), Mock(), Mock())

            result = service.get_position(symbol="600519")

            assert result["success"] is True
            assert result["data"]["symbol"] == "600519"
            assert result["data"]["quantity"] == 100
            assert result["data"]["floating_pl"] == 20000.0

    def test_get_position_not_found(self, service):
        """测试获取持仓 - 未找到"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position_service.get_position.return_value = None
            mock_get_services.return_value = (Mock(), mock_position_service, Mock(), Mock(), Mock())

            result = service.get_position(symbol="600000")

            assert result["success"] is False
            assert "not found" in result["message"]

    def test_get_all_positions_success(self, service):
        """测试获取所有持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = Mock()
            mock_position.symbol = "600519"
            mock_position.quantity = 100
            mock_position.cost_price = 1500.0
            mock_position.current_price = 1700.0
            mock_position.market_value = 170000.0
            mock_position.cost_value = 150000.0
            mock_position.floating_pl = 20000.0
            mock_position.position_ratio = 0.0
            mock_position.last_updated = datetime.now()
            mock_position_service.get_all_positions.return_value = [mock_position]
            mock_get_services.return_value = (Mock(), mock_position_service, Mock(), Mock(), Mock())

            result = service.get_all_positions(page=1, page_size=20)

            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["total"] == 1
            assert result["page"] == 1

    def test_add_position_success(self, service):
        """测试新增持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = Mock()
            mock_position.symbol = "600519"
            mock_position.quantity = 100
            mock_position.cost_price = 1500.0
            mock_position.current_price = 1700.0
            mock_position.market_value = 170000.0
            mock_position.cost_value = 150000.0
            mock_position.floating_pl = 20000.0
            mock_position.last_updated = datetime.now()
            mock_position_service.add_position.return_value = mock_position
            mock_get_services.return_value = (Mock(), mock_position_service, Mock(), Mock(), Mock())

            result = service.add_position(
                symbol="600519",
                quantity=100,
                cost_price=1500.0,
                current_price=1700.0
            )

            assert result["success"] is True
            assert result["data"]["symbol"] == "600519"
            assert result["data"]["quantity"] == 100

    def test_add_position_failure(self, service):
        """测试新增持仓失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.add_position(
                symbol="600519",
                quantity=100,
                cost_price=1500.0
            )

            assert result["success"] is False
            assert "error" in result

    def test_update_position_success(self, service):
        """测试更新持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = Mock()
            mock_position.symbol = "600519"
            mock_position.quantity = 150
            mock_position.cost_price = 1500.0
            mock_position.current_price = 1750.0
            mock_position.market_value = 262500.0
            mock_position.cost_value = 225000.0
            mock_position.floating_pl = 37500.0
            mock_position.last_updated = datetime.now()
            mock_position_service.update_position.return_value = mock_position
            mock_get_services.return_value = (Mock(), mock_position_service, Mock(), Mock(), Mock())

            result = service.update_position(
                symbol="600519",
                quantity=150,
                current_price=1750.0
            )

            assert result["success"] is True
            assert result["data"]["quantity"] == 150
            assert result["data"]["current_price"] == 1750.0

    def test_record_buy_success(self, service):
        """测试记录买入交易成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = Mock()
            mock_transaction.symbol = "600519"
            mock_transaction.transaction_type = "buy"
            mock_transaction.quantity = 100
            mock_transaction.price = 1700.0
            mock_transaction.amount = 169800.0  # 扣除手续费后
            mock_transaction.fee = 200.0
            mock_transaction.transaction_date = datetime.now()
            mock_transaction_service.record_buy.return_value = mock_transaction
            mock_get_services.return_value = (Mock(), Mock(), mock_transaction_service, Mock(), Mock())

            result = service.record_buy(
                symbol="600519",
                quantity=100,
                price=1700.0,
                transaction_date="2024-03-15T10:30:00"
            )

            assert result["success"] is True
            assert result["data"]["transaction_type"] == "buy"
            assert result["data"]["quantity"] == 100
            assert result["data"]["price"] == 1700.0

    def test_record_sell_success(self, service):
        """测试记录卖出交易成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = Mock()
            mock_transaction.symbol = "600519"
            mock_transaction.transaction_type = "sell"
            mock_transaction.quantity = 50
            mock_transaction.price = 1750.0
            mock_transaction.amount = 87300.0  # 扣除手续费后
            mock_transaction.fee = 200.0
            mock_transaction.transaction_date = datetime.now()
            mock_transaction_service.record_sell.return_value = mock_transaction
            mock_get_services.return_value = (Mock(), Mock(), mock_transaction_service, Mock(), Mock())

            result = service.record_sell(
                symbol="600519",
                quantity=50,
                price=1750.0,
                transaction_date="2024-03-15T14:30:00"
            )

            assert result["success"] is True
            assert result["data"]["transaction_type"] == "sell"
            assert result["data"]["quantity"] == 50

    def test_get_transaction_history_success(self, service):
        """测试获取交易历史成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = Mock()
            mock_transaction.symbol = "600519"
            mock_transaction.transaction_type = "buy"
            mock_transaction.quantity = 100
            mock_transaction.price = 1700.0
            mock_transaction.amount = 169800.0
            mock_transaction.fee = 200.0
            mock_transaction.transaction_date = datetime(2024, 3, 15, 10, 30, 0)
            mock_transaction_service.get_transaction_history.return_value = [mock_transaction]
            mock_get_services.return_value = (Mock(), Mock(), mock_transaction_service, Mock(), Mock())

            result = service.get_transaction_history(
                symbol="600519",
                start_date="2024-03-01T00:00:00",
                end_date="2024-03-31T23:59:59",
                page=1,
                page_size=20
            )

            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["total"] == 1

    def test_get_cash_balance_success(self, service):
        """测试获取现金余额成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_account_service.get_cash_balance.return_value = 50000.0
            mock_get_services.return_value = (Mock(), Mock(), Mock(), mock_account_service, Mock())

            result = service.get_cash_balance()

            assert result["success"] is True
            assert result["data"]["cash"] == 50000.0

    def test_set_cash_balance_success(self, service):
        """测试设置现金余额成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_get_services.return_value = (Mock(), Mock(), Mock(), mock_account_service, Mock())

            result = service.set_cash_balance(amount=100000.0)

            assert result["success"] is True
            assert "set to 100000.0" in result["message"]
