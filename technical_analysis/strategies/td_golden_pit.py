#!/usr/bin/env python3
"""
TD Golden Pit Strategy (九转黄金坑策略)

策略逻辑:
1. 等待神奇九转低九信号 (TD Buy Signal)
2. 确认趋势向上 (EMA 多头排列)
3. 确认位置超卖 (RSI < 30)
4. 结合其他指标确认
"""

import pandas as pd
from typing import Dict
from ..indicators import TDSequential, BaseIndicators


class TDGoldenPitStrategy:
    """九转黄金坑策略"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化九转黄金坑策略

        Args:
            df: pandas DataFrame，包含 OHLCV 数据
        """
        self.df = df.copy()
        self.td_sequential = TDSequential(self.df)
        self.base_indicators = BaseIndicators(self.df)
        self.df = self.base_indicators.calculate_all_indicators()

    def analyze(self) -> Dict:
        """
        分析九转黄金坑策略信号

        Returns:
            策略分析结果
        """
        # 获取神奇九转信号
        td_result = self.td_sequential.get_td_sequential()

        # 获取最新数据
        latest = self.df.iloc[-1]
        current_price = latest['close']

        # 基础信号
        signal = 'HOLD'
        score = 0
        confidence = 'low'
        entry_price = current_price
        stop_loss = None
        take_profit = None

        # 检查低九信号
        if td_result['td_buy_signal']:
            # 检查趋势是否向上
            ma_trend = self.base_indicators.get_latest_signals()['ma_trend']
            trend_up = ma_trend in ['strong_uptrend', 'weak_uptrend']

            # 检查是否超卖
            rsi_condition = self.base_indicators.get_latest_signals()['rsi_condition']
            oversold = rsi_condition == 'oversold'

            # 检查有效低九
            is_valid = self.td_sequential.check_valid_low_nine(trend_up=trend_up, oversold=oversold)

            if is_valid:
                signal = 'BUY'
                score += 50

                if trend_up and oversold:
                    score += 30
                    confidence = 'high'
                elif trend_up or oversold:
                    score += 15
                    confidence = 'medium'

                # 止损 = 当前价 - 2 * ATR
                stop_loss = current_price - latest['atr'] * 2

                # 止盈 = 当前价 + 3 * (当前价 - 止损)
                take_profit = current_price + 3 * (current_price - stop_loss)

        # 趋势加分
        if self.base_indicators.get_latest_signals()['ma_trend'] == 'strong_uptrend':
            score += 15
        elif self.base_indicators.get_latest_signals()['ma_trend'] == 'strong_downtrend':
            score -= 20

        # MACD 信号加分
        macd_signal = self.base_indicators.get_latest_signals()['macd_signal']
        if macd_signal == 'bullish':
            score += 10
        elif macd_signal == 'bearish':
            score -= 10

        # 布林带位置
        bb_position = self.base_indicators.get_latest_signals()['bb_position']
        if bb_position in ['lower_half', 'below_lower']:
            score += 10

        # ADX 趋势强度
        adx_strength = self.base_indicators.get_latest_signals()['adx_strength']
        if adx_strength == 'strong_trend':
            score += 10

        return {
            'strategy': 'TD_Golden_Pit',
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'current_price': current_price,
            'td_details': td_result,
            'trend_up': trend_up if 'trend_up' in locals() else False,
            'oversold': oversold if 'oversold' in locals() else False,
            'is_valid_low_nine': is_valid if 'is_valid' in locals() else False,
            'recommendation': self._get_recommendation(signal, score, confidence),
            'risk_reward_ratio': self._calculate_rr_ratio(entry_price, stop_loss, take_profit)
        }

    def _get_recommendation(self, signal: str, score: int, confidence: str) -> str:
        """获取推荐文字"""
        if signal == 'BUY':
            if score >= 80 and confidence == 'high':
                return '💎 强烈建议买入 - 九转黄金坑，趋势向上+超卖'
            elif score >= 60:
                return '📈 建议买入 - 有效低九信号'
            else:
                return '⚠️ 谨慎买入 - 低九信号，但条件不完全满足'
        else:
            if td_result := self.td_sequential.get_td_sequential():
                count = td_result['td_buy_count']
                if count > 0:
                    return f'⏳ 等待 - 低九计数 {count}/9'
            return '⏸️ 观望 - 无明确信号'

    def _calculate_rr_ratio(self, entry: float, stop: float, target: float) -> float:
        """计算风险回报比"""
        if entry is None or stop is None or target is None:
            return 0
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0
