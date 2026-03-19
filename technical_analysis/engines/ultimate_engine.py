#!/usr/bin/env python3
"""
Ultimate Engine (五维共振总控引擎)

整合六大核心指标，实现五维评分系统：

五维评分:
- D1 趋势维 (20 分): EMA50/200, ZigZag 趋势
- D2 形态维 (30 分): VCP, 布林带收口
- D3 位置维 (20 分): 布林带上下轨，RSI
- D4 动能维 (10 分): MACD 背离，成交量
- D5 触发维 (20 分): 神奇九转，枢轴突破

决策阈值:
- S 级 (≥85 分): STRONG_BUY (满仓 20%)
- A 级 (≥65 分): BUY (半仓 10%)
- B 级 (<65 分): HOLD
"""

import pandas as pd
from typing import Dict
from ..indicators import BaseIndicators, TDSequential, VCPDetector, DivergenceCheck, ZigZag


# 配置常量
FIVE_DIMENSION_WEIGHTS = {
    'D1': 20,  # 趋势维
    'D2': 30,  # 形态维
    'D3': 20,  # 位置维
    'D4': 10,  # 动能维
    'D5': 20   # 触发维
}

DECISION_THRESHOLD = {
    'strong_buy': 85,  # S级
    'buy': 65,         # A级
    'hold': 40,        # B级
    'wait': 0          # C级
}


