"""测试从 YAML 配置文件加载"""
import pytest
from common.config import Config, SyncConfig, DataRetentionConfig, TradingHoursConfig


def test_load_config_from_yaml():
    """测试从 YAML 文件加载配置"""
    config = Config()

    # 测试嵌套模型可用
    assert hasattr(config.stock_market, 'sync')
    assert isinstance(config.stock_market.sync, SyncConfig)
    assert hasattr(config.stock_market.sync, 'concurrency')
    assert hasattr(config.stock_market.sync, 'kline_workers')
    assert hasattr(config.stock_market.sync, 'retry_times')
    assert hasattr(config.stock_market.sync, 'retry_delay')

    assert hasattr(config.stock_market, 'data_retention')
    assert isinstance(config.stock_market.data_retention, DataRetentionConfig)
    assert hasattr(config.stock_market.data_retention, 'kline_days')

    assert hasattr(config.stock_market, 'trading_hours')
    assert isinstance(config.stock_market.trading_hours, TradingHoursConfig)
    assert hasattr(config.stock_market.trading_hours, 'morning_open')
    assert hasattr(config.stock_market.trading_hours, 'afternoon_close')


def test_config_values_from_yaml():
    """测试 YAML 配置的值正确加载"""
    config = Config()

    # 测试 sync 配置
    assert config.stock_market.sync.incremental is True
    assert config.stock_market.sync.concurrency == 10
    assert config.stock_market.sync.kline_workers == 5
    assert config.stock_market.sync.retry_times == 3
    assert config.stock_market.sync.retry_delay == 1.0

    # 测试 data_retention 配置
    assert config.stock_market.data_retention.kline_days == 365
    assert config.stock_market.data_retention.fundamentals_days == 730

    # 测试 trading_hours 配置
    assert config.stock_market.trading_hours.morning_open == "09:30"
    assert config.stock_market.trading_hours.morning_close == "11:30"
    assert config.stock_market.trading_hours.afternoon_open == "13:00"
    assert config.stock_market.trading_hours.afternoon_close == "15:00"


def test_type_safety():
    """测试类型安全"""
    config = Config()

    # sync 是 SyncConfig 实例
    assert isinstance(config.stock_market.sync, SyncConfig)

    # data_retention 是 DataRetentionConfig 实例
    assert isinstance(config.stock_market.data_retention, DataRetentionConfig)

    # trading_hours 是 TradingHoursConfig 实例
    assert isinstance(config.stock_market.trading_hours, TradingHoursConfig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
