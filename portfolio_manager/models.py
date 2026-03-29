# portfolio_manager/models.py
"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FeeConfig(BaseModel):
    """手续费配置（通过配置文件传入）"""
    stamp_duty: float = Field(0.0005, ge=0, le=1, description="印花税 0.05%")
    exchange_fee: float = Field(6e-05, ge=0, le=1, description="交易所费用 0.006%")
    broker_commission: float = Field(0.00015, ge=0, le=1, description="券商佣金 0.015%")
    min_commission: float = Field(5.0, ge=0, description="最低佣金 5 元")


class PositionModel(BaseModel):
    """持仓数据模型"""
    symbol: str
    quantity: int
    cost_price: float  # 支持负数
    current_price: Optional[float] = None

    # 计算字段
    market_value: float = 0.0      # 市值 = 数量 * 现价
    cost_value: float = 0.0        # 持仓成本 = 数量 * 成本价
    floating_pl: float = 0.0       # 浮动盈亏 = 市值 - 成本
    position_ratio: float = 0.0    # 仓位比例

    last_updated: datetime


class TransactionModel(BaseModel):
    """交易记录模型"""
    symbol: str
    transaction_type: str  # 'buy' or 'sell'
    quantity: int
    price: float
    amount: float
    fee: float
    transaction_date: datetime


class AccountSummary(BaseModel):
    """账户汇总模型"""
    total_market_value: float = 0.0    # 总市值（股票市值 + 现金）
    stock_market_value: float = 0.0    # 股票市值
    cash: float = 0.0                  # 现金
    initial_capital: float = 0.0       # 初始资金
    total_floating_pl: float = 0.0     # 总浮动盈亏
    total_realized_pl: float = 0.0     # 总实际盈亏
    positions_count: int = 0           # 持仓股票数量
