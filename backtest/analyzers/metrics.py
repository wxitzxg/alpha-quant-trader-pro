"""Metrics Calculator - 绩效指标计算"""

import numpy as np
from typing import List


class MetricsCalculator:
    """
    绩效指标计算

    计算以下指标:
    - 总收益率
    - 年化收益率
    - 最大回撤
    - 夏普比率
    - 索提诺比率
    - 波动率
    - 卡尔玛比率
    """

    def calculate_total_return(self, equity_curve: List[float]) -> float:
        """
        总收益率

        Args:
            equity_curve: 权益曲线

        Returns:
            总收益率 (%)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0

        return (equity_curve[-1] / equity_curve[0] - 1) * 100

    def calculate_annual_return(
        self,
        total_return: float,
        days: int
    ) -> float:
        """
        年化收益率

        Args:
            total_return: 总收益率 (%)
            days: 回测天数

        Returns:
            年化收益率 (%)
        """
        if days <= 0:
            return 0.0

        years = days / 365.0
        if years <= 0:
            return 0.0

        return ((1 + total_return / 100) ** (1 / years) - 1) * 100

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        最大回撤

        Args:
            equity_curve: 权益曲线

        Returns:
            最大回撤 (%)
        """
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            if peak > 0:
                dd = (peak - value) / peak * 100
                max_dd = max(max_dd, dd)

        return max_dd

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        夏普比率

        Args:
            returns: 日收益率列表
            risk_free_rate: 无风险利率 (年化)

        Returns:
            夏普比率
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Convert annual risk-free rate to daily
        risk_free_daily = risk_free_rate / 252

        excess_returns = [r - risk_free_daily for r in returns]

        mean_excess_return = np.mean(excess_returns)
        std_excess_return = np.std(excess_returns)

        if std_excess_return == 0:
            return 0.0

        return (mean_excess_return / std_excess_return) * np.sqrt(252)

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        索提诺比率 (只惩罚下行风险)

        Args:
            returns: 日收益率列表
            risk_free_rate: 无风险利率 (年化)

        Returns:
            索提诺比率
        """
        if not returns:
            return 0.0

        risk_free_daily = risk_free_rate / 252
        excess_returns = [r - risk_free_daily for r in returns]

        # Only consider downside returns
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return 0.0

        mean_excess_return = np.mean(excess_returns)
        downside_std = np.std(downside_returns)

        if downside_std == 0:
            return 0.0

        return (mean_excess_return / downside_std) * np.sqrt(252)

    def calculate_volatility(self, returns: List[float]) -> float:
        """
        波动率

        Args:
            returns: 日收益率列表

        Returns:
            年化波动率 (%)
        """
        if not returns or len(returns) < 2:
            return 0.0

        return np.std(returns) * np.sqrt(252) * 100

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> float:
        """
        卡尔玛比率 (年化收益 / 最大回撤)

        Args:
            annual_return: 年化收益率 (%)
            max_drawdown: 最大回撤 (%)

        Returns:
            卡尔玛比率
        """
        if max_drawdown == 0:
            return 0.0

        return annual_return / abs(max_drawdown)
