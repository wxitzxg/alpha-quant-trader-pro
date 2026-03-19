"""
并发同步管理模块
"""
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime
from stock_market.database import DatabaseManager
from stock_market.models import SyncRecord
from stock_market.managers.kline_manager import KLineDataManager

logger = logging.getLogger(__name__)


class ConcurrentSyncManager:
    """并发同步管理器"""

    def __init__(self, db_manager: DatabaseManager, max_workers: int = 5):
        """
        初始化并发同步管理器

        Args:
            db_manager: 数据库管理器
            max_workers: 线程池大小
        """
        self.db = db_manager
        self.max_workers = max_workers

    def sync_klines_concurrently(
        self,
        symbols: List[str],
        interval: str = "1d",
        max_workers: Optional[int] = None,
        **sync_kwargs
    ) -> Dict[str, dict]:
        """
        并发同步多只股票K线

        Args:
            symbols: 股票代码列表
            interval: 周期
            max_workers: 线程池大小（覆盖默认值）
            **sync_kwargs: 传递给 sync_single_kline 的参数

        Returns:
            {symbol: {"status": "success/failed", "count": int, "error": str}}
        """
        max_workers = max_workers or self.max_workers
        results = {}
        manager = KLineDataManager(self.db)

        logger.info(f"Starting concurrent sync for {len(symbols)} stocks with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures: Dict[Future, str] = {}

            for symbol in symbols:
                future = executor.submit(
                    self._sync_single_kline_task,
                    manager,
                    symbol,
                    interval,
                    **sync_kwargs
                )
                futures[future] = symbol

            # 收集结果
            success_count = 0
            failed_count = 0

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    results[symbol] = result

                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failed_count += 1

                    logger.info(
                        f"[{success_count + failed_count}/{len(symbols)}] "
                        f"{symbol}: {result['status']} ({result.get('count', 0)} records)"
                    )

                except Exception as e:
                    failed_count += 1
                    results[symbol] = {
                        "status": "failed",
                        "error": str(e),
                        "count": 0
                    }
                    logger.error(f"Exception for {symbol}: {e}")

        # 记录总体同步日志
        self._log_batch_sync(
            sync_type="klines_batch",
            interval=interval,
            total_count=len(symbols),
            success_count=success_count,
            failed_count=failed_count,
            status="partial" if failed_count > 0 else "success"
        )

        logger.info(
            f"Concurrent sync completed: "
            f"{success_count} success, {failed_count} failed"
        )

        return results

    def _sync_single_kline_task(
        self,
        manager: KLineDataManager,
        symbol: str,
        interval: str,
        **sync_kwargs
    ) -> dict:
        """
        单个股票同步任务（线程池中执行）

        Args:
            manager: KLineDataManager 实例
            symbol: 股票代码
            interval: 周期
            **sync_kwargs: 同步参数

        Returns:
            {"status": "success/failed", "count": int, "error": str}
        """
        try:
            count = manager.sync_single_kline(
                symbol=symbol,
                interval=interval,
                **sync_kwargs
            )

            return {
                "status": "success",
                "count": count
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "count": 0
            }

    def _log_batch_sync(
        self,
        sync_type: str,
        interval: str,
        total_count: int,
        success_count: int,
        failed_count: int,
        status: str
    ):
        """记录批量同步日志"""
        with self.db.get_session() as session:
            record = SyncRecord(
                sync_type=sync_type,
                interval=interval,
                status=status,
                records_count=success_count,
                error_message=f"Failed: {failed_count}/{total_count}" if failed_count > 0 else None,
                created_at=datetime.now()
            )
            session.add(record)
