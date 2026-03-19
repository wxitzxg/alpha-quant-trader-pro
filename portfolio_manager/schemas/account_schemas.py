"""
账户数据验证模型（Pydantic Schemas）
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountSummarySchema(BaseModel):
    """账户汇总数据模型"""
    total_market_value: float = Field(0.0, ge=0, description="总市值")
    stock_market_value: float = Field(0.0, ge=0, description="股票市值")
    cash: float = Field(0.0, ge=0, description="现金")
    total_floating_pl: float = Field(0.0, description="总浮动盈亏")
    total_realized_pl: float = Field(0.0, description="总实际盈亏")
    positions_count: int = Field(0, ge=0, description="持仓股票数量")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_market_value": 100000.0,
                "stock_market_value": 90000.0,
                "cash": 10000.0,
                "total_floating_pl": 5000.0,
                "total_realized_pl": 2000.0,
                "positions_count": 5
            }
        }
    }


class CashBalanceSchema(BaseModel):
    """现金余额数据模型"""
    amount: float = Field(..., ge=0, description="现金余额")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "amount": 10000.0,
                "updated_at": "2026-03-16T10:30:00"
            }
        }
    }
