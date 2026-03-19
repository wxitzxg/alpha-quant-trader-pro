"""Test Backtest Config"""

import pytest
from backtest.config import BacktestConfig


def test_default_config():
    """测试默认配置"""
    config = BacktestConfig()
    assert config.initial_capital == 100000.0
    assert config.commission_rate == 0.00025
    assert config.start_date == "2023-01-01"


def test_custom_config():
    """测试自定义配置"""
    config = BacktestConfig(
        initial_capital=500000,
        commission_rate=0.0003,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    assert config.initial_capital == 500000
    assert config.commission_rate == 0.0003
    assert config.start_date == "2024-01-01"


def test_invalid_config_negative_capital():
    """测试无效配置 - 负初始资金"""
    with pytest.raises(ValueError, match="initial_capital"):
        BacktestConfig(initial_capital=-10000)


def test_invalid_config_invalid_dates():
    """测试无效配置 - 无效日期"""
    with pytest.raises(ValueError, match="start_date must be before"):
        BacktestConfig(start_date="2024-12-31", end_date="2024-01-01")


def test_invalid_config_position_size():
    """测试无效配置 - 仓位大小"""
    with pytest.raises(ValueError, match="position_size"):
        BacktestConfig(position_size=1.5)
