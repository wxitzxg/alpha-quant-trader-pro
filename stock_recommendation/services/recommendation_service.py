#!/usr/bin/env python3
"""
Recommendation Service - 股票推荐服务

协调选股引擎和数据源，提供股票扫描和分析功能。
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from stock_recommendation.models import (
    ScanRequest,
    ScanResult,
    StockRecommendation,
    StockPoolType,
    StrategyType,
    Rating,
    AnalysisDetail,
    DimensionScore,
)
from stock_recommendation.engines.short_term_selector import ShortTermSelector
from stock_recommendation.engines.long_term_selector import LongTermSelector
from stock_recommendation.strategies.strategy_config import (
    DEFAULT_SCAN_CONFIG,
    FilterRules,
)
from data_sources.aggregator import DataSourceAggregator
from stock_market.repositories import StockRepository

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    股票推荐服务

    提供股票扫描、分析功能，协调选股引擎和数据源。
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        short_term_selector: Optional[ShortTermSelector] = None,
        long_term_selector: Optional[LongTermSelector] = None,
        data_aggregator: Optional[DataSourceAggregator] = None,
    ):
        """
        初始化推荐服务

        Args:
            session: 数据库会话（用于获取股票池）
            short_term_selector: 短线选股引擎（可选，默认创建新实例）
            long_term_selector: 中长线选股引擎（可选，默认创建新实例）
            data_aggregator: 数据源聚合器（可选，默认使用单例）
        """
        self.session = session
        self._short_term_selector = short_term_selector
        self._long_term_selector = long_term_selector
        self._data_aggregator = data_aggregator
        self._scan_config = DEFAULT_SCAN_CONFIG

    @property
    def short_term_selector(self) -> ShortTermSelector:
        """延迟初始化短线选股引擎"""
        if self._short_term_selector is None:
            self._short_term_selector = ShortTermSelector()
        return self._short_term_selector

    @property
    def long_term_selector(self) -> LongTermSelector:
        """延迟初始化中长线选股引擎"""
        if self._long_term_selector is None:
            self._long_term_selector = LongTermSelector()
        return self._long_term_selector

    @property
    def data_aggregator(self) -> DataSourceAggregator:
        """延迟初始化数据聚合器"""
        if self._data_aggregator is None:
            self._data_aggregator = DataSourceAggregator()
        return self._data_aggregator

    def scan_stocks(self, request: ScanRequest) -> ScanResult:
        """
        扫描股票池

        根据请求参数扫描股票池，应用过滤规则，
        并行分析多只股票，汇总排序返回结果。

        Args:
            request: 扫描请求参数

        Returns:
            ScanResult 扫描结果
        """
        logger.info(
            f"Starting stock scan - strategy: {request.strategy_type}, "
            f"pool: {request.stock_pool}, top_n: {request.top_n}"
        )

        # 1. 获取股票池
        codes = self.get_stock_pool(
            stock_pool_type=request.stock_pool.value,
            custom_codes=request.custom_codes
        )
        logger.info(f"Stock pool size: {len(codes)}")

        # 2. 应用过滤规则
        filter_rules = {
            "exclude_gem": request.exclude_gem,
            "exclude_star": request.exclude_star,
            "min_score": request.min_score,
        }
        filtered_codes = self.apply_filters(codes, filter_rules)
        logger.info(f"Filtered stock pool size: {len(filtered_codes)}")

        # 3. 并行分析股票
        results = self._parallel_analyze(
            codes=filtered_codes,
            strategy_type=request.strategy_type.value,
            min_score=request.min_score
        )

        # 4. 排序并截取前N只
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_results = results[:request.top_n]

        # 5. 转换为 StockRecommendation 模型
        recommendations = []
        for r in top_results:
            if r.get("error"):
                continue

            try:
                recommendation = self._convert_to_recommendation(r)
                recommendations.append(recommendation)
            except Exception as e:
                logger.warning(f"Failed to convert result for {r.get('code')}: {e}")

        # 6. 构建返回结果
        return ScanResult(
            strategy_type=request.strategy_type.value,
            scan_time=datetime.now().isoformat(),
            total_analyzed=len(results),
            qualified_count=len([r for r in results if r.get("score", 0) >= request.min_score]),
            recommendations=recommendations,
            filters_applied=filter_rules
        )

    def analyze_stock(self, code: str, strategy_type: str = "both") -> Dict[str, Any]:
        """
        分析单只股票

        根据策略类型选择对应的选股引擎，返回详细评分和信号。

        Args:
            code: 股票代码
            strategy_type: 策略类型 (short/long/both)

        Returns:
            分析结果字典
        """
        result = {
            "code": code,
            "short_term": None,
            "long_term": None,
            "error": None
        }

        try:
            # 短线分析
            if strategy_type in ["short", "both"]:
                short_result = self.short_term_selector.analyze_single_stock(code)
                result["short_term"] = short_result

            # 中长线分析
            if strategy_type in ["long", "both"]:
                long_result = self.long_term_selector.analyze_single_stock(code)
                result["long_term"] = long_result

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to analyze stock {code}: {e}")

        return result

    def get_stock_pool(
        self,
        stock_pool_type: str,
        custom_codes: Optional[List[str]] = None
    ) -> List[str]:
        """
        获取股票池

        Args:
            stock_pool_type: 股票池类型 (all/watchlist/custom)
            custom_codes: 自定义股票代码列表

        Returns:
            股票代码列表
        """
        if stock_pool_type == StockPoolType.CUSTOM.value:
            return custom_codes or []

        if stock_pool_type == StockPoolType.WATCHLIST.value:
            # 自选股池 - 从数据库获取（如果有实现）
            if self.session:
                try:
                    repo = StockRepository(self.session)
                    # 这里可以扩展自选股逻辑
                    stocks = repo.get_active()
                    return [s.symbol for s in stocks[:100]]  # 限制数量
                except Exception as e:
                    logger.warning(f"Failed to get watchlist: {e}")
            return []

        # 全市场
        if stock_pool_type == StockPoolType.ALL.value:
            try:
                stock_list = self.data_aggregator.get_stock_list()
                return [s.get("symbol") for s in stock_list if s.get("symbol")]
            except Exception as e:
                logger.error(f"Failed to get all stocks: {e}")
                return []

        return []

    def apply_filters(self, codes: List[str], filters: Dict) -> List[str]:
        """
        应用过滤规则

        过滤规则包括：
        - 排除创业板（3开头）
        - 排除科创板（688开头）
        - 价格/成交量过滤（需要实时数据，暂不实现）

        Args:
            codes: 股票代码列表
            filters: 过滤规则配置

        Returns:
            过滤后的股票代码列表
        """
        filtered = []

        for code in codes:
            if not code or len(code) != 6:
                continue

            # 排除创业板（300xxx, 301xxx）
            if filters.get("exclude_gem", True):
                if code.startswith("30"):
                    continue

            # 排除科创板（688xxx, 689xxx）
            if filters.get("exclude_star", True):
                if code.startswith("68"):
                    continue

            # 排除北交所（8xxxxx, 4xxxxx）
            if filters.get("exclude_bse", True):
                if code.startswith("8") or code.startswith("4"):
                    continue

            # 排除ST股票（需要股票名称判断，这里暂不实现）
            # 价格和成交量过滤需要实时数据，这里暂不实现

            filtered.append(code)

        return filtered

    def _parallel_analyze(
        self,
        codes: List[str],
        strategy_type: str,
        min_score: int = 60
    ) -> List[Dict[str, Any]]:
        """
        并行分析多只股票

        Args:
            codes: 股票代码列表
            strategy_type: 策略类型
            min_score: 最低评分

        Returns:
            分析结果列表
        """
        results = []
        max_workers = self._scan_config.max_workers

        # 限制并发数量，避免过多请求
        batch_size = min(len(codes), self._scan_config.batch_size)
        codes_to_analyze = codes[:batch_size]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_code = {}
            for code in codes_to_analyze:
                if strategy_type == "short":
                    future = executor.submit(
                        self.short_term_selector.analyze_single_stock, code
                    )
                elif strategy_type == "long":
                    future = executor.submit(
                        self.long_term_selector.analyze_single_stock, code
                    )
                else:
                    # both - 优先使用短线分析（速度更快）
                    future = executor.submit(
                        self.short_term_selector.analyze_single_stock, code
                    )
                future_to_code[future] = code

            # 收集结果
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    result = future.result(timeout=self._scan_config.timeout)
                    if result and not result.get("error"):
                        # 只保留达到最低评分的股票
                        if result.get("score", 0) >= min_score:
                            results.append(result)
                except Exception as e:
                    logger.debug(f"Failed to analyze {code}: {e}")

        return results

    def _convert_to_recommendation(self, result: Dict[str, Any]) -> StockRecommendation:
        """
        将分析结果转换为 StockRecommendation 模型

        Args:
            result: 分析结果字典

        Returns:
            StockRecommendation 实例
        """
        # 转换评级
        rating_str = result.get("rating", "D")
        rating = self._get_rating_enum(rating_str)

        # 转换分析详情
        analysis_detail = None
        if result.get("analysis_detail"):
            analysis_detail = self._convert_analysis_detail(result["analysis_detail"])
        elif result.get("details"):
            analysis_detail = self._convert_details_to_analysis_detail(result["details"])

        return StockRecommendation(
            code=result.get("code", ""),
            name=result.get("name", ""),
            price=result.get("price", result.get("current_price", 0)),
            change_pct=result.get("change_pct", 0),
            score=result.get("score", 0),
            rating=rating,
            buy_signals=result.get("buy_signals", []),
            sell_signals=result.get("sell_signals", []),
            stop_loss=result.get("stop_loss", 0),
            take_profit=result.get("take_profit", 0),
            stop_loss_pct=result.get("stop_loss_pct", 0),
            take_profit_pct=result.get("take_profit_pct", 0),
            risk_reward_ratio=result.get("risk_reward_ratio", 0),
            recommend=result.get("recommend", result.get("recommendation", False)),
            analysis_detail=analysis_detail
        )

    def _get_rating_enum(self, rating_str: str) -> Rating:
        """将评级字符串转换为枚举"""
        rating_map = {
            "A+": Rating.STRONG_BUY,
            "A": Rating.BUY,
            "B+": Rating.HOLD,
            "B": Rating.HOLD,
            "C": Rating.SELL,
            "D": Rating.STRONG_SELL,
        }
        return rating_map.get(rating_str, Rating.SELL)

    def _convert_analysis_detail(self, detail: Dict[str, Any]) -> AnalysisDetail:
        """转换分析详情"""
        dimensions = {}

        for key in ["rsi", "kdj", "macd", "bollinger", "volume", "fund_flow",
                    "trend", "fundamentals", "valuation", "momentum",
                    "volume_energy", "dmi"]:
            if key in detail:
                d = detail[key]
                if isinstance(d, dict):
                    dimensions[key] = DimensionScore(
                        score=d.get("score", 0),
                        weight=d.get("weight", 0),
                        signal=d.get("signal", "hold"),
                        details=d.get("details")
                    )

        return AnalysisDetail(
            rsi=dimensions.get("rsi"),
            kdj=dimensions.get("kdj"),
            macd=dimensions.get("macd"),
            bollinger=dimensions.get("bollinger"),
            volume=dimensions.get("volume", dimensions.get("volume_energy")),
            fund_flow=dimensions.get("fund_flow"),
            trend=dimensions.get("trend"),
            support_resistance=None,
            overall_score=detail.get("overall_score", 0),
            analysis_time=datetime.now()
        )

    def _convert_details_to_analysis_detail(
        self,
        details: Dict[str, Any]
    ) -> Optional[AnalysisDetail]:
        """将短线引擎的 details 转换为 AnalysisDetail"""
        dimension_map = {
            "rsi": "rsi",
            "kdj": "kdj",
            "macd": "macd",
            "bollinger": "bollinger",
            "volume_price": "volume",
            "fund_flow": "fund_flow",
        }

        dimensions = {}
        for src_key, dst_key in dimension_map.items():
            if src_key in details:
                d = details[src_key]
                if isinstance(d, dict):
                    dimensions[dst_key] = DimensionScore(
                        score=d.get("score", 0),
                        weight=d.get("max_score", 0),
                        signal=d.get("signal", "hold"),
                        details=d.get("value")
                    )

        if not dimensions:
            return None

        return AnalysisDetail(
            rsi=dimensions.get("rsi"),
            kdj=dimensions.get("kdj"),
            macd=dimensions.get("macd"),
            bollinger=dimensions.get("bollinger"),
            volume=dimensions.get("volume"),
            fund_flow=dimensions.get("fund_flow"),
            overall_score=sum(d.score for d in dimensions.values()),
            analysis_time=datetime.now()
        )
