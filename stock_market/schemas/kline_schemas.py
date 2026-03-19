"""
K线数据验证模型（Pydantic Schemas）

用于输入验证和序列化
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Annotated
from datetime import date


class KLineCreateSchema(BaseModel):
    """创建K线数据的验证模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    trade_date: Annotated[date, Field(..., description="交易日期")]
    interval: str = Field(..., min_length=1, max_length=10, description="周期")
    open: float = Field(..., gt=0, description="开盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    close: float = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")
    amount: Optional[float] = Field(None, ge=0, description="成交额")
    source: Optional[str] = Field(None, max_length=50, description="数据源")
    
    @field_validator('high')
    @classmethod
    def high_must_be_ge_open(cls, v, info):
        if 'open' in info.data and v < info.data['open']:
            raise ValueError('最高价必须大于等于开盘价')
        return v

    @field_validator('low')
    @classmethod
    def low_must_be_le_close(cls, v, info):
        if 'close' in info.data and v > info.data['close']:
            raise ValueError('最低价必须小于等于收盘价')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "trade_date": "2023-01-01",
                "interval": "1d",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "amount": 10200000.0,
                "source": "tushare"
            }
        }
    }


class KLineQuerySchema(BaseModel):
    """查询K线数据的验证模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    interval: str = Field("1d", min_length=1, max_length=10, description="周期")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    limit: Optional[int] = Field(100, ge=1, le=5000, description="限制数量")
    order_by: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="排序")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "interval": "1d",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "limit": 250,
                "order_by": "asc"
            }
        }
    }


class KLineResponseSchema(BaseModel):
    """K线数据响应模型"""
    id: int
    symbol: str
    trade_date: date
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: Optional[float] = None
    source: Optional[str] = None
    sync_time: str  # ISO 8601 format

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "symbol": "600000",
                "trade_date": "2023-01-01",
                "interval": "1d",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "amount": 10200000.0,
                "source": "tushare",
                "sync_time": "2026-03-16T10:30:00"
            }
        }
    }
