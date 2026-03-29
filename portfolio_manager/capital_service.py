# portfolio_manager/capital_service.py
"""
资金调整服务
"""

from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from portfolio_manager.database import CapitalAdjustment, CashBalance
from portfolio_manager.repositories import CapitalAdjustmentRepository, CashBalanceRepository
from portfolio_manager.schemas.capital_schemas import (
    AdjustmentType,
    CapitalAdjustRequest,
    CapitalAdjustResponse,
    CapitalAdjustmentItem,
    CapitalAdjustmentHistory
)
from common.exceptions import InsufficientFundsError, BusinessError


# 大额操作阈值（10万）
LARGE_AMOUNT_THRESHOLD = 100000


class CapitalService:
    """资金调整服务"""

    def __init__(
        self,
        session: Session,
        capital_repo: CapitalAdjustmentRepository,
        cash_repo: CashBalanceRepository
    ):
        """
        初始化资金调整服务

        Args:
            session: 数据库会话
            capital_repo: 资金调整仓库
            cash_repo: 现金余额仓库
        """
        self.session = session
        self.capital_repo = capital_repo
        self.cash_repo = cash_repo

    def adjust_capital(
        self,
        request: CapitalAdjustRequest
    ) -> Tuple[CapitalAdjustResponse, Optional[dict]]:
        """
        调整初始资金

        流程：
        1. 验证金额 > 0
        2. 检查大额操作确认
        3. 如果是转出，检查现金充足性
        4. 创建 capital_adjustments 记录
        5. 更新 cash_balance.initial_capital
        6. 更新 cash_balance.amount（转入增加，转出减少）

        Args:
            request: 资金调整请求

        Returns:
            Tuple[CapitalAdjustResponse, Optional[dict]]:
                - 响应对象
                - 如果需要确认，返回确认提示；否则 None

        Raises:
            InsufficientFundsError: 转出时现金不足
            BusinessError: 业务错误
        """
        # 大额操作检查
        if request.amount >= LARGE_AMOUNT_THRESHOLD and not request.confirm:
            return None, {
                "require_confirmation": True,
                "message": f"金额超过 {LARGE_AMOUNT_THRESHOLD}，请确认后重试",
                "hint": "设置 confirm=true 进行确认"
            }

        # 转出时检查现金充足性
        if request.adjustment_type == AdjustmentType.WITHDRAW:
            current_cash = self.cash_repo.get_current_balance()
            if current_cash < request.amount:
                raise InsufficientFundsError(
                    required=request.amount,
                    available=current_cash
                )

        # 创建调整记录
        adjustment = CapitalAdjustment(
            amount=Decimal(str(request.amount)),
            adjustment_type=request.adjustment_type.value,
            reason=request.reason
        )
        self.capital_repo.add(adjustment)

        # 更新初始资金
        current_initial = self._get_initial_capital_internal()
        if request.adjustment_type == AdjustmentType.DEPOSIT:
            new_initial = current_initial + Decimal(str(request.amount))
        else:
            new_initial = current_initial - Decimal(str(request.amount))

        # 更新 cash_balance 表
        self._update_cash_balance(request.adjustment_type, request.amount, new_initial)

        # 提交事务
        self.session.commit()

        # 获取新的现金余额
        new_cash = self.cash_repo.get_current_balance()

        response = CapitalAdjustResponse(
            adjustment_id=adjustment.id,
            new_initial_capital=float(new_initial),
            adjustment_type=request.adjustment_type,
            amount=request.amount,
            new_cash_balance=new_cash
        )

        return response, None

    def _update_cash_balance(
        self,
        adjustment_type: AdjustmentType,
        amount: float,
        new_initial: Decimal
    ):
        """
        更新现金余额表

        Args:
            adjustment_type: 调整类型
            amount: 调整金额
            new_initial: 新的初始资金
        """
        from sqlalchemy import select, update

        # 获取当前记录
        stmt = select(CashBalance).where(CashBalance.id == 1)
        current = self.session.execute(stmt).scalar_one_or_none()

        if current:
            # 更新金额
            if adjustment_type == AdjustmentType.DEPOSIT:
                new_amount = current.amount + Decimal(str(amount))
            else:
                new_amount = current.amount - Decimal(str(amount))

            # 更新记录
            current.amount = new_amount
            current.initial_capital = new_initial
            current.updated_at = datetime.now()
        else:
            # 创建新记录
            new_balance = CashBalance(
                id=1,
                amount=Decimal(str(amount)) if adjustment_type == AdjustmentType.DEPOSIT else Decimal('0'),
                initial_capital=new_initial,
                version=0
            )
            self.session.add(new_balance)

    def _get_initial_capital_internal(self) -> Decimal:
        """
        内部方法：获取初始资金

        Returns:
            初始资金
        """
        return self.capital_repo.get_sum()

    def get_initial_capital(self) -> float:
        """
        获取初始资金

        逻辑：从 capital_adjustments 汇总
        - 无记录时返回 0
        - SUM(CASE WHEN type='deposit' THEN amount ELSE -amount END)

        Returns:
            初始资金
        """
        return float(self.capital_repo.get_sum())

    def get_adjustment_history(self, limit: int = 20) -> CapitalAdjustmentHistory:
        """
        获取调整历史

        Args:
            limit: 限制返回数量

        Returns:
            调整历史
        """
        adjustments = self.capital_repo.get_all(limit)
        total = self.capital_repo.get_count()

        items = [
            CapitalAdjustmentItem.model_validate(adj)
            for adj in adjustments
        ]

        return CapitalAdjustmentHistory(
            items=items,
            total=total
        )
