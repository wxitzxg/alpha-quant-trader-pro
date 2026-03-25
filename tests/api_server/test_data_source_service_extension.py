#!/usr/bin/env python3
"""测试数据源服务层扩展功能"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api_server.services.data_source_service import DataSourceService
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_CODE_2,
    TEST_STOCK_NAME,
    assert_success_response,
    assert_error_response
)


# ==================== DataSourceService 扩展方法测试 ====================
class TestDataSourceServiceExtension:
    """DataSourceService 扩展方法测试"""

    def test_get_stock_list_success(self) -> None:
        """测试获取股票列表成功"""
        mock_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "000001", "name": "平安银行", "exchange": "SZ"},
        ]

        with patch('api_server.services.data_source_service.StockListAPI') as MockStockListAPI:
            MockStockListAPI.get.return_value = mock_stocks

            result = DataSourceService.get_stock_list(page=1, page_size=10)

            assert_success_response(result)
            assert result["data"]["total"] == 2
            assert len(result["data"]["stocks"]) == 2
            assert result["data"]["page"] == 1
            assert result["data"]["page_size"] == 10

    def test_get_stock_list_pagination(self) -> None:
        """测试获取股票列表 - 分页"""
        # 生成 30 只股票，格式为 600500-600529
        mock_stocks = [
            {"symbol": f"6005{str(i).zfill(2)}", "name": f"股票{i}"} for i in range(30)
        ]

        with patch('api_server.services.data_source_service.StockListAPI') as MockStockListAPI:
            MockStockListAPI.get.return_value = mock_stocks

            # 第一页
            result1 = DataSourceService.get_stock_list(page=1, page_size=10)
            assert len(result1["data"]["stocks"]) == 10
            assert result1["data"]["stocks"][0]["symbol"] == "600500"

            # 第二页
            result2 = DataSourceService.get_stock_list(page=2, page_size=10)
            assert len(result2["data"]["stocks"]) == 10
            assert result2["data"]["stocks"][0]["symbol"] == "600510"

    def test_get_stock_list_with_exchange_filter(self) -> None:
        """测试获取股票列表 - 按交易所筛选"""
        mock_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "600000", "name": "浦发银行", "exchange": "SH"},
        ]

        with patch('api_server.services.data_source_service.StockListAPI') as MockStockListAPI:
            MockStockListAPI.get.return_value = mock_stocks

            result = DataSourceService.get_stock_list(page=1, page_size=20, exchange="SH")

            assert_success_response(result)
            MockStockListAPI.get.assert_called_once_with(exchange="SH")

    def test_get_stock_list_failure(self) -> None:
        """测试获取股票列表失败"""
        with patch('api_server.services.data_source_service.StockListAPI') as MockStockListAPI:
            MockStockListAPI.get.side_effect = Exception("API Error")

            result = DataSourceService.get_stock_list(page=1, page_size=20)

            assert_error_response(result)
            assert result["success"] is False
            assert "Failed to get stock list" in result["message"]

    def test_get_stock_info_success(self) -> None:
        """测试获取股票详情成功"""
        mock_detail = {
            "symbol": TEST_STOCK_CODE,
            "name": TEST_STOCK_NAME,
            "industry": "白酒",
            "market": "主板"
        }

        with patch('api_server.services.data_source_service.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_detail.return_value = mock_detail

            result = DataSourceService.get_stock_info(TEST_STOCK_CODE)

            assert_success_response(result)
            assert result["data"]["symbol"] == TEST_STOCK_CODE
            assert result["data"]["name"] == TEST_STOCK_NAME

    def test_get_stock_info_not_found(self) -> None:
        """测试获取股票详情 - 未找到"""
        with patch('api_server.services.data_source_service.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_detail.return_value = None

            result = DataSourceService.get_stock_info("INVALID")

            assert_error_response(result)
            assert "not found" in result["message"]

    def test_get_stock_info_failure(self) -> None:
        """测试获取股票详情失败"""
        with patch('api_server.services.data_source_service.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_detail.side_effect = Exception("Network Error")

            result = DataSourceService.get_stock_info(TEST_STOCK_CODE)

            assert_error_response(result)
            assert "Failed to get stock info" in result["message"]

    def test_get_top_list_gain(self) -> None:
        """测试获取涨幅榜"""
        mock_items = [
            {"symbol": "600519", "name": "贵州茅台", "change_pct": 5.0, "current_price": 1700.0},
            {"symbol": "000001", "name": "平安银行", "change_pct": 3.0, "current_price": 15.0},
        ]

        with patch('api_server.services.data_source_service.TopListAPI') as MockTopListAPI:
            MockTopListAPI.get.return_value = mock_items

            result = DataSourceService.get_top_list(type="gain")

            assert_success_response(result)
            assert result["data"]["type"] == "gain"
            assert len(result["data"]["items"]) == 2
            assert result["data"]["total"] == 2

    def test_get_top_list_loss(self) -> None:
        """测试获取跌幅榜"""
        mock_items = [
            {"symbol": "600519", "name": "贵州茅台", "change_pct": -5.0, "current_price": 1600.0},
        ]

        with patch('api_server.services.data_source_service.TopListAPI') as MockTopListAPI:
            MockTopListAPI.get.return_value = mock_items

            result = DataSourceService.get_top_list(type="loss")

            assert_success_response(result)
            assert result["data"]["type"] == "loss"

    def test_get_top_list_with_date(self) -> None:
        """测试获取涨跌排行 - 指定日期"""
        mock_items = []

        with patch('api_server.services.data_source_service.TopListAPI') as MockTopListAPI:
            MockTopListAPI.get.return_value = mock_items

            result = DataSourceService.get_top_list(type="gain", date="2024-03-15")

            assert_success_response(result)
            assert result["data"]["date"] == "2024-03-15"

    def test_get_top_list_failure(self) -> None:
        """测试获取涨跌排行失败"""
        with patch('api_server.services.data_source_service.TopListAPI') as MockTopListAPI:
            MockTopListAPI.get.side_effect = Exception("API Error")

            result = DataSourceService.get_top_list(type="gain")

            assert_error_response(result)
            assert "Failed to get top list" in result["message"]

    def test_get_kline_stats_success(self) -> None:
        """测试获取K线统计成功"""
        mock_stats = {
            "symbol": TEST_STOCK_CODE,
            "period": "1y",
            "total_trading_days": 244,
            "price_range": {"min": 1500.0, "max": 2000.0, "avg": 1750.0},
            "volume_stats": {"min": 100000, "max": 500000, "avg": 200000, "total": 48800000},
            "volatility": 15.5
        }

        with patch('api_server.services.data_source_service.KLineStatsAPI') as MockKLineStatsAPI:
            MockKLineStatsAPI.get.return_value = mock_stats

            result = DataSourceService.get_kline_stats(TEST_STOCK_CODE, period="1y")

            assert_success_response(result)
            assert result["data"]["symbol"] == TEST_STOCK_CODE
            assert result["data"]["period"] == "1y"
            assert result["data"]["total_trading_days"] == 244

    def test_get_kline_stats_different_periods(self) -> None:
        """测试获取K线统计 - 不同周期"""
        mock_stats = {
            "symbol": TEST_STOCK_CODE,
            "period": "1m",
            "total_trading_days": 22
        }

        with patch('api_server.services.data_source_service.KLineStatsAPI') as MockKLineStatsAPI:
            MockKLineStatsAPI.get.return_value = mock_stats

            result = DataSourceService.get_kline_stats(TEST_STOCK_CODE, period="1m")

            assert_success_response(result)
            assert result["data"]["period"] == "1m"

    def test_get_kline_stats_failure(self) -> None:
        """测试获取K线统计失败"""
        with patch('api_server.services.data_source_service.KLineStatsAPI') as MockKLineStatsAPI:
            MockKLineStatsAPI.get.side_effect = Exception("Data Error")

            result = DataSourceService.get_kline_stats(TEST_STOCK_CODE)

            assert_error_response(result)
            assert "Failed to get kline stats" in result["message"]

    def test_get_financial_indicators_success(self) -> None:
        """测试获取财务指标成功"""
        mock_indicators = {
            "roe": 0.15,
            "gross_margin": 0.40,
            "net_margin": 0.20,
            "debt_ratio": 0.30
        }

        with patch('api_server.services.data_source_service.FundamentalsAPI') as MockFundamentalsAPI:
            MockFundamentalsAPI.get_indicators.return_value = mock_indicators

            result = DataSourceService.get_financial_indicators(TEST_STOCK_CODE)

            assert_success_response(result)
            assert result["data"]["roe"] == 0.15
            assert result["data"]["gross_margin"] == 0.40

    def test_get_financial_indicators_not_found(self) -> None:
        """测试获取财务指标 - 无数据"""
        with patch('api_server.services.data_source_service.FundamentalsAPI') as MockFundamentalsAPI:
            MockFundamentalsAPI.get_indicators.return_value = None

            result = DataSourceService.get_financial_indicators(TEST_STOCK_CODE)

            assert_error_response(result)
            assert "No financial indicators" in result["message"]

    def test_get_financial_indicators_empty(self) -> None:
        """测试获取财务指标 - 空结果"""
        with patch('api_server.services.data_source_service.FundamentalsAPI') as MockFundamentalsAPI:
            MockFundamentalsAPI.get_indicators.return_value = {}

            result = DataSourceService.get_financial_indicators(TEST_STOCK_CODE)

            assert_error_response(result)
            assert "No financial indicators" in result["message"]

    def test_get_financial_indicators_failure(self) -> None:
        """测试获取财务指标失败"""
        with patch('api_server.services.data_source_service.FundamentalsAPI') as MockFundamentalsAPI:
            MockFundamentalsAPI.get_indicators.side_effect = Exception("Data Error")

            result = DataSourceService.get_financial_indicators(TEST_STOCK_CODE)

            assert_error_response(result)
            assert "Failed to get financial indicators" in result["message"]

    def test_get_financial_indicators_calculates_quarter(self) -> None:
        """测试获取财务指标 - 自动计算季度"""
        mock_indicators = {"roe": 0.15}

        with patch('api_server.services.data_source_service.FundamentalsAPI') as MockFundamentalsAPI:
            MockFundamentalsAPI.get_indicators.return_value = mock_indicators

            # 调用方法
            DataSourceService.get_financial_indicators(TEST_STOCK_CODE)

            # 验证传递了正确的参数
            call_args = MockFundamentalsAPI.get_indicators.call_args
            assert call_args[0][0] == TEST_STOCK_CODE
            # year 和 quarter 应该是当前值
            assert isinstance(call_args[0][1], int)
            assert isinstance(call_args[0][2], int)
            assert 1 <= call_args[0][2] <= 4  # 季度在 1-4 之间


# ==================== DataSourceService 现有方法测试补充 ====================
class TestDataSourceServiceExisting:
    """DataSourceService 现有方法测试补充"""

    def test_get_realtime_quote_success(self) -> None:
        """测试获取实时行情成功"""
        mock_quote = Mock()
        mock_quote.ts_code = f"{TEST_STOCK_CODE}.SH"
        mock_quote.name = TEST_STOCK_NAME
        mock_quote.current_price = 1700.0
        mock_quote.change = 10.0
        mock_quote.change_pct = 0.5
        mock_quote.open = 1690.0
        mock_quote.high = 1720.0
        mock_quote.low = 1680.0
        mock_quote.close = 1700.0
        mock_quote.volume = 100000
        mock_quote.amount = 170000000.0
        mock_quote.turnover_rate = 0.5

        with patch('api_server.services.data_source_service.QuoteAPI') as MockQuoteAPI:
            MockQuoteAPI.get_realtime.return_value = mock_quote

            result = DataSourceService.get_realtime_quote(TEST_STOCK_CODE)

            assert result is not None
            assert result["symbol"] == TEST_STOCK_CODE
            assert result["name"] == TEST_STOCK_NAME
            assert result["current_price"] == 1700.0

    def test_get_realtime_quote_not_found(self) -> None:
        """测试获取实时行情 - 未找到"""
        with patch('api_server.services.data_source_service.QuoteAPI') as MockQuoteAPI:
            MockQuoteAPI.get_realtime.return_value = None

            result = DataSourceService.get_realtime_quote("INVALID")

            assert result is None

    def test_get_realtime_quote_error(self) -> None:
        """测试获取实时行情 - 错误"""
        with patch('api_server.services.data_source_service.QuoteAPI') as MockQuoteAPI:
            MockQuoteAPI.get_realtime.side_effect = Exception("API Error")

            result = DataSourceService.get_realtime_quote(TEST_STOCK_CODE)

            assert result is None

    def test_get_batch_quotes_success(self) -> None:
        """测试批量获取行情成功"""
        with patch.object(DataSourceService, 'get_realtime_quote') as mock_get_quote:
            mock_get_quote.side_effect = [
                {"symbol": TEST_STOCK_CODE, "name": "贵州茅台"},
                {"symbol": TEST_STOCK_CODE_2, "name": "平安银行"},
            ]

            result = DataSourceService.get_batch_quotes([TEST_STOCK_CODE, TEST_STOCK_CODE_2])

            assert len(result) == 2
            assert TEST_STOCK_CODE in result
            assert TEST_STOCK_CODE_2 in result

    def test_get_batch_quotes_partial_failure(self) -> None:
        """测试批量获取行情 - 部分失败"""
        with patch.object(DataSourceService, 'get_realtime_quote') as mock_get_quote:
            mock_get_quote.side_effect = [
                {"symbol": TEST_STOCK_CODE, "name": "贵州茅台"},
                None,  # 第二个返回 None
            ]

            result = DataSourceService.get_batch_quotes([TEST_STOCK_CODE, TEST_STOCK_CODE_2])

            assert len(result) == 1
            assert TEST_STOCK_CODE in result
            assert TEST_STOCK_CODE_2 not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
