"""
交易数据验证模型（Pydantic Schemas）
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TransactionCreateSchema(BaseModel):
    """创建交易数据的验证模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    transaction_type: str = Field(..., pattern="^(buy|sell)$", description="交易类型")
    quantity: int = Field(..., gt=0, description="交易数量")
    price: float = Field(..., gt=0, description="交易价格")
    transaction_date: Optional[datetime] = Field(None, description="交易日期")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "transaction_type": "buy",
                "quantity": 100,
                "price": 10.0,
                "transaction_date": "2026-03-16T10:30:00"
            }
        }
    }


class TransactionQuerySchema(BaseModel):
    """查询交易数据的验证模型"""
    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    transaction_type: Optional[str] = Field(None, pattern="^(buy|sell)$")
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    limit: Optional[int] = Field(100, ge=1, le=1000)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "transaction_type": "buy",
                "start_date": "2026-01-01T00:00:00",
                "end_date": "2026-03-31T23:59:59",
                "limit": 50
            }
        }
    }


class TransactionResponseSchema(BaseModel):
    """交易数据响应模型"""
    symbol: str
    transaction_type: str
    quantity: int
    price: float
    amount: float
    fee: float
    transaction_date: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "transaction_type": "buy",
                "quantity": 100,
                "price": 10.0,
                "amount": 1000.0,
                "fee": 5.0,
                "transaction_date": "2026-03-16T10:30:00"
            }
        }
    }
