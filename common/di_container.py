"""
依赖注入容器配置

使用 dependency_injector 管理模块依赖关系
"""

from dependency_injector import containers, providers
from common.database import DatabaseManager
from common.config import get_config
from data_sources import DataSourceAggregator


class Container(containers.DeclarativeContainer):
    """
    依赖注入容器（根容器）

    管理所有模块的依赖关系
    子模块使用动态容器（DynamicContainer）
    """

    # ========== 配置 ==========
    config = providers.Configuration()

    # ========== 数据源层 ==========

    # 数据库管理器
    database_manager = providers.Singleton(
        DatabaseManager,
        db_url=config.database.url,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        pool_pre_ping=config.database.pool_pre_ping,
        pool_recycle=config.database.pool_recycle
    )

    # 数据源聚合器
    data_source_aggregator = providers.Singleton(
        DataSourceAggregator,
        config_path=config.data_source.config_path
    )

    # ========== 子模块容器 ==========

    # 注：子模块容器在需要时动态创建，使用 DynamicContainer

    # ========== 工厂方法 ==========

    @classmethod
    def create_container(cls) -> "Container":
        """
        创建容器实例

        从全局配置加载配置
        """
        container = cls()
        config = get_config()

        # 配置容器
        container.config.from_dict({
            "database": {
                "url": config.database.url,
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow,
                "pool_pre_ping": config.database.pool_pre_ping,
                "pool_recycle": config.database.pool_recycle,
            },
            "data_source": {
                "config_path": config.data_source.config_path,
                "timeout": config.data_source.timeout,
                "max_retries": config.data_source.max_retries,
            },
        })

        return container

    def create_stock_market_container(self, db_session):
        """
        创建股票市场模块容器

        Args:
            db_session: 数据库会话

        Returns:
            StockMarketContainer 实例
        """
        from stock_market.containers import StockMarketContainer

        container = StockMarketContainer()
        container.db_session.override(db_session)
        container.data_source_aggregator.override(self.data_source_aggregator())

        return container

    def create_portfolio_manager_container(self, db_session):
        """
        创建持仓管理模块容器

        Args:
            db_session: 数据库会话

        Returns:
            PortfolioManagerContainer 实例
        """
        from portfolio_manager.containers import PortfolioManagerContainer

        container = PortfolioManagerContainer()
        container.db_session.override(db_session)
        container.data_source_aggregator.override(self.data_source_aggregator())

        return container

    def shutdown(self):
        """关闭容器，清理资源"""
        # 清理数据库连接
        if self.database_manager.provided:
            try:
                db_manager = self.database_manager()
                db_manager.dispose()
            except Exception:
                pass


# ========== 工具函数 ==========

def init_container() -> Container:
    """
    初始化全局容器

    Returns:
        Container 实例
    """
    return Container.create_container()


def get_container() -> Container:
    """
    获取容器实例（单例）

    Returns:
        Container 实例
    """
    if not hasattr(get_container, "_instance"):
        get_container._instance = init_container()
    return get_container._instance
