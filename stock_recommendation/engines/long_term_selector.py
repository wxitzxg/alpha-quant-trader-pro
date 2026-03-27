#!/usr/bin/env python3
"""
Long Term Selector - 中长线选股引擎

基于趋势+基本面+估值+动量的综合评分体系，用于中长线投资选股。

评分维度 (满分130分，归一化到100分):
1. 趋势评分 (30分): MA趋势 + ADX强度
2. 基本面评分 (30分): ROE (10分) + 利润增长 (10分) + 股息率 (10分)
3. 估值评分 (15分): PEG估值
4. 动量评分 (15分): 20日涨幅
5. 量能评分 (15分): OBV趋势 + 量比
6. DMI评分 (15分): 多头趋势确认
7. 资金流评分 (10分): 主力净流入
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from stock_recommendation.engines.base_selector import BaseSelector
from stock_recommendation.strategies.strategy_config import (
    LongTermWeights,
    FundamentalsWeights,
    LongTermConfig,
    DEFAULT_LONG_TERM_CONFIG,
    RatingThresholds,
    DEFAULT_RATING_THRESHOLDS,
)
from data_sources.aggregator import DataSourceAggregator
from data_sources.models import KLine, Quote
from technical_analysis.indicators.base_indicators import BaseIndicators
from api_server.services.financial_service import FinancialService
from api_server.services.fundflow_service import FundFlowService


class LongTermSelector(BaseSelector):
    """
    中长线选股引擎

    继承自 BaseSelector，实现中长线投资选股逻辑。
    """

    def __init__(
        self,
        config: Optional[LongTermConfig] = None,
        rating_thresholds: Optional[RatingThresholds] = None
    ):
        """
        初始化中长线选股引擎

        Args:
            config: 长线策略配置，默认使用 DEFAULT_LONG_TERM_CONFIG
            rating_thresholds: 评级阈值配置
        """
        super().__init__(rating_thresholds=rating_thresholds or DEFAULT_RATING_THRESHOLDS)
        self.config = config or DEFAULT_LONG_TERM_CONFIG
        self.weights = self.config.weights
        self.fundamentals_weights = self.config.fundamentals_weights

        # 初始化数据服务
        self._data_aggregator = None
        self._financial_service = None
        self._fundflow_service = None

    @property
    def data_aggregator(self) -> DataSourceAggregator:
        """延迟初始化数据聚合器"""
        if self._data_aggregator is None:
            self._data_aggregator = DataSourceAggregator()
        return self._data_aggregator

    @property
    def financial_service(self) -> FinancialService:
        """延迟初始化财务服务"""
        if self._financial_service is None:
            self._financial_service = FinancialService()
        return self._financial_service

    @property
    def fundflow_service(self) -> FundFlowService:
        """延迟初始化资金流服务"""
        if self._fundflow_service is None:
            self._fundflow_service = FundFlowService()
        return self._fundflow_service

    def analyze_single_stock(self, code: str) -> Dict[str, Any]:
        """
        分析单只股票

        Args:
            code: 股票代码 (如 '000001')

        Returns:
            分析结果字典，包含评分、信号、止损止盈等信息
        """
        # 验证股票代码
        if not self._validate_stock_code(code):
            return self._create_error_result(code, "无效的股票代码")

        code = self._normalize_code(code)

        try:
            # 1. 获取实时行情
            quote = self._get_realtime_quote(code)
            if quote is None:
                return self._create_error_result(code, "无法获取实时行情数据")

            # 2. 获取K线数据
            klines = self._get_kline_data(code)
            if not klines:
                return self._create_error_result(code, "无法获取K线数据")

            # 3. 计算技术指标
            df = self._prepare_technical_data(klines)
            if df is None or len(df) < 50:
                return self._create_error_result(code, "K线数据不足，至少需要50条数据")

            # 4. 获取基本面数据
            fundamentals = self._get_fundamentals(code)

            # 5. 获取资金流数据
            fund_flow = self._get_fund_flow_data(code)

            # 6. 计算各维度评分
            scores = self._calculate_all_scores(df, fundamentals, fund_flow)

            # 7. 计算综合评分 (归一化到100分)
            raw_total = sum(scores.get(key, 0) for key in [
                "trend", "fundamentals", "valuation", "momentum",
                "volume_energy", "dmi", "fund_flow"
            ])
            normalized_score = raw_total * self.weights.normalization_factor

            # 8. 计算止损止盈
            latest = df.iloc[-1]
            current_price = float(quote.price)
            atr = float(latest.get("atr", 0))

            trade_points = {}
            if atr > 0:
                trade_points = self._calc_trade_points(
                    current_price=current_price,
                    atr=atr,
                    stop_multiplier=self.config.atr_stop_multiplier,
                    profit_multiplier=self.config.atr_profit_multiplier
                )

            # 9. 判断是否推荐
            recommend = normalized_score >= self.config.score_threshold

            # 10. 生成买卖信号
            buy_signals, sell_signals = self._generate_signals(
                scores, df, fundamentals, normalized_score
            )

            # 11. 构建结果
            result = {
                "code": code,
                "name": quote.name or "",
                "price": self._convert_to_json_safe(current_price),
                "change_pct": self._convert_to_json_safe(quote.percent * 100),
                "score": round(normalized_score, 2),
                "raw_score": round(raw_total, 2),
                "rating": self._get_rating(normalized_score),
                "recommend": recommend,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "analysis_detail": {
                    "trend": self._create_dimension_detail(scores, "trend", self.weights.trend),
                    "fundamentals": self._create_dimension_detail(scores, "fundamentals", self.weights.fundamentals),
                    "valuation": self._create_dimension_detail(scores, "valuation", self.weights.valuation),
                    "momentum": self._create_dimension_detail(scores, "momentum", self.weights.momentum),
                    "volume_energy": self._create_dimension_detail(scores, "volume_energy", self.weights.volume_energy),
                    "dmi": self._create_dimension_detail(scores, "dmi", self.weights.dmi),
                    "fund_flow": self._create_dimension_detail(scores, "fund_flow", self.weights.fund_flow),
                    "overall_score": round(normalized_score, 2),
                    "analysis_time": datetime.now().isoformat()
                },
                "stop_loss": trade_points.get("stop_loss", 0),
                "take_profit": trade_points.get("take_profit", 0),
                "stop_loss_pct": trade_points.get("stop_loss_pct", 0),
                "take_profit_pct": trade_points.get("take_profit_pct", 0),
                "risk_reward_ratio": trade_points.get("risk_reward_ratio", 0),
                "error": None
            }

            return self._convert_to_json_safe(result)

        except Exception as e:
            return self._create_error_result(code, f"分析异常: {str(e)}")

    def _get_realtime_quote(self, code: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            return self.data_aggregator.get_realtime(code)
        except Exception:
            return None

    def _get_kline_data(self, code: str, days: int = 250) -> List[KLine]:
        """获取K线数据"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            return self.data_aggregator.get_kline(code, "1d", start_date, end_date)
        except Exception:
            return []

    def _prepare_technical_data(self, klines: List[KLine]) -> Optional[pd.DataFrame]:
        """准备技术分析数据"""
        try:
            data = []
            for k in klines:
                data.append({
                    "open": k.open_price,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                    "date": k.datetime
                })

            df = pd.DataFrame(data)

            # 计算技术指标
            indicators = BaseIndicators(df)
            df = indicators.calculate_all_indicators()

            return df
        except Exception:
            return None

    def _get_fundamentals(self, code: str) -> Dict[str, Any]:
        """获取基本面数据"""
        try:
            # 获取最近季度的财务指标
            result = self.financial_service.get_financial_indicators(code, page=1, page_size=1)
            if result.get("success") and result.get("data"):
                return result["data"][0]
            return {}
        except Exception:
            return {}

    def _get_fund_flow_data(self, code: str) -> Dict[str, Any]:
        """获取资金流向数据"""
        try:
            result = self.fundflow_service.get_fund_flows(code, page=1, page_size=5)
            if result.get("success") and result.get("data"):
                return result["data"][0] if result["data"] else {}
            return {}
        except Exception:
            return {}

    def _calculate_all_scores(
        self,
        df: pd.DataFrame,
        fundamentals: Dict[str, Any],
        fund_flow: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        计算所有维度评分

        Args:
            df: 技术指标数据
            fundamentals: 基本面数据
            fund_flow: 资金流数据

        Returns:
            各维度评分字典
        """
        scores = {}

        # 1. 趋势评分 (30分)
        scores["trend"] = self._calc_trend_score(df)

        # 2. 基本面评分 (30分)
        scores["fundamentals"] = self._calc_fundamentals_score(fundamentals)

        # 3. 估值评分 (15分)
        scores["valuation"] = self._calc_valuation_score(df, fundamentals)

        # 4. 动量评分 (15分)
        scores["momentum"] = self._calc_momentum_score(df)

        # 5. 量能评分 (15分)
        scores["volume_energy"] = self._calc_volume_energy_score(df)

        # 6. DMI评分 (15分)
        scores["dmi"] = self._calc_dmi_score(df)

        # 7. 资金流评分 (10分)
        scores["fund_flow"] = self._calc_fund_flow_score(fund_flow)

        return scores

    def _calc_trend_score(self, df: pd.DataFrame) -> float:
        """
        计算趋势评分 (30分)

        评分规则:
        - MA趋势 (15分): 多头排列得分高
        - ADX强度 (15分): ADX>25表示趋势强
        """
        score = 0.0
        latest = df.iloc[-1]

        # MA趋势评分 (15分)
        ma5 = latest.get("ma5", 0)
        ma10 = latest.get("ma10", 0)
        ma20 = latest.get("ma20", 0)
        ma50 = latest.get("ma50", 0)
        close = latest.get("close", 0)

        if all(v > 0 for v in [ma5, ma10, ma20, ma50, close]):
            # 完美多头排列 (MA5 > MA10 > MA20 > MA50)
            if ma5 > ma10 > ma20 > ma50:
                score += 15
            # 多头排列 (MA5 > MA20 > MA50)
            elif ma5 > ma20 > ma50:
                score += 12
            # 部分多头 (MA5 > MA20)
            elif ma5 > ma20:
                score += 8
            # 价格站上MA20
            elif close > ma20:
                score += 5

        # ADX强度评分 (15分)
        adx = latest.get("adx", 0)
        plus_di = latest.get("plus_di", 0)
        minus_di = latest.get("minus_di", 0)

        if adx > 0:
            if adx >= 40:
                score += 15  # 非常强的趋势
            elif adx >= 30:
                score += 12  # 强趋势
            elif adx >= 25:
                score += 10  # 趋势确立
            elif adx >= 20:
                score += 5   # 趋势萌芽

            # +DI > -DI 表示多头趋势
            if plus_di > minus_di:
                score = min(score + 3, 30)

        return min(score, 30)

    def _calc_fundamentals_score(self, fundamentals: Dict[str, Any]) -> float:
        """
        计算基本面评分 (30分)

        评分规则:
        - ROE (10分): >=20%得10分，>=15%得8分，>=10%得5分
        - 利润增长率 (10分): >=25%得10分，>=15%得7分，>=10%得5分
        - 股息率 (10分): >=4%得10分，>=2%得6分，>=1%得3分
        """
        score = 0.0

        # ROE评分 (10分)
        roe = fundamentals.get("roe", 0)
        if isinstance(roe, (int, float)):
            if roe >= 0.20:  # 20%
                score += 10
            elif roe >= 0.15:  # 15%
                score += 8
            elif roe >= 0.10:  # 10%
                score += 5

        # 利润增长率评分 (10分)
        profit_growth = fundamentals.get("net_profit_growth", 0)
        if isinstance(profit_growth, (int, float)):
            if profit_growth >= 0.25:  # 25%
                score += 10
            elif profit_growth >= 0.15:  # 15%
                score += 7
            elif profit_growth >= 0.10:  # 10%
                score += 5

        # 股息率评分 (10分)
        dividend_yield = fundamentals.get("dividend_yield", 0)
        if isinstance(dividend_yield, (int, float)):
            if dividend_yield >= 0.04:  # 4%
                score += 10
            elif dividend_yield >= 0.02:  # 2%
                score += 6
            elif dividend_yield >= 0.01:  # 1%
                score += 3

        return min(score, 30)

    def _calc_valuation_score(
        self,
        df: pd.DataFrame,
        fundamentals: Dict[str, Any]
    ) -> float:
        """
        计算估值评分 (15分)

        PEG估值:
        - <0.8: 15分 (低估)
        - 0.8-1.2: 10分 (合理)
        - 1.2-2.0: 5分 (偏高)
        - >=2.0: 0分 (高估)
        """
        pe_ratio = fundamentals.get("pe_ratio", 0)
        profit_growth = fundamentals.get("net_profit_growth", 0)

        # 如果没有PE比率，尝试从其他数据计算或返回中等分数
        if not isinstance(pe_ratio, (int, float)) or pe_ratio <= 0:
            return 7.5  # 默认中等估值

        # 计算PEG
        if isinstance(profit_growth, (int, float)) and profit_growth > 0:
            peg = pe_ratio / (profit_growth * 100)
        else:
            # 没有利润增长率，无法计算PEG
            return 7.5

        # 根据PEG评分
        if peg < 0.8:
            return 15
        elif peg < 1.2:
            return 10
        elif peg < 2.0:
            return 5
        else:
            return 0

    def _calc_momentum_score(self, df: pd.DataFrame) -> float:
        """
        计算动量评分 (15分)

        基于20日涨幅计算:
        - 涨幅>=20%: 15分
        - 涨幅>=10%: 12分
        - 涨幅>=5%: 8分
        - 涨幅>=0%: 5分
        - 涨幅<0%: 按比例递减
        """
        if len(df) < 20:
            return 0

        # 计算20日涨幅
        close_20d_ago = df.iloc[-20]["close"]
        close_today = df.iloc[-1]["close"]

        if close_20d_ago <= 0:
            return 0

        pct_change = (close_today - close_20d_ago) / close_20d_ago

        # 评分
        if pct_change >= 0.20:
            return 15
        elif pct_change >= 0.10:
            return 12
        elif pct_change >= 0.05:
            return 8
        elif pct_change >= 0:
            return 5
        elif pct_change >= -0.10:
            return 3
        else:
            return 0

    def _calc_volume_energy_score(self, df: pd.DataFrame) -> float:
        """
        计算量能评分 (15分)

        评分规则:
        - OBV趋势 (8分): OBV上升趋势得分高
        - 量比 (7分): 量比>1表示放量
        """
        score = 0.0
        latest = df.iloc[-1]

        # OBV趋势评分 (8分)
        obv = latest.get("obv", 0)
        obv_ma20 = df["obv"].rolling(20).mean().iloc[-1] if "obv" in df.columns and len(df) >= 20 else 0

        if obv > 0 and obv_ma20 > 0:
            if obv > obv_ma20 * 1.2:  # OBV明显高于均线
                score += 8
            elif obv > obv_ma20:
                score += 6
            elif obv > obv_ma20 * 0.9:
                score += 4

        # 量比评分 (7分)
        volume_ratio = latest.get("volume_ratio", 0)
        if volume_ratio > 0:
            if volume_ratio >= 2.0:  # 放量明显
                score += 7
            elif volume_ratio >= 1.5:
                score += 5
            elif volume_ratio >= 1.0:
                score += 3

        return min(score, 15)

    def _calc_dmi_score(self, df: pd.DataFrame) -> float:
        """
        计算DMI评分 (15分)

        DMI多头趋势确认:
        - +DI > -DI 且 ADX >= 25: 满分
        - +DI > -DI 且 ADX >= 20: 高分
        - 其他情况按比例给分
        """
        score = 0.0
        latest = df.iloc[-1]

        adx = latest.get("adx", 0)
        plus_di = latest.get("plus_di", 0)
        minus_di = latest.get("minus_di", 0)

        if adx <= 0:
            return 0

        # 多头趋势强度
        if plus_di > minus_di:
            # 多头占优
            if adx >= 25:
                score += 15  # 强多头趋势
            elif adx >= 20:
                score += 12  # 中等多头趋势
            elif adx >= 15:
                score += 8   # 弱多头趋势
            else:
                score += 5   # 多头萌芽

            # +DI明显高于-DI
            if plus_di > minus_di * 1.5:
                score = min(score + 2, 15)
        else:
            # 空头占优
            if adx >= 25:
                score += 0   # 强空头趋势，不加分
            elif adx >= 20:
                score += 3   # 中等空头
            else:
                score += 5   # 趋势不明显

        return min(score, 15)

    def _calc_fund_flow_score(self, fund_flow: Dict[str, Any]) -> float:
        """
        计算资金流评分 (10分)

        主力净流入评分:
        - 大单净流入为正: 高分
        - 主力净流入为正: 中等分数
        - 流出: 低分
        """
        score = 0.0

        # 尝试获取主力净流入数据
        # Investoday API 返回的字段名可能不同
        main_net_inflow = fund_flow.get("mainNetInflow") or fund_flow.get("main_net_inflow") or fund_flow.get("netInflow")
        large_net_inflow = fund_flow.get("largeNetInflow") or fund_flow.get("large_net_inflow")

        if main_net_inflow is not None:
            try:
                inflow_value = float(main_net_inflow)
                if inflow_value > 0:
                    # 主力净流入为正
                    score += 8
                    if large_net_inflow and float(large_net_inflow) > 0:
                        score += 2
                elif inflow_value >= -10000000:  # 小幅流出
                    score += 4
                # 大幅流出不加分
            except (ValueError, TypeError):
                score += 5  # 默认中等分数

        return min(score, 10)

    def _generate_signals(
        self,
        scores: Dict[str, float],
        df: pd.DataFrame,
        fundamentals: Dict[str, Any],
        total_score: float
    ) -> tuple:
        """
        生成买卖信号

        Args:
            scores: 各维度评分
            df: 技术数据
            fundamentals: 基本面数据
            total_score: 综合评分

        Returns:
            (买入信号列表, 卖出信号列表)
        """
        buy_signals = []
        sell_signals = []

        latest = df.iloc[-1]

        # 趋势信号
        if scores.get("trend", 0) >= 20:
            buy_signals.append("趋势向上，MA多头排列")
        elif scores.get("trend", 0) < 10:
            sell_signals.append("趋势走弱")

        # 基本面信号
        if scores.get("fundamentals", 0) >= 25:
            buy_signals.append("基本面优秀")
        elif scores.get("fundamentals", 0) < 15:
            sell_signals.append("基本面一般")

        # 估值信号
        if scores.get("valuation", 0) >= 10:
            buy_signals.append("估值合理或低估")

        # 动量信号
        if scores.get("momentum", 0) >= 12:
            buy_signals.append("动量强劲")

        # DMI信号
        plus_di = latest.get("plus_di", 0)
        minus_di = latest.get("minus_di", 0)
        if plus_di > minus_di and scores.get("dmi", 0) >= 12:
            buy_signals.append("DMI多头确认")

        # 资金流信号
        if scores.get("fund_flow", 0) >= 8:
            buy_signals.append("主力资金流入")

        return buy_signals, sell_signals

    def _create_dimension_detail(
        self,
        scores: Dict[str, float],
        dimension: str,
        weight: float
    ) -> Dict[str, Any]:
        """
        创建维度详情

        Args:
            scores: 各维度评分
            dimension: 维度名称
            weight: 权重

        Returns:
            维度详情字典
        """
        score = scores.get(dimension, 0)
        return {
            "score": score,
            "weight": weight,
            "signal": "buy" if score >= weight * 0.6 else ("sell" if score < weight * 0.3 else "hold"),
            "details": None
        }

    def _create_error_result(self, code: str, error_msg: str) -> Dict[str, Any]:
        """
        创建错误结果

        Args:
            code: 股票代码
            error_msg: 错误信息

        Returns:
            错误结果字典
        """
        return {
            "code": code,
            "name": "",
            "price": 0,
            "change_pct": 0,
            "score": 0,
            "raw_score": 0,
            "rating": "D",
            "recommend": False,
            "buy_signals": [],
            "sell_signals": [],
            "analysis_detail": None,
            "stop_loss": 0,
            "take_profit": 0,
            "stop_loss_pct": 0,
            "take_profit_pct": 0,
            "risk_reward_ratio": 0,
            "error": error_msg
        }
