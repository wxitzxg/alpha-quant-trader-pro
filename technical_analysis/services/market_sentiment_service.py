"""
Market Sentiment Service - 市场情绪服务层

提供市场情绪评分功能，支持实时数据优先和 K 线数据降级
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session

from stock_market.repositories import StockRepository, KLineRepository
from data_sources.aggregator import DataSourceAggregator
from technical_analysis.schemas.market_sentiment import (
    MarketStockData,
    MarketSentimentResult,
)
from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator

logger = logging.getLogger(__name__)


class MarketSentimentService:
    """市场情绪评分服务"""

    def __init__(self, session: Session):
        """
        初始化市场情绪服务

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.stock_repo = StockRepository(session)
        self.kline_repo = KLineRepository(session)
        self.calculator = MarketSentimentCalculator()
        self.data_aggregator = DataSourceAggregator()

    def get_market_sentiment(
        self,
        use_realtime: bool = True,
        stock_filter: Optional[Dict] = None
    ) -> MarketSentimentResult:
        """
        获取市场情绪评分

        Args:
            use_realtime: 是否优先使用实时数据
            stock_filter: 可选的股票过滤条件

        Returns:
            市场情绪评分结果
        """
        stocks_data: List[MarketStockData] = []
        data_source = "unknown"

        # 尝试获取实时数据
        if use_realtime:
            try:
                stocks_data = self._get_realtime_data(stock_filter)
                if stocks_data:
                    data_source = "realtime"
                    logger.info(f"获取实时行情数据: {len(stocks_data)} 只股票")
            except Exception as e:
                logger.warning(f"实时数据获取失败: {e}，尝试 K 线数据")

        # 降级到 K 线数据
        if not stocks_data:
            try:
                stocks_data = self._get_kline_data(stock_filter)
                if stocks_data:
                    data_source = "kline"
                    logger.info(f"获取 K 线数据: {len(stocks_data)} 只股票")
            except Exception as e:
                logger.error(f"K 线数据获取失败: {e}")

        # 计算评分
        result = self.calculator.calculate(stocks_data)
        result.data_source = data_source

        return result

    def get_sentiment_for_stocks(
        self,
        symbols: List[str],
        use_realtime: bool = True
    ) -> MarketSentimentResult:
        """
        计算指定股票池的市场情绪

        Args:
            symbols: 股票代码列表
            use_realtime: 是否使用实时数据

        Returns:
            市场情绪评分结果
        """
        stocks_data: List[MarketStockData] = []
        data_source = "unknown"

        if use_realtime:
            try:
                quotes = self.data_aggregator.batch_get_realtime(symbols)
                stocks_data = self._quotes_to_stock_data(quotes)
                if stocks_data:
                    data_source = "realtime"
            except Exception as e:
                logger.warning(f"实时数据获取失败: {e}")

        if not stocks_data:
            try:
                klines = self.kline_repo.get_all_latest_klines()
                # 过滤指定股票
                klines = [k for k in klines if k.symbol in symbols]
                stocks_data = self._klines_to_stock_data(klines)
                if stocks_data:
                    data_source = "kline"
            except Exception as e:
                logger.error(f"K 线数据获取失败: {e}")

        result = self.calculator.calculate(stocks_data)
        result.data_source = data_source

        return result

    def _get_realtime_data(
        self,
        stock_filter: Optional[Dict] = None
    ) -> List[MarketStockData]:
        """获取实时行情数据"""
        # 获取所有上市股票代码
        stocks = self.stock_repo.get_active()
        symbols = [s.symbol for s in stocks]

        # 应用过滤条件
        if stock_filter:
            exclude_gem = stock_filter.get('exclude_gem', False)
            exclude_star = stock_filter.get('exclude_star', False)

            if exclude_gem:
                symbols = [s for s in symbols if not s.startswith('3')]
            if exclude_star:
                symbols = [s for s in symbols if not s.startswith('688')]

        # 分批获取实时数据 (每批 500 只)
        all_quotes = []
        batch_size = 500

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            try:
                quotes = self.data_aggregator.batch_get_realtime(batch)
                all_quotes.extend(quotes)
            except Exception as e:
                logger.warning(f"批量获取实时数据失败 (batch {i}): {e}")

        return self._quotes_to_stock_data(all_quotes)

    def _get_kline_data(
        self,
        stock_filter: Optional[Dict] = None
    ) -> List[MarketStockData]:
        """获取 K 线数据"""
        klines = self.kline_repo.get_all_latest_klines()

        # 应用过滤条件
        if stock_filter:
            exclude_gem = stock_filter.get('exclude_gem', False)
            exclude_star = stock_filter.get('exclude_star', False)

            if exclude_gem:
                klines = [k for k in klines if not k.symbol.startswith('3')]
            if exclude_star:
                klines = [k for k in klines if not k.symbol.startswith('688')]

        return self._klines_to_stock_data(klines)

    def _quotes_to_stock_data(self, quotes: List) -> List[MarketStockData]:
        """将 Quote 对象转换为 MarketStockData"""
        result = []

        for quote in quotes:
            if not quote:
                continue

            # 计算涨跌幅 (Quote.percent 是小数，需乘 100)
            change_pct = quote.percent * 100 if quote.percent else 0

            # 计算振幅
            amplitude = 0.0
            if quote.high and quote.low and quote.pre_close and quote.pre_close > 0:
                amplitude = ((quote.high - quote.low) / quote.pre_close) * 100

            result.append(MarketStockData(
                symbol=quote.symbol,
                name=quote.name or "",
                price=quote.price,
                change_pct=round(change_pct, 2),
                turnover=0.0,  # 实时数据通常无换手率
                amplitude=round(amplitude, 2)
            ))

        return result

    def _klines_to_stock_data(self, klines: List) -> List[MarketStockData]:
        """将 KLine 对象转换为 MarketStockData"""
        result = []

        for kline in klines:
            if not kline:
                continue

            # 计算涨跌幅
            change_pct = 0.0
            if kline.open and kline.open > 0:
                change_pct = ((kline.close - kline.open) / kline.open) * 100

            # 计算振幅
            amplitude = 0.0
            if kline.open and kline.open > 0:
                amplitude = ((kline.high - kline.low) / kline.open) * 100

            result.append(MarketStockData(
                symbol=kline.symbol,
                name="",  # K 线数据通常无名称
                price=float(kline.close),
                change_pct=round(change_pct, 2),
                turnover=float(kline.turnover) if kline.turnover else 0.0,
                amplitude=round(amplitude, 2)
            ))

        return result
