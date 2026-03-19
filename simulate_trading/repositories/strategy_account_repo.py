"""
策略账户仓库 - 封装数据库操作
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from simulate_trading.models import StrategyAccount
from datetime import datetime


class StrategyAccountRepository:
    """策略账户仓库"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(self, strategy_name: str) -> Optional[StrategyAccount]:
        """根据策略名称获取账户"""
        return self.session.query(StrategyAccount).filter_by(strategy_name=strategy_name).first()

    def get_all(self) -> List[StrategyAccount]:
        """获取所有策略账户"""
        return self.session.query(StrategyAccount).all()

    def create(self, account: StrategyAccount) -> StrategyAccount:
        """创建新账户"""
        self.session.add(account)
        self.session.flush()
        return account

    def update(self, account: StrategyAccount) -> StrategyAccount:
        """更新账户"""
        account.updated_at = datetime.utcnow()
        self.session.add(account)
        return account

    def delete(self, account: StrategyAccount):
        """删除账户"""
        self.session.delete(account)

    def get_total_assets(self) -> float:
        """获取所有策略的总资产"""
        result = self.session.query(func.sum(StrategyAccount.total_value)).scalar()
        return float(result) if result else 0.0
