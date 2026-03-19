#!/usr/bin/env python3
"""测试股票市场服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api_server.services.stock_market_service import StockMarketService


class TestStockMarketService:
    """股票市场服务层测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return StockMarketService(db_url="postgresql://test:test@localhost/test_db")

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session

    def test_sync_all_stocks_success(self, service):
        """测试同步股票列表成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            # 模拟服务
            mock_session = Mock()
            mock_stock_service = Mock()
            mock_stock_service.sync_all_stocks.return_value = 100
            mock_get_services.return_value = (mock_session, mock_stock_service, Mock())

            result = service.sync_all_stocks(force_update=False)

            assert result["success"] is True
            assert result["count"] == 100
            assert "Successfully synced 100 stocks" in result["message"]

    def test_sync_all_stocks_failure(self, service):
        """测试同步股票列表失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.sync_all_stocks(force_update=False)

            assert result["success"] is False
            assert "error" in result
            assert "Failed to sync stocks" in result["message"]

    def test_get_stock_list_success(self, service):
        """测试获取股票列表成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            # 模拟股票数据
            mock_stock = Mock()
            mock_stock.ts_code = "600519.SH"
            mock_stock.symbol = "600519"
            mock_stock.name = "贵州茅台"
            mock_stock.industry = "白酒"
            mock_stock.market = "主板"
            mock_stock.list_date = datetime(2001, 8, 27)

            mock_session = Mock()
            mock_stock_service = Mock()
            mock_stock_service.get_active_stocks.return_value = [mock_stock]
            mock_get_services.return_value = (mock_session, mock_stock_service, Mock())

            result = service.get_stock_list(page=1, page_size=20)

            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["data"][0]["symbol"] == "600519"
            assert result["data"][0]["name"] == "贵州茅台"
            assert result["total"] == 1

    def test_get_stock_list_failure(self, service):
        """测试获取股票列表失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_stock_list(page=1, page_size=20)

            assert result["success"] is False
            assert "error" in result

    def test_sync_single_kline_success(self, service):
        """测试同步单只股票K线成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_session = Mock()
            mock_kline_service = Mock()
            mock_kline_service.sync_single_kline.return_value = 120
            mock_get_services.return_value = (mock_session, Mock(), mock_kline_service)

            result = service.sync_single_kline(
                stock_code="600519",
                interval="1d",
                start_date="2024-01-01",
                end_date="2024-03-31",
                force_update=False
            )

            assert result["success"] is True
            assert result["count"] == 120
            assert "Successfully synced 120 klines" in result["message"]

    def test_sync_single_kline_failure(self, service):
        """测试同步单只股票K线失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("API error")

            result = service.sync_single_kline(
                stock_code="600519",
                interval="1d",
                start_date="2024-01-01",
                end_date="2024-03-31",
                force_update=False
            )

            assert result["success"] is False
            assert "error" in result

    def test_get_kline_data_success(self, service):
        """测试获取K线数据成功"""
        with patch.object(service, '_get_services') as mock_get_services:
            # 模拟K线数据
            mock_kline = Mock()
            mock_kline.symbol = "600519"
            mock_kline.date = datetime(2024, 3, 15)
            mock_kline.open = 1700.0
            mock_kline.high = 1720.0
            mock_kline.low = 1690.0
            mock_kline.close = 1710.0
            mock_kline.volume = 100000
            mock_kline.amount = 171000000

            mock_session = Mock()
            mock_kline_service = Mock()
            mock_kline_service.query_klines.return_value = [mock_kline]
            mock_get_services.return_value = (mock_session, Mock(), mock_kline_service)

            result = service.get_kline_data(
                stock_code="600519",
                interval="1d",
                start_date="2024-01-01",
                end_date="2024-03-31",
                limit=100
            )

            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["data"][0]["symbol"] == "600519"
            assert result["data"][0]["close"] == 1710.0
            assert result["total"] == 1

    def test_get_kline_data_failure(self, service):
        """测试获取K线数据失败"""
        with patch.object(service, '_get_services') as mock_get_services:
            mock_get_services.side_effect = Exception("Database error")

            result = service.get_kline_data(
                stock_code="600519",
                interval="1d",
                start_date="2024-01-01",
                end_date="2024-03-31",
                limit=100
            )

            assert result["success"] is False
            assert "error" in result

    def test_get_sync_status_success(self, service):
        """测试获取同步状态成功"""
        with patch.object(service.db_manager, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = Mock(return_value=False)

            # 模拟同步记录
            mock_sync_record = Mock()
            mock_sync_record.sync_type = "stocks"
            mock_sync_record.status = "completed"
            mock_sync_record.records_count = 5000
            mock_sync_record.start_time = datetime(2024, 3, 15, 10, 0, 0)
            mock_sync_record.end_time = datetime(2024, 3, 15, 10, 5, 0)
            mock_sync_record.error_message = None

            mock_sync_repo = Mock()
            mock_sync_repo.get_latest_by_type.return_value = mock_sync_record
            with patch('api_server.services.stock_market_service.SyncRecordRepository', return_value=mock_sync_repo):
                result = service.get_sync_status(sync_type="stocks")

                assert result["success"] is True
                assert result["data"]["sync_type"] == "stocks"
                assert result["data"]["status"] == "completed"
                assert result["data"]["records_count"] == 5000

    def test_get_sync_status_no_records(self, service):
        """测试获取同步状态 - 无记录"""
        with patch.object(service.db_manager, 'get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = Mock(return_value=False)

            mock_sync_repo = Mock()
            mock_sync_repo.get_latest_by_type.return_value = None
            with patch('api_server.services.stock_market_service.SyncRecordRepository', return_value=mock_sync_repo):
                result = service.get_sync_status(sync_type="stocks")

                assert result["success"] is True
                assert result["data"] is None
                assert "No sync records found" in result["message"]
