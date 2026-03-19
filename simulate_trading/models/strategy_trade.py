"""
策略交易记录模型
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StrategyTrade(Base):
    """策略交易记录表 - 存储每种策略的交易历史"""

    __tablename__ = 'strategy_trades'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # buy/sell
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    fee = Column(DECIMAL(10, 2), nullable=False)
    reason = Column(String(200))
    transaction_date = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<StrategyTrade(strategy={self.strategy_name}, {self.transaction_type} {self.symbol} {self.quantity}@{self.price})>"

# 索引
Index('idx_strategy_trades_strategy', StrategyTrade.strategy_name)
Index('idx_strategy_trades_symbol', StrategyTrade.symbol)
Index('idx_strategy_trades_date', StrategyTrade.transaction_date)
