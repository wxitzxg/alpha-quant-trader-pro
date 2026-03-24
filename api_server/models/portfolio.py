#!/usr/bin/env python3
"""持仓管理模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AccountSummary(BaseModel):
    """账户汇总"""
    total_market_value: float = Field(..., description="总市值")
    total_cash: float = Field(..., description="总现金")
    total_assets: float = Field(..., description="总资产")
    total_profit: float = Field(..., description="总盈亏")
    total_profit_rate: float = Field(..., description="总盈亏率")
    position_count: int = Field(..., description="持仓股票数")
    today_profit: float = Field(..., description="今日盈亏")


class PositionInfo(BaseModel):
    """持仓信息"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    quantity: int = Field(..., description="持仓数量")
    available_quantity: int = Field(..., description="可用数量")
    cost_price: float = Field(..., description="成本价")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    profit: float = Field(..., description="盈亏")
    profit_rate: float = Field(..., description="盈亏率")
    position_ratio: float = Field(..., description="仓位占比")


class TradeRecord(BaseModel):
    """交易记录"""
    trade_id: str = Field(..., description="交易ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_type: str = Field(..., description="交易类型 (buy/sell)")
    quantity: int = Field(..., description="交易数量")
    price: float = Field(..., description="交易价格")
    amount: float = Field(..., description="交易金额")
    fee: float = Field(..., description="手续费")
    trade_time: datetime = Field(..., description="交易时间")


class CashOperation(BaseModel):
    """现金操作"""
    operation_type: str = Field(..., description="操作类型 (deposit/withdraw)")
    amount: float = Field(..., gt=0, description="金额")
    operation_time: datetime = Field(default_factory=datetime.now, description="操作时间")


class TradeRequest(BaseModel):
    """交易请求"""
    stock_code: str = Field(..., description="股票代码")
    quantity: int = Field(..., gt=0, description="数量")
    price: Optional[float] = Field(None, description="价格 (市价单可为空)")
    trade_type: str = Field(..., pattern="^(buy|sell)$", description="交易类型")
    transaction_date: Optional[datetime] = Field(None, description="交易日期")


class PositionSyncRequest(BaseModel):
    """持仓同步请求"""
    stock_code: str = Field(..., description="股票代码")
    quantity: int = Field(..., ge=0, description="持仓数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    current_price: float = Field(..., gt=0, description="当前价格")


class PortfolioResponse(BaseModel):
    """持仓响应"""
    account: Optional[AccountSummary] = None
    positions: Optional[List[PositionInfo]] = None
    trades: Optional[List[TradeRecord]] = None
    total: Optional[int] = None


class TransactionHistory(BaseModel):
    """交易历史"""
    transactions: List[TradeRecord]
    total: int
    page: int
    page_size: int
    total_pages: int
