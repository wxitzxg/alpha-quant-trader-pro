#!/usr/bin/env python3
"""回测数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class BacktestConfigRequest(BaseModel):
    """回测配置请求"""
    initial_capital: float = Field(100000.0, gt=0, description="初始资金")
    commission_rate: float = Field(0.00025, ge=0, le=0.01, description="手续费率")
    slippage_rate: float = Field(0.001, ge=0, le=0.01, description="滑点率")
    stamp_duty_rate: float = Field(0.001, ge=0, le=0.01, description="印花税率")
    start_date: str = Field("2023-01-01", description="回测开始日期")
    end_date: str = Field("2024-12-31", description="回测结束日期")
    interval: str = Field("1d", description="K线周期")
    position_size: float = Field(0.1, gt=0, le=1, description="单笔仓位")
    max_positions: int = Field(5, gt=0, description="最大持仓数")
    stop_loss_pct: float = Field(0.08, gt=0, le=0.5, description="止损比例")
    take_profit_pct: float = Field(0.2, gt=0, le=1.0, description="止盈比例")


class BacktestRequest(BaseModel):
    """回测请求"""
    symbol: Optional[str] = Field(None, description="股票代码（单股票）")
    symbols: Optional[List[str]] = Field(None, description="股票代码列表（组合）")
    strategy: str = Field(..., description="策略名称")
    config: BacktestConfigRequest = Field(default_factory=BacktestConfigRequest)


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    volatility: float = Field(..., description="波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(..., description="索提诺比率")
    calmar_ratio: float = Field(..., description="卡尔玛比率")
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利次数")
    losing_trades: int = Field(..., description="亏损次数")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈亏比")
    avg_holding_days: float = Field(..., description="平均持仓天数")


class Trade(BaseModel):
    """交易记录"""
    trade_id: int
    symbol: str
    date: str
    action: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float] = None


class BacktestResultResponse(BaseModel):
    """回测结果响应"""
    task_id: str
    symbol: Optional[str]
    symbols: Optional[List[str]]
    strategy: str
    config: BacktestConfigRequest
    performance: PerformanceMetrics
    trades: List[Trade]
    equity_curve: List[float]
    dates: List[str]


class ReportRequest(BaseModel):
    """报告请求"""
    task_id: str
    format: str = Field("json", description="报告格式: json, text, html")
