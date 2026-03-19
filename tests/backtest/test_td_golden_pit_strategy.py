"""Test TD Golden Pit Strategy"""

import pytest
from unittest.mock import patch, Mock
import pandas as pd
from backtest.strategies.prebuilt.td_golden_pit import TDGoldenPitStrategy


def test_td_strategy_import():
    """测试九转策略导入"""
    assert TDGoldenPitStrategy is not None


def test_td_strategy_name():
    """测试策略名称"""
    strategy = TDGoldenPitStrategy()
    assert strategy.get_name() == "TDGoldenPitStrategy"


@patch('backtest.strategies.prebuilt.td_golden_pit.TDSequential')
def test_td_buy_signal(mock_td_sequential):
    """测试九转买入信号"""
    strategy = TDGoldenPitStrategy()

    # Mock TD Sequential - buy count 9
    mock_td = Mock()
    mock_td.get_signals.return_value = {
        'buy_count': 9,
        'sell_count': 0,
        'buy_setup': True,
        'sell_setup': False
    }
    mock_td_sequential.return_value = mock_td

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.symbol == "600519"
    assert signal.action == "BUY"
    assert signal.position_size == 0.12
    assert "九转低九" in signal.reason


@patch('backtest.strategies.prebuilt.td_golden_pit.TDSequential')
def test_td_sell_signal(mock_td_sequential):
    """测试九转卖出信号"""
    strategy = TDGoldenPitStrategy()

    # Mock TD Sequential - sell count 9
    mock_td = Mock()
    mock_td.get_signals.return_value = {
        'buy_count': 0,
        'sell_count': 9,
        'buy_setup': False,
        'sell_setup': True
    }
    mock_td_sequential.return_value = mock_td

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "SELL"
    assert "九转高九" in signal.reason


@patch('backtest.strategies.prebuilt.td_golden_pit.TDSequential')
def test_td_no_signal(mock_td_sequential):
    """测试无九转信号"""
    strategy = TDGoldenPitStrategy()

    # Mock TD Sequential - no signal
    mock_td = Mock()
    mock_td.get_signals.return_value = {
        'buy_count': 5,
        'sell_count': 3,
        'buy_setup': True,
        'sell_setup': False
    }
    mock_td_sequential.return_value = mock_td

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"


def test_td_insufficient_data():
    """测试数据不足"""
    strategy = TDGoldenPitStrategy()

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    # Only 1 row, insufficient for TD Sequential
    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"
