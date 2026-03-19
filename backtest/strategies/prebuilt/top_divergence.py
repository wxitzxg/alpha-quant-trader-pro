"""Top Divergence Strategy - 顶部背离策略"""

from typing import Dict, Union
import pandas as pd
from backtest.strategies.base_strategy import BaseStrategy, Signal
from technical_analysis.indicators import DivergenceCheck


class TopDivergenceStrategy(BaseStrategy):
    """
    顶部背离策略 - 止盈策略

    策略逻辑:
    1. 检测顶背离信号 (价格新高，指标未新高)
    2. 确认超买状态 (RSI > 70)
    3. 提供止盈建议

    注意: 这是一个止盈策略，主要用于卖出信号
    """

    def on_data(self, symbol: str, data: Union[Dict, pd.DataFrame], date: str) -> Signal:
        """
        顶部背离策略

        Args:
            symbol: 股票代码
            data: K线数据 (DataFrame 或 Dict)
            date: 日期

        Returns:
            Signal: 交易信号
        """
        # 确保 data 是 DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        else:
            df = data

        if len(df) < 30:
            # Data insufficient for divergence detection
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=df['close'].iloc[-1] if len(df) > 0 else 0,
                reason="Data insufficient for divergence detection (<30 bars)"
            )

        current_price = df['close'].iloc[-1]

        # 检测背离
        divergence_checker = DivergenceCheck(df)
        divergence_result = divergence_checker.check_divergence()

        divergence_detected = divergence_result.get('divergence_detected', False)
        divergence_type = divergence_result.get('divergence_type', None)  # 'bullish' or 'bearish'
        strength = divergence_result.get('strength', None)

        # 顶部背离 (bearish divergence) - 卖出信号
        if divergence_detected and divergence_type == 'bearish':
            return Signal(
                symbol=symbol,
                date=date,
                action="SELL",
                price=current_price,
                reason=f"顶部背离检测到 (类型: {divergence_type}, 强度: {strength})"
            )

        # 底部背离 (bullish divergence) - 持有或观望 (这不是本策略的主要信号)
        if divergence_detected and divergence_type == 'bullish':
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=current_price,
                reason=f"底部背离 (非本策略主要信号): {divergence_type}"
            )

        # 无背离 - 持有
        return Signal(
            symbol=symbol,
            date=date,
            action="HOLD",
            price=current_price,
            reason="无背离信号"
        )

    def get_name(self) -> str:
        """获取策略名称"""
        return "TopDivergenceStrategy"