class UltimateEngine:
    """五维共振总控引擎"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化五维共振引擎

        Args:
            df: pandas DataFrame，必须包含 OHLCV 数据
        """
        self.df = df.copy()
        self._validate_data()

        # 初始化各指标计算器
        self.base_indicators = BaseIndicators(self.df)
        self.td_sequential = None  # 延迟初始化
        self.vcp_detector = None
        self.divergence_check = None
        self.zigzag = None

        # 计算基础指标并更新 self.df
        self.df = self.base_indicators.calculate_all_indicators()

        # 评分详情
        self.dimension_scores = {}
        self.dimension_details = {}

    def _validate_data(self):
        """验证数据格式"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必需的列：{col}")

    def _init_special_indicators(self):
        """延迟初始化特殊指标 (避免不必要的计算)"""
        if self.td_sequential is None:
            self.td_sequential = TDSequential(self.df)
        if self.vcp_detector is None:
            self.vcp_detector = VCPDetector(self.df)
        if self.divergence_check is None:
            self.divergence_check = DivergenceCheck(self.df)
        if self.zigzag is None:
            self.zigzag = ZigZag(self.df)

    def evaluate_d1_trend(self) -> int:
        """
        D1 趋势维评分 (20 分)

        评估条件:
        - 股价 > EMA50 > EMA200 (多头排列)
        - ZigZag 显示上升趋势

        Returns:
            评分 (0-20)
        """
        latest = self.df.iloc[-1]
        score = 0
        details = {}

        # EMA 多头排列 (10 分)
        if 'ema50' in self.df.columns and 'ema200' in self.df.columns:
            if latest['close'] > latest['ema50'] > latest['ema200']:
                score += 10
                details['ema_alignment'] = 'bullish'
            elif latest['close'] > latest['ema50']:
                score += 5
                details['ema_alignment'] = 'partial_bullish'
            else:
                details['ema_alignment'] = 'bearish'
        else:
            # 使用简单均线
            if latest['close'] > latest.get('ma50', latest['close']) > latest.get('ma200', latest['close']):
                score += 10
                details['ema_alignment'] = 'bullish'

        # ZigZag 趋势 (10 分)
        self._init_special_indicators()
        zigzag_signal = self.zigzag.get_zigzag_signal()

        if zigzag_signal['trend'] == 'up':
            score += 10
            details['zigzag_trend'] = 'up'
        elif zigzag_signal['trend'] == 'down':
            details['zigzag_trend'] = 'down'
        else:
            details['zigzag_trend'] = 'insufficient_data'

        self.dimension_scores['D1'] = score
        self.dimension_details['D1'] = details

        return score

    def evaluate_d2_pattern(self) -> int:
        """
        D2 形态维评分 (30 分)

        评估条件:
        - VCP 形态识别
        - 布林带收口

        Returns:
            评分 (0-30)
        """
        latest = self.df.iloc[-1]
        score = 0
        details = {}

        # VCP 形态 (20 分)
        self._init_special_indicators()
        vcp_result = self.vcp_detector.detect_vcp()

        if vcp_result['breakout_detected']:
            score += 20
            details['vcp'] = 'breakout_confirmed'
        elif vcp_result['is_vcp']:
            if vcp_result['stage'] == 'ready_to_breakout':
                score += 15
                details['vcp'] = 'ready_to_breakout'
            elif vcp_result['stage'] == 'tightening':
                score += 10
                details['vcp'] = 'tightening'
            elif vcp_result['stage'] == 'forming':
                score += 5
                details['vcp'] = 'forming'
            else:
                details['vcp'] = vcp_result['stage']
        else:
            details['vcp'] = 'no_pattern'

        # 布林带收口 (10 分)
        if 'bb_bandwidth' in self.df.columns:
            # 计算带宽分位数，判断是否极度收口
            bb_bandwidth = self.df['bb_bandwidth']
            current_bb = bb_bandwidth.iloc[-1]
            bb_percentile = (bb_bandwidth.rolling(120).min() / bb_bandwidth.rolling(120).max()).iloc[-1]

            if not pd.isna(bb_percentile):
                if bb_percentile < 0.3:  # 处于带宽范围的下 30%
                    score += 10
                    details['bb_squeeze'] = 'strong'
                elif bb_percentile < 0.5:
                    score += 5
                    details['bb_squeeze'] = 'moderate'
                else:
                    details['bb_squeeze'] = 'normal'
            else:
                details['bb_squeeze'] = 'insufficient_data'
        else:
            details['bb_squeeze'] = 'not_calculated'

        self.dimension_scores['D2'] = score
        self.dimension_details['D2'] = details

        return score

    def evaluate_d3_position(self) -> int:
        """
        D3 位置维评分 (20 分)

        评估条件:
        - 布林带位置
        - RSI 位置

        Returns:
            评分 (0-20)
        """
        latest = self.df.iloc[-1]
        score = 0
        details = {}

        # 布林带位置 (10 分)
        if 'bb_position' in self.df.columns:
            bb_position = latest['bb_position']

            if bb_position < 0.2:  # 接近下轨，超卖
                score += 10
                details['bb_position'] = 'oversold'
            elif bb_position < 0.4:  # 中下部
                score += 5
                details['bb_position'] = 'lower_half'
            elif bb_position > 0.8:  # 接近上轨，超买
                details['bb_position'] = 'overbought'
            elif bb_position > 0.6:  # 中上部
                score += 3
                details['bb_position'] = 'upper_half'
            else:
                score += 5
                details['bb_position'] = 'neutral'
        else:
            details['bb_position'] = 'not_calculated'

        # RSI 位置 (10 分)
        if 'rsi' in self.df.columns:
            rsi = latest['rsi']

            if rsi < 30:  # 超卖区
                score += 10
                details['rsi'] = 'oversold'
            elif rsi < 45:  # 偏低区域
                score += 7
                details['rsi'] = 'low'
            elif rsi > 70:  # 超买区
                details['rsi'] = 'overbought'
            elif rsi > 55:  # 偏高区域
                score += 3
                details['rsi'] = 'high'
            else:  # 中性区域
                score += 5
                details['rsi'] = 'neutral'
        else:
            details['rsi'] = 'not_calculated'

        self.dimension_scores['D3'] = score
        self.dimension_details['D3'] = details

        return score

    def evaluate_d4_momentum(self) -> int:
        """
        D4 动能维评分 (10 分)

        评估条件:
        - MACD 背离
        - 成交量确认

        Returns:
            评分 (0-10)
        """
        latest = self.df.iloc[-1]
        score = 0
        details = {}

        # MACD 背离 (6 分)
        self._init_special_indicators()
        divergence_result = self.divergence_check.detect_all_divergences()

        if divergence_result['macd']['bullish_divergence']['detected']:
            score += 6
            details['macd_divergence'] = 'bullish'
        elif divergence_result['macd']['bearish_divergence']['detected']:
            details['macd_divergence'] = 'bearish'
        else:
            details['macd_divergence'] = 'none'

        # 成交量确认 (4 分)
        if 'volume_ratio' in self.df.columns:
            volume_ratio = latest['volume_ratio']

            if volume_ratio > 2:  # 放量
                score += 4
                details['volume'] = 'surge'
            elif volume_ratio > 1.5:  # 温和放量
                score += 2
                details['volume'] = 'increasing'
            elif volume_ratio < 0.5:  # 缩量
                details['volume'] = 'shrink'
            else:
                score += 1
                details['volume'] = 'normal'
        else:
            details['volume'] = 'not_calculated'

        self.dimension_scores['D4'] = score
        self.dimension_details['D4'] = details

        return score

    def evaluate_d5_trigger(self) -> int:
        """
        D5 触发维评分 (20 分)

        评估条件:
        - 神奇九转信号
        - 枢轴突破确认

        Returns:
            评分 (0-20)
        """
        latest = self.df.iloc[-1]
        score = 0
        details = {}

        # 神奇九转 (10 分)
        self._init_special_indicators()
        td_result = self.td_sequential.get_td_sequential()

        if td_result['td_buy_signal']:
            # 检查是否符合有效低九条件
            trend_up = self.dimension_scores.get('D1', 0) >= 10
            oversold = self.dimension_details.get('D3', {}).get('rsi') == 'oversold'

            if trend_up and oversold:
                score += 10
                details['td_sequential'] = 'valid_low_nine'
            else:
                score += 5
                details['td_sequential'] = 'low_nine_weak'
        elif td_result['td_sell_signal']:
            details['td_sequential'] = 'high_nine'
        else:
            details['td_sequential'] = td_result['status']

        # 枢轴突破 (10 分)
        self._init_special_indicators()
        vcp_result = self.vcp_detector.detect_vcp()

        if vcp_result['breakout_detected'] and vcp_result['breakout_volume']:
            score += 10
            details['pivot_breakout'] = 'confirmed'
        elif vcp_result['breakout_detected']:
            score += 5
            details['pivot_breakout'] = 'weak_volume'
        else:
            details['pivot_breakout'] = 'no_breakout'

        self.dimension_scores['D5'] = score
        self.dimension_details['D5'] = details

        return score

    def evaluate_all(self) -> Dict:
        """
        完整五维评估

        Returns:
            包含所有评估结果的字典
        """
        # 依次评估五个维度
        d1_score = self.evaluate_d1_trend()
        d2_score = self.evaluate_d2_pattern()
        d3_score = self.evaluate_d3_position()
        d4_score = self.evaluate_d4_momentum()
        d5_score = self.evaluate_d5_trigger()

        # 计算总分
        total_score = d1_score + d2_score + d3_score + d4_score + d5_score
        max_score = sum(FIVE_DIMENSION_WEIGHTS.values())

        # 确定决策
        if total_score >= DECISION_THRESHOLD['strong_buy']:
            action = 'STRONG_BUY'
            position_suggestion = 0.20  # 满仓 20%
        elif total_score >= DECISION_THRESHOLD['buy']:
            action = 'BUY'
            position_suggestion = 0.10  # 半仓 10%
        elif total_score >= DECISION_THRESHOLD['hold']:
            action = 'HOLD'
            position_suggestion = 0.05  # 轻仓观察
        else:
            action = 'WAIT'
            position_suggestion = 0.0  # 观望

        return {
            'total_score': total_score,
            'max_score': max_score,
            'score_percentage': total_score / max_score * 100,
            'action': action,
            'position_suggestion': position_suggestion,
            'dimension_scores': self.dimension_scores,
            'dimension_details': self.dimension_details,
            'confidence_level': self._get_confidence_level(total_score)
        }

    def _get_confidence_level(self, score: int) -> str:
        """
        获取置信度等级

        Args:
            score: 总分

        Returns:
            置信度等级字符串
        """
        if score >= 85:
            return 'S'  # 高置信度
        elif score >= 65:
            return 'A'  # 中置信度
        elif score >= 40:
            return 'B'  # 低置信度
        else:
            return 'C'  # 观望

    def generate_report(self) -> str:
        """
        生成人类可读的分析报告

        Returns:
            格式化报告字符串
        """
        result = self.evaluate_all()

        report = f"""
