#!/usr/bin/env python3
"""
VCP Breakout Strategy (VCP 爆发突击策略)

策略逻辑:
1. 识别 VCP 形态 (波动收缩形态)
2. 等待突破枢轴点
3. 成交量确认 (>1.5 倍均量)
4. 结合其他维度确认 (趋势向上、位置合理)
"""

import pandas as pd
from typing import Dict
from ..indicators import VCPDetector, BaseIndicators


class VCPBreakoutStrategy:
    """VCP 爆发突击策略"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化 VCP 策略

        Args:
            df: pandas DataFrame，包含 OHLCV 数据
        """
        self.df = df.copy()
        self.vcp_detector = VCPDetector(self.df)
        self.base_indicators = BaseIndicators(self.df)
        self.df = self.base_indicators.calculate_all_indicators()

    def analyze(self) -> Dict:
        """
        分析 VCP 策略信号

        Returns:
            策略分析结果
        """
        # 检测 VCP 形态
        vcp_result = self.vcp_detector.detect_vcp()

        # 获取最新数据
        latest = self.df.iloc[-1]
        current_price = latest['close']

        # 基础信号
        signal = 'HOLD'
        score = 0
        confidence = 'low'
        entry_price = None
        stop_loss = None
        take_profit = None

        # VCP 突破信号
        if vcp_result['breakout_detected']:
            signal = 'BUY'
            score += 40

            if vcp_result['breakout_volume']:
                score += 20
                confidence = 'high'
            else:
                confidence = 'medium'

            # 建议入场价 = 突破价
            entry_price = vcp_result['breakout_price']

            # 止损 = 最近谷底 - ATR
            if len(vcp_result['drops']) > 0:
                last_trough = vcp_result['drops'][-1]['trough_price']
                stop_loss = last_trough - latest['atr'] * 1.5
            else:
                stop_loss = current_price * 0.95

            # 止盈 = 入场价 + 2 * (入场价 - 止损)
            take_profit = entry_price + 2 * (entry_price - stop_loss)

        # VCP 形态已就绪，等待突破
        elif vcp_result['stage'] == 'ready_to_breakout':
            signal = 'WATCH'
            score += 30
            confidence = 'medium'
            entry_price = '等待突破枢轴点'
            stop_loss = '突破后确认'

        # 趋势确认加分
        ma_trend = self.base_indicators.get_latest_signals()['ma_trend']
        if ma_trend in ['strong_uptrend', 'weak_uptrend']:
            score += 15
        elif ma_trend == 'strong_downtrend':
            score -= 20

        # RSI 位置确认
        rsi_condition = self.base_indicators.get_latest_signals()['rsi_condition']
        if rsi_condition == 'oversold':
            score += 10
        elif rsi_condition == 'overbought':
            score -= 10

        # 布林带位置
        bb_position = self.base_indicators.get_latest_signals()['bb_position']
        if bb_position in ['lower_half', 'below_lower']:
            score += 10
        elif bb_position == 'above_upper':
            score -= 10

        return {
            'strategy': 'VCP_Breakout',
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'current_price': current_price,
            'vcp_details': vcp_result,
            'recommendation': self._get_recommendation(signal, score, confidence),
            'risk_reward_ratio': self._calculate_rr_ratio(entry_price, stop_loss, take_profit)
        }

    def _get_recommendation(self, signal: str, score: int, confidence: str) -> str:
        """获取推荐文字"""
        if signal == 'BUY':
            if score >= 70 and confidence == 'high':
                return '🚀 强烈建议买入 - VCP 突破确认，成交量放大'
            elif score >= 50:
                return '📈 建议买入 - VCP 突破形态良好'
            else:
                return '⚠️ 谨慎买入 - 需结合其他指标确认'
        elif signal == 'WATCH':
            return '👀 观察 - VCP 形态已就绪，等待突破'
        else:
            return '⏸️ 观望 - 无明确信号'

    def _calculate_rr_ratio(self, entry: float, stop: float, target: float) -> float:
        """计算风险回报比"""
        if entry is None or stop is None or target is None:
            return 0
        if isinstance(entry, str) or isinstance(stop, str) or isinstance(target, str):
            return 0
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0
