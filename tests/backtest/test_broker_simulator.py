"""Test Broker Simulator"""

import pytest
from backtest.core.broker_simulator import BrokerSimulator, ExecutionResult


def test_broker_initialization():
    """测试经纪商初始化"""
    broker = BrokerSimulator()
    assert broker.commission_rate == 0.00025
    assert broker.slippage_rate == 0.001
    assert broker.stamp_duty_rate == 0.001


def test_custom_broker_initialization():
    """测试自定义参数初始化"""
    broker = BrokerSimulator(
        commission_rate=0.0003,
        slippage_rate=0.002,
        stamp_duty_rate=0.002
    )
    assert broker.commission_rate == 0.0003
    assert broker.slippage_rate == 0.002
    assert broker.stamp_duty_rate == 0.002


def test_calculate_commission():
    """测试手续费计算"""
    broker = BrokerSimulator(commission_rate=0.00025)
    commission = broker.calculate_commission(100000)
    assert commission == 25.0  # 100000 * 0.00025

    commission = broker.calculate_commission(150000)
    assert commission == 37.5  # 150000 * 0.00025


def test_apply_slippage_buy():
    """测试买入滑点"""
    broker = BrokerSimulator(slippage_rate=0.001)
    adjusted_price = broker.apply_slippage(price=1500.0, direction='buy')
    assert adjusted_price == pytest.approx(1500.0 * 1.001, rel=1e-9)
    assert adjusted_price > 1500.0  # Buy price should be higher


def test_apply_slippage_sell():
    """测试卖出滑点"""
    broker = BrokerSimulator(slippage_rate=0.001)
    adjusted_price = broker.apply_slippage(price=1500.0, direction='sell')
    assert adjusted_price == pytest.approx(1500.0 * 0.999, rel=1e-9)
    assert adjusted_price < 1500.0  # Sell price should be lower


def test_apply_slippage_invalid_direction():
    """测试无效方向"""
    broker = BrokerSimulator()
    with pytest.raises(ValueError, match="Invalid direction"):
        broker.apply_slippage(price=1500.0, direction='invalid')


def test_execute_order_buy():
    """测试执行买入订单"""
    broker = BrokerSimulator()
    result = broker.execute_order(
        symbol="600519",
        quantity=100,
        price=1500.0,
        direction="buy"
    )

    assert isinstance(result, ExecutionResult)
    assert result.symbol == "600519"
    assert result.direction == "buy"
    assert result.quantity == 100
    assert result.requested_price == 1500.0
    assert result.actual_price > 1500.0  # With slippage
    assert result.commission == 1500.0 * 100 * 0.00025
    assert result.slippage == result.actual_price - 1500.0
    assert result.total_cost == result.commission  # No stamp duty for buy


def test_execute_order_sell():
    """测试执行卖出订单"""
    broker = BrokerSimulator()
    result = broker.execute_order(
        symbol="600519",
        quantity=100,
        price=1500.0,
        direction="sell"
    )

    assert result.direction == "sell"
    assert result.actual_price < 1500.0  # With slippage
    assert result.commission == 1500.0 * 100 * 0.00025
    # Stamp duty is not included in total_cost for now


def test_execute_order_with_custom_params():
    """测试使用自定义参数执行订单"""
    broker = BrokerSimulator(
        commission_rate=0.0003,
        slippage_rate=0.002
    )
    result = broker.execute_order(
        symbol="600519",
        quantity=100,
        price=1500.0,
        direction="buy"
    )

    assert result.commission == 1500.0 * 100 * 0.0003
    assert result.actual_price == 1500.0 * 1.002
