"""
股票收藏数据验证模型（Pydantic Schemas）
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AddFavoriteRequest(BaseModel):
    """添加收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    tag: Optional[str] = Field(None, max_length=50, description="标签")
    note: Optional[str] = Field(None, max_length=200, description="备注")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "自选股",
                "note": "业绩超预期"
            }
        }
    }


class RemoveFavoriteRequest(BaseModel):
    """移除收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")


class UpdateFavoriteRequest(BaseModel):
    """更新收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    tag: Optional[str] = Field(None, max_length=50, description="新标签（不传表示不修改）")
    note: Optional[str] = Field(None, max_length=200, description="新备注（不传表示不修改）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "策略池",
                "note": "突破形态"
            }
        }
    }


class FavoriteResponse(BaseModel):
    """收藏信息响应"""
    symbol: str
    tag: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "自选股",
                "note": "业绩超预期",
                "created_at": "2026-03-26T10:00:00",
                "updated_at": "2026-03-26T10:00:00"
            }
        }
    }
