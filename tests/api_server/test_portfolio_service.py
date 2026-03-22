#!/usr/bin/env python3
"""测试持仓管理服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from api_server.services.portfolio_service import PortfolioService
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_QUANTITY,
    TEST_PRICE_COST,
    TEST_PRICE_CLOSE,
    TEST_QUANTITY_2,
    PAGE_SIZE_DEFAULT,
    create_mock_summary,
    create_mock_position,
    create_mock_transaction,
    assert_success_response,
    assert_error_response,
    assert_pagination_response,
    assert_position_data
)


class TestPortfolioService:
    """持仓管理服务层测试"""

    @pytest.fixture
    def service(self) -> PortfolioService:
        """创建服务实例"""
        return PortfolioService(db_url="postgresql://test:test@localhost/test_db")

    @pytest.fixture
    def mock_services_tuple(
        self,
        position_service: Mock = None,
        transaction_service: Mock = None,
        account_service: Mock = None
    ) -> tuple:
        """创建服务元组的 fixture"""
        return (
            Mock(),  # kline_service
            position_service or Mock(),
            transaction_service or Mock(),
            account_service or Mock(),
            Mock()  # stock_service
        )

    def test_get_account_summary_success(self, service: PortfolioService) -> None:
        """测试获取账户汇总成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_summary = create_mock_summary()
            mock_account_service.get_account_summary.return_value = mock_summary
            mock_get_services.return_value = (
                Mock(), Mock(), Mock(), mock_account_service, Mock()
            )

            result = service.get_account_summary()

            assert_success_response(result)
            assert result["data"]["total_market_value"] == 100000.0
            assert result["data"]["stock_market_value"] == 80000.0
            assert result["data"]["cash"] == 20000.0
            assert result["data"]["total_floating_pl"] == 5000.0
            assert result["data"]["total_realized_pl"] == 3000.0
            assert result["data"]["positions_count"] == 5

    def test_get_account_summary_failure(self, service: PortfolioService) -> None:
        """测试获取账户汇总失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_account_summary()

            assert_error_response(result, "database")
            assert result["success"] is False

    def test_get_position_success(self, service: PortfolioService) -> None:
        """测试获取持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = create_mock_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY,
                cost_price=TEST_PRICE_COST,
                current_price=TEST_PRICE_CLOSE
            )
            mock_position_service.get_position.return_value = mock_position
            mock_get_services.return_value = (
                Mock(), mock_position_service, Mock(), Mock(), Mock()
            )

            result = service.get_position(symbol=TEST_STOCK_CODE)

            assert_success_response(result)
            assert_position_data(result["data"], expected_symbol=TEST_STOCK_CODE)
            assert result["data"]["quantity"] == TEST_QUANTITY
            assert result["data"]["cost_price"] == TEST_PRICE_COST
            assert result["data"]["current_price"] == TEST_PRICE_CLOSE
            assert result["data"]["floating_pl"] == 20000.0

    def test_get_position_not_found(self, service: PortfolioService) -> None:
        """测试获取持仓 - 未找到"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position_service.get_position.return_value = None
            mock_get_services.return_value = (
                Mock(), mock_position_service, Mock(), Mock(), Mock()
            )

            result = service.get_position(symbol="600000")

            assert result["success"] is False
            assert result["message"] == "Position not found for symbol: 600000"

    def test_get_all_positions_success(self, service: PortfolioService) -> None:
        """测试获取所有持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = create_mock_position()
            mock_position_service.get_all_positions.return_value = [mock_position]
            mock_get_services.return_value = (
                Mock(), mock_position_service, Mock(), Mock(), Mock()
            )

            result = service.get_all_positions(page=1, page_size=PAGE_SIZE_DEFAULT)

            assert_success_response(result)
            assert_pagination_response(result, expected_total=1, expected_page=1)
            assert len(result["data"]) == 1
            assert_position_data(result["data"][0])

    def test_add_position_success(self, service: PortfolioService) -> None:
        """测试新增持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = create_mock_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY,
                cost_price=TEST_PRICE_COST,
                current_price=TEST_PRICE_CLOSE
            )
            mock_position_service.add_position.return_value = mock_position
            mock_get_services.return_value = (
                Mock(), mock_position_service, Mock(), Mock(), Mock()
            )

            result = service.add_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY,
                cost_price=TEST_PRICE_COST,
                current_price=TEST_PRICE_CLOSE
            )

            assert_success_response(result)
            assert_position_data(result["data"], expected_symbol=TEST_STOCK_CODE)
            assert result["data"]["quantity"] == TEST_QUANTITY

    def test_add_position_failure(self, service: PortfolioService) -> None:
        """测试新增持仓失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.add_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY,
                cost_price=TEST_PRICE_COST
            )

            assert_error_response(result, "database")
            assert result["success"] is False

    def test_update_position_success(self, service: PortfolioService) -> None:
        """测试更新持仓成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_position_service = Mock()
            mock_position = create_mock_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY + 50,
                cost_price=TEST_PRICE_COST,
                current_price=TEST_PRICE_CLOSE + 40.0
            )
            mock_position_service.update_position.return_value = mock_position
            mock_get_services.return_value = (
                Mock(), mock_position_service, Mock(), Mock(), Mock()
            )

            result = service.update_position(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY + 50,
                current_price=TEST_PRICE_CLOSE + 40.0
            )

            assert_success_response(result)
            assert result["data"]["quantity"] == TEST_QUANTITY + 50
            assert result["data"]["current_price"] == TEST_PRICE_CLOSE + 40.0

    def test_record_buy_success(self, service: PortfolioService) -> None:
        """测试记录买入交易成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = create_mock_transaction(
                symbol=TEST_STOCK_CODE,
                transaction_type="buy",
                quantity=TEST_QUANTITY,
                price=TEST_PRICE_CLOSE
            )
            mock_transaction_service.record_buy.return_value = mock_transaction
            mock_get_services.return_value = (
                Mock(), Mock(), mock_transaction_service, Mock(), Mock()
            )

            result = service.record_buy(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY,
                price=TEST_PRICE_CLOSE,
                transaction_date="2024-03-15T10:30:00"
            )

            assert_success_response(result)
            assert result["data"]["transaction_type"] == "buy"
            assert result["data"]["quantity"] == TEST_QUANTITY
            assert result["data"]["price"] == TEST_PRICE_CLOSE

    def test_record_sell_success(self, service: PortfolioService) -> None:
        """测试记录卖出交易成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = create_mock_transaction(
                symbol=TEST_STOCK_CODE,
                transaction_type="sell",
                quantity=TEST_QUANTITY_2,
                price=TEST_PRICE_CLOSE + 40.0
            )
            mock_transaction_service.record_sell.return_value = mock_transaction
            mock_get_services.return_value = (
                Mock(), Mock(), mock_transaction_service, Mock(), Mock()
            )

            result = service.record_sell(
                symbol=TEST_STOCK_CODE,
                quantity=TEST_QUANTITY_2,
                price=TEST_PRICE_CLOSE + 40.0,
                transaction_date="2024-03-15T14:30:00"
            )

            assert_success_response(result)
            assert result["data"]["transaction_type"] == "sell"
            assert result["data"]["quantity"] == TEST_QUANTITY_2

    def test_get_transaction_history_success(self, service: PortfolioService) -> None:
        """测试获取交易历史成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_transaction_service = Mock()
            mock_transaction = create_mock_transaction(
                symbol=TEST_STOCK_CODE,
                transaction_type="buy",
                quantity=TEST_QUANTITY,
                price=TEST_PRICE_CLOSE
            )
            mock_transaction_service.get_transaction_history.return_value = [mock_transaction]
            mock_get_services.return_value = (
                Mock(), Mock(), mock_transaction_service, Mock(), Mock()
            )

            result = service.get_transaction_history(
                symbol=TEST_STOCK_CODE,
                start_date="2024-03-01T00:00:00",
                end_date="2024-03-31T23:59:59",
                page=1,
                page_size=PAGE_SIZE_DEFAULT
            )

            assert_success_response(result)
            assert_pagination_response(result, expected_total=1, expected_page=1)
            assert len(result["data"]) == 1
            assert result["data"][0]["symbol"] == TEST_STOCK_CODE

    def test_get_cash_balance_success(self, service: PortfolioService) -> None:
        """测试获取现金余额成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_account_service.get_cash_balance.return_value = 50000.0
            mock_get_services.return_value = (
                Mock(), Mock(), Mock(), mock_account_service, Mock()
            )

            result = service.get_cash_balance()

            assert_success_response(result)
            assert result["data"]["cash"] == 50000.0

    def test_set_cash_balance_success(self, service: PortfolioService) -> None:
        """测试设置现金余额成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_account_service = Mock()
            mock_get_services.return_value = (
                Mock(), Mock(), Mock(), mock_account_service, Mock()
            )

            result = service.set_cash_balance(amount=100000.0)

            assert_success_response(result)
            assert "set to 100000.0" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
