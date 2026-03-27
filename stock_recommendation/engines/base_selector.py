#!/usr/bin/env python3
"""
Base Selector - 选股引擎基类

提供选股引擎的公共方法和抽象接口，供短线和中长线选股引擎继承。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from stock_recommendation.strategies.strategy_config import (
    RatingLevel,
    RatingThresholds,
    DEFAULT_RATING_THRESHOLDS,
)


class BaseSelector(ABC):
    """
    选股引擎抽象基类

    提供公共工具方法，子类需实现 analyze_single_stock 方法。
    """

    def __init__(
        self,
        rating_thresholds: Optional[RatingThresholds] = None
    ):
        """
        初始化基类选择器

        Args:
            rating_thresholds: 评级阈值配置，默认使用 DEFAULT_RATING_THRESHOLDS
        """
        self.rating_thresholds = rating_thresholds or DEFAULT_RATING_THRESHOLDS

    @abstractmethod
    def analyze_single_stock(self, code: str) -> Dict[str, Any]:
        """
        分析单只股票（抽象方法，子类必须实现）

        Args:
            code: 股票代码（如 '000001'）

        Returns:
            分析结果字典，包含评分、信号、止损止盈等信息
        """
        pass

    def _get_rating(self, score: float) -> str:
        """
        根据评分返回评级

        评级标准:
        - >=85: A+ (强烈推荐)
        - 70-84: A (推荐)
        - 60-69: B+ (可操作)
        - 50-59: B (关注)
        - 40-49: C (观望)
        - <40: D (不推荐)

        Args:
            score: 评分 (0-100)

        Returns:
            评级字符串 (A+/A/B+/B/C/D)
        """
        rating = self.rating_thresholds.get_rating(score)
        return rating.value

    def _convert_to_json_safe(self, obj: Any) -> Any:
        """
        转换 numpy/pandas 类型为 JSON 安全类型

        处理以下类型转换:
        - numpy.integer -> int
        - numpy.floating -> float
        - numpy.bool_ -> bool
        - numpy.ndarray -> list
        - pandas.Timestamp -> str (ISO format)
        - pandas.NaT -> None
        - numpy.nan -> None

        Args:
            obj: 待转换的对象

        Returns:
            JSON 安全的对象
        """
        if obj is None:
            return None

        # 处理 NaN 和 NaT
        if isinstance(obj, float) and np.isnan(obj):
            return None
        if pd.isna(obj):
            return None

        # 处理 numpy 数值类型
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj):
                return None
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return [self._convert_to_json_safe(item) for item in obj.tolist()]

        # 处理 pandas 时间类型
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, (pd.Timedelta, type(pd.NaT))):
            if pd.isna(obj):
                return None
            return str(obj)

        # 处理字典
        if isinstance(obj, dict):
            return {k: self._convert_to_json_safe(v) for k, v in obj.items()}

        # 处理列表/元组
        if isinstance(obj, (list, tuple)):
            return [self._convert_to_json_safe(item) for item in obj]

        return obj

    def _calc_trade_points(
        self,
        current_price: float,
        atr: float,
        stop_multiplier: float = 2.0,
        profit_multiplier: float = 3.0
    ) -> Dict[str, float]:
        """
        计算止损止盈点位

        计算公式:
        - 止损价 = 当前价 - ATR * 止损倍数
        - 止盈价 = 当前价 + ATR * 止盈倍数
        - 止损百分比 = (止损价 - 当前价) / 当前价 * 100
        - 止盈百分比 = (止盈价 - 当前价) / 当前价 * 100
        - 盈亏比 = 止盈百分比 / abs(止损百分比)

        Args:
            current_price: 当前价格
            atr: ATR 值 (Average True Range)
            stop_multiplier: 止损倍数 (默认 2.0)
            profit_multiplier: 止盈倍数 (默认 3.0)

        Returns:
            包含止损止盈信息的字典:
            - stop_loss: 止损价
            - take_profit: 止盈价
            - stop_loss_pct: 止损百分比 (负数)
            - take_profit_pct: 止盈百分比 (正数)
            - risk_reward_ratio: 盈亏比

        Raises:
            ValueError: 当参数无效时 (价格<=0, ATR<=0, 倍数<=0)
        """
        # 参数验证
        if current_price <= 0:
            raise ValueError(f"当前价格必须大于0，当前值: {current_price}")
        if atr <= 0:
            raise ValueError(f"ATR必须大于0，当前值: {atr}")
        if stop_multiplier <= 0:
            raise ValueError(f"止损倍数必须大于0，当前值: {stop_multiplier}")
        if profit_multiplier <= 0:
            raise ValueError(f"止盈倍数必须大于0，当前值: {profit_multiplier}")

        # 计算止损价
        stop_loss = current_price - atr * stop_multiplier
        # 确保止损价不为负
        stop_loss = max(stop_loss, 0.01)

        # 计算止盈价
        take_profit = current_price + atr * profit_multiplier

        # 计算百分比
        stop_loss_pct = (stop_loss - current_price) / current_price * 100
        take_profit_pct = (take_profit - current_price) / current_price * 100

        # 计算盈亏比
        if abs(stop_loss_pct) > 0.001:  # 避免除零
            risk_reward_ratio = abs(take_profit_pct / stop_loss_pct)
        else:
            risk_reward_ratio = float('inf')

        return {
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "stop_loss_pct": round(stop_loss_pct, 2),
            "take_profit_pct": round(take_profit_pct, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2)
        }

    def _validate_stock_code(self, code: str) -> bool:
        """
        验证股票代码格式

        Args:
            code: 股票代码

        Returns:
            是否有效
        """
        if not code or not isinstance(code, str):
            return False

        # 去除可能的前后空格
        code = code.strip()

        # A股代码通常是6位数字
        if len(code) != 6:
            return False

        if not code.isdigit():
            return False

        return True

    def _normalize_code(self, code: str) -> str:
        """
        标准化股票代码

        Args:
            code: 原始股票代码

        Returns:
            标准化后的代码 (6位数字字符串)
        """
        if not code:
            return ""

        # 去除可能的前缀 (如 sh, sz, SH, SZ)
        code = code.strip().lower()
        for prefix in ["sh", "sz", "bj"]:
            if code.startswith(prefix):
                code = code[2:]
                break

        return code.zfill(6)
