"""Test Five Dimension Strategy"""

import pytest
from unittest.mock import Mock, patch
from backtest.strategies.prebuilt.five_dimension import FiveDimensionStrategy


def test_five_dimension_strategy_import():
    """测试五维共振策略导入"""
    assert FiveDimensionStrategy is not None


def test_five_dimension_strategy_name():
    """测试策略名称"""
    mock_analysis_service = Mock()
    strategy = FiveDimensionStrategy(mock_analysis_service)
    assert strategy.get_name() == "FiveDimensionStrategy"


@patch('backtest.strategies.prebuilt.five_dimension.AnalysisService')
def test_five_dimension_strategy_buy_signal(mock_analysis_service_class):
    """测试买入信号 (高分)"""
    from backtest.strategies.prebuilt.five_dimension import FiveDimensionStrategy

    # Mock analysis result with high score
    mock_result = {
        'total_score': 90,
        'action': 'STRONG_BUY'
    }
    mock_analysis_service = Mock()
    mock_analysis_service.analyze_stock.return_value = mock_result
    mock_analysis_service_class.return_value = mock_analysis_service

    strategy = FiveDimensionStrategy(mock_analysis_service)

    # Create mock data
    mock_data = {
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    }

    signal = strategy.on_data("600519", mock_data, "2024-01-01")

    assert signal.symbol == "600519"
    assert signal.date == "2024-01-01"
    assert signal.action == "BUY"
    assert signal.position_size == 0.2  # S级信号
    assert "S 级" in signal.reason


@patch('backtest.strategies.prebuilt.five_dimension.AnalysisService')
def test_five_dimension_strategy_hold_signal(mock_analysis_service_class):
    """测试持有信号 (中等分数)"""
    from backtest.strategies.prebuilt.five_dimension import FiveDimensionStrategy

    # Mock analysis result with medium score
    mock_result = {
        'total_score': 65,
        'action': 'BUY'
    }
    mock_analysis_service = Mock()
    mock_analysis_service.analyze_stock.return_value = mock_result
    mock_analysis_service_class.return_value = mock_analysis_service

    strategy = FiveDimensionStrategy(mock_analysis_service)

    mock_data = {
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    }

    signal = strategy.on_data("600519", mock_data, "2024-01-01")

    assert signal.action == "BUY"
    assert signal.position_size == 0.1  # A级信号
    assert "A 级" in signal.reason


@patch('backtest.strategies.prebuilt.five_dimension.AnalysisService')
def test_five_dimension_strategy_wait_signal(mock_analysis_service_class):
    """测试观望信号 (低分)"""
    from backtest.strategies.prebuilt.five_dimension import FiveDimensionStrategy

    # Mock analysis result with low score
    mock_result = {
        'total_score': 30,
        'action': 'WAIT'
    }
    mock_analysis_service = Mock()
    mock_analysis_service.analyze_stock.return_value = mock_result
    mock_analysis_service_class.return_value = mock_analysis_service

    strategy = FiveDimensionStrategy(mock_analysis_service)

    mock_data = {
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    }

    signal = strategy.on_data("600519", mock_data, "2024-01-01")

    assert signal.action == "SELL"
    assert "C 级" in signal.reason


@patch('backtest.strategies.prebuilt.five_dimension.AnalysisService')
def test_five_dimension_strategy_no_score(mock_analysis_service_class):
    """测试无评分的情况"""
    from backtest.strategies.prebuilt.five_dimension import FiveDimensionStrategy

    # Mock analysis result without score
    mock_result = {}
    mock_analysis_service = Mock()
    mock_analysis_service.analyze_stock.return_value = mock_result
    mock_analysis_service_class.return_value = mock_analysis_service

    strategy = FiveDimensionStrategy(mock_analysis_service)

    mock_data = {
        'open': [1500.0],
        'high': [1520.0],
        'low': [1490.0],
        'close': [1510.0],
        'volume': [1000000]
    }

    signal = strategy.on_data("600519", mock_data, "2024-01-01")

    assert signal.action == "SELL"  # Default to SELL if no score
