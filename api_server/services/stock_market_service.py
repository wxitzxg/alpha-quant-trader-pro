#!/usr/bin/env python3
"""股票市场服务层 - 连接 API Router 和现有 stock_market 模块"""

import sys
import os
sys.path.insert(0, '.')

from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from common.database import DatabaseManager
from stock_market.repositories import StockRepository, KLineRepository, SyncRecordRepository
from stock_market.services import StockService, KLineService


class StockMarketService:
    """股票市场服务"""

    def __init__(self, db_url: Optional[str] = None):
        """
        初始化股票市场服务

        Args:
            db_url: 数据库连接字符串
        """
        self.db_url = db_url or os.getenv("DATABASE__URL", "postgresql://localhost/stock_market")
        self.db_manager = DatabaseManager(self.db_url)

    def _get_services(self):
        """获取服务实例"""
        with self.db_manager.get_session() as session:
            stock_repo = StockRepository(session)
            kline_repo = KLineRepository(session)
            sync_repo = SyncRecordRepository(session)

            stock_service = StockService(stock_repo, sync_repo)
            kline_service = KLineService(kline_repo, sync_repo, stock_repo)

            return session, stock_service, kline_service

    def sync_all_stocks(self, force_update: bool = False) -> Dict:
        """
        同步所有股票列表

        Args:
            force_update: 是否强制更新

        Returns:
            同步结果字典
        """
        try:
            session, stock_service, _ = self._get_services()

            count = stock_service.sync_all_stocks(force_update=force_update)

            return {
                "success": True,
                "count": count,
                "message": f"Successfully synced {count} stocks"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to sync stocks: {str(e)}"
            }

    def get_stock_list(self, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取股票列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            股票列表响应
        """
        try:
            session, stock_service, _ = self._get_services()

            stocks = stock_service.get_active_stocks()

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_stocks = stocks[start:end]

            return {
                "success": True,
                "data": [
                    {
                        "ts_code": f"{s.symbol}.{s.exchange}",
                        "symbol": s.symbol,
                        "name": s.name,
                        "industry": s.industry,
                        "market": s.exchange,
                        "list_date": s.list_date.isoformat() if s.list_date else None,
                        "status": "L" if s.is_active else "D"
                    }
                    for s in paginated_stocks
                ],
                "total": len(stocks),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(stocks) + page_size - 1) // page_size
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def sync_single_kline(
        self,
        stock_code: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_update: bool = False
    ) -> Dict:
        """
        同步单只股票K线

        Args:
            stock_code: 股票代码
            interval: 周期 (1d/1w/1m)
            start_date: 开始日期
            end_date: 结束日期
            force_update: 是否强制更新

        Returns:
            同步结果
        """
        try:
            session, _, kline_service = self._get_services()

            count = kline_service.sync_single_kline(
                symbol=stock_code,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                force_update=force_update
            )

            return {
                "success": True,
                "count": count,
                "message": f"Successfully synced {count} klines for {stock_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to sync kline: {str(e)}"
            }

    def get_kline_data(
        self,
        stock_code: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        获取K线数据

        Args:
            stock_code: 股票代码
            interval: 周期
            start_date: 开始日期
            end_date: 结束日期
            limit: 数据条数限制

        Returns:
            K线数据
        """
        try:
            session, _, kline_service = self._get_services()

            klines = kline_service.query_klines(
                symbol=stock_code,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                order_by="desc"
            )

            return {
                "success": True,
                "data": [
                    {
                        "symbol": k.symbol,
                        "trade_date": k.date.isoformat() if k.date else "",
                        "open": float(k.open),
                        "high": float(k.high),
                        "low": float(k.low),
                        "close": float(k.close),
                        "volume": int(k.volume),
                        "amount": float(k.amount)
                    }
                    for k in klines
                ],
                "total": len(klines)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_sync_status(self, sync_type: str = "stocks") -> Dict:
        """
        获取同步状态

        Args:
            sync_type: 同步类型 (stocks/klines)

        Returns:
            同步状态
        """
        try:
            with self.db_manager.get_session() as session:
                sync_repo = SyncRecordRepository(session)

                # 查询最近的同步记录
                latest = sync_repo.get_latest_by_type(sync_type)

                if latest:
                    return {
                        "success": True,
                        "data": {
                            "sync_type": latest.sync_type,
                            "status": latest.status,
                            "records_count": latest.records_count,
                            "start_time": latest.start_time.isoformat() if latest.start_time else None,
                            "end_time": latest.end_time.isoformat() if latest.end_time else None,
                            "error_message": latest.error_message
                        }
                    }
                else:
                    return {
                        "success": True,
                        "data": None,
                        "message": "No sync records found"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def sync_realtime_to_kline(
        self,
        stock_codes: List[str],
        interval: str = "1d"
    ) -> Dict:
        """
        从实时行情同步今日K线

        Args:
            stock_codes: 股票代码列表
            interval: 周期

        Returns:
            同步结果
        """
        try:
            session, _, kline_service = self._get_services()

            result = kline_service.sync_realtime_to_kline(
                symbols=stock_codes,
                interval=interval
            )

            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
