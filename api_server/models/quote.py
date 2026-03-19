#!/usr/bin/env python3
"""行情数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RealtimeQuote(BaseModel):
    """实时行情"""
    ts_code: str = Field(..., description="TS代码")
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅(%)")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量（手）")
    amount: float = Field(..., description="成交额（万元）")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    pe: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    market_cap: Optional[float] = Field(None, description="总市值（亿元）")
    pe_ttm: Optional[float] = Field(None, description="市盈率TTM")
    ps_ttm: Optional[float] = Field(None, description="市销率TTM")
    update_time: datetime = Field(..., description="更新时间")


class BatchQuoteRequest(BaseModel):
    """批量行情请求"""
    symbols: List[str] = Field(..., description="股票代码列表", min_length=1, max_length=100)


class BatchQuoteResponse(BaseModel):
    """批量行情响应"""
    quotes: List[RealtimeQuote]
    timestamp: datetime


class TopListEntry(BaseModel):
    """涨跌幅排行条目"""
    ts_code: str
    symbol: str
    name: str
    change_pct: float
    current_price: float
    change: float
    volume: int


class TopListResponse(BaseModel):
    """涨跌幅排行响应"""
    type: str = Field(..., description="排行类型（gain/loss）")
    date: str
    items: List[TopListEntry]
    total: int
