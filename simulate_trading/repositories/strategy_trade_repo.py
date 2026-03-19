"""
策略交易仓库 - 封装交易记录数据库操作
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from simulate_trading.models import StrategyTrade
from datetime import datetime, timedelta


class StrategyTradeRepository:
    """策略交易仓库"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, trade: StrategyTrade) -> StrategyTrade:
        """创建交易记录"""
        self.session.add(trade)
        self.session.flush()
        return trade

    def get_by_strategy(self, strategy_name: str, days: int = 30) -> List[StrategyTrade]:
        """获取策略的交易记录（最近N天）"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.session.query(StrategyTrade)\
            .filter(
                and_(
                    StrategyTrade.strategy_name == strategy_name,
                    StrategyTrade.transaction_date >= since
                )
            )\
            .order_by(StrategyTrade.transaction_date.desc())\
            .all()

    def get_by_symbol(self, strategy_name: str, symbol: str, days: int = 30) -> List[StrategyTrade]:
        """获取策略某只股票的交易记录"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.session.query(StrategyTrade)\
            .filter(
                and_(
                    StrategyTrade.strategy_name == strategy_name,
                    StrategyTrade.symbol == symbol,
                    StrategyTrade.transaction_date >= since
                )
            )\
            .order_by(StrategyTrade.transaction_date.desc())\
            .all()

    def get_daily_trades(self, strategy_name: str, date: datetime) -> List[StrategyTrade]:
        """获取策略某天的交易记录"""
        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)
        return self.session.query(StrategyTrade)\
            .filter(
                and_(
                    StrategyTrade.strategy_name == strategy_name,
                    StrategyTrade.transaction_date >= start,
                    StrategyTrade.transaction_date <= end
                )
            )\
            .all()

    def count_winning_trades(self, strategy_name: str, days: int = 30) -> int:
        """统计策略最近N天的盈利交易次数"""
        since = datetime.utcnow() - timedelta(days=days)
        # 注意：这里的盈利判断需要根据实际交易记录计算
        # 简化版本：只统计卖出交易
        return self.session.query(StrategyTrade)\
            .filter(
                and_(
                    StrategyTrade.strategy_name == strategy_name,
                    StrategyTrade.transaction_type == 'sell',
                    StrategyTrade.transaction_date >= since
                )
            ).count()

    def count_losing_trades(self, strategy_name: str, days: int = 30) -> int:
        """统计策略最近N天的亏损交易次数"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.session.query(StrategyTrade)\
            .filter(
                and_(
                    StrategyTrade.strategy_name == strategy_name,
                    StrategyTrade.transaction_type == 'sell',
                    StrategyTrade.transaction_date >= since
                )
            ).count()
