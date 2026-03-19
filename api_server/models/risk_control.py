#!/usr/bin/env python3
"""风险控制模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RiskMetrics(BaseModel):
    """风险指标"""
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    volatility: float = Field(..., description="波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    beta: Optional[float] = Field(None, description="Beta 系数")


class StopLossConfig(BaseModel):
    """止损配置"""
    stock_code: str = Field(..., description="股票代码")
    stop_loss_type: str = Field(..., description="止损类型 (fixed/atr/percentage)")
    stop_loss_value: float = Field(..., description="止损值")
    current_price: float = Field(..., description="当前价格")
    stop_loss_price: float = Field(..., description="止损价格")


class PositionRisk(BaseModel):
    """仓位风险"""
    stock_code: str = Field(..., description="股票代码")
    position_size: float = Field(..., description="仓位大小")
    risk_contribution: float = Field(..., description="风险贡献")
    concentration_risk: float = Field(..., description="集中度风险")
    is_overweight: bool = Field(..., description="是否超重")


class RiskControlResponse(BaseModel):
    """风险控制响应"""
    stock_code: Optional[str] = None
    risk_metrics: Optional[RiskMetrics] = None
    stop_loss: Optional[StopLossConfig] = None
    position_risk: Optional[PositionRisk] = None
    warnings: Optional[List[str]] = Field(None, description="风险警告")
