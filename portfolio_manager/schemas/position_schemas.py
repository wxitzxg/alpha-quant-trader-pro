"""
持仓数据验证模型（Pydantic Schemas）
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PositionCreateSchema(BaseModel):
    """创建持仓数据的验证模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    quantity: int = Field(..., gt=0, description="持仓数量")
    cost_price: float = Field(..., description="成本价（支持负数）")
    current_price: Optional[float] = Field(None, ge=0, description="当前价格")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "quantity": 100,
                "cost_price": 10.0,
                "current_price": 10.5
            }
        }
    }


class PositionUpdateSchema(BaseModel):
    """更新持仓数据的验证模型"""
    quantity: Optional[int] = Field(None, gt=0, description="持仓数量")
    cost_price: Optional[float] = Field(None, description="成本价")
    current_price: Optional[float] = Field(None, ge=0, description="当前价格")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "quantity": 150,
                "current_price": 11.0
            }
        }
    }


class PositionResponseSchema(BaseModel):
    """持仓数据响应模型"""
    symbol: str
    quantity: int
    cost_price: float
    current_price: Optional[float] = None
    market_value: float
    cost_value: float
    floating_pl: float
    position_ratio: float
    last_updated: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "quantity": 100,
                "cost_price": 10.0,
                "current_price": 10.5,
                "market_value": 1050.0,
                "cost_value": 1000.0,
                "floating_pl": 50.0,
                "position_ratio": 0.1,
                "last_updated": "2026-03-16T10:30:00"
            }
        }
    }
