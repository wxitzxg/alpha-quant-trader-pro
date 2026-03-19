"""
持仓管理模块依赖注入容器
"""

from dependency_injector import containers, providers
from data_sources import DataSourceAggregator
from portfolio_manager.repositories import PositionRepository, TransactionRepository, CashBalanceRepository
from portfolio_manager.services import PositionService, TransactionService, AccountService
from portfolio_manager.fee_calculator import FeeCalculator
from common.config import get_config


class PortfolioManagerContainer(containers.DeclarativeContainer):
    """
    持仓管理模块容器

    依赖：common.Container 的 database_manager 和 data_source_aggregator
    """

    # ========== 外部依赖 ==========

    # 数据库会话（由外部提供）
    db_session = providers.Dependency()

    # 数据源聚合器（由外部提供）
    data_source_aggregator = providers.Dependency()

    # ========== 配置 ==========

    # 手续费配置（从统一配置加载）
    fee_config = providers.Callable(
        lambda: get_config().get_fee_config()
    )

    # ========== 工厂 ==========

    fee_calculator = providers.Singleton(
        FeeCalculator,
        fee_config=fee_config
    )

    # ========== 仓库层 ==========

    position_repository = providers.Factory(
        PositionRepository,
        session=db_session
    )

    transaction_repository = providers.Factory(
        TransactionRepository,
        session=db_session
    )

    cash_balance_repository = providers.Factory(
        CashBalanceRepository,
        session=db_session
    )

    # ========== 服务层 ==========

    position_service = providers.Factory(
        PositionService,
        repository=position_repository,
        data_source_aggregator=data_source_aggregator
    )

    account_service = providers.Factory(
        AccountService,
        cash_repo=cash_balance_repository,
        position_service=position_service
    )

    transaction_service = providers.Factory(
        TransactionService,
        transaction_repo=transaction_repository,
        position_repo=position_repository,
        position_service=position_service,
        account_service=account_service,
        fee_calculator=fee_calculator
    )

    # ========== 工具方法 ==========

    def get_services(self):
        """获取所有服务实例"""
        return {
            'position_service': self.position_service(),
            'transaction_service': self.transaction_service(),
            'account_service': self.account_service()
        }
