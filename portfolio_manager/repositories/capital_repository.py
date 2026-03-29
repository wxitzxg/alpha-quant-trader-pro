"""资金调整记录仓库层"""

from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from common.repositories.base import BaseRepository
from portfolio_manager.database import CapitalAdjustment


class CapitalAdjustmentRepository(BaseRepository[CapitalAdjustment]):
    """资金调整记录仓库"""

    def __init__(self, session: Session):
        super().__init__(session, CapitalAdjustment)

    def get_all(self, limit: int = 20) -> List[CapitalAdjustment]:
        """
        获取所有调整记录

        Args:
            limit: 限制返回数量

        Returns:
            调整记录列表
        """
        stmt = select(CapitalAdjustment).order_by(
            CapitalAdjustment.created_at.desc()
        ).limit(limit)
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_sum(self) -> Decimal:
        """
        获取初始资金汇总

        计算逻辑：
        - deposit（转入）为正数
        - withdraw（转出）为负数
        - 返回总和

        Returns:
            初始资金汇总值
        """
        # 使用 CASE WHEN 计算：deposit 为正，withdraw 为负
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (CapitalAdjustment.adjustment_type == 'deposit', CapitalAdjustment.amount),
                        (CapitalAdjustment.adjustment_type == 'withdraw', -CapitalAdjustment.amount),
                        else_=Decimal('0')
                    )
                ),
                Decimal('0')
            )
        )
        result = self.session.execute(stmt).scalar()
        return Decimal(str(result)) if result else Decimal('0')

    def get_count(self) -> int:
        """获取调整记录数量"""
        return self.count()
