# portfolio_manager/commands.py
"""
用户股票管理模块 - 统一命令入口（重构版 - 使用 Repository 模式）
"""

from typing import List, Optional, ContextManager
from datetime import datetime
from contextlib import contextmanager
from common.config import get_config
from portfolio_manager.models import PositionModel, TransactionModel, AccountSummary
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.transaction_service import TransactionService
from portfolio_manager.repositories import (
    PositionRepository,
    TransactionRepository,
    CashBalanceRepository
)
from common.database import DatabaseManager
from common.exceptions import handle_exceptions


@handle_exceptions
class PortfolioCommands:
    """
    用户股票管理模块 - 统一命令入口（重构版）

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
        self.db_manager = self._init_database()

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

    def _init_database(self) -> DatabaseManager:
        """初始化数据库连接"""
        db_url = self.config.get_database_url()
        return DatabaseManager(db_url)

    @contextmanager
    def _with_services(self):
        """
        上下文管理器：每次操作创建新的 session 和服务实例

        使用示例：
        >>> with self._with_services() as (position_service, account_service, transaction_service):
        ...     result = position_service.get_position(symbol)
        """
        with self.db_manager.get_session() as session:
            # 创建 Repository
            position_repo = PositionRepository(session)
            transaction_repo = TransactionRepository(session)
            cash_repo = CashBalanceRepository(session)

            # 创建服务
            position_service = PositionService(position_repo, self.data_source)
            account_service = AccountService(cash_repo, position_service)
            transaction_service = TransactionService(
                transaction_repo,
                position_repo,
                position_service,
                account_service,
                self.fee_calculator
            )

            yield position_service, account_service, transaction_service

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
        with self._with_services() as (position_service, _, _):
            return position_service.add_position(symbol, quantity, cost_price)

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
        with self._with_services() as (position_service, _, _):
            return position_service.update_position(symbol, quantity, cost_price)

    def get_position(self, symbol: str) -> Optional[PositionModel]:
        """
        获取单只持仓股

        Args:
            symbol: 股票代码

        Returns:
            PositionModel 或 None
        """
        with self._with_services() as (position_service, _, _):
            return position_service.get_position(symbol)

    def positions(self) -> List[PositionModel]:
        """
        获取持仓股列表

        Returns:
            PositionModel 列表
        """
        with self._with_services() as (position_service, _, _):
            return position_service.get_all_positions()

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
            InsufficientFundsError: 现金不足
        """
        with self._with_services() as (_, _, transaction_service):
            return transaction_service.record_buy(symbol, quantity, price)

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
            InsufficientSharesError: 持仓不足
        """
        with self._with_services() as (_, _, transaction_service):
            return transaction_service.record_sell(symbol, quantity, price)

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
        with self._with_services() as (_, _, transaction_service):
            return transaction_service.get_transaction_history(
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
        with self._with_services() as (_, account_service, _):
            return account_service.get_account_summary()

    def cash_balance(self) -> float:
        """
        获取现金余额

        Returns:
            现金余额
        """
        with self._with_services() as (_, account_service, _):
            return account_service.get_cash_balance()

    def add_cash(self, amount: float):
        """
        增加现金

        Args:
            amount: 增加金额
        """
        with self._with_services() as (_, account_service, _):
            account_service.add_cash(amount)

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
        self.db_manager.dispose()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()
