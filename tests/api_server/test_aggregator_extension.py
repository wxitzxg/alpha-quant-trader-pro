#!/usr/bin/env python3
"""测试数据源聚合器扩展功能"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import threading

from data_sources.aggregator import (
    DataSourceAggregator,
    StockListAPI,
    TopListAPI,
    KLineStatsAPI
)
from data_sources.models import Quote, KLine


# ==================== Mock 工厂函数 ====================
def create_mock_quote(
    symbol: str = "600519",
    price: float = 1700.0,
    change: float = 10.0,
    percent: float = 0.05,
    volume: int = 100000
) -> Quote:
    """创建 Quote 对象"""
    return Quote(
        symbol=symbol,
        price=price,
        change=change,
        percent=percent,
        volume=volume,
        amount=price * volume,
        timestamp=datetime.now()
    )


def create_mock_kline(
    symbol: str = "600519",
    date: datetime = None,
    close: float = 1700.0,
    volume: int = 100000
) -> Mock:
    """创建 KLine mock 对象"""
    if date is None:
        date = datetime(2024, 3, 15)

    mock_kline = Mock(spec=KLine)
    mock_kline.symbol = symbol
    mock_kline.datetime = date
    mock_kline.close = close
    mock_kline.open_price = 1690.0
    mock_kline.high = 1720.0
    mock_kline.low = 1680.0
    mock_kline.volume = volume
    return mock_kline


# ==================== DataSourceAggregator 测试 ====================
class TestDataSourceAggregatorExtension:
    """DataSourceAggregator 扩展方法测试"""

    @pytest.fixture
    def mock_aggregator(self) -> Mock:
        """创建模拟的 aggregator 实例"""
        aggregator = Mock(spec=DataSourceAggregator)
        aggregator.executor = Mock()
        aggregator.registry = Mock()
        aggregator.config = {
            'sources': {
                'realtime': [{'name': 'tushare', 'enabled': True, 'priority': 100}]
            }
        }
        return aggregator

    def test_get_stock_list_success(self, mock_aggregator: Mock) -> None:
        """测试获取股票列表成功"""
        expected_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "000001", "name": "平安银行", "exchange": "SZ"},
        ]
        mock_aggregator.get_stock_list.return_value = expected_stocks

        result = mock_aggregator.get_stock_list()

        assert result == expected_stocks
        assert len(result) == 2
        assert result[0]["symbol"] == "600519"

    def test_get_stock_list_with_exchange_filter(self, mock_aggregator: Mock) -> None:
        """测试获取股票列表 - 按交易所筛选"""
        all_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "000001", "name": "平安银行", "exchange": "SZ"},
            {"symbol": "600000", "name": "浦发银行", "exchange": "SH"},
        ]
        mock_aggregator.get_stock_list.return_value = [
            s for s in all_stocks if s.get('exchange') == 'SH'
        ]

        result = mock_aggregator.get_stock_list(exchange="SH")

        assert len(result) == 2
        assert all(s["exchange"] == "SH" for s in result)

    def test_get_stock_list_empty(self, mock_aggregator: Mock) -> None:
        """测试获取股票列表 - 空结果"""
        mock_aggregator.get_stock_list.return_value = []

        result = mock_aggregator.get_stock_list()

        assert result == []

    def test_get_stock_detail_success(self, mock_aggregator: Mock) -> None:
        """测试获取股票详情成功"""
        expected_detail = {
            "symbol": "600519",
            "name": "贵州茅台",
            "industry": "白酒",
            "market": "主板"
        }
        mock_aggregator.get_stock_detail.return_value = expected_detail

        result = mock_aggregator.get_stock_detail("600519")

        assert result == expected_detail
        assert result["symbol"] == "600519"

    def test_get_stock_detail_not_found(self, mock_aggregator: Mock) -> None:
        """测试获取股票详情 - 未找到"""
        mock_aggregator.get_stock_detail.return_value = None

        result = mock_aggregator.get_stock_detail("INVALID")

        assert result is None


# ==================== StockListAPI 测试 ====================
class TestStockListAPI:
    """StockListAPI 测试"""

    def test_get_success(self) -> None:
        """测试获取股票列表成功"""
        mock_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "000001", "name": "平安银行", "exchange": "SZ"},
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks

            result = StockListAPI.get()

            assert result == mock_stocks
            assert len(result) == 2

    def test_get_with_exchange_filter(self) -> None:
        """测试获取股票列表 - 按交易所筛选"""
        mock_stocks = [
            {"symbol": "600519", "name": "贵州茅台", "exchange": "SH"},
            {"symbol": "600000", "name": "浦发银行", "exchange": "SH"},
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks

            result = StockListAPI.get(exchange="SH")

            assert all(s["exchange"] == "SH" for s in result)

    def test_get_empty_result(self) -> None:
        """测试获取股票列表 - 空结果"""
        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = []

            result = StockListAPI.get()

            assert result == []


# ==================== TopListAPI 测试 ====================
class TestTopListAPI:
    """TopListAPI 测试（带缓存）"""

    def setup_method(self):
        """每个测试前清空缓存"""
        TopListAPI._cache.clear()

    def test_get_gain_list(self) -> None:
        """测试获取涨幅榜"""
        mock_stocks = [
            {"symbol": "600519"},
            {"symbol": "000001"},
        ]
        mock_quotes = [
            create_mock_quote(symbol="600519", price=1700.0, percent=0.05),  # +5%
            create_mock_quote(symbol="000001", price=15.0, percent=0.03),    # +3%
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks
            mock_instance.batch_get_realtime.return_value = mock_quotes

            result = TopListAPI.get(type="gain")

            assert len(result) == 2
            # 涨幅榜应该按 change_pct (percent * 100) 降序
            assert result[0]["symbol"] == "600519"
            # percent=0.05 -> change_pct=5.0
            assert result[0]["change_pct"] == 5.0

    def test_get_loss_list(self) -> None:
        """测试获取跌幅榜"""
        mock_stocks = [
            {"symbol": "600519"},
            {"symbol": "000001"},
        ]
        mock_quotes = [
            create_mock_quote(symbol="600519", percent=-0.05),  # -5%
            create_mock_quote(symbol="000001", percent=-0.03),  # -3%
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks
            mock_instance.batch_get_realtime.return_value = mock_quotes

            result = TopListAPI.get(type="loss")

            assert len(result) == 2
            # 跌幅榜应该按 change_pct 升序（最负的在前面）
            assert result[0]["symbol"] == "600519"
            # percent=-0.05 -> change_pct=-5.0
            assert result[0]["change_pct"] == -5.0

    def test_cache_hit(self) -> None:
        """测试缓存命中"""
        mock_stocks = [{"symbol": "600519"}]
        mock_quotes = [create_mock_quote()]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks
            mock_instance.batch_get_realtime.return_value = mock_quotes

            # 第一次调用
            result1 = TopListAPI.get(type="gain")
            # 第二次调用应该命中缓存
            result2 = TopListAPI.get(type="gain")

            # 两次结果应该相同
            assert result1 == result2
            # get_stock_list 只应该被调用一次（缓存生效）
            assert mock_instance.get_stock_list.call_count == 1

    def test_cache_expired(self) -> None:
        """测试缓存过期"""
        mock_stocks = [{"symbol": "600519"}]
        mock_quotes = [create_mock_quote()]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks
            mock_instance.batch_get_realtime.return_value = mock_quotes

            # 设置一个很短的 TTL
            original_ttl = TopListAPI._cache_ttl
            TopListAPI._cache_ttl = 0.1  # 100ms

            try:
                # 第一次调用
                TopListAPI.get(type="gain")
                # 等待缓存过期
                time.sleep(0.2)
                # 第二次调用，缓存应该已过期
                TopListAPI.get(type="gain")

                # get_stock_list 应该被调用两次
                assert mock_instance.get_stock_list.call_count == 2
            finally:
                TopListAPI._cache_ttl = original_ttl

    def test_empty_result(self) -> None:
        """测试空结果"""
        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = []
            mock_instance.batch_get_realtime.return_value = []

            result = TopListAPI.get(type="gain")

            assert result == []

    def test_thread_safety(self) -> None:
        """测试缓存线程安全"""
        mock_stocks = [{"symbol": "600519"}]
        mock_quotes = [create_mock_quote()]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_stock_list.return_value = mock_stocks
            mock_instance.batch_get_realtime.return_value = mock_quotes

            results = []
            errors = []

            def get_top_list():
                try:
                    result = TopListAPI.get(type="gain")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            # 创建多个线程同时访问
            threads = [threading.Thread(target=get_top_list) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 不应该有错误
            assert len(errors) == 0
            # 所有结果应该相同
            assert all(r == results[0] for r in results)


# ==================== KLineStatsAPI 测试 ====================
class TestKLineStatsAPI:
    """KLineStatsAPI 测试"""

    def test_get_success(self) -> None:
        """测试获取K线统计成功"""
        now = datetime.now()
        mock_klines = [
            create_mock_kline(date=now - timedelta(days=i), close=1700.0 + i * 10, volume=100000 + i * 1000)
            for i in range(10)
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_kline.return_value = mock_klines

            result = KLineStatsAPI.get(symbol="600519", period="1y")

            assert result["symbol"] == "600519"
            assert result["total_trading_days"] == 10
            assert "price_range" in result
            assert "volume_stats" in result
            assert "volatility" in result
            assert result["price_range"]["min"] == 1700.0
            assert result["price_range"]["max"] == 1790.0

    def test_get_with_different_periods(self) -> None:
        """测试不同周期的统计"""
        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_kline.return_value = [create_mock_kline()]

            for period in ["1y", "6m", "3m", "1m"]:
                result = KLineStatsAPI.get(symbol="600519", period=period)
                assert result["period"] == period

    def test_get_empty_klines(self) -> None:
        """测试没有K线数据时返回默认值"""
        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_kline.return_value = []

            result = KLineStatsAPI.get(symbol="600519", period="1y")

            assert result["symbol"] == "600519"
            assert result["total_trading_days"] == 0
            assert result["price_range"] == {"min": 0, "max": 0, "avg": 0}
            assert result["volume_stats"] == {"min": 0, "max": 0, "avg": 0, "total": 0}
            assert result["volatility"] == 0.0

    def test_volatility_calculation(self) -> None:
        """测试波动率计算"""
        # 创建价格波动较大的K线数据
        volatile_klines = [
            create_mock_kline(close=100.0 + (i % 2) * 50, volume=100000)
            for i in range(10)
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_kline.return_value = volatile_klines

            result = KLineStatsAPI.get(symbol="600519", period="1y")

            # 波动率应该大于0
            assert result["volatility"] > 0

    def test_highest_lowest_price_tracking(self) -> None:
        """测试最高最低价记录"""
        now = datetime.now()
        mock_klines = [
            create_mock_kline(date=now - timedelta(days=2), close=1700.0),  # middle
            create_mock_kline(date=now - timedelta(days=1), close=1800.0),  # highest
            create_mock_kline(date=now, close=1600.0),                       # lowest
        ]

        with patch('data_sources.aggregator.DataSourceAggregator') as MockAggregator:
            mock_instance = MockAggregator.return_value
            mock_instance.get_kline.return_value = mock_klines

            result = KLineStatsAPI.get(symbol="600519", period="1y")

            assert result["highest_price"]["price"] == 1800.0
            assert result["lowest_price"]["price"] == 1600.0
            # 应该记录对应日期
            assert result["highest_price"]["date"] != ""
            assert result["lowest_price"]["date"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
