#!/usr/bin/env python3
"""
TD Sequential (神奇九转) - 用于识别趋势衰竭和反转点

低九：连续 9 日收盘价 < 4 日前收盘价 (下跌衰竭，买入信号)
高九：连续 9 日收盘价 > 4 日前收盘价 (上涨衰竭，卖出信号)
"""

import pandas as pd
import numpy as np
from typing import Dict


class TDSequential:
    """神奇九转指标计算器"""

    def __init__(
        self,
        df: pd.DataFrame,
        period: int = 9,
        compare_period: int = 4
    ):
        """
        初始化神奇九转计算器

        Args:
            df: pandas DataFrame，必须包含 'close' 列
            period: 九转周期 (默认 9)
            compare_period: 比较周期 (默认 4)
        """
        self.df = df.copy()
        self.period = period
        self.compare_period = compare_period
        self._validate_data()

    def _validate_data(self):
        """验证数据格式"""
        if 'close' not in self.df.columns:
            raise ValueError("缺少必需的列：close")

    def calculate_td_count(self) -> pd.DataFrame:
        """
        计算 TD 计数

        Returns:
            包含 TD 计数结果的 DataFrame
        """
        df = self.df.copy()
        n = len(df)

        # 初始化列
        td_buy_count = np.zeros(n)
        td_sell_count = np.zeros(n)
        td_buy_signal = np.zeros(n)
        td_sell_signal = np.zeros(n)

        for i in range(self.compare_period, n):
            # 低九条件：收盘价 < 4 日前收盘价
            if df['close'].iloc[i] < df['close'].iloc[i - self.compare_period]:
                td_buy_count[i] = td_buy_count[i - 1] + 1 if i > 0 else 1
            else:
                td_buy_count[i] = 0

            # 高九条件：收盘价 > 4 日前收盘价
            if df['close'].iloc[i] > df['close'].iloc[i - self.compare_period]:
                td_sell_count[i] = td_sell_count[i - 1] + 1 if i > 0 else 1
            else:
                td_sell_count[i] = 0

            # 检查是否完成九转
            if td_buy_count[i] >= self.period:
                td_buy_signal[i] = 1
            if td_sell_count[i] >= self.period:
                td_sell_signal[i] = 1

        df['td_buy_count'] = td_buy_count
        df['td_sell_count'] = td_sell_count
        df['td_buy_signal'] = td_buy_signal
        df['td_sell_signal'] = td_sell_signal

        return df

    def get_td_sequential(self) -> Dict:
        """
        获取神奇九转信号

        Returns:
            包含当前 TD 计数和信号的字典
        """
        df_with_td = self.calculate_td_count()
        latest = df_with_td.iloc[-1]

        return {
            'td_buy_count': int(latest['td_buy_count']),
            'td_sell_count': int(latest['td_sell_count']),
            'td_buy_signal': bool(latest['td_buy_signal']),
            'td_sell_signal': bool(latest['td_sell_signal']),
            'status': self._get_status(latest)
        }

    def _get_status(self, latest: pd.Series) -> str:
        """
        获取当前状态

        Args:
            latest: 最新一行数据

        Returns:
            状态字符串
        """
        buy_count = latest['td_buy_count']
        sell_count = latest['td_sell_count']

        if buy_count >= self.period:
            return 'low_nine_complete'  # 低九完成，潜在买入点
        elif sell_count >= self.period:
            return 'high_nine_complete'  # 高九完成，潜在卖出点
        elif buy_count > 0:
            return f'counting_low_{int(buy_count)}'  # 正在计数低九
        elif sell_count > 0:
            return f'counting_high_{int(sell_count)}'  # 正在计数高九
        else:
            return 'neutral'  # 无信号

    def check_valid_low_nine(
        self,
        trend_up: bool = False,
        oversold: bool = False
    ) -> bool:
        """
        检查有效的低九信号

        根据波段策略，低九仅在以下条件满足时有效：
        1. 趋势向上 (D1 条件)
        2. 位置超卖 (D3 条件)

        Args:
            trend_up: 趋势是否向上
            oversold: 是否超卖

        Returns:
            是否为有效低九
        """
        td_result = self.get_td_sequential()

        if not td_result['td_buy_signal']:
            return False

        # 如果提供了额外条件，需要满足
        if trend_up or oversold:
            return trend_up and oversold

        return True

    def get_recent_signals(self, lookback: int = 20) -> pd.DataFrame:
        """
        获取最近的 TD 信号

        Args:
            lookback: 回溯天数

        Returns:
            包含最近信号的 DataFrame
        """
        df_with_td = self.calculate_td_count()

        # 筛选出有信号的行
        signals = df_with_td[
            (df_with_td['td_buy_signal'] > 0) |
            (df_with_td['td_sell_signal'] > 0)
        ].tail(lookback)

        return signals
