#!/usr/bin/env python3
"""
Short-Term Stock Selector - 短线选股引擎

基于技术指标的短线选股策略，评分维度:
- RSI信号 (20分): 超卖/超买判断
- KDJ信号 (20分): 金叉/死叉判断
- MACD信号 (15分): 金叉/翻红判断
- 布林带信号 (15分): 下轨反弹判断
- 量价异动 (15分): 放量上涨判断
- 资金流向 (15分): 主力流入判断
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from stock_recommendation.engines.base_selector import BaseSelector
from stock_recommendation.strategies.strategy_config import (
    ShortTermWeights,
    IndicatorThresholds,
    ShortTermConfig,
    DEFAULT_SHORT_TERM_CONFIG,
    DEFAULT_RATING_THRESHOLDS,
    RatingThresholds,
)
from technical_analysis.indicators.base_indicators import BaseIndicators


class ShortTermSelector(BaseSelector):
    """
    短线选股引擎

    基于技术分析进行短线选股推荐，提供:
    - 多维度技术指标评分
    - 买入信号统计
    - ATR动态止损止盈
    """

    def __init__(
        self,
        config: Optional[ShortTermConfig] = None,
        rating_thresholds: Optional[RatingThresholds] = None
    ):
        """
        初始化短线选股引擎

        Args:
            config: 短线策略配置，默认使用 DEFAULT_SHORT_TERM_CONFIG
            rating_thresholds: 评级阈值配置
        """
        super().__init__(rating_thresholds or DEFAULT_RATING_THRESHOLDS)
        self.config = config or DEFAULT_SHORT_TERM_CONFIG
        self.weights = self.config.weights
        self.thresholds = self.config.thresholds

    def analyze_single_stock(
        self,
        code: str,
        kline_data: Optional[pd.DataFrame] = None,
        fund_flow: Optional[Dict[str, Any]] = None,
        stock_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析单只股票

        Args:
            code: 股票代码 (6位数字字符串)
            kline_data: K线数据 DataFrame，需包含 open, high, low, close, volume 列
            fund_flow: 资金流向数据，包含 main_net_inflow 字段 (单位: 元)
            stock_info: 股票基本信息 (可选)

        Returns:
            分析结果字典:
            - code: 股票代码
            - score: 综合评分 (0-100)
            - rating: 评级 (A+/A/B+/B/C/D)
            - recommendation: 是否推荐
            - signals: 信号详情
            - buy_signal_count: 买入信号数量
            - stop_loss: 止损价
            - take_profit: 止盈价
            - details: 各维度评分详情
            - error: 错误信息 (如果有)
        """
        # 标准化股票代码
        code = self._normalize_code(code)

        # 验证股票代码
        if not self._validate_stock_code(code):
            return self._create_error_result(code, "无效的股票代码")

        # 验证K线数据
        if kline_data is None or len(kline_data) < 50:
            return self._create_error_result(code, "K线数据不足，至少需要50条数据")

        try:
            # 计算技术指标
            indicators = BaseIndicators(kline_data)
            df = indicators.calculate_all_indicators()

            if len(df) < 2:
                return self._create_error_result(code, "计算指标后数据不足")

            # 获取最新两日数据用于信号判断
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # 各维度评分
            rsi_result = self._score_rsi(latest)
            kdj_result = self._score_kdj(df, latest, prev)
            macd_result = self._score_macd(latest, prev)
            bollinger_result = self._score_bollinger(latest, prev)
            volume_result = self._score_volume_price(latest, prev)

            # 资金流向评分
            fund_flow_value = fund_flow.get("main_net_inflow", 0) if fund_flow else 0
            fund_result = self._score_fund_flow(fund_flow_value)

            # 汇总评分
            score_details = {
                "rsi": rsi_result,
                "kdj": kdj_result,
                "macd": macd_result,
                "bollinger": bollinger_result,
                "volume_price": volume_result,
                "fund_flow": fund_result,
            }

            total_score = sum(r["score"] for r in score_details.values())

            # 统计买入信号
            buy_signals = self._count_buy_signals(score_details)

            # 判断是否推荐
            is_recommended = (
                total_score >= self.config.score_threshold
                and buy_signals >= self.config.min_buy_signals
            )

            # 计算止损止盈
            current_price = float(latest["close"])
            atr = float(latest["atr"]) if pd.notna(latest["atr"]) else current_price * 0.02

            trade_points = self._calc_trade_points(
                current_price=current_price,
                atr=atr,
                stop_multiplier=self.config.atr_stop_multiplier,
                profit_multiplier=self.config.atr_profit_multiplier
            )

            # 构建结果
            result = {
                "code": code,
                "score": round(total_score, 2),
                "rating": self._get_rating(total_score),
                "recommendation": is_recommended,
                "buy_signal_count": buy_signals,
                "current_price": self._convert_to_json_safe(current_price),
                "stop_loss": trade_points["stop_loss"],
                "take_profit": trade_points["take_profit"],
                "stop_loss_pct": trade_points["stop_loss_pct"],
                "take_profit_pct": trade_points["take_profit_pct"],
                "risk_reward_ratio": trade_points["risk_reward_ratio"],
                "details": self._convert_to_json_safe(score_details),
                "signals": self._build_signal_summary(score_details, latest),
            }

            # 添加股票基本信息
            if stock_info:
                result["stock_info"] = stock_info

            return result

        except Exception as e:
            return self._create_error_result(code, f"分析异常: {str(e)}")

    def _score_rsi(self, latest: pd.Series) -> Dict[str, Any]:
        """
        RSI评分 (满分20分)

        评分规则:
        - RSI < 30: 20分 (超卖)
        - RSI 30-40: 12分
        - RSI 40-60: 5分
        - RSI > 70: 0分 (超买)
        """
        rsi = float(latest["rsi"]) if pd.notna(latest["rsi"]) else 50

        if rsi < 30:
            score = 20
            signal = "oversold"
            desc = "RSI超卖，反弹机会"
        elif rsi < 40:
            score = 12
            signal = "near_oversold"
            desc = "RSI接近超卖"
        elif rsi <= 60:
            score = 5
            signal = "neutral"
            desc = "RSI中性"
        elif rsi <= 70:
            score = 3
            signal = "near_overbought"
            desc = "RSI接近超买"
        else:
            score = 0
            signal = "overbought"
            desc = "RSI超买，风险较高"

        return {
            "score": score,
            "max_score": self.weights.rsi,
            "signal": signal,
            "description": desc,
            "value": round(rsi, 2),
            "is_buy_signal": rsi < 40,
        }

    def _score_kdj(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        prev: pd.Series
    ) -> Dict[str, Any]:
        """
        KDJ评分 (满分20分)

        评分规则:
        - 金叉 + J<50: 20分
        - 超卖 (J<20): 15分
        - 死叉 + J>70: -10分
        - 超买 (J>80): -5分
        """
        # 计算KDJ指标
        kdj = self._calculate_kdj(df)
        k = kdj["k"]
        d = kdj["d"]
        j = kdj["j"]

        prev_k = kdj["prev_k"]
        prev_d = kdj["prev_d"]

        score = 0
        signal = "neutral"
        desc = "KDJ中性"

        # 判断金叉/死叉
        is_golden_cross = prev_k <= prev_d and k > d  # K上穿D
        is_death_cross = prev_k >= prev_d and k < d   # K下穿D

        if is_golden_cross and j < 50:
            score = 20
            signal = "golden_cross_oversold"
            desc = "KDJ金叉且J值较低，买入信号强"
        elif is_golden_cross:
            score = 15
            signal = "golden_cross"
            desc = "KDJ金叉"
        elif j < 20:
            score = 15
            signal = "oversold"
            desc = "J值超卖，反弹机会"
        elif is_death_cross and j > 70:
            score = -10
            signal = "death_cross_overbought"
            desc = "KDJ死叉且J值较高，卖出信号"
        elif is_death_cross:
            score = -5
            signal = "death_cross"
            desc = "KDJ死叉"
        elif j > 80:
            score = -5
            signal = "overbought"
            desc = "J值超买，风险较高"

        return {
            "score": score,
            "max_score": self.weights.kdj,
            "signal": signal,
            "description": desc,
            "value": {"k": round(k, 2), "d": round(d, 2), "j": round(j, 2)},
            "is_buy_signal": is_golden_cross or j < 30,
        }

    def _score_macd(
        self,
        latest: pd.Series,
        prev: pd.Series
    ) -> Dict[str, Any]:
        """
        MACD评分 (满分15分)

        评分规则:
        - 金叉: 15分
        - 翻红 (MACD柱>0): 10分
        - 死叉: -10分
        - 翻绿: -5分
        """
        macd = float(latest["macd"]) if pd.notna(latest["macd"]) else 0
        signal_line = float(latest["macd_signal"]) if pd.notna(latest["macd_signal"]) else 0
        histogram = float(latest["macd_histogram"]) if pd.notna(latest["macd_histogram"]) else 0

        prev_macd = float(prev["macd"]) if pd.notna(prev["macd"]) else 0
        prev_signal = float(prev["macd_signal"]) if pd.notna(prev["macd_signal"]) else 0
        prev_histogram = float(prev["macd_histogram"]) if pd.notna(prev["macd_histogram"]) else 0

        score = 0
        signal = "neutral"
        desc = "MACD中性"

        # 判断金叉/死叉
        is_golden_cross = prev_macd <= prev_signal and macd > signal_line
        is_death_cross = prev_macd >= prev_signal and macd < signal_line

        # 判断翻红/翻绿
        is_turning_red = prev_histogram <= 0 and histogram > 0
        is_turning_green = prev_histogram >= 0 and histogram < 0

        if is_golden_cross:
            score = 15
            signal = "golden_cross"
            desc = "MACD金叉，买入信号"
        elif is_turning_red:
            score = 10
            signal = "turning_red"
            desc = "MACD柱翻红，趋势转强"
        elif histogram > 0:
            score = 8
            signal = "bullish"
            desc = "MACD柱为正，多头趋势"
        elif is_death_cross:
            score = -10
            signal = "death_cross"
            desc = "MACD死叉，卖出信号"
        elif is_turning_green:
            score = -5
            signal = "turning_green"
            desc = "MACD柱翻绿，趋势转弱"

        return {
            "score": score,
            "max_score": self.weights.macd,
            "signal": signal,
            "description": desc,
            "value": {
                "macd": round(macd, 4),
                "signal": round(signal_line, 4),
                "histogram": round(histogram, 4)
            },
            "is_buy_signal": is_golden_cross or is_turning_red or histogram > 0,
        }

    def _score_bollinger(
        self,
        latest: pd.Series,
        prev: pd.Series
    ) -> Dict[str, Any]:
        """
        布林带评分 (满分15分)

        评分规则:
        - 下轨反弹: 15分
        - 中轨支撑: 10分
        - 触及上轨: -5分
        """
        close = float(latest["close"])
        bb_upper = float(latest["bb_upper"]) if pd.notna(latest["bb_upper"]) else close * 1.02
        bb_middle = float(latest["bb_middle"]) if pd.notna(latest["bb_middle"]) else close
        bb_lower = float(latest["bb_lower"]) if pd.notna(latest["bb_lower"]) else close * 0.98

        prev_close = float(prev["close"])
        prev_bb_lower = float(prev["bb_lower"]) if pd.notna(prev["bb_lower"]) else prev_close * 0.98

        score = 0
        signal = "neutral"
        desc = "布林带中性"

        # 计算价格在布林带中的位置
        bb_width = bb_upper - bb_lower
        if bb_width > 0:
            bb_position = (close - bb_lower) / bb_width
        else:
            bb_position = 0.5

        # 下轨反弹: 前一日接近或低于下轨，今日回升
        if prev_close <= prev_bb_lower * 1.01 and close > bb_lower:
            score = 15
            signal = "lower_bounce"
            desc = "下轨反弹，买入机会"
        elif close <= bb_lower * 1.01:
            score = 12
            signal = "near_lower"
            desc = "接近下轨，关注反弹"
        elif close >= bb_middle and bb_position <= 0.6:
            score = 10
            signal = "middle_support"
            desc = "中轨支撑，趋势稳定"
        elif close >= bb_upper * 0.99:
            score = -5
            signal = "near_upper"
            desc = "触及上轨，注意风险"
        elif bb_position < 0.3:
            score = 8
            signal = "lower_half"
            desc = "位于下轨区域"

        return {
            "score": score,
            "max_score": self.weights.bollinger,
            "signal": signal,
            "description": desc,
            "value": {
                "upper": round(bb_upper, 2),
                "middle": round(bb_middle, 2),
                "lower": round(bb_lower, 2),
                "position": round(bb_position, 3)
            },
            "is_buy_signal": signal in ["lower_bounce", "near_lower", "middle_support"],
        }

    def _score_volume_price(
        self,
        latest: pd.Series,
        prev: pd.Series
    ) -> Dict[str, Any]:
        """
        量价异动评分 (满分15分)

        评分规则:
        - 放量上涨: 15分
        - 温和放量 (>1.5倍且涨幅>2%): 12分
        - 放量下跌: -10分
        """
        close = float(latest["close"])
        prev_close = float(prev["close"])
        volume = float(latest["volume"]) if pd.notna(latest["volume"]) else 0
        prev_volume = float(prev["volume"]) if pd.notna(prev["volume"]) else volume

        volume_ma5 = float(latest["volume_ma5"]) if pd.notna(latest["volume_ma5"]) else volume

        score = 0
        signal = "neutral"
        desc = "量价正常"

        # 计算涨跌幅
        price_change_pct = (close - prev_close) / prev_close * 100 if prev_close > 0 else 0

        # 计算量比
        volume_ratio = volume / volume_ma5 if volume_ma5 > 0 else 1.0

        # 放量上涨: 量比>2 且 涨幅>3%
        if volume_ratio > 2.0 and price_change_pct > 3:
            score = 15
            signal = "volume_surge_up"
            desc = "放量上涨，资金介入明显"
        # 温和放量上涨: 量比>1.5 且 涨幅>2%
        elif volume_ratio > 1.5 and price_change_pct > 2:
            score = 12
            signal = "moderate_volume_up"
            desc = "温和放量上涨"
        # 放量下跌
        elif volume_ratio > 2.0 and price_change_pct < -3:
            score = -10
            signal = "volume_surge_down"
            desc = "放量下跌，资金流出"
        # 缩量上涨
        elif volume_ratio < 0.8 and price_change_pct > 0:
            score = 5
            signal = "shrink_volume_up"
            desc = "缩量上涨"
        # 缩量下跌
        elif volume_ratio < 0.8 and price_change_pct < 0:
            score = 3
            signal = "shrink_volume_down"
            desc = "缩量下跌，抛压较轻"

        return {
            "score": score,
            "max_score": self.weights.volume_price,
            "signal": signal,
            "description": desc,
            "value": {
                "volume_ratio": round(volume_ratio, 2),
                "price_change_pct": round(price_change_pct, 2)
            },
            "is_buy_signal": signal in ["volume_surge_up", "moderate_volume_up"],
        }

    def _score_fund_flow(self, main_net_inflow: float) -> Dict[str, Any]:
        """
        资金流向评分 (满分15分)

        评分规则:
        - 主力流入>500万: 15分
        - 主力流入>0: 8分
        - 主力流出>500万: 0分

        Args:
            main_net_inflow: 主力净流入金额 (单位: 元)
        """
        # 转换为万元
        inflow_wan = main_net_inflow / 10000

        score = 0
        signal = "neutral"
        desc = "资金流向中性"

        if inflow_wan > 500:
            score = 15
            signal = "strong_inflow"
            desc = f"主力大幅流入{inflow_wan:.0f}万"
        elif inflow_wan > 100:
            score = 12
            signal = "moderate_inflow"
            desc = f"主力流入{inflow_wan:.0f}万"
        elif inflow_wan > 0:
            score = 8
            signal = "slight_inflow"
            desc = f"主力小幅流入{inflow_wan:.0f}万"
        elif inflow_wan > -100:
            score = 5
            signal = "slight_outflow"
            desc = f"主力小幅流出{abs(inflow_wan):.0f}万"
        elif inflow_wan > -500:
            score = 3
            signal = "moderate_outflow"
            desc = f"主力流出{abs(inflow_wan):.0f}万"
        else:
            score = 0
            signal = "strong_outflow"
            desc = f"主力大幅流出{abs(inflow_wan):.0f}万"

        return {
            "score": score,
            "max_score": self.weights.fund_flow,
            "signal": signal,
            "description": desc,
            "value": {"main_net_inflow_wan": round(inflow_wan, 2)},
            "is_buy_signal": inflow_wan > 0,
        }

    def _calculate_kdj(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        计算KDJ指标

        使用标准KDJ计算方法:
        RSV = (Close - LowN) / (HighN - LowN) * 100
        K = SMA(RSV, 3)
        D = SMA(K, 3)
        J = 3K - 2D
        """
        n = 9  # KDJ周期

        # 获取最后几日数据
        if len(df) < n:
            return {"k": 50, "d": 50, "j": 50, "prev_k": 50, "prev_d": 50}

        # 计算RSV
        def calc_rsv(data):
            low_n = data["low"].min()
            high_n = data["high"].max()
            close = data["close"].iloc[-1]
            if high_n == low_n:
                return 50
            return (close - low_n) / (high_n - low_n) * 100

        # 计算最近两天的RSV
        rsv_values = []
        for i in range(-2, 0):
            window = df.iloc[i-n+1:i+1] if i + 1 <= -1 else df.iloc[i-n+1:]
            if len(window) >= n:
                rsv = calc_rsv(window)
            else:
                rsv = 50
            rsv_values.append(rsv)

        # 使用随机指标计算K、D
        # 使用ta库的stoch_k和stoch_d
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        k = float(latest["stoch_k"]) if pd.notna(latest.get("stoch_k")) else 50
        d = float(latest["stoch_d"]) if pd.notna(latest.get("stoch_d")) else 50
        prev_k = float(prev["stoch_k"]) if pd.notna(prev.get("stoch_k")) else 50
        prev_d = float(prev["stoch_d"]) if pd.notna(prev.get("stoch_d")) else 50

        # J值
        j = 3 * k - 2 * d

        return {
            "k": k,
            "d": d,
            "j": j,
            "prev_k": prev_k,
            "prev_d": prev_d
        }

    def _count_buy_signals(self, score_details: Dict[str, Dict]) -> int:
        """统计买入信号数量"""
        count = 0
        for detail in score_details.values():
            if detail.get("is_buy_signal", False):
                count += 1
        return count

    def _build_signal_summary(
        self,
        score_details: Dict[str, Dict],
        latest: pd.Series
    ) -> Dict[str, Any]:
        """构建信号摘要"""
        signals = []

        for name, detail in score_details.items():
            if detail.get("is_buy_signal"):
                signals.append({
                    "type": name,
                    "description": detail.get("description", "")
                })

        return {
            "buy_signals": signals,
            "rsi_condition": score_details["rsi"]["signal"],
            "kdj_condition": score_details["kdj"]["signal"],
            "macd_condition": score_details["macd"]["signal"],
            "bollinger_position": score_details["bollinger"]["signal"],
            "volume_condition": score_details["volume_price"]["signal"],
            "fund_flow_condition": score_details["fund_flow"]["signal"],
        }

    def _create_error_result(self, code: str, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "code": code,
            "score": 0,
            "rating": "D",
            "recommendation": False,
            "error": error_msg,
            "buy_signal_count": 0,
        }

    def analyze_batch(
        self,
        stocks_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量分析股票

        Args:
            stocks_data: 股票数据列表，每个元素包含:
                - code: 股票代码
                - kline_data: K线数据 DataFrame
                - fund_flow: 资金流向数据 (可选)
                - stock_info: 股票基本信息 (可选)

        Returns:
            分析结果列表
        """
        results = []
        for stock_data in stocks_data:
            code = stock_data.get("code", "")
            kline_data = stock_data.get("kline_data")
            fund_flow = stock_data.get("fund_flow")
            stock_info = stock_data.get("stock_info")

            result = self.analyze_single_stock(
                code=code,
                kline_data=kline_data,
                fund_flow=fund_flow,
                stock_info=stock_info
            )
            results.append(result)

        # 按评分排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return results

    def filter_recommended(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        过滤出推荐股票

        Args:
            results: analyze_batch 返回的结果列表

        Returns:
            推荐股票列表
        """
        return [
            r for r in results
            if r.get("recommendation", False)
        ]
