# tests/portfolio_manager/test_fee_calculator.py
"""手续费计算器测试"""

import pytest
from decimal import Decimal
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.models import FeeConfig


def test_fee_calculator_default():
    """测试默认手续费配置"""
    calculator = FeeCalculator()

    # 测试买入手续费（不含印花税）
    buy_amount = 100000.0
    buy_fee = calculator.calculate_buy_fee(buy_amount)

    # 预期：交易所费用 6元 + 券商佣金 15元（最低5元） = 21元
    expected_exchange_fee = buy_amount * 0.00006
    expected_broker_commission = max(buy_amount * 0.00015, 5.0)
    expected_fee = expected_exchange_fee + expected_broker_commission

    assert abs(buy_fee - expected_fee) < 0.01

    # 测试卖出手续费（含印花税）
    sell_amount = 100000.0
    sell_fee = calculator.calculate_sell_fee(sell_amount)

    # 预期：印花税 50元 + 交易所费用 6元 + 券商佣金 15元 = 71元
    expected_stamp_duty = sell_amount * 0.0005
    expected_fee = expected_stamp_duty + expected_exchange_fee + expected_broker_commission

    assert abs(sell_fee - expected_fee) < 0.01


def test_fee_calculator_custom():
    """测试自定义手续费配置"""
    custom_config = FeeConfig(
        stamp_duty=0.001,
        exchange_fee=0.0001,
        broker_commission=0.0002,
        min_commission=10.0
    )

    calculator = FeeCalculator(custom_config)

    # 测试买入（佣金未达最低）
    small_buy = calculator.calculate_buy_fee(20000.0)
    # 20000 * 0.0001 = 2（交易所）+ max(20000 * 0.0002, 10) = 10（佣金）= 12元
    assert abs(small_buy - 12.0) < 0.01

    # 测试买入（佣金超过最低）
    large_buy = calculator.calculate_buy_fee(100000.0)
    # 100000 * 0.0001 = 10（交易所）+ 100000 * 0.0002 = 20（佣金）= 30元
    assert abs(large_buy - 30.0) < 0.01


def test_fee_calculator_properties():
    """测试手续费配置属性"""
    calculator = FeeCalculator()

    assert calculator.stamp_duty == Decimal('0.0005')
    assert calculator.exchange_fee == Decimal('0.00006')
    assert calculator.broker_commission == Decimal('0.00015')
    assert calculator.min_commission == Decimal('5.0')


def test_sell_fee_higher_than_buy():
    """测试卖出手续费高于买入（因为有印花税）"""
    calculator = FeeCalculator()

    amount = 50000.0
    buy_fee = calculator.calculate_buy_fee(amount)
    sell_fee = calculator.calculate_sell_fee(amount)

    assert sell_fee > buy_fee  # 卖出有印花税，所以更高
