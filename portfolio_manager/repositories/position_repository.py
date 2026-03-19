"""用户持仓数据仓库层"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from common.repositories.base import BaseRepository
from portfolio_manager.database import Position, Transaction, CashBalance


class PositionRepository(BaseRepository[Position]):
    """持仓信息仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Position)

    def get_by_symbol(self, symbol: str) -> Optional[Position]:
        """根据股票代码获取持仓信息"""
        return self.get_by(symbol=symbol)

    def get_all_active(self) -> List[Position]:
        """获取所有持仓（按更新时间倒序）"""
        stmt = select(Position).order_by(Position.last_updated.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_by_symbols(self, symbols: List[str]) -> List[Position]:
        """根据股票代码列表获取持仓"""
        stmt = select(Position).filter(Position.symbol.in_(symbols))
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def bulk_upsert(self, positions: List[Position]) -> int:
        """
        批量插入或更新持仓

        Args:
            positions: 持仓列表

        Returns:
            成功处理的数量
        """
        success_count = 0
        for position in positions:
            existing = self.get_by(symbol=position.symbol)
            if existing:
                # 更新现有记录
                existing.quantity = position.quantity
                existing.cost_price = position.cost_price
                existing.current_price = position.current_price
                existing.calculate_metrics()
            else:
                # 插入新记录
                position.calculate_metrics()
                self.add(position)
            success_count += 1

        return success_count

    def get_total_market_value(self) -> float:
        """获取持仓总市值"""
        stmt = select(func.sum(Position.market_value))
        result = self.session.execute(stmt).scalar()
        return float(result) if result else 0.0

    def get_positions_count(self) -> int:
        """获取持仓股票数量"""
        return self.count()


class TransactionRepository(BaseRepository[Transaction]):
    """交易记录仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Transaction)

    def get_by_symbol(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        根据股票代码和日期范围获取交易记录

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易记录列表
        """
        stmt = select(Transaction).filter_by(symbol=symbol)

        if start_date:
            stmt = stmt.filter(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.filter(Transaction.transaction_date <= end_date)

        stmt = stmt.order_by(Transaction.transaction_date.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_all_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Transaction]:
        """
        获取所有交易记录

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制返回数量

        Returns:
            交易记录列表
        """
        stmt = select(Transaction)

        if start_date:
            stmt = stmt.filter(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.filter(Transaction.transaction_date <= end_date)

        stmt = stmt.order_by(Transaction.transaction_date.desc())

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_buy_transactions(self, symbol: str) -> List[Transaction]:
        """获取买入交易记录"""
        stmt = select(Transaction).filter_by(
            symbol=symbol,
            transaction_type='buy'
        ).order_by(Transaction.transaction_date.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_sell_transactions(self, symbol: str) -> List[Transaction]:
        """获取卖出交易记录"""
        stmt = select(Transaction).filter_by(
            symbol=symbol,
            transaction_type='sell'
        ).order_by(Transaction.transaction_date.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_total_buy_amount(self, symbol: str) -> float:
        """获取买入总金额（不含手续费）"""
        stmt = select(func.sum(Transaction.amount + Transaction.fee)).filter_by(
            symbol=symbol,
            transaction_type='buy'
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result else 0.0

    def get_total_sell_amount(self, symbol: str) -> float:
        """获取卖出总金额（不含手续费）"""
        stmt = select(func.sum(Transaction.amount - Transaction.fee)).filter_by(
            symbol=symbol,
            transaction_type='sell'
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result else 0.0

    def get_last_transaction_date(self, symbol: str) -> Optional[datetime]:
        """获取最后交易日期"""
        stmt = select(Transaction.transaction_date).filter_by(
            symbol=symbol
        ).order_by(Transaction.transaction_date.desc()).limit(1)
        result = self.session.execute(stmt).scalar()
        return result


class CashBalanceRepository(BaseRepository[CashBalance]):
    """现金余额仓库"""

    def __init__(self, session: Session):
        super().__init__(session, CashBalance)

    def get_current_balance(self) -> float:
        """获取当前现金余额"""
        # 现金余额表通常只有一条记录
        stmt = select(CashBalance).order_by(CashBalance.id.desc()).limit(1)
        result = self.session.execute(stmt).scalar_one_or_none()
        return float(result.amount) if result else 0.0

    def update_balance(self, amount: float) -> CashBalance:
        """
        更新现金余额（累加）

        Args:
            amount: 变更金额（正数为增加，负数为减少）

        Returns:
            更新后的现金余额记录
        """
        # 获取当前余额
        stmt = select(CashBalance).order_by(CashBalance.id.desc()).limit(1)
        current = self.session.execute(stmt).scalar_one_or_none()

        if current:
            # 更新现有记录
            current.amount += amount
            current.updated_at = datetime.now()
            return current
        else:
            # 创建新记录
            new_balance = CashBalance(amount=amount)
            self.add(new_balance)
            return new_balance

    def set_balance(self, amount: float) -> CashBalance:
        """
        设置现金余额（覆盖）

        Args:
            amount: 新的余额

        Returns:
            现金余额记录
        """
        # 获取当前余额
        stmt = select(CashBalance).order_by(CashBalance.id.desc()).limit(1)
        current = self.session.execute(stmt).scalar_one_or_none()

        if current:
            # 更新现有记录
            current.amount = amount
            current.updated_at = datetime.now()
            return current
        else:
            # 创建新记录
            new_balance = CashBalance(amount=amount)
            self.add(new_balance)
            return new_balance

    def get_balance_history(self, limit: int = 10) -> List[CashBalance]:
        """
        获取现金余额历史记录

        Args:
            limit: 限制返回数量

        Returns:
            余额记录列表
        """
        stmt = select(CashBalance).order_by(
            CashBalance.updated_at.desc()
        ).limit(limit)
        result = self.session.execute(stmt).scalars().all()
        return list(result)
