"""Strategy Combiner - 策略组合器"""

from typing import List, Dict, Optional
from backtest.strategies.base_strategy import BaseStrategy, Signal


class StrategyCombiner(BaseStrategy):
    """
    策略组合器

    支持多种组合规则:
    - AND: 所有策略都发出买入信号才买入
    - OR: 任一策略发出买入信号就买入
    - Weighted: 按权重加权评分
    """

    def __init__(
        self,
        strategies: List[BaseStrategy],
        combination_rule: str = "and",  # "and", "or", "weighted"
        weights: Optional[List[float]] = None
    ):
        """
        初始化策略组合器

        Args:
            strategies: 策略列表
            combination_rule: 组合规则 ('and', 'or', 'weighted')
            weights: 权重列表 (仅 weighted 模式使用)
        """
        self.strategies = strategies
        self.combination_rule = combination_rule.lower()

        # 设置权重
        if weights is None:
            # Default equal weights
            self.weights = [1.0 / len(strategies)] * len(strategies) if strategies else []
        else:
            self.weights = weights

        # 验证权重
        if self.combination_rule == "weighted" and len(self.weights) != len(strategies):
            raise ValueError(
                f"Weights length ({len(weights)}) must match strategies length ({len(strategies)})"
            )

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        组合多个策略信号

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        # 获取所有策略的信号
        signals = [s.on_data(symbol, data, date) for s in self.strategies]

        # 根据组合规则生成最终信号
        if self.combination_rule == "and":
            return self._combine_and(signals)
        elif self.combination_rule == "or":
            return self._combine_or(signals)
        elif self.combination_rule == "weighted":
            return self._combine_weighted(signals)
        else:
            raise ValueError(f"Unknown combination rule: {self.combination_rule}")

    def _combine_and(self, signals: List[Signal]) -> Signal:
        """
        AND 规则: 所有策略都买入才买入

        Returns:
            BUY if all signals are BUY, otherwise HOLD
        """
        if all(s.action == "BUY" for s in signals):
            # 取最小仓位 (保守)
            min_position = min(
                (s.position_size for s in signals if s.position_size is not None),
                default=0.1
            )
            reasons = [s.reason for s in signals if s.reason]
            return Signal(
                action="BUY",
                position_size=min_position,
                reason=f"AND组合: {' + '.join(reasons)}"
            )
        else:
            # Any non-BUY signal results in HOLD
            return Signal(action="HOLD", reason="AND: Not all strategies signal BUY")

    def _combine_or(self, signals: List[Signal]) -> Signal:
        """
        OR 规则: 任一策略买入就买入

        Returns:
            BUY if any signal is BUY, otherwise HOLD
        """
        buy_signals = [s for s in signals if s.action == "BUY"]
        if buy_signals:
            # 取最大仓位
            max_position = max(
                (s.position_size for s in buy_signals if s.position_size is not None),
                default=0.1
            )
            reasons = [s.reason for s in buy_signals if s.reason]
            return Signal(
                action="BUY",
                position_size=max_position,
                reason=f"OR组合: {' + '.join(reasons)}"
            )
        else:
            return Signal(action="HOLD", reason="OR: No strategy signals BUY")

    def _combine_weighted(self, signals: List[Signal]) -> Signal:
        """
        加权规则: 按权重计算综合评分

        Returns:
            BUY if weighted score >= threshold, otherwise HOLD
        """
        # 只计算 BUY 信号的加权仓位
        buy_score = sum(
            (s.position_size or 0) * w
            for s, w in zip(signals, self.weights)
            if s.action == "BUY"
        )

        # 阈值: 10% 仓位
        if buy_score >= 0.1:
            return Signal(
                action="BUY",
                position_size=min(buy_score, 0.3),  # Max 30% position
                reason=f"Weighted: score={buy_score:.3f}"
            )
        else:
            return Signal(
                action="HOLD",
                reason=f"Weighted: score={buy_score:.3f} < 0.1 threshold"
            )

    def get_name(self) -> str:
        """获取策略名称"""
        strategy_names = [s.get_name() for s in self.strategies]
        return f"Combiner({','.join(strategy_names)})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"<StrategyCombiner: {self.combination_rule} of {len(self.strategies)} strategies>"
