"""
资金调整数据验证模型（Pydantic Schemas）
"""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AdjustmentType(str, Enum):
    """调整类型枚举"""
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class CapitalAdjustRequest(BaseModel):
    """资金调整请求"""
    amount: float = Field(..., gt=0, description="调整金额（必须大于0）")
    adjustment_type: AdjustmentType = Field(..., description="调整类型")
    reason: Optional[str] = Field(None, max_length=200, description="调整原因")
    confirm: bool = Field(False, description="大额操作确认标志")


class CapitalAdjustResponse(BaseModel):
    """资金调整响应"""
    adjustment_id: int = Field(..., description="调整记录ID")
    new_initial_capital: float = Field(..., description="新的初始资金")
    adjustment_type: AdjustmentType = Field(..., description="调整类型")
    amount: float = Field(..., description="调整金额")
    new_cash_balance: float = Field(..., description="新的现金余额")


class CapitalAdjustmentItem(BaseModel):
    """资金调整记录项"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    amount: float = Field(..., description="调整金额")
    adjustment_type: AdjustmentType = Field(..., description="调整类型")
    reason: Optional[str] = Field(None, description="调整原因")
    created_at: datetime = Field(..., description="创建时间")


class CapitalAdjustmentHistory(BaseModel):
    """资金调整历史"""
    items: list[CapitalAdjustmentItem] = Field(default_factory=list, description="调整记录列表")
    total: int = Field(0, description="总记录数")
