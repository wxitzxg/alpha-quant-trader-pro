"""Test VCP Breakout Strategy"""

import pytest
from unittest.mock import patch, Mock
import pandas as pd
from backtest.strategies.prebuilt.vcp_breakout import VCPBreakoutStrategy


def test_vcp_strategy_import():
    """测试 VCP 策略导入"""
    assert VCPBreakoutStrategy is not None


def test_vcp_strategy_name():
    """测试策略名称"""
    strategy = VCPBreakoutStrategy()
    assert strategy.get_name() == "VCPBreakoutStrategy"


@patch('backtest.strategies.prebuilt.vcp_breakout.VCPDetector')
@patch('backtest.strategies.prebuilt.vcp_breakout.BaseIndicators')
def test_vcp_breakout_signal(mock_base_indicators, mock_vcp_detector):
    """测试 VCP 突破信号"""
    strategy = VCPBreakoutStrategy()

    # Mock VCP detector - breakout detected
    mock_vcp = Mock()
    mock_vcp.detect_vcp.return_value = {'breakout_detected': True}
    mock_vcp_detector.return_value = mock_vcp

    # Mock base indicators - strong uptrend
    mock_indicators = Mock()
    mock_signals = {'ma_trend': 'strong_uptrend'}
    mock_indicators.get_latest_signals.return_value = mock_signals
    mock_base_indicators.return_value = mock_indicators

    # Create test data
    df = pd.DataFrame({
        'open': [1500.0, 1510.0, 1520.0],
        'high': [1520.0, 1530.0, 1540.0],
        'low': [1490.0, 1500.0, 1510.0],
        'close': [1510.0, 1520.0, 1530.0],
        'volume': [1000000, 1100000, 1500000]  # Volume spike on breakout
    })

    signal = strategy.on_data("600519", df, "2024-01-03")

    assert signal.symbol == "600519"
    assert signal.action == "BUY"
    assert signal.position_size == 0.15
    assert "VCP 突破" in signal.reason


@patch('backtest.strategies.prebuilt.vcp_breakout.VCPDetector')
def test_vcp_no_breakout(mock_vcp_detector):
    """测试无 VCP 突破"""
    strategy = VCPBreakoutStrategy()

    # Mock VCP detector - no breakout
    mock_vcp = Mock()
    mock_vcp.detect_vcp.return_value = {'breakout_detected': False}
    mock_vcp_detector.return_value = mock_vcp

    df = pd.DataFrame({
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    })

    signal = strategy.on_data("600519", df, "2024-01-01")

    assert signal.action == "HOLD"


@patch('backtest.strategies.prebuilt.vcp_breakout.VCPDetector')
@patch('backtest.strategies.prebuilt.vcp_breakout.BaseIndicators')
def test_vcp_low_volume(mock_base_indicators, mock_vcp_detector):
    """测试 VCP 突破但成交量不足"""
    strategy = VCPBreakoutStrategy()

    # Mock VCP detector - breakout detected
    mock_vcp = Mock()
    mock_vcp.detect_vcp.return_value = {'breakout_detected': True}
    mock_vcp_detector.return_value = mock_vcp

    # Mock indicators
    mock_indicators = Mock()
    mock_indicators.get_latest_signals.return_value = {'ma_trend': 'strong_uptrend'}
    mock_base_indicators.return_value = mock_indicators

    # Low volume breakout
    df = pd.DataFrame({
        'open': [1500.0, 1510.0, 1520.0],
        'high': [1520.0, 1530.0, 1540.0],
        'low': [1490.0, 1500.0, 1510.0],
        'close': [1510.0, 1520.0, 1530.0],
        'volume': [1000000, 1100000, 1200000]  # No volume spike
    })

    signal = strategy.on_data("600519", df, "2024-01-03")

    assert signal.action == "HOLD"  # Should be HOLD due to low volume


@patch('backtest.strategies.prebuilt.vcp_breakout.VCPDetector')
@patch('backtest.strategies.prebuilt.vcp_breakout.BaseIndicators')
def test_vcp_weak_trend(mock_base_indicators, mock_vcp_detector):
    """测试 VCP 突破但趋势不强"""
    strategy = VCPBreakoutStrategy()

    # Mock VCP detector - breakout detected
    mock_vcp = Mock()
    mock_vcp.detect_vcp.return_value = {'breakout_detected': True}
    mock_vcp_detector.return_value = mock_vcp

    # Mock indicators - weak trend
    mock_indicators = Mock()
    mock_indicators.get_latest_signals.return_value = {'ma_trend': 'sideways'}
    mock_base_indicators.return_value = mock_indicators

    df = pd.DataFrame({
        'open': [1500.0, 1510.0, 1520.0],
        'high': [1520.0, 1530.0, 1540.0],
        'low': [1490.0, 1500.0, 1510.0],
        'close': [1510.0, 1520.0, 1530.0],
        'volume': [1000000, 1100000, 1500000]
    })

    signal = strategy.on_data("600519", df, "2024-01-03")

    assert signal.action == "HOLD"  # Should be HOLD due to weak trend
