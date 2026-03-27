#!/usr/bin/env python3
"""
Stock Recommendation Data Models

Data models for stock scanning, recommendation, and analysis results.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    """策略类型枚举"""
    SHORT = "short"
    LONG = "long"
    BOTH = "both"


class StockPoolType(str, Enum):
    """股票池类型枚举"""
    ALL = "all"
    WATCHLIST = "watchlist"
    CUSTOM = "custom"


class Rating(str, Enum):
    """评级枚举"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class ScanRequest(BaseModel):
    """扫描请求模型"""
    strategy_type: StrategyType = Field(
        StrategyType.BOTH,
        description="策略类型: short(短线), long(长线), both(两者)"
    )
    top_n: int = Field(
        10,
        ge=1,
        le=100,
        description="返回前N只股票"
    )
    stock_pool: StockPoolType = Field(
        StockPoolType.ALL,
        description="股票池: all(全市场), watchlist(自选股), custom(自定义)"
    )
    custom_codes: Optional[List[str]] = Field(
        None,
        description="自定义股票池代码列表"
    )
    exclude_gem: bool = Field(
        True,
        description="是否排除创业板"
    )
    exclude_star: bool = Field(
        True,
        description="是否排除科创板"
    )
    min_score: int = Field(
        60,
        ge=0,
        le=100,
        description="最低评分过滤(0-100)"
    )


class DimensionScore(BaseModel):
    """维度评分详情"""
    score: int = Field(..., ge=0, le=100, description="得分(0-100)")
    weight: float = Field(..., ge=0, le=1, description="权重")
    signal: str = Field(..., description="信号类型(buy/sell/hold)")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class AnalysisDetail(BaseModel):
    """分析详情模型 - 包含各维度详细评分"""
    rsi: Optional[DimensionScore] = Field(None, description="RSI指标评分")
    kdj: Optional[DimensionScore] = Field(None, description="KDJ指标评分")
    macd: Optional[DimensionScore] = Field(None, description="MACD指标评分")
    bollinger: Optional[DimensionScore] = Field(None, description="布林带评分")
    volume: Optional[DimensionScore] = Field(None, description="成交量评分")
    fund_flow: Optional[DimensionScore] = Field(None, description="资金流向评分")
    trend: Optional[DimensionScore] = Field(None, description="趋势评分")
    support_resistance: Optional[DimensionScore] = Field(None, description="支撑阻力评分")
    overall_score: int = Field(0, ge=0, le=100, description="综合评分")
    analysis_time: datetime = Field(
        default_factory=datetime.now,
        description="分析时间"
    )


class StockRecommendation(BaseModel):
    """单只股票推荐结果"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    price: float = Field(..., ge=0, description="当前价格")
    change_pct: float = Field(..., description="涨跌幅百分比")
    score: float = Field(..., ge=0, le=100, description="综合评分(0-100)")
    rating: Rating = Field(..., description="评级")
    buy_signals: List[str] = Field(
        default_factory=list,
        description="买入信号列表"
    )
    sell_signals: List[str] = Field(
        default_factory=list,
        description="卖出信号列表"
    )
    stop_loss: float = Field(..., ge=0, description="止损价")
    take_profit: float = Field(..., ge=0, description="止盈价")
    stop_loss_pct: float = Field(..., description="止损百分比")
    take_profit_pct: float = Field(..., description="止盈百分比")
    risk_reward_ratio: float = Field(..., ge=0, description="风险收益比")
    recommend: bool = Field(..., description="是否推荐")
    analysis_detail: Optional[AnalysisDetail] = Field(
        None,
        description="详细分析数据"
    )


class ScanResult(BaseModel):
    """扫描结果模型"""
    strategy_type: str = Field(..., description="策略类型")
    scan_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="扫描时间"
    )
    total_analyzed: int = Field(0, ge=0, description="分析总数")
    qualified_count: int = Field(0, ge=0, description="符合条件的数量")
    recommendations: List[StockRecommendation] = Field(
        default_factory=list,
        description="推荐股票列表"
    )
    filters_applied: Optional[Dict[str, Any]] = Field(
        None,
        description="应用的过滤条件"
    )


class RecommendationHistory(BaseModel):
    """推荐历史记录"""
    id: Optional[int] = Field(None, description="记录ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    strategy_type: str = Field(..., description="策略类型")
    recommendation_type: str = Field(..., description="推荐类型(buy/sell)")
    score: float = Field(..., description="评分")
    price_at_recommendation: float = Field(..., description="推荐时价格")
    target_price: Optional[float] = Field(None, description="目标价格")
    stop_loss: Optional[float] = Field(None, description="止损价")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    status: str = Field("active", description="状态(active/closed/expired)")
    result: Optional[str] = Field(None, description="结果(profit/loss/neutral)")


class BatchScanRequest(BaseModel):
    """批量扫描请求"""
    strategies: List[StrategyType] = Field(
        ...,
        min_length=1,
        description="策略类型列表"
    )
    top_n_per_strategy: int = Field(
        5,
        ge=1,
        le=50,
        description="每个策略返回的前N只"
    )
    stock_pool: StockPoolType = Field(
        StockPoolType.ALL,
        description="股票池类型"
    )
    custom_codes: Optional[List[str]] = Field(
        None,
        description="自定义股票代码"
    )
    min_score: int = Field(
        60,
        ge=0,
        le=100,
        description="最低评分"
    )
