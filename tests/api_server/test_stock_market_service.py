#!/usr/bin/env python3
"""测试股票市场服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from api_server.services.stock_market_service import StockMarketService
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_NAME,
    TEST_START_DATE,
    TEST_END_DATE,
    PAGE_SIZE_DEFAULT,
    create_mock_stock,
    create_mock_kline,
    create_mock_sync_record,
    assert_success_response,
    assert_error_response,
    assert_pagination_response,
    assert_stock_data,
    assert_kline_data
)


class TestStockMarketService:
    """股票市场服务层测试"""

    @pytest.fixture
    def service(self) -> StockMarketService:
        """创建服务实例"""
        return StockMarketService(db_url="postgresql://test:test@localhost/test_db")

    @pytest.fixture
    def mock_session(self) -> Mock:
        """模拟数据库会话"""
        session = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session

    def test_sync_all_stocks_success(self, service: StockMarketService) -> None:
        """测试同步股票列表成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_session = Mock()
            mock_stock_service = Mock()
            mock_stock_service.sync_all_stocks.return_value = 100
            mock_get_services.return_value = (mock_session, mock_stock_service, Mock())

            result = service.sync_all_stocks(force_update=False)

            assert_success_response(result)
            assert result["count"] == 100
            assert "Successfully synced 100 stocks" in result["message"]

    def test_sync_all_stocks_failure(self, service: StockMarketService) -> None:
        """测试同步股票列表失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.sync_all_stocks(force_update=False)

            assert_error_response(result, "database")
            assert result["success"] is False
            assert "Failed to sync stocks" in result["message"]

    def test_get_stock_list_success(self, service: StockMarketService) -> None:
        """测试获取股票列表成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_stock = create_mock_stock(
                ts_code="600519.SH",
                symbol=TEST_STOCK_CODE,
                name=TEST_STOCK_NAME
            )

            mock_session = Mock()
            mock_stock_service = Mock()
            mock_stock_service.get_active_stocks.return_value = [mock_stock]
            mock_get_services.return_value = (mock_session, mock_stock_service, Mock())

            result = service.get_stock_list(page=1, page_size=PAGE_SIZE_DEFAULT)

            assert_success_response(result)
            assert_pagination_response(result, expected_total=1, expected_page=1)
            assert len(result["data"]) == 1
            assert_stock_data(result["data"][0], expected_symbol=TEST_STOCK_CODE)
            assert result["data"][0]["name"] == TEST_STOCK_NAME
            assert result["data"][0]["industry"] == "白酒"

    def test_get_stock_list_failure(self, service: StockMarketService) -> None:
        """测试获取股票列表失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_stock_list(page=1, page_size=PAGE_SIZE_DEFAULT)

            assert_error_response(result, "database")
            assert result["success"] is False

    def test_sync_single_kline_success(self, service: StockMarketService) -> None:
        """测试同步单只股票K线成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_session = Mock()
            mock_kline_service = Mock()
            mock_kline_service.sync_single_kline.return_value = 120
            mock_get_services.return_value = (mock_session, Mock(), mock_kline_service)

            result = service.sync_single_kline(
                stock_code=TEST_STOCK_CODE,
                interval="1d",
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                force_update=False
            )

            assert_success_response(result)
            assert result["count"] == 120
            assert "Successfully synced 120 klines" in result["message"]

    def test_sync_single_kline_failure(self, service: StockMarketService) -> None:
        """测试同步单只股票K线失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("API error")

            result = service.sync_single_kline(
                stock_code=TEST_STOCK_CODE,
                interval="1d",
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                force_update=False
            )

            assert_error_response(result, "error")
            assert result["success"] is False

    def test_get_kline_data_success(self, service: StockMarketService) -> None:
        """测试获取K线数据成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_kline = create_mock_kline(
                symbol=TEST_STOCK_CODE,
                date=datetime(2024, 3, 15),
                open_price=1700.0,
                high_price=1720.0,
                low_price=1690.0,
                close_price=1710.0,
                volume=100000
            )

            mock_session = Mock()
            mock_kline_service = Mock()
            mock_kline_service.query_klines.return_value = [mock_kline]
            mock_get_services.return_value = (mock_session, Mock(), mock_kline_service)

            result = service.get_kline_data(
                stock_code=TEST_STOCK_CODE,
                interval="1d",
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                limit=100
            )

            assert_success_response(result)
            assert_pagination_response(result, expected_total=1, expected_page=1)
            assert len(result["data"]) == 1
            assert_kline_data(result["data"][0], expected_symbol=TEST_STOCK_CODE)
            assert result["data"][0]["close"] == 1710.0
            assert result["data"][0]["volume"] == 100000

    def test_get_kline_data_failure(self, service: StockMarketService) -> None:
        """测试获取K线数据失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_kline_data(
                stock_code=TEST_STOCK_CODE,
                interval="1d",
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                limit=100
            )

            assert_error_response(result, "database")
            assert result["success"] is False

    def test_get_sync_status_success(self, service: StockMarketService) -> None:
        """测试获取同步状态成功"""
        with patch.object(service.db_manager, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = Mock(return_value=False)

            mock_sync_record = create_mock_sync_record(
                sync_type="stocks",
                status="completed",
                records_count=5000
            )

            mock_sync_repo = Mock()
            mock_sync_repo.get_latest_by_type.return_value = mock_sync_record
            with patch(
                'api_server.services.stock_market_service.SyncRecordRepository',
                return_value=mock_sync_repo
            ):
                result = service.get_sync_status(sync_type="stocks")

                assert_success_response(result)
                assert result["data"]["sync_type"] == "stocks"
                assert result["data"]["status"] == "completed"
                assert result["data"]["records_count"] == 5000

    def test_get_sync_status_no_records(self, service: StockMarketService) -> None:
        """测试获取同步状态 - 无记录"""
        with patch.object(service.db_manager, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = Mock(return_value=False)

            mock_sync_repo = Mock()
            mock_sync_repo.get_latest_by_type.return_value = None
            with patch(
                'api_server.services.stock_market_service.SyncRecordRepository',
                return_value=mock_sync_repo
            ):
                result = service.get_sync_status(sync_type="stocks")

                assert_success_response(result)
                assert result["data"] is None
                assert "No sync records found" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
