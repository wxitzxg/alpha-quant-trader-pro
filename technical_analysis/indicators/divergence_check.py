#!/usr/bin/env python3
"""
Divergence Check (背离检测) - 检测价格与指标之间的背离现象

顶背离：价格创新高，但指标未创新高 (看跌信号)
底背离：价格创新低，但指标未创新低 (看涨信号)
"""

import pandas as pd
import numpy as np
from typing import Dict


class DivergenceCheck:
    """背离检测器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化背离检测器

        Args:
            df: pandas DataFrame，必须包含 'close'、'macd'、'macd_signal' 列
        """
        self.df = df.copy()
        self._validate_data()

    def _validate_data(self):
        """验证数据格式"""
        required_columns = ['close']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必需的列：{col}")

    def _find_extremes(self, series: pd.Series, window: int = 5, mode: str = 'max') -> pd.Series:
        """
        寻找极值点

        Args:
            series: 数据序列
            window: 窗口大小
            mode: 'max' 或 'min'

        Returns:
            极值点序列 (非极值点为 NaN)
        """
        result = pd.Series(index=series.index, dtype=float)

        for i in range(window, len(series) - window):
            sub_series = series.iloc[i - window:i + window + 1]

            if mode == 'max' and series.iloc[i] == sub_series.max():
                result.iloc[i] = series.iloc[i]
            elif mode == 'min' and series.iloc[i] == sub_series.min():
                result.iloc[i] = series.iloc[i]

        return result

    def detect_macd_divergence(self, lookback: int = 60) -> Dict:
        """
        检测 MACD 背离

        Args:
            lookback: 回溯天数

        Returns:
            背离检测结果
        """
        df_subset = self.df.tail(lookback).copy()

        # 需要 MACD 数据
        if 'macd' not in df_subset.columns or 'macd_signal' not in df_subset.columns:
            return {
                'bullish_divergence': {'detected': False, 'message': '缺少 MACD 数据'},
                'bearish_divergence': {'detected': False, 'message': '缺少 MACD 数据'}
            }

        # 寻找价格极值
        price_highs = self._find_extremes(df_subset['close'], window=5, mode='max')
        price_lows = self._find_extremes(df_subset['close'], window=5, mode='min')

        # 寻找 MACD 极值
        macd_highs = self._find_extremes(df_subset['macd'], window=5, mode='max')
        macd_lows = self._find_extremes(df_subset['macd'], window=5, mode='min')

        # 检测顶背离
        bullish_detected = False
        bearish_detected = False
        bullish_details = {}
        bearish_details = {}

        # 顶背离：价格创新高，MACD 未创新高
        valid_highs = price_highs.dropna().index
        if len(valid_highs) >= 2:
            last_high_idx = valid_highs[-1]
            prev_high_idx = valid_highs[-2]

            price_increased = df_subset['close'].iloc[last_high_idx] > df_subset['close'].iloc[prev_high_idx]
            macd_increased = df_subset['macd'].iloc[last_high_idx] > df_subset['macd'].iloc[prev_high_idx]

            if price_increased and not macd_increased:
                bearish_detected = True
                bearish_details = {
                    'price_change': df_subset['close'].iloc[last_high_idx] / df_subset['close'].iloc[prev_high_idx] - 1,
                    'macd_change': df_subset['macd'].iloc[last_high_idx] / df_subset['macd'].iloc[prev_high_idx] - 1,
                    'price_high_1': df_subset['close'].iloc[prev_high_idx],
                    'price_high_2': df_subset['close'].iloc[last_high_idx],
                    'macd_high_1': df_subset['macd'].iloc[prev_high_idx],
                    'macd_high_2': df_subset['macd'].iloc[last_high_idx]
                }

        # 底背离：价格创新低，MACD 未创新低
        valid_lows = price_lows.dropna().index
        if len(valid_lows) >= 2:
            last_low_idx = valid_lows[-1]
            prev_low_idx = valid_lows[-2]

            price_decreased = df_subset['close'].iloc[last_low_idx] < df_subset['close'].iloc[prev_low_idx]
            macd_decreased = df_subset['macd'].iloc[last_low_idx] < df_subset['macd'].iloc[prev_low_idx]

            if price_decreased and not macd_decreased:
                bullish_detected = True
                bullish_details = {
                    'price_change': df_subset['close'].iloc[last_low_idx] / df_subset['close'].iloc[prev_low_idx] - 1,
                    'macd_change': df_subset['macd'].iloc[last_low_idx] / df_subset['macd'].iloc[prev_low_idx] - 1,
                    'price_low_1': df_subset['close'].iloc[prev_low_idx],
                    'price_low_2': df_subset['close'].iloc[last_low_idx],
                    'macd_low_1': df_subset['macd'].iloc[prev_low_idx],
                    'macd_low_2': df_subset['macd'].iloc[last_low_idx]
                }

        return {
            'bullish_divergence': {
                'detected': bullish_detected,
                'details': bullish_details,
                'message': '发现底背离，看涨信号' if bullish_detected else '无底背离'
            },
            'bearish_divergence': {
                'detected': bearish_detected,
                'details': bearish_details,
                'message': '发现顶背离，看跌信号' if bearish_detected else '无顶背离'
            }
        }

    def detect_all_divergences(self, lookback: int = 60) -> Dict:
        """
        检测所有类型的背离

        Args:
            lookback: 回溯天数

        Returns:
            所有背离检测结果
        """
        results = {}

        # MACD 背离
        results['macd'] = self.detect_macd_divergence(lookback)

        return results
