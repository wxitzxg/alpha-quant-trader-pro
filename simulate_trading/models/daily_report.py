"""
每日报告模型
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Date, func, UniqueConstraint, Index
from common.database import Base


class DailyReport(Base):
    """每日报告表 - 存储每种策略的每日交易报告"""

    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    cash = Column(DECIMAL(15, 2), nullable=False)
    stock_value = Column(DECIMAL(15, 2), nullable=False)
    total_assets = Column(DECIMAL(15, 2), nullable=False)
    profit = Column(DECIMAL(15, 2), nullable=False)
    profit_pct = Column(DECIMAL(10, 4), nullable=False)
    position_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('strategy_name', 'report_date', name='uq_strategy_date'),
    )

    def __repr__(self):
        return f"<DailyReport(strategy={self.strategy_name}, date={self.report_date}, profit={self.profit_pct}%)>"

# 索引
Index('idx_daily_reports_strategy', DailyReport.strategy_name)
Index('idx_daily_reports_date', DailyReport.report_date)
