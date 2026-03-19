"""
股票市场模块依赖注入容器
"""

from dependency_injector import containers, providers
from data_sources import DataSourceAggregator
from stock_market.repositories import StockRepository, KLineRepository, SyncRecordRepository
from stock_market.services import StockService, KLineService


class StockMarketContainer(containers.DeclarativeContainer):
    """
    股票市场模块容器

    依赖：common.Container 的 database_manager 和 data_source_aggregator
    """

    # ========== 外部依赖 ==========

    # 数据库会话（由外部提供）
    db_session = providers.Dependency()

    # 数据源聚合器（由外部提供）
    data_source_aggregator = providers.Dependency()

    # ========== 仓库层 ==========

    stock_repository = providers.Factory(
        StockRepository,
        session=db_session
    )

    kline_repository = providers.Factory(
        KLineRepository,
        session=db_session
    )

    sync_record_repository = providers.Factory(
        SyncRecordRepository,
        session=db_session
    )

    # ========== 服务层 ==========

    stock_service = providers.Factory(
        StockService,
        stock_repo=stock_repository,
        sync_repo=sync_record_repository
    )

    kline_service = providers.Factory(
        KLineService,
        kline_repo=kline_repository,
        sync_repo=sync_record_repository,
        stock_repo=stock_repository
    )

    # ========== 工具方法 ==========

    def get_services(self):
        """获取所有服务实例"""
        return {
            'stock_service': self.stock_service(),
            'kline_service': self.kline_service()
        }
