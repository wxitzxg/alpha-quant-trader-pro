"""
K线数据管理模块
"""
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from stock_market.database import DatabaseManager
from stock_market.models import KLine, SyncRecord

logger = logging.getLogger(__name__)


class KLineDataManager:
    """K线数据管理器"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化K线数据管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager

    def sync_single_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_update: bool = False
    ) -> int:
        """
        同步单只股票K线数据

        Args:
            symbol: 股票代码
            interval: 周期 (1d, 5d, 10d, 1M)
            start_date: 开始日期 (YYYY-MM-DD)，None 表示从最后同步时间开始
            end_date: 结束日期 (YYYY-MM-DD)，None 表示到今天
            force_update: 是否强制更新已存在的数据

        Returns:
            成功同步的K线数量
        """
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        with self.db.get_session() as session:
            # 确定同步时间范围
            if start_date is None:
                # 增量同步：从最后同步时间开始
                start_date_obj, end_date_obj = self._get_incremental_range(
                    session, symbol, interval
                )
            else:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                else:
                    end_date_obj = date.today()

            if start_date_obj > end_date_obj:
                logger.info(f"No data to sync for {symbol} {interval}")
                return 0

            # 从数据源获取K线数据
            try:
                klines = aggregator.get_kline(
                    symbol=symbol,
                    interval=interval,
                    start_date=start_date_obj.strftime("%Y-%m-%d"),
                    end_date=end_date_obj.strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.error(f"Failed to get kline from data source: {e}")
                return 0

            if not klines:
                logger.warning(f"No kline data returned for {symbol}")
                return 0

            success_count = 0
            for kline in klines:
                try:
                    kline_date = kline.datetime.date()

                    # 检查是否已存在
                    existing = session.query(KLine).filter_by(
                        symbol=symbol,
                        date=kline_date,
                        interval=interval
                    ).first()

                    if existing:
                        if force_update:
                            # 更新现有记录
                            existing.open = kline.open
                            existing.high = kline.high
                            existing.low = kline.low
                            existing.close = kline.close
                            existing.volume = kline.volume
                            existing.amount = kline.amount
                            existing.sync_time = datetime.now()
                            success_count += 1
                            logger.debug(f"Updated kline: {symbol} {kline_date}")
                    else:
                        # 新增K线
                        new_kline = KLine(
                            symbol=symbol,
                            date=kline_date,
                            interval=interval,
                            open=kline.open,
                            high=kline.high,
                            low=kline.low,
                            close=kline.close,
                            volume=kline.volume,
                            amount=kline.amount,
                            source=getattr(kline, 'source', None),
                            sync_time=datetime.now()
                        )
                        session.add(new_kline)
                        success_count += 1
                        logger.debug(f"Added kline: {symbol} {kline_date}")

                except Exception as e:
                    logger.error(f"Failed to save kline for {symbol} on {kline.datetime}: {e}")
                    continue

            # 记录同步日志
            self._log_sync(
                sync_type="klines",
                symbol=symbol,
                interval=interval,
                start_date=start_date_obj,
                end_date=end_date_obj,
                status="success" if success_count > 0 else "failed",
                records_count=success_count
            )

            logger.info(f"Synced {success_count} klines for {symbol} {interval}")
            return success_count

    def _get_incremental_range(
        self,
        session,
        symbol: str,
        interval: str
    ) -> Tuple[date, date]:
        """
        获取增量同步的时间范围

        策略：
        1. 查询数据库中该股票+周期的最后同步时间
        2. 从最后同步时间的下一天开始同步
        3. 同步到当前日期

        Returns:
            (start_date, end_date)
        """
        from stock_market.models import Stock

        # 查询最后一条记录
        last_kline = session.query(KLine).filter_by(
            symbol=symbol,
            interval=interval
        ).order_by(KLine.date.desc()).first()

        if last_kline:
            # 从最后一天的下一天开始
            start_date = last_kline.date + timedelta(days=1)
        else:
            # 首次同步，查询股票上市日期
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if stock and stock.list_date:
                start_date = stock.list_date
            else:
                # 默认从2010年1月1日开始
                start_date = date(2010, 1, 1)

        end_date = date.today()

        return start_date, end_date

    def query_klines(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: str = "asc"
    ) -> List[KLine]:
        """
        查询K线数据

        Args:
            symbol: 股票代码
            interval: 周期
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数量限制
            order_by: 排序 (asc: 升序, desc: 降序)

        Returns:
            KLine 对象列表
        """
        with self.db.get_session() as session:
            query = session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            )

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(KLine.date >= start)

            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(KLine.date <= end)

            if order_by == "desc":
                query = query.order_by(KLine.date.desc())
            else:
                query = query.order_by(KLine.date.asc())

            if limit:
                query = query.limit(limit)

            return query.all()

    def get_latest_kline(self, symbol: str, interval: str = "1d") -> Optional[KLine]:
        """
        获取最新的K线数据

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            最新的 KLine 对象或 None
        """
        with self.db.get_session() as session:
            return session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            ).order_by(KLine.date.desc()).first()

    def get_kline_count(self, symbol: str, interval: str = "1d") -> int:
        """
        获取K线数据条数

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            K线数量
        """
        with self.db.get_session() as session:
            return session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            ).count()

    def _log_sync(self, sync_type: str, status: str, records_count: int, **kwargs):
        """记录同步日志"""
        with self.db.get_session() as session:
            record = SyncRecord(
                sync_type=sync_type,
                status=status,
                records_count=records_count,
                **kwargs
            )
            session.add(record)
