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
                # Quote 模型来自 data_sources/models.py，字段映射如下:
                # symbol, name, price, change, percent, volume, amount, open_price, high, low, pre_close
                exchange = "SH" if stock_code.startswith(('6', '9', '5')) else "SZ"
                return {
                    "ts_code": f"{stock_code}.{exchange}",
                    "symbol": stock_code,
                    "name": quote.name or "",
                    "current_price": float(quote.price or 0),
                    "change": float(quote.change or 0),
                    "change_pct": float(quote.percent or 0),
                    "open": float(quote.open_price or 0),
                    "high": float(quote.high or 0),
                    "low": float(quote.low or 0),
                    "pre_close": float(quote.pre_close or 0),
                    "close": float(quote.price or 0),
                    "volume": int(quote.volume or 0),
                    "amount": float(quote.amount or 0),
                    "turnover_rate": None,
                    "update_time": quote.timestamp or datetime.now()
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
                result = klines.to_dict('records')
            elif isinstance(klines, list):
                # 处理 KLine 对象列表
                result = []
                for k in klines:
                    if hasattr(k, 'model_dump'):
                        # Pydantic v2 模型
                        result.append(k.model_dump())
                    elif hasattr(k, 'dict'):
                        # Pydantic v1 模型
                        result.append(k.dict())
                    elif hasattr(k, 'close'):
                        # 手动提取字段
                        result.append({
                            'symbol': k.symbol,
                            'datetime': k.datetime,
                            'open': getattr(k, 'open_price', k.open) if hasattr(k, 'open_price') else k.open,
                            'high': k.high,
                            'low': k.low,
                            'close': k.close,
                            'volume': k.volume,
                            'amount': k.amount
                        })
                    else:
                        # 已经是字典
                        result.append(k)
            else:
                return []
            
            # 应用 limit 限制，返回最近的 N 条数据
            # 注意: K线数据按日期降序排列 (最新的在前)
            if limit and len(result) > limit:
                result = result[:limit]
            
            # 将数据反转为升序 (最旧的在前，最新的在后)
            # 这样更符合分析习惯，current_price = prices[-1]
            result = list(reversed(result))
            
            return result
            
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
            
            # 转换字段格式以匹配响应模型
            formatted_stocks = []
            for s in all_stocks:
                exchange_val = s.get('exchange', '')
                formatted_stocks.append({
                    "ts_code": f"{s.get('symbol', '')}.{exchange_val}",
                    "symbol": s.get('symbol', ''),
                    "name": s.get('name', ''),
                    "exchange": exchange_val,
                    "market": exchange_val,
                    "industry": s.get('industry'),
                    "list_date": s.get('list_date'),
                    "status": "L"  # 默认为上市状态
                })
            
            start = (page - 1) * page_size
            end = start + page_size
            return {
                "success": True,
                "data": {
                    "stocks": formatted_stocks[start:end],
                    "total": len(formatted_stocks),
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
            # 计算当前季度：(month-1)//3+1 结果范围 1-4
            quarter = (now.month - 1) // 3 + 1

            indicators = FundamentalsAPI.get_indicators(stock_code, year, quarter)
            if indicators:
                return {"success": True, "data": indicators}
            return {"success": False, "message": f"No financial indicators for {stock_code}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to get financial indicators: {e}"}
