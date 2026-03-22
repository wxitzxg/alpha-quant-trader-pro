# portfolio_manager/transaction_service.py
"""
交易管理服务（重构版 - 使用 Repository 模式）
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from portfolio_manager.database import Transaction, Position
from portfolio_manager.models import TransactionModel
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.repositories import TransactionRepository, PositionRepository
from common.exceptions import InsufficientFundsError, InsufficientSharesError, BusinessError


class TransactionService:
    """交易管理服务 - 记录交易并自动联动持仓和资金"""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        position_repo: PositionRepository,
        position_service: PositionService,
        account_service: AccountService,
        fee_calculator: FeeCalculator
    ):
        """
        初始化交易服务

        Args:
            transaction_repo: 交易记录仓库（依赖注入）
            position_repo: 持仓仓库（依赖注入）
            position_service: 持仓服务
            account_service: 资金服务
            fee_calculator: 手续费计算器
        """
        self.transaction_repo = transaction_repo
        self.position_repo = position_repo
        self.position_service = position_service
        self.account_service = account_service
        self.fee_calculator = fee_calculator

    def record_buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[datetime] = None
    ) -> TransactionModel:
        """
        记录买入交易

        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新/创建持仓
        4. 扣减现金

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（可选）

        Returns:
            TransactionModel

        Raises:
            InsufficientFundsError: 现金不足
        """
        # 计算交易金额
        amount = quantity * price

        # 计算手续费
        fee = self.fee_calculator.calculate_buy_fee(amount)
        total_amount = amount + fee  # 买入需要额外支付手续费

        # 检查现金是否足够
        cash = self.account_service.get_cash_balance()
        if cash < total_amount:
            raise InsufficientFundsError(required=float(total_amount), available=float(cash))

        try:
            # 创建交易记录
            transaction = Transaction(
                symbol=symbol,
                transaction_type='buy',
                quantity=quantity,
                price=Decimal(str(price)),
                amount=Decimal(str(amount)),
                fee=Decimal(str(fee)),
                transaction_date=transaction_date or datetime.now()
            )
            # 设置买入交易的成本基础
            transaction.cost_basis = Decimal(str(amount))
            self.transaction_repo.add(transaction)

            # 更新持仓
            self._update_position_on_buy(symbol, quantity, price)

            # 扣减现金
            self.account_service.deduct_cash(total_amount)

            return self._to_pydantic(transaction)
        except Exception as e:
            raise BusinessError(f"买入交易失败: {str(e)}", context={"symbol": symbol})

    def record_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[datetime] = None
    ) -> TransactionModel:
        """
        记录卖出交易

        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新持仓
        4. 增加现金

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（可选）

        Returns:
            TransactionModel

        Raises:
            InsufficientSharesError: 持仓不足
        """
        # 检查持仓是否足够
        position = self.position_service.get_position(symbol)
        if not position or position.quantity < quantity:
            raise InsufficientSharesError(
                required=quantity,
                available=position.quantity if position else 0
            )

        # 计算交易金额
        amount = quantity * price

        # 计算手续费
        fee = self.fee_calculator.calculate_sell_fee(amount)
        total_amount = amount - fee  # 卖出后实际到账金额

        try:
            # 创建交易记录
            transaction = Transaction(
                symbol=symbol,
                transaction_type='sell',
                quantity=quantity,
                price=Decimal(str(price)),
                amount=Decimal(str(total_amount)),
                fee=Decimal(str(fee)),
                transaction_date=transaction_date or datetime.now()
            )
            self.transaction_repo.add(transaction)

            # 更新持仓
            self._update_position_on_sell(symbol, quantity, transaction)

            # 增加现金
            self.account_service.add_cash(total_amount)

            return self._to_pydantic(transaction)
        except Exception as e:
            raise BusinessError(f"卖出交易失败: {str(e)}", context={"symbol": symbol})

    def _update_position_on_buy(self, symbol: str, quantity: int, price: float):
        """买入后更新持仓"""
        position = self.position_repo.get_by_symbol(symbol)

        if position:
            # 已有持仓：加权平均成本
            old_value = Decimal(position.quantity) * position.cost_price
            new_value = Decimal(quantity) * Decimal(str(price))
            total_quantity = position.quantity + quantity
            total_value = old_value + new_value

            position.quantity = total_quantity
            position.cost_price = total_value / total_quantity if total_quantity > 0 else Decimal('0')

            # 更新现价
            position.current_price = Decimal(str(price))
            position.calculate_metrics()
        else:
            # 新增持仓
            position = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=Decimal(str(price)),
                current_price=Decimal(str(price))
            )
            position.calculate_metrics()
            self.position_repo.add(position)

    def _update_position_on_sell(self, symbol: str, quantity: int, transaction: Transaction):
        """卖出后更新持仓并计算成本和盈亏"""
        position = self.position_repo.get_by_symbol(symbol)

        if not position:
            raise BusinessError(f"持仓 {symbol} 不存在")

        # 计算成本基础（使用加权平均成本）
        cost_basis_per_share = position.cost_price
        total_cost_basis = Decimal(str(quantity)) * cost_basis_per_share

        # 计算实际盈亏
        sale_proceeds = transaction.amount + transaction.fee  # 销售收入（不含手续费）
        realized_pl = sale_proceeds - total_cost_basis

        # 更新交易记录
        transaction.cost_basis = total_cost_basis
        transaction.realized_pl = realized_pl

        if position.quantity <= quantity:
            # 全部卖出，删除持仓
            self.position_repo.delete(position)
        else:
            # 部分卖出，更新数量（成本价不变）
            position.quantity -= quantity
            position.calculate_metrics()

    def get_transaction_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TransactionModel]:
        """
        获取交易历史

        Args:
            symbol: 股票代码（可选，不传则返回所有交易）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            TransactionModel 列表
        """
        if symbol:
            transactions = self.transaction_repo.get_by_symbol(symbol, start_date, end_date)
        else:
            transactions = self.transaction_repo.get_all_transactions(start_date, end_date)

        return [self._to_pydantic(t) for t in transactions]

    def _to_pydantic(self, transaction: Transaction) -> TransactionModel:
        """转换为 Pydantic 模型"""
        return TransactionModel(
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=float(transaction.price),
            amount=float(transaction.amount),
            fee=float(transaction.fee),
            transaction_date=transaction.transaction_date
        )
