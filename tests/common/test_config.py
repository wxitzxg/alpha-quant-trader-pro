"""
Unit tests for the configuration models in common/config.py
"""

import pytest
from datetime import time
from pydantic import ValidationError

from common.config import (
    SyncConfig,
    DataRetentionConfig,
    TradingHoursConfig,
    StockMarketConfig
)


def test_sync_config_valid():
    """Test valid SyncConfig"""
    config = SyncConfig(
        incremental=True,
        concurrency=5,
        kline_workers=3,
        retry_times=3,
        retry_delay=1.0
    )

    assert config.incremental is True
    assert config.concurrency == 5
    assert config.kline_workers == 3
    assert config.retry_times == 3
    assert config.retry_delay == 1.0


def test_sync_config_validation():
    """Test SyncConfig validation rules"""
    # Test invalid concurrency
    with pytest.raises(ValidationError):
        SyncConfig(concurrency=0)

    with pytest.raises(ValidationError):
        SyncConfig(concurrency=101)

    # Test invalid kline_workers
    with pytest.raises(ValidationError):
        SyncConfig(kline_workers=0)

    with pytest.raises(ValidationError):
        SyncConfig(kline_workers=21)

    # Test invalid retry_times
    with pytest.raises(ValidationError):
        SyncConfig(retry_times=-1)

    with pytest.raises(ValidationError):
        SyncConfig(retry_times=11)

    # Test invalid retry_delay
    with pytest.raises(ValidationError):
        SyncConfig(retry_delay=-1.0)

    with pytest.raises(ValidationError):
        SyncConfig(retry_delay=61.0)


def test_data_retention_config_valid():
    """Test valid DataRetentionConfig"""
    config = DataRetentionConfig(
        kline_days=365,
        fundamentals_days=730
    )

    assert config.kline_days == 365
    assert config.fundamentals_days == 730


def test_data_retention_config_validation():
    """Test DataRetentionConfig validation rules"""
    # Test invalid kline_days
    with pytest.raises(ValidationError):
        DataRetentionConfig(kline_days=0)

    with pytest.raises(ValidationError):
        DataRetentionConfig(kline_days=3651)

    # Test invalid fundamentals_days
    with pytest.raises(ValidationError):
        DataRetentionConfig(fundamentals_days=0)

    with pytest.raises(ValidationError):
        DataRetentionConfig(fundamentals_days=3651)


def test_trading_hours_config_valid():
    """Test valid TradingHoursConfig"""
    config = TradingHoursConfig(
        morning_open="09:30",
        morning_close="11:30",
        afternoon_open="13:00",
        afternoon_close="15:00"
    )

    assert config.morning_open == "09:30"
    assert config.morning_close == "11:30"
    assert config.afternoon_open == "13:00"
    assert config.afternoon_close == "15:00"


def test_trading_hours_config_validation():
    """Test TradingHoursConfig validation rules"""
    # Test invalid time format
    with pytest.raises(ValidationError):
        TradingHoursConfig(morning_open="9:30")  # Missing leading zero

    with pytest.raises(ValidationError):
        TradingHoursConfig(morning_open="09:3")  # Missing leading zero

    with pytest.raises(ValidationError):
        TradingHoursConfig(morning_open="25:00")  # Invalid hour

    with pytest.raises(ValidationError):
        TradingHoursConfig(morning_open="09:60")  # Invalid minute


def test_stock_market_config_with_nested_models():
    """Test StockMarketConfig with nested models"""
    config = StockMarketConfig(
        sync=SyncConfig(
            incremental=True,
            concurrency=10,
            kline_workers=5,
            retry_times=3,
            retry_delay=1.0
        ),
        data_retention=DataRetentionConfig(
            kline_days=365,
            fundamentals_days=730
        ),
        trading_hours=TradingHoursConfig(
            morning_open="09:30",
            morning_close="11:30",
            afternoon_open="13:00",
            afternoon_close="15:00"
        )
    )

    assert isinstance(config.sync, SyncConfig)
    assert isinstance(config.data_retention, DataRetentionConfig)
    assert isinstance(config.trading_hours, TradingHoursConfig)


def test_stock_market_config_default_values():
    """Test StockMarketConfig default values"""
    config = StockMarketConfig()

    # Should have default nested models
    assert isinstance(config.sync, SyncConfig)
    assert isinstance(config.data_retention, DataRetentionConfig)
    assert isinstance(config.trading_hours, TradingHoursConfig)

    # Check default values
    assert config.sync.incremental is True
    assert config.sync.concurrency == 10
    assert config.sync.kline_workers == 5
    assert config.sync.retry_times == 3
    assert config.sync.retry_delay == 1.0

    assert config.data_retention.kline_days == 365
    assert config.data_retention.fundamentals_days == 730

    assert config.trading_hours.morning_open == "09:30"
    assert config.trading_hours.morning_close == "11:30"
    assert config.trading_hours.afternoon_open == "13:00"
    assert config.trading_hours.afternoon_close == "15:00"