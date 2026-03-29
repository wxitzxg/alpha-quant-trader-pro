# portfolio_manager/account_service.py
"""
资金管理服务（重构版 - 使用 Repository 模式）
"""

from typing import List, Optional
from decimal import Decimal
from portfolio_manager.database import CashBalance, Transaction
from portfolio_manager.models import AccountSummary
from portfolio_manager.position_service import PositionService
from portfolio_manager.repositories import CashBalanceRepository
from common.exceptions import InsufficientFundsError, BusinessError


class AccountService:
    """资金管理服务"""

    def __init__(
        self,
        cash_repo: CashBalanceRepository,
        position_service: PositionService,
        capital_service: Optional['CapitalService'] = None
    ):
        """
        初始化资金服务

        Args:
            cash_repo: 现金余额仓库（依赖注入）
            position_service: 持仓服务
            capital_service: 资金调整服务（可选，用于获取初始资金）
        """
        self.cash_repo = cash_repo
        self.position_service = position_service
        self.capital_service = capital_service

    def get_account_summary(self) -> AccountSummary:
        """
        获取账户汇总信息

        计算逻辑：
        - 总市值 = 股票市值 + 现金
        - 股票市值 = 所有持仓市值之和
        - 现金 = 现金余额表
        - 初始资金 = 从 capital_adjustments 汇总
        - 总盈亏 = (现金 + 股票市值) - 初始资金
        - 总浮动盈亏 = 所有持仓浮动盈亏之和
        - 总实际盈亏 = 历史卖出交易的累计盈利

        Returns:
            AccountSummary
        """
        # 获取所有持仓
        positions = self.position_service.get_all_positions()

        # 计算汇总指标
        stock_market_value = sum(p.market_value for p in positions)
        total_floating_pl = sum(p.floating_pl for p in positions)

        # 获取现金
        cash = self.get_cash_balance()

        # 计算总市值
        total_market_value = stock_market_value + cash

        # 获取初始资金
        initial_capital = 0.0
        if self.capital_service:
            initial_capital = self.capital_service.get_initial_capital()

        # 计算总盈亏
        total_pl = total_market_value - initial_capital

        # 计算实际盈亏（卖出交易的累计盈利）
        total_realized_pl = self._calculate_realized_pl()

        return AccountSummary(
            total_market_value=total_market_value,
            stock_market_value=stock_market_value,
            cash=cash,
            initial_capital=initial_capital,
            total_pl=total_pl,
            total_floating_pl=total_floating_pl,
            total_realized_pl=total_realized_pl,
            positions_count=len(positions)
        )

    def get_cash_balance(self) -> float:
        """
        获取现金余额

        Returns:
            现金余额
        """
        return self.cash_repo.get_current_balance()

    def add_cash(self, amount: float):
        """
        增加现金

        Args:
            amount: 增加金额
        """
        self.cash_repo.update_balance(amount)

    def deduct_cash(self, amount: float):
        """
        扣减现金

        Args:
            amount: 扣减金额

        Raises:
            InsufficientFundsError: 现金不足
        """
        cash = self.get_cash_balance()
        if cash < amount:
            raise InsufficientFundsError(required=amount, available=cash)

        self.cash_repo.update_balance(-amount)

    def set_cash_balance(self, amount: float):
        """
        设置现金余额（覆盖）

        Args:
            amount: 新的余额
        """
        self.cash_repo.set_balance(amount)

    def _calculate_realized_pl(self) -> float:
        """
        计算实际盈亏（历史卖出交易的累计盈利）

        使用 Transaction 表中的 realized_pl 字段

        Returns:
            实际盈亏
        """
        from portfolio_manager.repositories import TransactionRepository

        # 获取当前 session
        session = self.cash_repo.session

        # 查询所有卖出交易的实际盈亏
        sell_transactions = session.query(Transaction).filter_by(transaction_type='sell').all()

        # 计算总盈利
        total_profit = Decimal('0')
        for tx in sell_transactions:
            if tx.realized_pl is not None:
                total_profit += tx.realized_pl

        return float(total_profit)
