#!/usr/bin/env python3
"""模拟交易数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SimulationAccountCreate(BaseModel):
    """创建账户请求"""
    account_name: str = Field(..., min_length=1, max_length=50, description="账户名称")
    initial_capital: float = Field(100000.0, gt=0, description="初始资金")
    commission_rate: float = Field(0.00025, ge=0, le=0.01, description="手续费率")


class Position(BaseModel):
    """持仓信息"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float
    market_value: float
    floating_pl: float
    floating_pl_pct: float
    entry_date: str


class PositionsResponse(BaseModel):
    """持仓列表响应"""
    account_id: str
    positions: List[Position]
    total_market_value: float
    total_floating_pl: float
    total_floating_pl_pct: float


class TradeOrder(BaseModel):
    """交易订单"""
    account_id: str
    symbol: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    order_type: str = Field("market", description="订单类型: market, limit")


class Trade(BaseModel):
    """交易记录"""
    trade_id: str
    account_id: str
    symbol: str
    action: str  # buy, sell
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float] = None
    total_cost: Optional[float] = None
    total_revenue: Optional[float] = None
    timestamp: datetime


class TradeResult(BaseModel):
    """交易结果"""
    trade_id: str
    account_id: str
    symbol: str
    action: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float]
    total_cost: Optional[float]
    total_revenue: Optional[float]
    timestamp: datetime
    account_balance: float


class SimulationAccount(BaseModel):
    """模拟账户"""
    account_id: str
    account_name: str
    initial_capital: float
    current_balance: float
    available_cash: float
    total_value: float
    floating_pl: float
    total_return: float
    positions_count: int
    commission_rate: float
    created_at: datetime
    updated_at: datetime
