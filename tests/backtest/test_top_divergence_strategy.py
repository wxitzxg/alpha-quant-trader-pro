"""Test Top Divergence Strategy"""

import pytest
from unittest.mock import patch, Mock
import pandas as pd
from backtest.strategies.prebuilt.top_divergence import TopDivergenceStrategy


def test_top_divergence_strategy_import():
    """测试顶部背离策略导入"""
    assert TopDivergenceStrategy is not None


def test_top_divergence_strategy_name():
    """测试策略名称"""
    strategy = TopDivergenceStrategy()
    assert strategy.get_name() == "TopDivergenceStrategy"


@patch('backtest.strategies.prebuilt.top_divergence.DivergenceCheck')
def test_top_divergence_sell_signal(mock_divergence_check):
    """测试顶部背离卖出信号"""
    strategy = TopDivergenceStrategy()

    # Mock divergence check - bearish divergence detected
    mock_divergence = Mock()
    mock_divergence.check_divergence.return_value = {
        'divergence_detected': True,
        'divergence_type': 'bearish',  # Top divergence
        'strength': 'strong'
    }
    mock_divergence_check.return_value = mock_divergence

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.symbol == "600519"
    assert signal.action == "SELL"
    assert "顶部背离" in signal.reason
    assert "bearish" in signal.reason


@patch('backtest.strategies.prebuilt.top_divergence.DivergenceCheck')
def test_top_divergence_no_signal(mock_divergence_check):
    """测试无顶部背离信号"""
    strategy = TopDivergenceStrategy()

    # Mock divergence check - no divergence
    mock_divergence = Mock()
    mock_divergence.check_divergence.return_value = {
        'divergence_detected': False,
        'divergence_type': None,
        'strength': None
    }
    mock_divergence_check.return_value = mock_divergence

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"


@patch('backtest.strategies.prebuilt.top_divergence.DivergenceCheck')
def test_top_divergence_bullish_signal(mock_divergence_check):
    """测试底部背离信号 (忽略)"""
    strategy = TopDivergenceStrategy()

    # Mock divergence check - bullish divergence (not for this strategy)
    mock_divergence = Mock()
    mock_divergence.check_divergence.return_value = {
        'divergence_detected': True,
        'divergence_type': 'bullish',  # Bottom divergence
        'strength': 'strong'
    }
    mock_divergence_check.return_value = mock_divergence

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"  # Top divergence strategy ignores bullish


def test_top_divergence_insufficient_data():
    """测试数据不足"""
    strategy = TopDivergenceStrategy()

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"
    assert "insufficient" in signal.reason.lower()
