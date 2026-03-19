"""Test Base Strategy"""

import pytest
from backtest.strategies.base_strategy import BaseStrategy, Signal


def test_base_strategy_abstract():
    """测试基类是抽象的"""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseStrategy()


def test_signal_creation():
    """测试信号创建"""
    signal = Signal(
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0
    )
    assert signal.symbol == "600519"
    assert signal.action == "BUY"
    assert signal.price == 1500.0
    assert signal.position_size == 0.1


def test_signal_with_custom_values():
    """测试自定义值的信号"""
    signal = Signal(
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0,
        position_size=0.2,
        quantity=100,
        reason="Test signal"
    )
    assert signal.position_size == 0.2
    assert signal.quantity == 100
    assert signal.reason == "Test signal"
