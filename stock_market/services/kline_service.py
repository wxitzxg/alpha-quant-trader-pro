import logging
from typing import List, Optional, Tuple, Dict, Any
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

        # 获取股票信息（用于 stock_id）
        stock = self.stock_repo.get_by_symbol(symbol)
        if not stock:
            logger.error(f"Stock {symbol} not found in database. Please sync stock list first.")
            return 0

        stock_id = stock.id

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
                        existing_kline.open = kline.open_price
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
                        stock_id=stock_id,
                        symbol=symbol,
                        date=kline_date,
                        interval=interval,
                        open=kline.open_price,
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

        # 提交事务
        try:
            self.repo.session.commit()
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            self.repo.session.rollback()
            return 0

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

    def sync_realtime_to_kline(
        self,
        symbols: List[str],
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        从实时行情同步今日K线

        Args:
            symbols: 股票代码列表
            interval: 周期（仅支持 1d）

        Returns:
            {
                "total_count": 10,
                "success_count": 8,
                "failed_count": 2,
                "skipped_count": 0,
                "details": [...]
            }
        """
        # 事务策略：每只股票独立提交，失败不影响其他股票
        from data_sources import DataSourceAggregator

        logger.info(f"Starting realtime to kline sync for {len(symbols)} symbols")

        aggregator = DataSourceAggregator()

        # 批量获取实时行情
        try:
            quotes = aggregator.batch_get_realtime(symbols)
        except Exception as e:
            logger.error(f"Failed to get realtime quotes: {e}")
            return {
                "total_count": len(symbols),
                "success_count": 0,
                "failed_count": len(symbols),
                "skipped_count": 0,
                "details": [
                    {"symbol": s, "status": "failed", "reason": "data_source_error"}
                    for s in symbols
                ]
            }

        today = date.today()
        details = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        # 用于记录哪些 symbol 在 quotes 中
        quote_symbols = {q.symbol for q in quotes}

        # 处理未返回行情的股票
        for symbol in symbols:
            if symbol not in quote_symbols:
                details.append({
                    "symbol": symbol,
                    "status": "failed",
                    "reason": "data_source_error"
                })
                failed_count += 1

        # 处理返回的行情
        for quote in quotes:
            # 检查 OHLC 数据是否完整
            if quote.open_price is None or quote.high is None or quote.low is None:
                logger.warning(f"Quote for {quote.symbol} missing OHLC data")
                details.append({
                    "symbol": quote.symbol,
                    "status": "skipped",
                    "reason": "no_ohlc_data"
                })
                skipped_count += 1
                continue

            try:
                # 获取 stock_id
                stock = self.stock_repo.get_by_symbol(quote.symbol)
                if not stock:
                    logger.warning(f"Stock {quote.symbol} not found in database")
                    details.append({
                        "symbol": quote.symbol,
                        "status": "failed",
                        "reason": "stock_not_found"
                    })
                    failed_count += 1
                    continue

                # 查询当日K线是否存在
                existing = self.repo.get_by_symbol_and_date(
                    symbol=quote.symbol,
                    interval=interval,
                    start_date=today.strftime("%Y-%m-%d"),
                    end_date=today.strftime("%Y-%m-%d")
                )

                if existing and len(existing) > 0:
                    # 覆盖更新
                    kline = existing[0]
                    kline.open = quote.open_price
                    kline.high = quote.high
                    kline.low = quote.low
                    kline.close = quote.price
                    kline.volume = quote.volume
                    kline.amount = quote.amount
                    kline.sync_time = datetime.now()
                    logger.debug(f"Updated kline: {quote.symbol} {today}")
                else:
                    # 新增
                    kline = KLine(
                        stock_id=stock.id,
                        symbol=quote.symbol,
                        date=today,
                        interval=interval,
                        open=quote.open_price,
                        high=quote.high,
                        low=quote.low,
                        close=quote.price,
                        volume=quote.volume,
                        amount=quote.amount,
                        source="realtime",
                        sync_time=datetime.now()
                    )
                    self.repo.add(kline)
                    logger.debug(f"Added kline: {quote.symbol} {today}")

                # 提交单只股票的事务
                self.repo.session.commit()
                success_count += 1
                details.append({
                    "symbol": quote.symbol,
                    "status": "updated",
                    "reason": None
                })

            except Exception as e:
                logger.error(f"Failed to sync kline for {quote.symbol}: {e}")
                self.repo.session.rollback()
                details.append({
                    "symbol": quote.symbol,
                    "status": "failed",
                    "reason": "db_error"
                })
                failed_count += 1

        logger.info(
            f"Realtime sync completed: total={len(symbols)}, "
            f"success={success_count}, failed={failed_count}, skipped={skipped_count}"
        )

        return {
            "total_count": len(symbols),
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "details": details
        }
