import logging
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from stock_market.models import KLine, SyncRecord
from stock_market.repositories import KLineRepository, SyncRecordRepository, StockRepository
from common.exceptions import handle_exceptions, BusinessError

logger = logging.getLogger(__name__)


@handle_exceptions
class KLineService:
    """K线数据服务"""

    def __init__(
        self,
        kline_repo: KLineRepository,
        sync_repo: SyncRecordRepository,
        stock_repo: StockRepository
    ):
        """
        初始化K线数据服务

        Args:
            kline_repo: K线仓库（依赖注入）
            sync_repo: 同步记录仓库（依赖注入）
            stock_repo: 股票仓库（依赖注入）
        """
        self.repo = kline_repo
        self.sync_repo = sync_repo
        self.stock_repo = stock_repo

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

        # 确定同步时间范围
        if start_date is None:
            # 增量同步：从最后同步时间开始
            start_date_obj, end_date_obj = self._get_incremental_range(symbol, interval)
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
                existing = self.repo.get_by_symbol_and_date(
                    symbol=symbol,
                    interval=interval,
                    start_date=kline_date.strftime("%Y-%m-%d"),
                    end_date=kline_date.strftime("%Y-%m-%d")
                )

                if existing and len(existing) > 0:
                    existing_kline = existing[0]
                    if force_update:
                        # 更新现有记录
                        existing_kline.open = kline.open
                        existing_kline.high = kline.high
                        existing_kline.low = kline.low
                        existing_kline.close = kline.close
                        existing_kline.volume = kline.volume
                        existing_kline.amount = kline.amount
                        existing_kline.sync_time = datetime.now()
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
                    self.repo.add(new_kline)
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

    def _get_incremental_range(self, symbol: str, interval: str) -> Tuple[date, date]:
        """
        获取增量同步的时间范围

        策略：
        1. 查询数据库中该股票+周期的最后同步时间
        2. 从最后同步时间的下一天开始同步
        3. 同步到当前日期

        Returns:
            (start_date, end_date)
        """
        # 查询最后一条记录
        last_kline = self.repo.get_latest_by_symbol(symbol, interval)

        if last_kline:
            # 从最后一天的下一天开始
            start_date = last_kline.date + timedelta(days=1)
        else:
            # 首次同步，查询股票上市日期
            stock = self.stock_repo.get_by_symbol(symbol)
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
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        klines = self.repo.get_by_symbol_and_date(
            symbol=symbol,
            interval=interval,
            start_date=start_date if start_date else "2010-01-01",
            end_date=end_date if end_date else date.today().strftime("%Y-%m-%d")
        )

        if order_by == "desc":
            klines.sort(key=lambda x: x.date, reverse=True)
        else:
            klines.sort(key=lambda x: x.date)

        if limit:
            klines = klines[:limit]

        return klines

    def get_latest_kline(self, symbol: str, interval: str = "1d") -> Optional[KLine]:
        """
        获取最新的K线数据

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            最新的 KLine 对象或 None
        """
        return self.repo.get_latest_by_symbol(symbol, interval)

    def get_kline_count(self, symbol: str, interval: str = "1d") -> int:
        """
        获取K线数据条数

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            K线数量
        """
        klines = self.repo.get_by_symbol_and_date(
            symbol=symbol,
            interval=interval,
            start_date="2010-01-01",
            end_date=date.today().strftime("%Y-%m-%d")
        )
        return len(klines)

    def _log_sync(self, sync_type: str, status: str, records_count: int, **kwargs):
        """记录同步日志"""
        record = SyncRecord(
            sync_type=sync_type,
            status=status,
            records_count=records_count,
            **kwargs
        )
        self.sync_repo.add(record)
