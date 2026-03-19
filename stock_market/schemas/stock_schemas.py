"""
股票数据验证模型（Pydantic Schemas）

用于输入验证和序列化
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class StockCreateSchema(BaseModel):
    """创建股票数据的验证模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    name: str = Field(..., min_length=1, max_length=100, description="股票名称")
    exchange: str = Field(..., min_length=2, max_length=10, description="交易所")
    list_date: date = Field(..., description="上市日期")
    
    # 可选字段
    delist_date: Optional[date] = Field(None, description="退市日期")
    industry: Optional[str] = Field(None, max_length=100, description="所属行业")
    concept: Optional[str] = Field(None, max_length=500, description="概念板块")
    region: Optional[str] = Field(None, max_length=50, description="所属地区")
    total_shares: Optional[int] = Field(None, ge=0, description="总股本")
    float_shares: Optional[int] = Field(None, ge=0, description="流通股本")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600000",
                "name": "浦发银行",
                "exchange": "SH",
                "list_date": "1999-11-10",
                "industry": "银行",
                "concept": "MSCI,沪股通",
                "region": "上海",
                "total_shares": 29352080397,
                "float_shares": 29352080397
            }
        }
    }


class StockUpdateSchema(BaseModel):
    """更新股票数据的验证模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    concept: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=50)
    total_shares: Optional[int] = Field(None, ge=0)
    float_shares: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "industry": "银行",
                "is_active": True
            }
        }
    }


class StockQuerySchema(BaseModel):
    """查询股票数据的验证模型"""
    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1)
    industry: Optional[str] = Field(None, max_length=100)
    concept: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    limit: Optional[int] = Field(100, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "industry": "银行",
                "is_active": True,
                "limit": 50,
                "offset": 0
            }
        }
    }


class StockResponseSchema(BaseModel):
    """股票数据响应模型"""
    id: int
    symbol: str
    name: str
    exchange: str
    list_date: date
    delist_date: Optional[date] = None
    industry: Optional[str] = None
    concept: Optional[str] = None
    region: Optional[str] = None
    total_shares: Optional[int] = None
    float_shares: Optional[int] = None
    is_active: bool
    last_sync_time: str  # ISO 8601 format
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "symbol": "600000",
                "name": "浦发银行",
                "exchange": "SH",
                "list_date": "1999-11-10",
                "industry": "银行",
                "is_active": True,
                "last_sync_time": "2026-03-16T10:30:00"
            }
        }
    }
