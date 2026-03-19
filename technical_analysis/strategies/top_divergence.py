#!/usr/bin/env python3
"""
Top Divergence Strategy (顶部背离止盈策略)

策略逻辑:
1. 检测顶背离信号 (价格创新高，但指标未创新高)
2. 确认超买状态 (RSI > 70)
3. 考虑趋势强度 (ADX)
4. 提供止盈建议
"""

import pandas as pd
from typing import Dict
from ..indicators import DivergenceCheck, BaseIndicators


class TopDivergenceStrategy:
    """顶部背离止盈策略"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化顶部背离策略

        Args:
            df: pandas DataFrame，包含 OHLCV 数据
        """
        self.df = df.copy()
        self.divergence_check = DivergenceCheck(self.df)
        self.base_indicators = BaseIndicators(self.df)
        self.df = self.base_indicators.calculate_all_indicators()

    def analyze(self) -> Dict:
        """
        分析顶部背离策略信号

        Returns:
            策略分析结果
        """
        # 检测背离
        divergence_result = self.divergence_check.detect_all_divergences()

        # 获取最新数据
        latest = self.df.iloc[-1]
        current_price = latest['close']

        # 基础信号
        signal = 'HOLD'
        score = 0
        confidence = 'low'
        suggested_action = 'HOLD'
        exit_price = None
        stop_profit = None

        # 检查顶背离
        macd_divergence = divergence_result['macd']
        bearish_detected = macd_divergence['bearish_divergence']['detected']

        if bearish_detected:
            signal = 'SELL'
            score += 50
            suggested_action = '考虑止盈'

            # 超买确认
            rsi_condition = self.base_indicators.get_latest_signals()['rsi_condition']
            if rsi_condition == 'overbought':
                score += 25
                confidence = 'high'
                suggested_action = '强烈建议止盈'
            else:
                confidence = 'medium'

            # 止盈建议价格
            if 'details' in macd_divergence['bearish_divergence']:
                details = macd_divergence['bearish_divergence']['details']
                # 建议在第二个高点附近止盈
                exit_price = details.get('price_high_2', current_price)
            else:
                exit_price = current_price

            # 止盈保护位
            stop_profit = exit_price * 0.98

        # 趋势强度检查
        adx_strength = self.base_indicators.get_latest_signals()['adx_strength']
        if adx_strength == 'strong_trend':
            # 强趋势下，背离信号可能失效
            score -= 10
            if signal == 'SELL':
                suggested_action = '谨慎 - 强趋势中，背离可能失效'

        # RSI 超买
        if self.base_indicators.get_latest_signals()['rsi_condition'] == 'overbought':
            score += 15
            if signal == 'HOLD':
                signal = 'WATCH'
                suggested_action = '注意风险 - 超买状态'

        # 布林带位置
        bb_position = self.base_indicators.get_latest_signals()['bb_position']
        if bb_position == 'above_upper':
            score += 10
            if signal == 'HOLD':
                signal = 'WATCH'

        # 成交量萎缩
        volume_condition = self.base_indicators.get_latest_signals()['volume_condition']
        if volume_condition == 'shrink':
            score += 10

        return {
            'strategy': 'Top_Divergence',
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'suggested_action': suggested_action,
            'exit_price': exit_price,
            'stop_profit': stop_profit,
            'current_price': current_price,
            'divergence_details': macd_divergence,
            'has_top_divergence': bearish_detected,
            'recommendation': self._get_recommendation(signal, score, confidence, suggested_action),
            'risk_level': self._get_risk_level(score)
        }

    def _get_recommendation(self, signal: str, score: int, confidence: str, action: str) -> str:
        """获取推荐文字"""
        if signal == 'SELL':
            if score >= 70 and confidence == 'high':
                return f'🚨 {action} - 顶背离+超买，高风险'
            elif score >= 50:
                return f'⚠️ {action} - 发现顶背离信号'
            else:
                return f'💭 {action} - 弱背离，需结合其他指标'
        elif signal == 'WATCH':
            return '👀 观察 - 超买或布林带上轨，注意风险'
        else:
            return '✅ 持有 - 无明显顶部信号'

    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 70:
            return 'HIGH'
        elif score >= 50:
            return 'MEDIUM'
        elif score >= 30:
            return 'LOW_MEDIUM'
        else:
            return 'LOW'
