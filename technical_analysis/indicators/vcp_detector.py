#!/usr/bin/env python3
"""
VCP Pattern Detector (波动收缩形态识别)
识别股价波动收缩形态，用于捕捉主力洗盘结束后的爆发点

VCP 特征:
1. 2-4 次回调，幅度依次减小 (如 -20% → -10% → -5%)
2. 成交量逐级萎缩
3. 最后一次回调的高点为枢轴点 (Pivot)
4. 突破确认：股价放量 (>1.5 倍均量) 突破枢轴点
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class VCPDetector:
    """VCP 形态检测器"""

    def __init__(
        self,
        df: pd.DataFrame,
        min_drops: int = 2,
        max_drops: int = 4,
        min_contraction: float = 0.5
    ):
        """
        初始化 VCP 检测器

        Args:
            df: pandas DataFrame，包含 OHLCV 数据
            min_drops: 最少回调次数 (默认 2)
            max_drops: 最多回调次数 (默认 4)
            min_contraction: 最小收缩比例 (默认 0.5)
        """
        self.df = df.copy()
        self.min_drops = min_drops
        self.max_drops = max_drops
        self.min_contraction = min_contraction
        self._validate_data()

    def _validate_data(self):
        """验证数据格式"""
        required_columns = ['close', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必需的列：{col}")

    def _find_pivot_points(self, window: int = 20) -> List[Tuple[int, float]]:
        """
        寻找枢轴点 (局部高点)

        Args:
            window: 窗口大小

        Returns:
            枢轴点列表 [(index, price), ...]
        """
        pivots = []
        n = len(self.df)

        for i in range(window, n - window):
            # 检查是否为局部高点
            high_window = self.df['high'].iloc[i - window:i + window + 1]
            if self.df['high'].iloc[i] == high_window.max():
                pivots.append((i, self.df['high'].iloc[i]))

        return pivots

    def _find_trough_points(self, window: int = 20) -> List[Tuple[int, float]]:
        """
        寻找谷底点 (局部低点)

        Args:
            window: 窗口大小

        Returns:
            谷底点列表 [(index, price), ...]
        """
        troughs = []
        n = len(self.df)

        for i in range(window, n - window):
            # 检查是否为局部低点
            low_window = self.df['low'].iloc[i - window:i + window + 1]
            if self.df['low'].iloc[i] == low_window.min():
                troughs.append((i, self.df['low'].iloc[i]))

        return troughs

    def _calculate_drop_magnitude(
        self,
        pivot: Tuple[int, float],
        trough: Tuple[int, float]
    ) -> float:
        """
        计算回调幅度

        Args:
            pivot: 枢轴点 (index, price)
            trough: 谷底点 (index, price)

        Returns:
            回调幅度 (百分比)
        """
        if pivot[1] == 0:
            return 0
        return (trough[1] - pivot[1]) / pivot[1]

    def _calculate_volume_trend(
        self,
        start_idx: int,
        end_idx: int
    ) -> float:
        """
        计算成交量趋势 (末期/初期)

        Args:
            start_idx: 起始索引
            end_idx: 结束索引

        Returns:
            成交量比率
        """
        if start_idx >= end_idx:
            return 1.0

        # 计算初期和末期的平均成交量
        window = min(5, (end_idx - start_idx) // 3)
        if window < 1:
            window = 1

        early_vol = self.df['volume'].iloc[start_idx:start_idx + window].mean()
        late_vol = self.df['volume'].iloc[end_idx - window:end_idx].mean()

        if early_vol == 0:
            return 1.0

        return late_vol / early_vol

    def detect_vcp(self) -> Dict:
        """
        检测 VCP 形态

        Returns:
            包含 VCP 检测结果的字典
        """
        n = len(self.df)
        if n < 60:  # 至少需要 60 天数据
            return {
                'is_vcp': False,
                'stage': 'insufficient_data',
                'message': '数据不足，需要至少 60 个交易日'
            }

        # 寻找枢轴点和谷底点
        pivots = self._find_pivot_points(window=10)
        troughs = self._find_trough_points(window=10)

        if len(pivots) < 2 or len(troughs) < 1:
            return {
                'is_vcp': False,
                'stage': 'no_pattern',
                'message': '未检测到明显的枢轴点'
            }

        # 从后往前分析，找到最近的形态
        recent_pivots = []
        recent_troughs = []

        # 找最近的枢轴点和谷底点
        for pivot in reversed(pivots):
            if len(recent_pivots) < self.max_drops + 1:
                recent_pivots.append(pivot)

        for trough in reversed(troughs):
            if len(recent_troughs) < self.max_drops:
                recent_troughs.append(trough)

        # 按索引排序
        recent_pivots.sort(key=lambda x: x[0])
        recent_troughs.sort(key=lambda x: x[0])

        # 检测回调次数和收缩情况
        drops = []
        volume_trends = []

        for i in range(len(recent_pivots) - 1):
            if i < len(recent_troughs):
                pivot = recent_pivots[i]
                trough = recent_troughs[i]
                next_pivot = recent_pivots[i + 1]

                # 确保时间顺序正确
                if pivot[0] < trough[0] < next_pivot[0]:
                    drop_mag = self._calculate_drop_magnitude(pivot, trough)
                    vol_trend = self._calculate_volume_trend(pivot[0], next_pivot[0])

                    drops.append({
                        'pivot_idx': pivot[0],
                        'pivot_price': pivot[1],
                        'trough_idx': trough[0],
                        'trough_price': trough[1],
                        'drop_magnitude': drop_mag,
                        'volume_trend': vol_trend
                    })

        # 检查是否符合 VCP 条件
        is_vcp, stage, contraction_ratio = self._check_vcp_conditions(drops)

        # 检查是否有突破
        breakout_detected = False
        breakout_price = None
        breakout_volume = False

        if is_vcp and len(drops) > 0:
            last_pivot = drops[-1]['pivot_price']
            current_price = self.df['close'].iloc[-1]
            current_volume = self.df['volume'].iloc[-1]
            avg_volume = self.df['volume_ma5'].iloc[-1] if 'volume_ma5' in self.df.columns else self.df['volume'].rolling(5).mean().iloc[-1]

            # 突破枢轴点
            if current_price > last_pivot:
                breakout_detected = True
                breakout_price = current_price

                # 检查成交量是否放大
                if current_volume > avg_volume * 1.5:
                    breakout_volume = True

        return {
            'is_vcp': is_vcp,
            'stage': stage,
            'contraction_ratio': contraction_ratio,
            'drops': drops,
            'drop_count': len(drops),
            'breakout_detected': breakout_detected,
            'breakout_price': breakout_price,
            'breakout_volume': breakout_volume,
            'current_price': self.df['close'].iloc[-1],
            'message': self._get_stage_message(stage, contraction_ratio, breakout_detected)
        }

    def _check_vcp_conditions(
        self,
        drops: List[Dict]
    ) -> Tuple[bool, str, float]:
        """
        检查 VCP 条件

        Args:
            drops: 回调列表

        Returns:
            (是否 VCP, 阶段，收缩比率)
        """
        if len(drops) < self.min_drops:
            return False, 'accumulating_drops', 0

        # 检查回调幅度是否递减
        contraction_ratios = []
        for i in range(1, len(drops)):
            if abs(drops[i - 1]['drop_magnitude']) > 0:
                ratio = abs(drops[i]['drop_magnitude']) / abs(drops[i - 1]['drop_magnitude'])
                contraction_ratios.append(ratio)

        if not contraction_ratios:
            return False, 'no_contraction', 0

        # 检查是否有收缩
        avg_contraction = np.mean(contraction_ratios)

        # 检查成交量是否萎缩
        volume_shrinking = all(d['volume_trend'] < 1 for d in drops[1:])

        # 判断阶段
        if len(drops) >= self.min_drops and avg_contraction <= self.min_contraction:
            if volume_shrinking:
                if drops[-1]['volume_trend'] < 0.7:  # 成交量萎缩到 70% 以下
                    return True, 'ready_to_breakout', avg_contraction
                else:
                    return True, 'tightening', avg_contraction
            else:
                return True, 'forming', avg_contraction

        return False, 'early_stage', avg_contraction

    def _get_stage_message(
        self,
        stage: str,
        contraction_ratio: float,
        breakout: bool
    ) -> str:
        """
        获取阶段描述信息

        Args:
            stage: 阶段
            contraction_ratio: 收缩比率
            breakout: 是否突破

        Returns:
            描述信息
        """
        messages = {
            'insufficient_data': '数据不足，无法检测 VCP 形态',
            'no_pattern': '未检测到明显的 VCP 形态',
            'accumulating_drops': f'正在积累回调，当前{len(self._find_pivot_points())}次',
            'no_contraction': '回调幅度未呈现收缩趋势',
            'early_stage': 'VCP 形态早期阶段',
            'forming': f'VCP 形态形成中，收缩比率{contraction_ratio:.1%}',
            'tightening': f'VCP 形态接近完成，收缩比率{contraction_ratio:.1%}',
            'ready_to_breakout': f'VCP 形态已就绪，等待突破，收缩比率{contraction_ratio:.1%}'
        }

        base_msg = messages.get(stage, '未知阶段')

        if breakout:
            return f'🚀 {base_msg} - 突破确认!'
        return base_msg
