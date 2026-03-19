#!/usr/bin/env python3
"""
ZigZag Indicator (之字转向) - 识别价格的主要转折点和趋势方向

通过设定百分比阈值来过滤噪音，只保留重要的价格转折
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class ZigZag:
    """ZigZag 之字转向指标"""

    def __init__(self, df: pd.DataFrame, threshold: float = 0.05):
        """
        初始化 ZigZag 指标

        Args:
            df: pandas DataFrame，必须包含 'close' 列
            threshold: 转折点阈值 (默认 5%)
        """
        self.df = df.copy()
        self.threshold = threshold
        self._validate_data()

    def _validate_data(self):
        """验证数据格式"""
        if 'close' not in self.df.columns:
            raise ValueError("缺少必需的列：close")

    def calculate_zigzag(self) -> pd.DataFrame:
        """
        计算 ZigZag 转折点

        Returns:
            包含 ZigZag 结果的 DataFrame
        """
        df = self.df.copy()
        n = len(df)

        # 初始化列
        df['zigzag'] = np.nan
        df['zigzag_high'] = np.nan
        df['zigzag_low'] = np.nan
        df['trend_direction'] = np.nan  # 1=上升, -1=下降

        if n < 3:
            return df

        # 找到第一个转折点
        last_pivot_price = df['close'].iloc[0]
        last_pivot_index = 0
        trend = 0  # 0=未确定, 1=上升, -1=下降

        for i in range(1, n):
            current_price = df['close'].iloc[i]
            price_change = abs(current_price - last_pivot_price) / last_pivot_price

            # 检查是否达到阈值
            if price_change >= self.threshold:
                # 确定趋势方向
                if current_price > last_pivot_price:
                    if trend != 1:
                        # 新的上升趋势开始，标记前一个低点
                        df['zigzag'].iloc[last_pivot_index] = last_pivot_price
                        df['zigzag_low'].iloc[last_pivot_index] = last_pivot_price
                        df['trend_direction'].iloc[last_pivot_index:i] = -1
                    trend = 1
                else:
                    if trend != -1:
                        # 新的下降趋势开始，标记前一个高点
                        df['zigzag'].iloc[last_pivot_index] = last_pivot_price
                        df['zigzag_high'].iloc[last_pivot_index] = last_pivot_price
                        df['trend_direction'].iloc[last_pivot_index:i] = 1
                    trend = -1

                # 更新转折点
                last_pivot_price = current_price
                last_pivot_index = i

        # 标记最后一个转折点
        df['zigzag'].iloc[last_pivot_index] = last_pivot_price
        if trend == 1:
            df['zigzag_high'].iloc[last_pivot_index] = last_pivot_price
        else:
            df['zigzag_low'].iloc[last_pivot_index] = last_pivot_price

        return df

    def get_zigzag_signal(self) -> Dict:
        """
        获取 ZigZag 信号

        Returns:
            ZigZag 信号字典
        """
        df_with_zigzag = self.calculate_zigzag()
        latest = df_with_zigzag.iloc[-1]

        # 获取最近的转折点
        zigzag_points = df_with_zigzag['zigzag'].dropna()
        if len(zigzag_points) >= 2:
            last_point = zigzag_points.iloc[-1]
            prev_point = zigzag_points.iloc[-2]

            if last_point > prev_point:
                trend = 'up'
                trend_strength = (last_point - prev_point) / prev_point
            else:
                trend = 'down'
                trend_strength = (prev_point - last_point) / prev_point

            last_change_date = zigzag_points.index[-1]
        else:
            trend = 'neutral'
            trend_strength = 0
            last_change_date = None

        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'last_change_date': last_change_date.strftime('%Y-%m-%d') if last_change_date is not None else None,
            'zigzag_points_count': len(zigzag_points),
            'current_price': latest['close'],
            'is_uptrend': trend == 'up',
            'is_downtrend': trend == 'down'
        }

    def get_recent_pivots(self, count: int = 5) -> List[Dict]:
        """
        获取最近的转折点

        Args:
            count: 转折点数量

        Returns:
            转折点列表
        """
        df_with_zigzag = self.calculate_zigzag()

        pivots = []
        zigzag_series = df_with_zigzag['zigzag'].dropna()

        for idx in zigzag_series.tail(count).index:
            price = df_with_zigzag['zigzag'].loc[idx]
            is_high = not pd.isna(df_with_zigzag['zigzag_high'].loc[idx])
            date = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)

            pivots.append({
                'date': date,
                'price': price,
                'type': 'high' if is_high else 'low'
            })

        return pivots
