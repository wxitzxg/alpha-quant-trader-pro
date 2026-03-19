"""Test Metrics Calculator"""

import pytest
import numpy as np
from backtest.analyzers.metrics import MetricsCalculator


def test_calculate_total_return():
    """测试总收益率计算"""
    calculator = MetricsCalculator()

    equity_curve = [100000, 105000, 110000, 108000]
    total_return = calculator.calculate_total_return(equity_curve)

    expected = (108000 / 100000 - 1) * 100
    assert total_return == pytest.approx(expected, rel=1e-6)


def test_calculate_annual_return():
    """测试年化收益率计算"""
    calculator = MetricsCalculator()

    total_return = 35.5  # 35.5%
    days = 365  # 1 year

    annual_return = calculator.calculate_annual_return(total_return, days)

    assert annual_return == pytest.approx(35.5, rel=1e-6)


def test_calculate_annual_return_two_years():
    """测试两年年化收益率"""
    calculator = MetricsCalculator()

    total_return = 80.0  # 80%
    days = 730  # 2 years

    annual_return = calculator.calculate_annual_return(total_return, days)

    # (1 + 0.8)^(1/2) - 1 = 0.3416 = 34.16%
    assert annual_return == pytest.approx(34.16, rel=0.01)


def test_calculate_max_drawdown():
    """测试最大回撤计算"""
    calculator = MetricsCalculator()

    # Peak at 110000, then drop to 100000
    equity_curve = [100000, 105000, 110000, 105000, 100000, 108000]

    max_dd = calculator.calculate_max_drawdown(equity_curve)

    # Max drawdown: (110000 - 100000) / 110000 = 9.09%
    assert max_dd == pytest.approx(9.09, rel=0.01)


def test_calculate_max_drawdown_no_drawdown():
    """测试无回撤情况"""
    calculator = MetricsCalculator()

    # Always increasing
    equity_curve = [100000, 105000, 110000, 115000]

    max_dd = calculator.calculate_max_drawdown(equity_curve)

    assert max_dd == 0.0


def test_calculate_sharpe_ratio():
    """测试夏普比率计算"""
    calculator = MetricsCalculator()

    # Daily returns ~1%
    returns = [0.01] * 252
    risk_free_rate = 0.02  # 2%

    sharpe = calculator.calculate_sharpe_ratio(returns, risk_free_rate)

    # Should be positive and reasonable
    assert sharpe > 0
    assert sharpe < 10  # Sanity check


def test_calculate_sharpe_ratio_negative():
    """测试负夏普比率"""
    calculator = MetricsCalculator()

    # Negative returns
    returns = [-0.01] * 252
    risk_free_rate = 0.02

    sharpe = calculator.calculate_sharpe_ratio(returns, risk_free_rate)

    assert sharpe < 0


def test_calculate_sortino_ratio():
    """测试索提诺比率计算"""
    calculator = MetricsCalculator()

    # Mixed returns with some negative
    returns = [0.02, 0.015, -0.005, 0.01, 0.025]
    risk_free_rate = 0.02

    sortino = calculator.calculate_sortino_ratio(returns, risk_free_rate)

    assert sortino > 0


def test_calculate_sortino_ratio_all_positive():
    """测试全部正收益的索提诺比率"""
    calculator = MetricsCalculator()

    returns = [0.01] * 252
    risk_free_rate = 0.02

    sortino = calculator.calculate_sortino_ratio(returns, risk_free_rate)

    # All positive, should be very high
    assert sortino > 0


def test_calculate_volatility():
    """测试波动率计算"""
    calculator = MetricsCalculator()

    # Constant returns = 0 volatility
    returns = [0.01] * 252

    volatility = calculator.calculate_volatility(returns)

    assert volatility == 0.0


def test_calculate_volatility_variable():
    """测试可变收益的波动率"""
    calculator = MetricsCalculator()

    returns = [0.01, -0.01, 0.02, -0.02, 0.015]
    volatility = calculator.calculate_volatility(returns)

    assert volatility > 0


def test_calculate_calmar_ratio():
    """测试卡尔玛比率计算"""
    calculator = MetricsCalculator()

    annual_return = 20.0  # 20%
    max_drawdown = 10.0  # 10%

    calmar = calculator.calculate_calmar_ratio(annual_return, max_drawdown)

    assert calmar == 2.0


def test_calculate_calmar_ratio_negative():
    """测试负最大回撤的卡尔玛比率"""
    calculator = MetricsCalculator()

    annual_return = 20.0
    max_drawdown = -10.0  # Negative max drawdown

    calmar = calculator.calculate_calmar_ratio(annual_return, max_drawdown)

    assert calmar == -2.0


def test_calculate_calmar_ratio_zero_drawdown():
    """测试零回撤的卡尔玛比率"""
    calculator = MetricsCalculator()

    annual_return = 20.0
    max_drawdown = 0.0

    calmar = calculator.calculate_calmar_ratio(annual_return, max_drawdown)

    assert calmar == 0.0
