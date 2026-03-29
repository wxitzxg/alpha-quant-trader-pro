# portfolio_manager/database.py
"""
SQLAlchemy ORM 模型定义
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, TIMESTAMP, Index
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from common.database import Base


class Position(Base):
    """持仓表"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, comment='股票代码')
    quantity = Column(Integer, nullable=False, comment='持仓数量')
    cost_price = Column(DECIMAL(10, 4), nullable=False, comment='成本价（支持负数）')
    current_price = Column(DECIMAL(10, 4), nullable=True, comment='当前价格（缓存）')
    market_value = Column(DECIMAL(15, 4), nullable=False, default=0, comment='市值')
    cost_value = Column(DECIMAL(15, 4), nullable=False, default=0, comment='持仓成本')
    floating_pl = Column(DECIMAL(15, 4), nullable=False, default=0, comment='浮动盈亏')
    last_updated = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_symbol', 'symbol'),
    )

    def calculate_metrics(self):
        """计算持仓指标"""
        if self.current_price:
            self.market_value = Decimal(str(self.quantity)) * Decimal(str(self.current_price))
            self.cost_value = Decimal(str(self.quantity)) * Decimal(str(self.cost_price))
            self.floating_pl = self.market_value - self.cost_value


class Transaction(Base):
    """交易记录表"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment='股票代码')
    transaction_type = Column(String(10), nullable=False, comment='交易类型 (buy/sell)')
    quantity = Column(Integer, nullable=False, comment='交易数量')
    price = Column(DECIMAL(10, 4), nullable=False, comment='交易价格')
    amount = Column(DECIMAL(15, 4), nullable=False, comment='交易金额（扣除手续费后）')
    fee = Column(DECIMAL(10, 4), nullable=False, comment='手续费')
    transaction_date = Column(DateTime, nullable=False, default=datetime.now)
    cost_basis = Column(DECIMAL(15, 4), nullable=True, comment='成本基础（买入时的成本，卖出时的加权平均成本）')
    realized_pl = Column(DECIMAL(15, 4), nullable=True, comment='实际盈亏（仅卖出交易有值）')

    __table_args__ = (
        Index('idx_transaction_symbol', 'symbol'),
        Index('idx_transaction_date', 'transaction_date'),
    )


class CashBalance(Base):
    """现金余额表（单条记录，id 固定为 1）"""
    __tablename__ = 'cash_balance'

    id = Column(Integer, primary_key=True, default=1, comment='固定 ID 为 1')
    amount = Column(DECIMAL(15, 4), nullable=False, default=0, comment='现金余额')
    initial_capital = Column(DECIMAL(15, 4), nullable=False, default=0, comment='初始资金')
    version = Column(Integer, nullable=False, default=0, comment='乐观锁版本号')
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())


class CapitalAdjustment(Base):
    """资金调整记录表"""
    __tablename__ = 'capital_adjustments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(DECIMAL(15, 4), nullable=False, comment='调整金额')
    adjustment_type = Column(String(20), nullable=False, comment='类型: deposit/withdraw')
    reason = Column(String(200), nullable=True, comment='调整原因')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_capital_adjustments_created_at', created_at.desc()),
    )


class StockFavorite(Base):
    """股票收藏表"""
    __tablename__ = 'stock_favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, comment='股票代码')
    tag = Column(String(50), nullable=True, comment='标签')
    note = Column(String(200), nullable=True, comment='备注')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_stock_favorites_created_at', created_at.desc()),
    )
