#!/usr/bin/env python3
"""
Base Technical Indicators - 基础技术指标计算模块

提供完整的趋势指标、动量指标、波动率指标、成交量指标计算
"""

import pandas as pd
import numpy as np
from ta.volatility import BollingerBands, AverageTrueRange
from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volume import OnBalanceVolumeIndicator
import warnings
warnings.filterwarnings('ignore')


class BaseIndicators:
    """基础技术指标计算类"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化基础指标计算器

        Args:
            df: pandas DataFrame，必须包含以下列：
                - 'open': 开盘价
                - 'high': 最高价
                - 'low': 最低价
                - 'close': 收盘价
                - 'volume': 成交量
        """
        self.df = df.copy()
        self._validate_data()

    def _validate_data(self):
        """验证数据格式"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必需的列：{col}")

        # 确保数据类型正确
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # 删除包含 NaN 的行
        self.df = self.df.dropna()

    def calculate_trend_indicators(self) -> pd.DataFrame:
        """计算趋势指标"""
        # 移动平均线
        self.df['ma5'] = SMAIndicator(close=self.df['close'], window=5).sma_indicator()
        self.df['ma10'] = SMAIndicator(close=self.df['close'], window=10).sma_indicator()
        self.df['ma20'] = SMAIndicator(close=self.df['close'], window=20).sma_indicator()
        self.df['ma50'] = SMAIndicator(close=self.df['close'], window=50).sma_indicator()
        self.df['ma200'] = SMAIndicator(close=self.df['close'], window=200).sma_indicator()

        # EMA 指数移动平均
        self.df['ema12'] = EMAIndicator(close=self.df['close'], window=12).ema_indicator()
        self.df['ema26'] = EMAIndicator(close=self.df['close'], window=26).ema_indicator()
        self.df['ema50'] = EMAIndicator(close=self.df['close'], window=50).ema_indicator()
        self.df['ema200'] = EMAIndicator(close=self.df['close'], window=200).ema_indicator()

        # MACD
        macd = MACD(close=self.df['close'], window_fast=12, window_slow=26, window_sign=9)
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_histogram'] = macd.macd_diff()

        # ADX
        self._calculate_adx()

        return self.df

    def _calculate_adx(self):
        """计算 ADX 指标"""
        adx = ADXIndicator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=14
        )
        self.df['adx'] = adx.adx()
        self.df['plus_di'] = adx.adx_pos()
        self.df['minus_di'] = adx.adx_neg()

    def calculate_momentum_indicators(self) -> pd.DataFrame:
        """计算动量指标"""
        # RSI
        self.df['rsi'] = RSIIndicator(close=self.df['close'], window=14).rsi()
        self.df['rsi_9'] = RSIIndicator(close=self.df['close'], window=9).rsi()
        self.df['rsi_21'] = RSIIndicator(close=self.df['close'], window=21).rsi()

        # 随机指标
        stoch = StochasticOscillator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=14,
            smooth_window=3
        )
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()

        # CCI
        self._calculate_cci()

        # Williams %R
        self._calculate_williams_r()

        return self.df

    def _calculate_cci(self):
        """计算 CCI 指标"""
        tp = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        self.df['cci'] = (tp - sma_tp) / (0.015 * mad)

    def _calculate_williams_r(self):
        """计算 Williams %R 指标"""
        highest_high = self.df['high'].rolling(window=14).max()
        lowest_low = self.df['low'].rolling(window=14).min()
        self.df['williams_r'] = -100 * (highest_high - self.df['close']) / (highest_high - lowest_low)

    def calculate_volatility_indicators(self) -> pd.DataFrame:
        """计算波动率指标"""
        # 布林带
        bb = BollingerBands(close=self.df['close'], window=20, window_dev=2)
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        self.df['bb_position'] = bb.bollinger_pband()

        # 带宽 (用于 VCP 检测)
        self.df['bb_bandwidth'] = (self.df['bb_upper'] - self.df['bb_lower']) / self.df['bb_middle']

        # ATR
        atr = AverageTrueRange(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=14
        )
        self.df['atr'] = atr.average_true_range()

        # 标准差
        self.df['std_20'] = self.df['close'].rolling(window=20).std()

        return self.df

    def calculate_volume_indicators(self) -> pd.DataFrame:
        """计算成交量指标"""
        # OBV
        obv = OnBalanceVolumeIndicator(close=self.df['close'], volume=self.df['volume'])
        self.df['obv'] = obv.on_balance_volume()

        # 成交量移动平均
        self.df['volume_ma5'] = self.df['volume'].rolling(window=5).mean()
        self.df['volume_ma20'] = self.df['volume'].rolling(window=20).mean()

        # 量比
        self.df['volume_ratio'] = self.df['volume'] / self.df['volume_ma5']

        return self.df

    def calculate_all_indicators(self) -> pd.DataFrame:
        """计算所有技术指标"""
        self.calculate_trend_indicators()
        self.calculate_momentum_indicators()
        self.calculate_volatility_indicators()
        self.calculate_volume_indicators()

        return self.df

    def get_latest_signals(self) -> dict:
        """获取最新的技术信号"""
        latest = self.df.iloc[-1]
        signals = {}

        # 趋势信号
        signals['ma_trend'] = self._get_ma_trend(latest)
        signals['macd_signal'] = self._get_macd_signal(latest)
        signals['adx_strength'] = self._get_adx_strength(latest)

        # 动量信号
        signals['rsi_condition'] = self._get_rsi_condition(latest)
        signals['stoch_condition'] = self._get_stoch_condition(latest)
        signals['cci_condition'] = self._get_cci_condition(latest)

        # 波动率信号
        signals['bb_position'] = self._get_bb_position(latest)
        signals['volatility_level'] = self._get_volatility_level(latest)

        # 成交量信号
        signals['volume_condition'] = self._get_volume_condition(latest)

        return signals

    def _get_ma_trend(self, latest: pd.Series) -> str:
        """获取均线趋势"""
        if latest['ma5'] > latest['ma10'] > latest['ma20']:
            return 'strong_uptrend'
        elif latest['ma5'] < latest['ma10'] < latest['ma20']:
            return 'strong_downtrend'
        elif latest['ma5'] > latest['ma20']:
            return 'weak_uptrend'
        elif latest['ma5'] < latest['ma20']:
            return 'weak_downtrend'
        else:
            return 'sideways'

    def _get_macd_signal(self, latest: pd.Series) -> str:
        """获取 MACD 信号"""
        if latest['macd'] > latest['macd_signal']:
            return 'bullish'
        elif latest['macd'] < latest['macd_signal']:
            return 'bearish'
        else:
            return 'neutral'

    def _get_adx_strength(self, latest: pd.Series) -> str:
        """获取 ADX 强度"""
        if latest['adx'] > 25:
            return 'strong_trend'
        elif latest['adx'] > 20:
            return 'moderate_trend'
        else:
            return 'weak_trend'

    def _get_rsi_condition(self, latest: pd.Series) -> str:
        """获取 RSI 状态"""
        if latest['rsi'] > 70:
            return 'overbought'
        elif latest['rsi'] < 30:
            return 'oversold'
        else:
            return 'neutral'

    def _get_stoch_condition(self, latest: pd.Series) -> str:
        """获取随机指标状态"""
        if latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
            return 'overbought'
        elif latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
            return 'oversold'
        elif latest['stoch_k'] > latest['stoch_d']:
            return 'bullish_crossover'
        elif latest['stoch_k'] < latest['stoch_d']:
            return 'bearish_crossover'
        else:
            return 'neutral'

    def _get_cci_condition(self, latest: pd.Series) -> str:
        """获取 CCI 状态"""
        if latest['cci'] > 100:
            return 'overbought'
        elif latest['cci'] < -100:
            return 'oversold'
        else:
            return 'neutral'

    def _get_bb_position(self, latest: pd.Series) -> str:
        """获取布林带位置"""
        if latest['close'] > latest['bb_upper']:
            return 'above_upper'
        elif latest['close'] < latest['bb_lower']:
            return 'below_lower'
        elif latest['close'] > latest['bb_middle']:
            return 'upper_half'
        else:
            return 'lower_half'

    def _get_volatility_level(self, latest: pd.Series) -> str:
        """获取波动率水平"""
        avg_atr = self.df['atr'].mean()
        if latest['atr'] > avg_atr * 1.5:
            return 'high'
        elif latest['atr'] < avg_atr * 0.5:
            return 'low'
        else:
            return 'normal'

    def _get_volume_condition(self, latest: pd.Series) -> str:
        """获取成交量状态"""
        if latest['volume_ratio'] > 2:
            return 'surge'
        elif latest['volume_ratio'] < 0.5:
            return 'shrink'
        else:
            return 'normal'
