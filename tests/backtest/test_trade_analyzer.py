"""Test Trade Analyzer"""

import pytest
from datetime import datetime
from backtest.analyzers.trade_analyzer import TradeAnalyzer
from backtest.models import Trade


def create_test_trades():
    """创建测试交易数据"""
    trades = [
        # Winning trades
        Trade(
            trade_id=1,
            symbol="600519",
            date="2024-01-01",
            action="BUY",
            price=1500.0,
            quantity=100,
            amount=150000.0,
            commission=37.5,
            slippage=150.0,
            total_cost=187.5
        ),
        Trade(
            trade_id=2,
            symbol="600519",
            date="2024-01-10",
            action="SELL",
            price=1600.0,
            quantity=100,
            amount=160000.0,
            commission=40.0,
            slippage=160.0,
            total_cost=200.0,
            pnl=9612.5  # (1600-1500)*100 - 37.5 - 40 - 150 - 160
        ),
        # Another winning trade
        Trade(
            trade_id=3,
            symbol="000001",
            date="2024-01-05",
            action="BUY",
            price=10.0,
            quantity=1000,
            amount=10000.0,
            commission=2.5,
            slippage=10.0,
            total_cost=12.5
        ),
        Trade(
            trade_id=4,
            symbol="000001",
            date="2024-01-15",
            action="SELL",
            price=12.0,
            quantity=1000,
            amount=12000.0,
            commission=3.0,
            slippage=12.0,
            total_cost=15.0,
            pnl=1970.0  # (12-10)*1000 - 2.5 - 3 - 10 - 12
        ),
        # Losing trade
        Trade(
            trade_id=5,
            symbol="300750",
            date="2024-01-08",
            action="BUY",
            price=300.0,
            quantity=200,
            amount=60000.0,
            commission=15.0,
            slippage=60.0,
            total_cost=75.0
        ),
        Trade(
            trade_id=6,
            symbol="300750",
            date="2024-01-18",
            action="SELL",
            price=280.0,
            quantity=200,
            amount=56000.0,
            commission=14.0,
            slippage=56.0,
            total_cost=70.0,
            pnl=-4145.0  # (280-300)*200 - 15 - 14 - 60 - 56
        )
    ]
    return trades


def test_trade_analyzer_analyze_trades():
    """测试交易统计分析"""
    analyzer = TradeAnalyzer()
    trades = create_test_trades()

    stats = analyzer.analyze_trades(trades)

    assert stats['total_trades'] == 3  # 3 complete pairs
    assert stats['winning_trades'] == 2
    assert stats['losing_trades'] == 1
    assert stats['win_rate'] == pytest.approx(2/3 * 100, rel=0.01)
    assert stats['profit_factor'] > 0


def test_trade_analyzer_calculate_profit_factor():
    """测试盈亏比计算"""
    analyzer = TradeAnalyzer()
    trades = create_test_trades()

    profit_factor = analyzer.calculate_profit_factor(trades)

    # Total profit = 9612.5 + 1970 = 11582.5
    # Total loss = 4145
    # Profit factor = 11582.5 / 4145 = 2.79
    assert profit_factor == pytest.approx(2.79, rel=0.01)


def test_trade_analyzer_no_trades():
    """测试无交易情况"""
    analyzer = TradeAnalyzer()
    trades = []

    stats = analyzer.analyze_trades(trades)

    assert stats['total_trades'] == 0
    assert stats['win_rate'] == 0


def test_trade_analyzer_all_winning():
    """测试全盈利情况"""
    analyzer = TradeAnalyzer()
    trades = [
        Trade(
            trade_id=1,
            symbol="600519",
            date="2024-01-01",
            action="BUY",
            price=1500.0,
            quantity=100,
            amount=150000.0,
            commission=37.5,
            slippage=150.0,
            total_cost=187.5
        ),
        Trade(
            trade_id=2,
            symbol="600519",
            date="2024-01-10",
            action="SELL",
            price=1600.0,
            quantity=100,
            amount=160000.0,
            commission=40.0,
            slippage=160.0,
            total_cost=200.0,
            pnl=9612.5
        )
    ]

    stats = analyzer.analyze_trades(trades)

    assert stats['total_trades'] == 1
    assert stats['winning_trades'] == 1
    assert stats['losing_trades'] == 0
    assert stats['win_rate'] == 100.0


def test_trade_analyzer_all_losing():
    """测试全亏损情况"""
    analyzer = TradeAnalyzer()
    trades = [
        Trade(
            trade_id=1,
            symbol="600519",
            date="2024-01-01",
            action="BUY",
            price=1500.0,
            quantity=100,
            amount=150000.0,
            commission=37.5,
            slippage=150.0,
            total_cost=187.5
        ),
        Trade(
            trade_id=2,
            symbol="600519",
            date="2024-01-10",
            action="SELL",
            price=1400.0,
            quantity=100,
            amount=140000.0,
            commission=35.0,
            slippage=140.0,
            total_cost=175.0,
            pnl=-10362.5
        )
    ]

    stats = analyzer.analyze_trades(trades)

    assert stats['total_trades'] == 1
    assert stats['winning_trades'] == 0
    assert stats['losing_trades'] == 1
    assert stats['win_rate'] == 0.0
