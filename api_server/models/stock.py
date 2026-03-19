#!/usr/bin/env python3
"""股票基础数据模型"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class StockInfo(BaseModel):
    """股票基本信息"""
    ts_code: str = Field(..., description="TS代码")
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    area: Optional[str] = Field(None, description="地域")
    industry: Optional[str] = Field(None, description="所属行业")
    market: str = Field(..., description="市场类型（主板/创业板/科创板等）")
    exchange: str = Field(..., description="交易所（SH/SZ）")
    list_date: Optional[date] = Field(None, description="上市日期")
    delist_date: Optional[date] = Field(None, description="退市日期")
    status: str = Field(..., description="交易状态（L上市 D退市 P暂停）")


class StockListResponse(BaseModel):
    """股票列表响应"""
    stocks: list[StockInfo]
    total: int
    page: int
    page_size: int


class StockFilterParams(BaseModel):
    """股票筛选参数"""
    market: Optional[str] = Field(None, description="市场类型")
    industry: Optional[str] = Field(None, description="行业")
    status: Optional[str] = Field("L", description="交易状态")
