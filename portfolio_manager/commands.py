# portfolio_manager/commands.py
"""
用户股票管理模块 - 统一命令入口
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.config import get_config
from portfolio_manager.models import PositionModel, TransactionModel, AccountSummary
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.transaction_service import TransactionService


class PortfolioCommands:
    """
    用户股票管理模块 - 统一命令入口

    ## 配置流程

    ```
    PortfolioCommands.__init__()
        ↓
        get_config() → Config 实例
            ↓
            配置来源 (优先级从高到低):
            - 运行时参数 (kwargs)
            - 环境变量 (Pydantic BaseSettings)
            - YAML 配置文件 (config/config.yaml)
            - 默认值 (Config 模型定义)
            ↓
        Config 方法:
        - get_database_url() → 数据库连接 URL
        - get_fee_config() → FeeConfig 对象 (手续费配置)
    ```

    使用示例：
    >>> from portfolio_manager import PortfolioCommands
    >>> portfolio = PortfolioCommands()

    # 增加初始资金
    >>> portfolio.add_cash(100000)

    # 记录买入交易
    >>> portfolio.buy("600519", quantity=50, price=1600)

    # 记录卖出交易
    >>> portfolio.sell("600519", quantity=30, price=1800)

    # 查看账户汇总
    >>> summary = portfolio.account_summary()
    >>> print(f"总市值: {summary.total_market_value:.2f}")

    # 查看持仓列表
    >>> positions = portfolio.positions()
    >>> for p in positions:
    ...     print(f"{p.symbol}: {p.quantity} 股, 盈亏: {p.floating_pl:.2f}")
    """

    def __init__(self):
        """
        初始化投资组合命令

        配置来源：统一配置系统 (common/config.py)
        """
        # 加载配置（使用统一配置）
        self.config = get_config()

        # 初始化数据库连接
        self.db = self._init_database()

        # 初始化底层数据源（可选）
        self.data_source = None
        try:
            from data_sources import DataSourceAggregator
            self.data_source = DataSourceAggregator()
        except ImportError:
            # data_sources 模块不存在，继续运行
            pass

        # 初始化服务（直接从统一配置获取手续费配置）
        self.fee_calculator = FeeCalculator(self.config.get_fee_config())

        # Initialize repositories
        from portfolio_manager.repositories import PositionRepository, TransactionRepository, CashBalanceRepository
        position_repo = PositionRepository(self.db)
        transaction_repo = TransactionRepository(self.db)
        cash_repo = CashBalanceRepository(self.db)

        self.position_service = PositionService(position_repo, self.data_source)
        self.account_service = AccountService(cash_repo, self.position_service)
        self.transaction_service = TransactionService(
            transaction_repo,
            position_repo,
            self.position_service,
            self.account_service,
            self.fee_calculator
        )

    def _init_database(self) -> Session:
        """初始化数据库连接"""
        db_url = self.config.get_database_url()

        # 支持 SQLite 用于测试
        if db_url.startswith('sqlite'):
            engine = create_engine(db_url, echo=False)
        elif db_url.startswith('postgresql'):
            # PostgreSQL 需要 psycopg2
            try:
                import psycopg2
                engine = create_engine(db_url, echo=False, pool_pre_ping=True)
            except ImportError:
                # 如果没有 psycopg2，回退到 SQLite
                print("Warning: psycopg2 not installed, using SQLite instead")
                engine = create_engine('sqlite:///:memory:', echo=False)
        else:
            engine = create_engine(db_url, echo=False)

        Session = sessionmaker(bind=engine)

        # 创建表（如果不存在）
        from portfolio_manager.database import Base
        Base.metadata.create_all(engine)

        return Session()

    # ========== 持仓管理 ==========

    def add_position(self, symbol: str, quantity: int, cost_price: float) -> PositionModel:
        """
        新增持仓股

        成本价支持负数，用于高位卖出留底仓场景

        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价（支持负数）

        Returns:
            PositionModel
        """
        return self.position_service.add_position(symbol, quantity, cost_price)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None
    ) -> PositionModel:
        """
        更新持仓股

        支持部分字段更新

        Args:
            symbol: 股票代码
            quantity: 持仓数量（可选）
            cost_price: 成本价（可选）

        Returns:
            PositionModel
        """
        return self.position_service.update_position(symbol, quantity, cost_price)

    def sync_position(self, symbol: str, quantity: int, cost_price: float) -> PositionModel:
        """
        同步持仓信息（存在则覆盖，不存在则新增）

        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价（支持负数）

        Returns:
            PositionModel
        """
        return self.position_service.sync_position(symbol, quantity, cost_price)

    def get_position(self, symbol: str) -> Optional[PositionModel]:
        """
        获取单只持仓股

        Args:
            symbol: 股票代码

        Returns:
            PositionModel 或 None
        """
        return self.position_service.get_position(symbol)

    def positions(self) -> List[PositionModel]:
        """
        获取持仓股列表

        Returns:
            PositionModel 列表
        """
        return self.position_service.get_all_positions()

    # ========== 交易管理 ==========

    def buy(self, symbol: str, quantity: int, price: float) -> TransactionModel:
        """
        记录买入交易

        自动：
        - 计算手续费
        - 更新持仓（加权平均成本）
        - 扣减现金

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格

        Returns:
            TransactionModel

        Raises:
            ValueError: 现金不足
        """
        return self.transaction_service.record_buy(symbol, quantity, price)

    def sell(self, symbol: str, quantity: int, price: float) -> TransactionModel:
        """
        记录卖出交易

        自动：
        - 计算手续费
        - 更新持仓
        - 增加现金

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            TransactionModel

        Raises:
            ValueError: 持仓不足
        """
        return self.transaction_service.record_sell(symbol, quantity, price)

    def transactions(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TransactionModel]:
        """
        获取交易历史

        Args:
            symbol: 股票代码（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            TransactionModel 列表
        """
        return self.transaction_service.get_transaction_history(
            symbol, start_date, end_date
        )

    # ========== 账户管理 ==========

    def account_summary(self) -> AccountSummary:
        """
        获取账户汇总信息

        包括：
        - 总市值（股票市值 + 现金）
        - 股票市值
        - 现金
        - 总浮动盈亏
        - 总实际盈亏
        - 持仓股票数量

        Returns:
            AccountSummary
        """
        return self.account_service.get_account_summary()

    def cash_balance(self) -> float:
        """
        获取现金余额

        Returns:
            现金余额
        """
        return self.account_service.get_cash_balance()

    def add_cash(self, amount: float):
        """
        增加现金

        Args:
            amount: 增加金额
        """
        self.account_service.add_cash(amount)

    # ========== 手续费管理 ==========

    def fee_config(self):
        """
        获取手续费配置

        Returns:
            FeeConfig
        """
        return self.fee_calculator.config

    def update_fee_config(
        self,
        stamp_duty: Optional[float] = None,
        exchange_fee: Optional[float] = None,
        broker_commission: Optional[float] = None,
        min_commission: Optional[float] = None
    ):
        """
        更新手续费配置

        注意：配置只在当前会话有效，不会持久化

        Args:
            stamp_duty: 印花税率
            exchange_fee: 交易所费用率
            broker_commission: 券商佣金率
            min_commission: 最低佣金
        """
        config = self.fee_calculator.config

        if stamp_duty is not None:
            from decimal import Decimal
            config.stamp_duty = Decimal(str(stamp_duty))
        if exchange_fee is not None:
            from decimal import Decimal
            config.exchange_fee = Decimal(str(exchange_fee))
        if broker_commission is not None:
            from decimal import Decimal
            config.broker_commission = Decimal(str(broker_commission))
        if min_commission is not None:
            from decimal import Decimal
            config.min_commission = Decimal(str(min_commission))

    # ========== 关闭连接 ==========

    def close(self):
        """关闭数据库连接"""
        self.db.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()
