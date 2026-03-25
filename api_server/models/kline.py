#!/usr/bin/env python3
"""K线数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class KLine(BaseModel):
    """K线数据"""
    ts_code: str = Field(..., description="TS代码")
    symbol: str = Field(..., description="股票代码")
    trade_date: str = Field(..., description="交易日期 (YYYY-MM-DD)")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量（手）")
    amount: float = Field(..., description="成交额（万元）")
    change_pct: Optional[float] = Field(None, description="涨跌幅")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    vol5: Optional[float] = Field(None, description="5日均量")


class KLineQueryParams(BaseModel):
    """K线查询参数"""
    interval: str = Field("1d", description="周期（1d/5d/1w/1m/1q/1y）")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    limit: int = Field(120, ge=1, le=1000, description="数据条数限制")


class KLineResponse(BaseModel):
    """K线响应"""
    symbol: str
    name: str
    interval: str
    klines: List[KLine]
    total: int
    start_date: Optional[str]
    end_date: Optional[str]


class BatchKLineRequest(BaseModel):
    """批量K线请求"""
    symbols: List[str] = Field(..., description="股票代码列表", min_length=1, max_length=50)
    interval: str = Field("1d", description="周期")
    limit: int = Field(60, ge=1, le=200, description="每只股票的数据条数")


class BatchKLineResponse(BaseModel):
    """批量K线响应"""
    data: dict[str, List[KLine]]  # symbol -> klines
    timestamp: datetime


class KLineStats(BaseModel):
    """K线统计信息"""
    symbol: str
    name: str = ""  # 股票名称，可选（无数据时为空）
    period: str
    total_trading_days: int
    price_range: dict = Field(..., description="价格范围 {min, max, avg}")
    volume_stats: dict = Field(..., description="成交量统计 {min, max, avg, total}")
    volatility: float = Field(..., description="波动率")
    highest_price: dict = Field(..., description="最高价 {price, date}")
    lowest_price: dict = Field(..., description="最低价 {price, date}")
