#!/usr/bin/env python3
"""数据源服务层 - 连接 API Router 和现有业务逻辑"""

import sys
sys.path.insert(0, '.')

from typing import Optional, List
from datetime import datetime
import pandas as pd

from data_sources import QuoteAPI, KLineAPI, FundamentalsAPI
from data_sources.aggregator import DataSourceAggregator, StockListAPI, TopListAPI, KLineStatsAPI
from data_sources.models import Quote, KLine


class DataSourceService:
    """数据源服务"""

    @staticmethod
    def get_realtime_quote(stock_code: str) -> Optional[dict]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            行情数据字典
        """
        try:
            quote = QuoteAPI.get_realtime(stock_code)
            if quote:
                return {
                    "ts_code": quote.ts_code or f"{stock_code}.SH",
                    "symbol": stock_code,
                    "name": quote.name or "Unknown",
                    "current_price": float(quote.current_price or 0),
                    "change": float(quote.change or 0),
                    "change_pct": float(quote.change_pct or 0),
                    "open": float(quote.open or 0),
                    "high": float(quote.high or 0),
                    "low": float(quote.low or 0),
                    "close": float(quote.close or 0),
                    "volume": int(quote.volume or 0),
                    "amount": float(quote.amount or 0),
                    "turnover_rate": float(quote.turnover_rate or 0) if quote.turnover_rate else None,
                    "update_time": datetime.now()
                }
        except Exception as e:
            print(f"Error getting quote for {stock_code}: {e}")
            return None
        return None

    @staticmethod
    def get_batch_quotes(symbols: List[str]) -> dict:
        """
        批量获取行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            股票代码 -> 行情数据字典
        """
        results = {}
        for symbol in symbols:
            quote = DataSourceService.get_realtime_quote(symbol)
            if quote:
                results[symbol] = quote
        return results

    @staticmethod
    def get_kline(
        stock_code: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 120
    ) -> Optional[List[dict]]:
        """
        获取K线数据
        
        Args:
            stock_code: 股票代码
            interval: 周期 (1d/1w/1m)
            start_date: 开始日期
            end_date: 结束日期
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        try:
            klines = KLineAPI.get(
                symbol=stock_code,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if isinstance(klines, pd.DataFrame) and not klines.empty:
                # 转换为字典列表
                return klines.to_dict('records')
            elif isinstance(klines, list):
                return klines
            
        except Exception as e:
            print(f"Error getting kline for {stock_code}: {e}")
            return None
        return []

    @staticmethod
    def get_batch_klines(
        symbols: List[str],
        interval: str = "1d",
        limit: int = 60
    ) -> dict:
        """
        批量获取K线
        
        Args:
            symbols: 股票代码列表
            interval: 周期
            limit: 每只股票的数据条数
            
        Returns:
            股票代码 -> K线数据列表
        """
        results = {}
        for symbol in symbols:
            klines = DataSourceService.get_kline(symbol, interval, limit=limit)
            if klines:
                results[symbol] = klines
        return results

    @staticmethod
    def get_stock_list(
        page: int = 1,
        page_size: int = 20,
        exchange: Optional[str] = None
    ) -> dict:
        """获取股票列表（分页）"""
        try:
            all_stocks = StockListAPI.get(exchange=exchange)
            start = (page - 1) * page_size
            end = start + page_size
            return {
                "success": True,
                "data": {
                    "stocks": all_stocks[start:end],
                    "total": len(all_stocks),
                    "page": page,
                    "page_size": page_size
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to get stock list: {e}"}


    @staticmethod
    def get_stock_info(stock_code: str) -> dict:
        """获取股票详情"""
        try:
            aggregator = DataSourceAggregator()
            detail = aggregator.get_stock_detail(stock_code)
            if detail:
                return {"success": True, "data": detail}
            return {"success": False, "message": f"Stock {stock_code} not found"}
        except Exception as e:
            return {"success": False, "message": f"Failed to get stock info: {e}"}

    @staticmethod
    def get_top_list(type: str, date: Optional[str] = None) -> dict:
        """获取涨跌排行"""
        try:
            items = TopListAPI.get(type=type, date=date)
            return {
                "success": True,
                "data": {
                    "type": type,
                    "date": date or datetime.now().strftime("%Y-%m-%d"),
                    "items": items,
                    "total": len(items)
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to get top list: {e}"}

    @staticmethod
    def get_kline_stats(symbol: str, period: str = "1y") -> dict:
        """获取K线统计"""
        try:
            stats = KLineStatsAPI.get(symbol=symbol, period=period)
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "message": f"Failed to get kline stats: {e}"}

    @staticmethod
    def get_financial_indicators(stock_code: str) -> dict:
        """获取财务指标"""
        try:
            now = datetime.now()
            year = now.year
            quarter = (now.month - 1) // 3 + 1
            if quarter == 0:
                quarter = 4
                year -= 1

            indicators = FundamentalsAPI.get_indicators(stock_code, year, quarter)
            if indicators:
                return {"success": True, "data": indicators}
            return {"success": False, "message": f"No financial indicators for {stock_code}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to get financial indicators: {e}"}
