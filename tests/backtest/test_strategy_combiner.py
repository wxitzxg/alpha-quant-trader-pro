"""Test Strategy Combiner"""

import pytest
from unittest.mock import Mock
from backtest.strategies.strategy_combiner import StrategyCombiner
from backtest.strategies.base_strategy import BaseStrategy, Signal


class MockStrategy(BaseStrategy):
    """Mock strategy for testing"""

    def __init__(self, name: str, action: str = "BUY", position_size: float = 0.1):
        self._name = name
        self._action = action
        self._position_size = position_size

    def on_data(self, symbol: str, data: dict, date: str) -> Signal:
        return Signal(
            symbol=symbol,
            date=date,
            action=self._action,
            price=data.get('close', 0),
            position_size=self._position_size,
            reason=f"{self._name} signal"
        )

    def get_name(self) -> str:
        return self._name


def test_strategy_combiner_and_rule_all_buy():
    """测试 AND 规则 - 所有策略都买入"""
    strategy1 = MockStrategy("Strategy1", action="BUY", position_size=0.1)
    strategy2 = MockStrategy("Strategy2", action="BUY", position_size=0.2)
    strategy3 = MockStrategy("Strategy3", action="BUY", position_size=0.15)

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2, strategy3],
        combination_rule="and"
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "BUY"
    assert signal.position_size == 0.1  # Min of all positions


def test_strategy_combiner_and_rule_one_hold():
    """测试 AND 规则 - 一个策略持有"""
    strategy1 = MockStrategy("Strategy1", action="BUY")
    strategy2 = MockStrategy("Strategy2", action="HOLD")
    strategy3 = MockStrategy("Strategy3", action="BUY")

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2, strategy3],
        combination_rule="and"
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "HOLD"  # All must be BUY


def test_strategy_combiner_or_rule_one_buy():
    """测试 OR 规则 - 一个策略买入"""
    strategy1 = MockStrategy("Strategy1", action="HOLD")
    strategy2 = MockStrategy("Strategy2", action="BUY", position_size=0.2)
    strategy3 = MockStrategy("Strategy3", action="HOLD")

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2, strategy3],
        combination_rule="or"
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "BUY"
    assert signal.position_size == 0.2  # Max of all buy positions


def test_strategy_combiner_or_rule_all_hold():
    """测试 OR 规则 - 所有策略持有"""
    strategy1 = MockStrategy("Strategy1", action="HOLD")
    strategy2 = MockStrategy("Strategy2", action="HOLD")

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2],
        combination_rule="or"
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "HOLD"


def test_strategy_combiner_weighted_rule():
    """测试加权规则"""
    strategy1 = MockStrategy("Strategy1", action="BUY", position_size=0.2)
    strategy2 = MockStrategy("Strategy2", action="BUY", position_size=0.1)

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2],
        combination_rule="weighted",
        weights=[0.6, 0.4]
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "BUY"
    expected_position = 0.2 * 0.6 + 0.1 * 0.4
    assert signal.position_size == pytest.approx(expected_position, rel=1e-9)


def test_strategy_combiner_weighted_rule_mixed():
    """测试加权规则 - 混合信号"""
    strategy1 = MockStrategy("Strategy1", action="BUY", position_size=0.2)
    strategy2 = MockStrategy("Strategy2", action="HOLD", position_size=0.0)
    strategy3 = MockStrategy("Strategy3", action="BUY", position_size=0.15)

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2, strategy3],
        combination_rule="weighted",
        weights=[0.5, 0.3, 0.2]
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "BUY"
    expected_position = 0.2 * 0.5 + 0.15 * 0.2  # Only BUY signals count
    assert signal.position_size == pytest.approx(expected_position, rel=1e-9)


def test_strategy_combiner_weighted_threshold():
    """测试加权规则 - 低于阈值"""
    strategy1 = MockStrategy("Strategy1", action="BUY", position_size=0.05)
    strategy2 = MockStrategy("Strategy2", action="BUY", position_size=0.05)

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2],
        combination_rule="weighted",
        weights=[0.5, 0.5]
    )

    data = {'close': 1500.0}
    signal = combiner.on_data("600519", data, "2024-01-01")

    assert signal.action == "HOLD"  # Position too low (< 0.1 threshold)


def test_strategy_combiner_name():
    """测试策略名称"""
    strategy1 = MockStrategy("VCP")
    strategy2 = MockStrategy("TD")

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2],
        combination_rule="and"
    )

    assert combiner.get_name() == "Combiner(VCP,TD)"


def test_strategy_combiner_default_weights():
    """测试默认权重"""
    strategy1 = MockStrategy("Strategy1")
    strategy2 = MockStrategy("Strategy2")

    combiner = StrategyCombiner(
        strategies=[strategy1, strategy2],
        combination_rule="weighted"
        # No weights provided, should use default [0.5, 0.5]
    )

    assert len(combiner.weights) == 2
    assert combiner.weights[0] == pytest.approx(0.5, rel=1e-9)
    assert combiner.weights[1] == pytest.approx(0.5, rel=1e-9)
