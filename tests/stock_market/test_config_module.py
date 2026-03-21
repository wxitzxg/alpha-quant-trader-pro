"""测试 stock_market 配置模块"""
import pytest
from stock_market.config import (
    get_stock_market_config,
    get_sync_config,
    get_trading_hours,
    get_data_retention_config
)


def test_get_stock_market_config():
    """测试获取完整的股票市场配置"""
    config = get_stock_market_config()
    from common.config import StockMarketConfig
    assert isinstance(config, StockMarketConfig)


def test_get_sync_config():
    """测试获取同步配置"""
    sync_config = get_sync_config()
    from common.config import SyncConfig
    assert isinstance(sync_config, SyncConfig)
    assert hasattr(sync_config, 'concurrency')
    assert hasattr(sync_config, 'kline_workers')
    assert hasattr(sync_config, 'retry_times')
    assert hasattr(sync_config, 'retry_delay')


def test_get_trading_hours():
    """测试获取交易时间配置"""
    trading_hours = get_trading_hours()
    from common.config import TradingHoursConfig
    assert isinstance(trading_hours, TradingHoursConfig)
    assert trading_hours.morning_open == "09:30"
    assert trading_hours.afternoon_close == "15:00"


def test_get_data_retention_config():
    """测试获取数据保留配置"""
    retention = get_data_retention_config()
    from common.config import DataRetentionConfig
    assert isinstance(retention, DataRetentionConfig)
    assert hasattr(retention, 'kline_days')
    assert hasattr(retention, 'fundamentals_days')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
