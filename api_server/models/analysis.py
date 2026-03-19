#!/usr/bin/env python3
"""技术分析模型"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class IndicatorResult(BaseModel):
    """指标计算结果"""
    indicator_name: str = Field(..., description="指标名称")
    values: List[float] = Field(..., description="指标值列表")
    dates: List[str] = Field(..., description="对应日期")
    parameters: Optional[Dict[str, Any]] = Field(None, description="指标参数")


class PatternDetection(BaseModel):
    """形态识别结果"""
    pattern_type: str = Field(..., description="形态类型")
    detected: bool = Field(..., description="是否检测到")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    start_date: Optional[str] = Field(None, description="形态开始日期")
    end_date: Optional[str] = Field(None, description="形态结束日期")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class StrategySignal(BaseModel):
    """策略信号"""
    strategy_name: str = Field(..., description="策略名称")
    signal: str = Field(..., description="信号 (buy/sell/hold)")
    strength: float = Field(..., ge=0, le=1, description="信号强度")
    price: Optional[float] = Field(None, description="建议价格")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    timestamp: datetime = Field(default_factory=datetime.now, description="信号时间")


class FiveDimensionResult(BaseModel):
    """五维共振结果"""
    total_score: int = Field(..., description="总分")
    max_score: int = Field(100, description="满分")
    score_percentage: float = Field(..., description="得分百分比")
    action: str = Field(..., description="决策 (STRONG_BUY/BUY/HOLD/WAIT)")
    position_suggestion: float = Field(..., description="建议仓位")
    confidence_level: str = Field(..., description="置信度 (S/A/B/C)")
    dimension_scores: Dict[str, int] = Field(..., description="维度得分")
    dimension_details: Dict[str, Dict] = Field(..., description="维度详情")


class AnalysisRequest(BaseModel):
    """分析请求"""
    stock_code: str = Field(..., description="股票代码")
    days: int = Field(120, ge=1, le=365, description="分析天数")
    indicators: Optional[List[str]] = Field(None, description="指标列表")
