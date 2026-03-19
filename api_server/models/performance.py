#!/usr/bin/env python3
"""收益统计模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    max_drawdown: float = Field(..., description="最大回撤")
    volatility: float = Field(..., description="波动率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈亏比")
    avg_holding_days: float = Field(..., description="平均持仓天数")


class PeriodPerformance(BaseModel):
    """时段收益"""
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    return_rate: float = Field(..., description="收益率")
    benchmark_return: Optional[float] = Field(None, description="基准收益率")
    alpha: Optional[float] = Field(None, description="超额收益")
    trades_count: int = Field(..., description="交易次数")


class ContributionAnalysis(BaseModel):
    """贡献度分析"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    contribution_rate: float = Field(..., description="贡献度")
    profit: float = Field(..., description="收益")
    trades_count: int = Field(..., description="交易次数")


class PerformanceResponse(BaseModel):
    """收益统计响应"""
    metrics: Optional[PerformanceMetrics] = None
    period_performance: Optional[List[PeriodPerformance]] = None
    contribution: Optional[List[ContributionAnalysis]] = None
    benchmark_comparison: Optional[dict] = Field(None, description="基准对比")
