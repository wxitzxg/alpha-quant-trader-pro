"""Test Backtest Service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from backtest.services.backtest_service import BacktestService
from backtest.config import BacktestConfig
from backtest.strategies.prebuilt import FiveDimensionStrategy
from backtest.models import BacktestResult


def test_backtest_service_initialization():
    """测试回测服务初始化"""
    mock_session = Mock(spec=Session)
    service = BacktestService(mock_session)
    assert service.session is not None
    assert service.data_feed is not None


@patch('backtest.services.backtest_service.DataFeed')
@patch('backtest.services.backtest_service.BacktestEngine')
@patch('backtest.services.backtest_service.AnalysisService')
def test_run_single_stock_backtest(mock_analysis_service, mock_engine, mock_data_feed):
    """测试单股票回测"""
    mock_session = Mock(spec=Session)

    # Mock data feed
    mock_df = Mock()
    mock_df.__len__ = Mock(return_value=100)
    mock_data_feed_instance = Mock()
    mock_data_feed_instance.get_stock_data.return_value = mock_df
    mock_data_feed.return_value = mock_data_feed_instance

    # Mock engine
    mock_result = Mock(spec=BacktestResult)
    mock_engine_instance = Mock()
    mock_engine_instance.run.return_value = mock_result
    mock_engine.return_value = mock_engine_instance

    # Mock analysis service
    mock_analysis_service_instance = Mock()
    mock_analysis_service.return_value = mock_analysis_service_instance

    service = BacktestService(mock_session)

    # Create mock strategy
    strategy = FiveDimensionStrategy(mock_analysis_service_instance)

    # Create config
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    # Run backtest
    result = service.run_single_stock_backtest(
        symbol="600519",
        strategy=strategy,
        config=config
    )

    assert result is not None
    mock_data_feed_instance.get_stock_data.assert_called_once()
    mock_engine_instance.run.assert_called_once()


@patch('backtest.services.backtest_service.DataFeed')
def test_run_single_stock_backtest_insufficient_data(mock_data_feed):
    """测试数据不足"""
    mock_session = Mock(spec=Session)

    # Mock data feed with insufficient data
    mock_df = Mock()
    mock_df.__len__ = Mock(return_value=20)  # Less than 30
    mock_data_feed_instance = Mock()
    mock_data_feed_instance.get_stock_data.return_value = mock_df
    mock_data_feed.return_value = mock_data_feed_instance

    service = BacktestService(mock_session)

    # Create mock strategy
    mock_strategy = Mock()
    mock_strategy.get_name.return_value = "MockStrategy"

    # Create config
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    with pytest.raises(ValueError, match="数据不足"):
        service.run_single_stock_backtest(
            symbol="600519",
            strategy=mock_strategy,
            config=config
        )


def test_generate_backtest_report_text():
    """测试生成文本报告"""
    mock_session = Mock(spec=Session)
    service = BacktestService(mock_session)

    # Create mock result
    mock_result = Mock(spec=BacktestResult)
    mock_result.summary = "Test Summary"
    mock_result.strategy_name = "TestStrategy"
    mock_result.config.start_date = "2024-01-01"
    mock_result.config.end_date = "2024-12-31"
    mock_result.performance.total_return = 35.5
    mock_result.performance.annual_return = 18.2

    report = service.generate_backtest_report(mock_result, format="text")

    assert isinstance(report, str)
    assert len(report) > 0


def test_generate_backtest_report_json():
    """测试生成 JSON 报告"""
    mock_session = Mock(spec=Session)
    service = BacktestService(mock_session)

    # Create mock result
    mock_result = Mock(spec=BacktestResult)
    mock_result.to_json.return_value = '{"test": "json"}'

    report = service.generate_backtest_report(mock_result, format="json")

    assert report == '{"test": "json"}'