📊 五维共振分析报告
{'=' * 60}
总分：{result['total_score']}/{result['max_score']} ({result['score_percentage']:.1f}%)
决策：{result['action']}
置信度：{result['confidence_level']}级
建议仓位：{result['position_suggestion'] * 100:.0f}%

【维度评分详情】
"""
        dimension_names = {
            'D1': '趋势维',
            'D2': '形态维',
            'D3': '位置维',
            'D4': '动能维',
            'D5': '触发维'
        }

        dimension_max_scores = {
            'D1': 20,
            'D2': 30,
            'D3': 20,
            'D4': 10,
            'D5': 20
        }

        for dim_id, dim_name in dimension_names.items():
            score = self.dimension_scores.get(dim_id, 0)
            max_score = dimension_max_scores[dim_id]
            details = self.dimension_details.get(dim_id, {})
            details_str = ', '.join(f"{k}={v}" for k, v in details.items())
            report += f"• {dim_id} {dim_name}: {score}/{max_score} [{details_str}]\n"

        report += f"""
【当前价格】¥{self.df['close'].iloc[-1]:.2f}
【分析日期】{self.df.index[-1].strftime('%Y-%m-%d') if hasattr(self.df.index[-1], 'strftime') else self.df.index[-1]}
{'=' * 60}
"""

        return report
