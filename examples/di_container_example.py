"""
依赖注入容器使用示例
"""

from common.di_container import get_container
from common.database import DatabaseManager
from common.config import get_config


def example_stock_market_di():
    """示例：股票市场模块使用 DI 容器"""
    print("=" * 60)
    print("股票市场模块 - 依赖注入示例")
    print("=" * 60)

    # 1. 获取根容器
    root_container = get_container()

    # 2. 获取数据库管理器
    db_manager = root_container.database_manager()

    # 3. 创建数据库会话
    with db_manager.get_session() as session:
        # 4. 创建股票市场模块容器
        stock_market_container = root_container.create_stock_market_container(session)

        # 5. 获取服务实例
        services = stock_market_container.get_services()
        stock_service = services['stock_service']
        kline_service = services['kline_service']

        print("✓ StockService 实例:", type(stock_service).__name__)
        print("✓ KLineService 实例:", type(kline_service).__name__)

        # 6. 使用服务
        # stock_service.sync_all_stocks()
        # print(f"✓ 同步股票列表成功")


def example_portfolio_manager_di():
    """示例：持仓管理模块使用 DI 容器"""
    print("\n" + "=" * 60)
    print("持仓管理模块 - 依赖注入示例")
    print("=" * 60)

    # 1. 获取根容器
    root_container = get_container()

    # 2. 获取数据库管理器
    db_manager = root_container.database_manager()

    # 3. 创建数据库会话
    with db_manager.get_session() as session:
        # 4. 创建持仓管理模块容器
        portfolio_container = root_container.create_portfolio_manager_container(session)

        # 5. 获取服务实例
        services = portfolio_container.get_services()
        position_service = services['position_service']
        transaction_service = services['transaction_service']
        account_service = services['account_service']

        print("✓ PositionService 实例:", type(position_service).__name__)
        print("✓ TransactionService 实例:", type(transaction_service).__name__)
        print("✓ AccountService 实例:", type(account_service).__name__)

        # 6. 使用服务
        # account_service.set_cash_balance(100000)
        # print(f"✓ 账户资金初始化成功")


def example_manual_di():
    """示例：手动依赖注入（不使用容器）"""
    print("\n" + "=" * 60)
    print("手动依赖注入示例")
    print("=" * 60)

    # 1. 配置
    config = get_config()
    db_url = config.database.url

    # 2. 初始化数据库
    db_manager = DatabaseManager(db_url)

    # 3. 创建会话
    with db_manager.get_session() as session:
        # 4. 手动创建依赖链
        from stock_market.repositories import StockRepository, SyncRecordRepository
        from stock_market.services import StockService

        stock_repo = StockRepository(session)
        sync_repo = SyncRecordRepository(session)

        # 5. 注入依赖
        stock_service = StockService(stock_repo=stock_repo, sync_repo=sync_repo)

        print("✓ 手动创建的 StockService:", type(stock_service).__name__)


if __name__ == "__main__":
    example_stock_market_di()
    example_portfolio_manager_di()
    example_manual_di()

    print("\n" + "=" * 60)
    print("✓ 所有依赖注入示例执行完成")
    print("=" * 60)
