"""
数据模型模块

定义所有数据源返回的统一数据结构
使用 Pydantic 进行数据验证和序列化
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 实时行情数据模型 ==========

class Quote(BaseModel):
    """实时行情数据模型"""
    symbol: str
    price: float
    change: float
    percent: float
    volume: int
    amount: float
    open_price: Optional[float] = None   # 开盘价
    high: Optional[float] = None         # 最高价
    low: Optional[float] = None          # 最低价
    bid_price: List[float] = Field(default_factory=list)
    bid_volume: List[int] = Field(default_factory=list)
    ask_price: List[float] = Field(default_factory=list)
    ask_volume: List[int] = Field(default_factory=list)
    timestamp: datetime

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========== K线数据模型 ==========

class KLine(BaseModel):
    """K线数据模型"""
    symbol: str
    datetime: datetime
    open_price: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover: Optional[float] = None

    model_config = {
        "arbitrary_types_allowed": True
    }


# ========== 财务报表基础模型 ==========

class FinancialStatement(BaseModel):
    """财务报表基础模型"""
    symbol: str
    year: int
    quarter: int = Field(ge=1, le=4)
    report_date: str

    model_config = {
        "arbitrary_types_allowed": True
    }


class BalanceSheet(FinancialStatement):
    """资产负债表"""
    total_assets: float
    total_liabilities: float
    shareholders_equity: float


class IncomeStatement(FinancialStatement):
    """利润表"""
    revenue: float
    net_profit: float
    eps: float


class CashFlowStatement(FinancialStatement):
    """现金流量表"""
    operating_cash_flow: float
    investing_cash_flow: float
    financing_cash_flow: float
