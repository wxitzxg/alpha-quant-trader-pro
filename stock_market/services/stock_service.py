import logging
from typing import List, Optional
from datetime import datetime
from stock_market.models import Stock
from stock_market.repositories import StockRepository, SyncRecordRepository
from common.exceptions import handle_exceptions, BusinessError

logger = logging.getLogger(__name__)


@handle_exceptions
class StockService:
    """股票基础数据服务"""

    def __init__(self, stock_repo: StockRepository, sync_repo: SyncRecordRepository):
        """
        初始化股票数据服务

        Args:
            stock_repo: 股票仓库（依赖注入）
            sync_repo: 同步记录仓库（依赖注入）
        """
        self.repo = stock_repo
        self.sync_repo = sync_repo

    def sync_all_stocks(self, force_update: bool = False) -> int:
        """
        同步所有股票列表（全量）

        Args:
            force_update: 是否强制更新（覆盖现有数据）

        Returns:
            成功同步的股票数量
        """
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        # 从数据源获取股票列表
        try:
            stock_list = aggregator.get_stock_list()
        except Exception as e:
            logger.error(f"Failed to get stock list from data source: {e}")
            return 0

        if not stock_list:
            logger.warning("Empty stock list returned from data source")
            return 0

        success_count = 0
        for stock_data in stock_list:
            try:
                symbol = stock_data.get('symbol')
                if not symbol:
                    continue

                # 检查是否已存在
                existing = self.repo.get_by_symbol(symbol)

                if existing:
                    if force_update:
                        # 更新现有记录
                        for key, value in stock_data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.last_sync_time = datetime.now()
                        success_count += 1
                        logger.debug(f"Updated stock: {symbol}")
                else:
                    # 新增股票
                    stock = Stock(**stock_data)
                    stock.last_sync_time = datetime.now()
                    self.repo.add(stock)
                    success_count += 1
                    logger.debug(f"Added new stock: {symbol}")

            except Exception as e:
                logger.error(f"Failed to sync stock {stock_data.get('symbol')}: {e}")
                continue

        # 记录同步日志
        self._log_sync(
            sync_type="stocks",
            status="success",
            records_count=success_count
        )

        logger.info(f"Synced {success_count} stocks")
        return success_count

    def sync_stock_details(self, symbols: List[str]) -> int:
        """
        同步股票详细信息

        Args:
            symbols: 股票代码列表

        Returns:
            成功同步的数量
        """
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        success_count = 0

        for symbol in symbols:
            try:
                # 获取股票详细信息
                detail = aggregator.get_stock_detail(symbol)

                if detail:
                    stock = self.repo.get_by_symbol(symbol)
                    if stock:
                        # 更新详细信息
                        for key, value in detail.items():
                            if hasattr(stock, key):
                                setattr(stock, key, value)
                        stock.last_sync_time = datetime.now()
                        success_count += 1
                        logger.debug(f"Synced detail for {symbol}")

            except Exception as e:
                logger.error(f"Failed to sync detail for {symbol}: {e}")
                continue

        logger.info(f"Synced details for {success_count} stocks")
        return success_count

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """
        获取单只股票信息

        Args:
            symbol: 股票代码

        Returns:
            Stock 对象或 None
        """
        return self.repo.get_by_symbol(symbol)

    def get_stocks_by_industry(self, industry: str) -> List[Stock]:
        """
        按行业查询股票

        Args:
            industry: 行业名称

        Returns:
            股票列表
        """
        return self.repo.get_by_industry(industry)

    def get_stocks_by_concept(self, concept: str) -> List[Stock]:
        """
        按概念查询股票

        Args:
            concept: 概念名称 (如: "白酒")

        Returns:
            股票列表
        """
        return self.repo.get_by_concept(concept)

    def get_active_stocks(self) -> List[Stock]:
        """
        获取所有上市股票

        Returns:
            股票列表
        """
        return self.repo.get_active()

    def _log_sync(self, sync_type: str, status: str, records_count: int, **kwargs):
        """记录同步日志"""
        from stock_market.models import SyncRecord
        record = SyncRecord(
            sync_type=sync_type,
            status=status,
            records_count=records_count,
            **kwargs
        )
        self.sync_repo.add(record)
