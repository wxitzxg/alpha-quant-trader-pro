"""
策略账户模型
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, func, Index
from common.database import Base


class StrategyAccount(Base):
    """策略账户表 - 存储每种策略的账户资金信息"""

    __tablename__ = 'strategy_accounts'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), unique=True, nullable=False, index=True)
    initial_cash = Column(DECIMAL(15, 2), nullable=False)
    current_cash = Column(DECIMAL(15, 2), nullable=False)
    total_value = Column(DECIMAL(15, 2), nullable=False)
    total_profit = Column(DECIMAL(15, 2), nullable=False)
    total_profit_pct = Column(DECIMAL(10, 4), nullable=False)
    position_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StrategyAccount(name={self.strategy_name}, value={self.total_value})>"
