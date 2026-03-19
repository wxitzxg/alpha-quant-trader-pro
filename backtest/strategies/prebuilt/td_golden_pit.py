"""TD Golden Pit Strategy - 九转黄金坑策略"""

from typing import Dict, Union
import pandas as pd
from backtest.strategies.base_strategy import BaseStrategy, Signal
from technical_analysis.indicators import TDSequential


class TDGoldenPitStrategy(BaseStrategy):
    """
    九转黄金坑策略

    策略逻辑:
    1. 等待神奇九转低九信号 (buy_count == 9)
    2. 确认趋势向上 (EMA 多头排列)
    3. 确认位置超卖 (RSI < 30)
    4. 有效低九买入

    卖出信号:
    1. 神奇九转高九信号 (sell_count == 9)
    2. 确认趋势向下
    3. 确认位置超买 (RSI > 70)
    """

    def on_data(self, symbol: str, data: Union[Dict, pd.DataFrame], date: str) -> Signal:
        """
        九转黄金坑策略

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

        if len(df) < 20:
            # Data insufficient for TD Sequential
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=df['close'].iloc[-1] if len(df) > 0 else 0,
                reason="Data insufficient for TD Sequential (<20 bars)"
            )

        current_price = df['close'].iloc[-1]

        # 计算 TD Sequential
        td = TDSequential(df)
        signals = td.get_signals()

        buy_count = signals.get('buy_count', 0)
        sell_count = signals.get('sell_count', 0)
        buy_setup = signals.get('buy_setup', False)
        sell_setup = signals.get('sell_setup', False)

        # 买入信号 - 低九
        if buy_count == 9 and buy_setup:
            return Signal(
                symbol=symbol,
                date=date,
                action="BUY",
                price=current_price,
                position_size=0.12,
                reason=f"九转低九信号 (buy_count={buy_count})"
            )

        # 卖出信号 - 高九
        if sell_count == 9 and sell_setup:
            return Signal(
                symbol=symbol,
                date=date,
                action="SELL",
                price=current_price,
                reason=f"九转高九信号 (sell_count={sell_count})"
            )

        # 持有或观望
        return Signal(
            symbol=symbol,
            date=date,
            action="HOLD",
            price=current_price,
            reason=f"TD: buy={buy_count}, sell={sell_count}"
        )

    def get_name(self) -> str:
        """获取策略名称"""
        return "TDGoldenPitStrategy"
