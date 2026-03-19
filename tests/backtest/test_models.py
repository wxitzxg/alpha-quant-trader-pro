"""Test Data Models"""

import pytest
from backtest.models import Signal, Trade, Position, DailyMetrics, PerformanceMetrics, BacktestResult
from backtest.config import BacktestConfig


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
    assert signal.position_size == 0.1  # Default position size


def test_signal_with_custom_position():
    """测试自定义仓位的信号"""
    signal = Signal(
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0,
        position_size=0.2
    )
    assert signal.position_size == 0.2


def test_trade_creation():
    """测试交易创建"""
    trade = Trade(
        trade_id=1,
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0,
        quantity=100,
        amount=150000.0,
        commission=37.5,
        slippage=150.0,
        total_cost=150187.5
    )
    assert trade.trade_id == 1
    assert trade.symbol == "600519"
    assert trade.pnl is None  # BUY has no pnl yet


def test_position_creation():
    """测试持仓创建"""
    position = Position(
        symbol="600519",
        quantity=100,
        cost_price=1500.0,
        market_price=1600.0,
        market_value=160000.0,
        floating_pl=10000.0,
        entry_date="2024-01-01"
    )
    assert position.symbol == "600519"
    assert position.quantity == 100
    assert position.floating_pl == 10000.0


def test_daily_metrics_creation():
    """测试每日指标创建"""
    metrics = DailyMetrics(
        date="2024-01-01",
        total_value=105000.0,
        cash=50000.0,
        stock_value=55000.0,
        positions_count=1,
        daily_return=1.5,
        cumulative_return=5.0
    )
    assert metrics.total_value == 105000.0
    assert metrics.daily_return == 1.5


def test_performance_metrics_creation():
    """测试绩效指标创建"""
    perf = PerformanceMetrics(
        total_return=35.5,
        annual_return=18.2,
        volatility=25.0,
        max_drawdown=15.3,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        calmar_ratio=1.19,
        total_trades=45,
        winning_trades=28,
        losing_trades=17,
        win_rate=62.2,
        profit_factor=1.8,
        avg_holding_days=5.3
    )
    assert perf.total_return == 35.5
    assert perf.sharpe_ratio == 1.2
    assert perf.win_rate == 62.2


def test_backtest_result_creation():
    """测试回测结果创建"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    result = BacktestResult(
        config=config,
        strategy_name="FiveDimensionStrategy",
        trades=[],
        daily_metrics=[],
        positions_history=[],
        performance=PerformanceMetrics(
            total_return=35.5,
            annual_return=18.2,
            volatility=25.0,
            max_drawdown=15.3,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            calmar_ratio=1.19,
            total_trades=45,
            winning_trades=28,
            losing_trades=17,
            win_rate=62.2,
            profit_factor=1.8,
            avg_holding_days=5.3
        ),
        equity_curve=[100000.0, 101000.0, 102500.0],
        dates=["2024-01-01", "2024-01-02", "2024-01-03"]
    )

    assert result.strategy_name == "FiveDimensionStrategy"
    assert len(result.equity_curve) == 3


def test_backtest_result_summary():
    """测试回测结果摘要"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    result = BacktestResult(
        config=config,
        strategy_name="FiveDimensionStrategy",
        trades=[],
        daily_metrics=[],
        positions_history=[],
        performance=PerformanceMetrics(
            total_return=35.5,
            annual_return=18.2,
            volatility=25.0,
            max_drawdown=15.3,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            calmar_ratio=1.19,
            total_trades=45,
            winning_trades=28,
            losing_trades=17,
            win_rate=62.2,
            profit_factor=1.8,
            avg_holding_days=5.3
        ),
        equity_curve=[100000.0],
        dates=["2024-01-01"]
    )

    summary = result.summary
    assert "FiveDimensionStrategy" in summary
    assert "35.50%" in summary  # total_return
    assert "18.20%" in summary  # annual_return
