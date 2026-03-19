"""Test Position Tracker"""

import pytest
from backtest.core.position_tracker import PositionTracker, Position
from backtest.exceptions import InsufficientFundsError, InsufficientSharesError


def test_position_tracker_initialization():
    """测试持仓跟踪器初始化"""
    tracker = PositionTracker(initial_capital=100000)
    assert tracker.cash == 100000
    assert len(tracker.positions) == 0


def test_buy_stock():
    """测试买入股票"""
    tracker = PositionTracker(initial_capital=100000)
    success = tracker.buy(symbol="600519", quantity=100, price=1500.0)

    assert success is True
    assert tracker.cash == 100000 - 150000  # 100 * 1500
    assert tracker.positions["600519"].quantity == 100
    assert tracker.positions["600519"].cost_price == 1500.0


def test_buy_stock_insufficient_funds():
    """测试资金不足"""
    tracker = PositionTracker(initial_capital=10000)
    with pytest.raises(InsufficientFundsError):
        tracker.buy(symbol="600519", quantity=100, price=1500.0)


def test_buy_add_position():
    """测试加仓 - 更新成本价"""
    tracker = PositionTracker(initial_capital=200000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    tracker.buy(symbol="600519", quantity=100, price=1600.0)

    # 验证加权平均成本
    assert tracker.positions["600519"].quantity == 200
    assert tracker.positions["600519"].cost_price == (1500 * 100 + 1600 * 100) / 200


def test_sell_stock():
    """测试卖出股票"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    success = tracker.sell(symbol="600519", quantity=50, price=1600.0)

    assert success is True
    assert tracker.cash == -50000 + 50 * 1600  # Initial cash after buy + sell proceeds
    assert tracker.positions["600519"].quantity == 50


def test_sell_all_stock():
    """测试全仓卖出"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    success = tracker.sell(symbol="600519", quantity=100, price=1600.0)

    assert success is True
    assert "600519" not in tracker.positions  # Position removed
    assert tracker.cash == -50000 + 100 * 1600


def test_sell_insufficient_shares():
    """测试持仓不足"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=50, price=1500.0)
    with pytest.raises(InsufficientSharesError):
        tracker.sell(symbol="600519", quantity=100, price=1600.0)


def test_sell_nonexistent_position():
    """测试卖出不存在的持仓"""
    tracker = PositionTracker(initial_capital=100000)
    with pytest.raises(InsufficientSharesError):
        tracker.sell(symbol="600519", quantity=100, price=1600.0)


def test_get_position():
    """测试获取持仓"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)

    position = tracker.get_position("600519")
    assert position is not None
    assert position.symbol == "600519"
    assert position.quantity == 100

    # Test nonexistent position
    assert tracker.get_position("000001") is None


def test_update_market_value():
    """测试更新市值"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    tracker.update_market_value(symbol="600519", current_price=1600.0)

    assert tracker.positions["600519"].market_price == 1600.0


def test_get_total_value():
    """测试获取总资产"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    tracker.update_market_value(symbol="600519", current_price=1600.0)

    total_value = tracker.get_total_value()
    assert total_value == -50000 + 100 * 1600  # Cash + stock value


def test_get_positions():
    """测试获取所有持仓"""
    tracker = PositionTracker(initial_capital=200000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    tracker.buy(symbol="000001", quantity=200, price=10.0)

    positions = tracker.get_positions()
    assert len(positions) == 2
    assert "600519" in positions
    assert "000001" in positions
