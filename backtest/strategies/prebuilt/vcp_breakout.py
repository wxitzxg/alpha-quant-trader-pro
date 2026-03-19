"""VCP Breakout Strategy - VCP 突破策略"""

from typing import Dict, Union
import pandas as pd
from backtest.strategies.base_strategy import BaseStrategy, Signal
from technical_analysis.indicators import VCPDetector, BaseIndicators


class VCPBreakoutStrategy(BaseStrategy):
    """
    VCP 突破策略

    策略逻辑:
    1. 检测 VCP 形态 (波动收缩)
    2. 等待突破枢轴点
    3. 确认成交量 > 1.5 倍均量
    4. 结合趋势和位置确认
    """

    def on_data(self, symbol: str, data: Union[Dict, pd.DataFrame], date: str) -> Signal:
        """
        VCP 突破策略

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
            # Data insufficient for VCP detection
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=df['close'].iloc[-1] if len(df) > 0 else 0,
                reason="Data insufficient for VCP detection"
            )

        current_price = df['close'].iloc[-1]

        # 1. 检测 VCP 形态
        vcp = VCPDetector(df)
        vcp_result = vcp.detect_vcp()

        if not vcp_result.get('breakout_detected', False):
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=current_price,
                reason="No VCP breakout detected"
            )

        # 2. 确认成交量 (需要至少 5 天数据)
        if len(df) >= 6:
            volume_ratio = df['volume'].iloc[-1] / df['volume'].iloc[-6:-1].mean()
            if volume_ratio < 1.5:
                return Signal(
                    symbol=symbol,
                    date=date,
                    action="HOLD",
                    price=current_price,
                    reason=f"Volume insufficient ({volume_ratio:.2f}x < 1.5x)"
                )
        else:
            # Not enough data for volume check
            volume_ratio = 1.0

        # 3. 确认趋势
        indicators = BaseIndicators(df)
        signals = indicators.get_latest_signals()
        ma_trend = signals.get('ma_trend', 'sideways')

        if ma_trend not in ['strong_uptrend', 'uptrend']:
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=current_price,
                reason=f"Trend not strong enough ({ma_trend})"
            )

        # 4. VCP 突破确认 - 买入信号
        return Signal(
            symbol=symbol,
            date=date,
            action="BUY",
            price=current_price,
            position_size=0.15,
            reason=f"VCP 突破 + 成交量确认 ({volume_ratio:.2f}x) + 趋势向上 ({ma_trend})"
        )

    def get_name(self) -> str:
        """获取策略名称"""
        return "VCPBreakoutStrategy"
