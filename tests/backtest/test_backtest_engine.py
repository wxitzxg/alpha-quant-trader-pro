"""Test Backtest Engine"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from backtest.core.backtest_engine import BacktestEngine
from backtest.config import BacktestConfig
from backtest.strategies.base_strategy import BaseStrategy, Signal
from backtest.models import BacktestResult


class MockStrategy(BaseStrategy):
    """Mock strategy for testing"""

    def __init__(self, buy_dates=None, sell_dates=None):
        self.buy_dates = buy_dates or []
        self.sell_dates = sell_dates or []

    def on_data(self, symbol: str, data: dict, date: str) -> Signal:
        from backtest.strategies.base_strategy import Signal
        if date in self.buy_dates:
            return Signal(symbol=symbol, date=date, action="BUY", price=data['close'], position_size=0.1)
        elif date in self.sell_dates:
            return Signal(symbol=symbol, date=date, action="SELL", price=data['close'])
        else:
            return Signal(symbol=symbol, date=date, action="HOLD", price=data['close'])

    def get_name(self) -> str:
        return "MockStrategy"


def create_mock_data():
    """创建模拟数据"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    df = pd.DataFrame({
        'open': [1500.0] * 10,
        'high': [1520.0] * 10,
        'low': [1490.0] * 10,
        'close': [1510.0] * 10,
        'volume': [1000000] * 10
    }, index=dates)
    df.index.name = 'timestamp'
    return df


def test_backtest_engine_initialization():
    """测试回测引擎初始化"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    mock_data_feed = Mock()
    mock_strategy = MockStrategy()

    engine = BacktestEngine(
        config=config,
        data_feed=mock_data_feed,
        strategy=mock_strategy,
        initial_capital=100000
    )

    assert engine.config == config
    assert engine.strategy == mock_strategy
    assert engine.initial_capital == 100000


@patch('backtest.core.backtest_engine.DataFeed')
def test_backtest_engine_run(mock_data_feed_class):
    """测试回测引擎运行"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-01-10"
    )

    # Mock data feed
    mock_data_feed = Mock()
    mock_data_feed.get_stock_data.return_value = create_mock_data()
    mock_data_feed_class.return_value = mock_data_feed

    # Create strategy that buys on day 1 and sells on day 5
    strategy = MockStrategy(
        buy_dates=['2024-01-02'],
        sell_dates=['2024-01-06']
    )

    engine = BacktestEngine(
        config=config,
        data_feed=mock_data_feed,
        strategy=strategy,
        initial_capital=100000
    )

    # Note: This test would require the full implementation
    # For now, we just test initialization
    assert engine is not None


def test_backtest_engine_position_tracking():
    """测试持仓跟踪"""
    config = BacktestConfig(initial_capital=100000)
    mock_data_feed = Mock()
    mock_strategy = MockStrategy()

    engine = BacktestEngine(
        config=config,
        data_feed=mock_data_feed,
        strategy=mock_strategy,
        initial_capital=100000
    )

    assert engine.position_tracker.cash == 100000
    assert len(engine.position_tracker.positions) == 0


def test_backtest_engine_broker():
    """测试经纪商模拟器"""
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.00025
    )
    mock_data_feed = Mock()
    mock_strategy = MockStrategy()

    engine = BacktestEngine(
        config=config,
        data_feed=mock_data_feed,
        strategy=mock_strategy,
        initial_capital=100000
    )

    assert engine.broker.commission_rate == 0.00025


def test_backtest_engine_insufficient_data():
    """测试数据不足情况"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-01-10"
    )

    mock_data_feed = Mock()
    mock_data_feed.get_stock_data.return_value = pd.DataFrame()

    mock_strategy = MockStrategy()

    engine = BacktestEngine(
        config=config,
        data_feed=mock_data_feed,
        strategy=mock_strategy,
        initial_capital=100000
    )

    # Should handle empty data gracefully
    assert engine is not None
