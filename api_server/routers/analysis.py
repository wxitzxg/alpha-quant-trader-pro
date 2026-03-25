#!/usr/bin/env python3
"""技术分析路由 - 集成业务逻辑"""

import os
from fastapi import APIRouter, HTTPException, Path, Query, Body, Depends
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..models.common import APIResponse
from ..models.analysis import (
    AnalysisRequest,
    FiveDimensionResult,
    StrategySignal,
    IndicatorResult
)
from ..services.data_source_service import DataSourceService
from technical_analysis.services import AnalysisService
from common.database import DatabaseManager

analysis_router = APIRouter()

# 从环境变量获取数据库URL
DATABASE_URL = os.environ.get(
    "DATABASE__URL",
    "postgresql://alpha_quant_trader_pro:alpha_quant_trader_pro@alpha-quant-db:5432/alpha_quant_trader_pro"
)

def get_db_session() -> Session:
    """获取数据库 session 依赖"""
    db_manager = DatabaseManager(DATABASE_URL)
    with db_manager.get_session() as session:
        yield session

@analysis_router.post("/analysis/five-dimension", response_model=APIResponse)
async def analyze_five_dimension(request: AnalysisRequest):
    """
    五维共振分析

    Args:
        request: 股票代码、分析天数、周期等参数

    Returns:
        五维共振分析结果
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.analyze_stock(
                symbol=request.stock_code,
                interval="1d",  # 默认使用日线
                days=request.days
            )

            if 'error' in result:
                raise HTTPException(
                    status_code=400,
                    detail=result.get('message', 'Analysis failed')
                )

            return APIResponse(
                data=result,
                message="Five dimension analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing stock: {str(e)}")

@analysis_router.get("/analysis/strategies/{stock_code}", response_model=APIResponse)
async def analyze_with_strategies(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    interval: str = Query("1d", description="周期 (1d/1w/1m)"),
    days: int = Query(120, ge=30, description="分析天数")
):
    """
    使用三大策略进行分析

    Args:
        stock_code: 股票代码
        interval: K线周期
        days: 回溯天数

    Returns:
        VCP、九转、背离三大策略分析结果
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.analyze_with_strategies(
                symbol=stock_code,
                interval=interval,
                days=days
            )

            if 'error' in result:
                raise HTTPException(
                    status_code=400,
                    detail=result.get('message', 'Analysis failed')
                )

            return APIResponse(
                data=result,
                message="Strategies analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing with strategies: {str(e)}")

@analysis_router.get("/analysis/indicator/{stock_code}", response_model=APIResponse)
async def get_indicator(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    indicator_name: str = Query(..., description="指标名称 (ma/macd/rsi/boll/td)")
):
    """
    获取技术指标

    Args:
        stock_code: 股票代码
        indicator_name: 指标名称

    Returns:
        技术指标数据
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.get_technical_indicators(
                symbol=stock_code,
                interval="1d",
                days=60
            )

            if 'error' in result:
                raise HTTPException(
                    status_code=400,
                    detail=result.get('message', 'Failed to get indicators')
                )

            return APIResponse(
                data={
                    "stock_code": stock_code,
                    "indicator_name": indicator_name,
                    "current_price": result.get("current_price"),
                    "signals": result.get("latest_signals"),
                    "data_points": result.get("data_points")
                },
                message=f"{indicator_name} indicator retrieved successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting indicator: {str(e)}")

@analysis_router.get("/analysis/report/{stock_code}", response_model=APIResponse)
async def generate_analysis_report(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    interval: str = Query("1d", description="周期 (1d/1w/1m)"),
    days: int = Query(120, ge=30, description="分析天数")
):
    """
    生成完整分析报告

    Args:
        stock_code: 股票代码
        interval: K线周期
        days: 回溯天数

    Returns:
        格式化的完整分析报告
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            report = analysis_service.generate_analysis_report(
                symbol=stock_code,
                interval=interval,
                days=days
            )

            return APIResponse(
                data={
                    "stock_code": stock_code,
                    "interval": interval,
                    "days": days,
                    "report": report
                },
                message="Analysis report generated successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@analysis_router.get("/analysis/strategy/vcp/{stock_code}", response_model=APIResponse)
async def analyze_vcp(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    days: int = Query(120, ge=30, description="分析天数")
):
    """
    VCP 策略分析

    Args:
        stock_code: 股票代码
        days: 回溯天数

    Returns:
        VCP 策略分析结果
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.analyze_with_strategies(
                symbol=stock_code,
                days=days
            )

            vcp_result = result.get("strategies", {}).get("vcp_breakout", {})

            return APIResponse(
                data={
                    "strategy_name": "VCP",
                    "stock_code": stock_code,
                    "signal": vcp_result.get("signal"),
                    "score": vcp_result.get("score"),
                    "confidence": vcp_result.get("confidence"),
                    "details": vcp_result.get("details", {})
                },
                message="VCP analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing VCP: {str(e)}")

@analysis_router.get("/analysis/strategy/td/{stock_code}", response_model=APIResponse)
async def analyze_td_golden_pit(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    days: int = Query(120, ge=30, description="分析天数")
):
    """
    九转黄金坑策略分析

    Args:
        stock_code: 股票代码
        days: 回溯天数

    Returns:
        九转策略分析结果
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.analyze_with_strategies(
                symbol=stock_code,
                days=days
            )

            td_result = result.get("strategies", {}).get("td_golden_pit", {})

            return APIResponse(
                data={
                    "strategy_name": "TD Golden Pit",
                    "stock_code": stock_code,
                    "signal": td_result.get("signal"),
                    "score": td_result.get("score"),
                    "td_count": td_result.get("td_count"),
                    "details": td_result.get("details", {})
                },
                message="TD Golden Pit analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing TD Golden Pit: {str(e)}")

@analysis_router.get("/analysis/strategy/divergence/{stock_code}", response_model=APIResponse)
async def analyze_top_divergence(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    days: int = Query(120, ge=30, description="分析天数")
):
    """
    顶部背离策略分析

    Args:
        stock_code: 股票代码
        days: 回溯天数

    Returns:
        背离策略分析结果
    """
    try:
        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            analysis_service = AnalysisService(session)

            result = analysis_service.analyze_with_strategies(
                symbol=stock_code,
                days=days
            )

            div_result = result.get("strategies", {}).get("top_divergence", {})

            return APIResponse(
                data={
                    "strategy_name": "Top Divergence",
                    "stock_code": stock_code,
                    "signal": div_result.get("signal"),
                    "score": div_result.get("score"),
                    "divergence_type": div_result.get("divergence_type"),
                    "details": div_result.get("details", {})
                },
                message="Top Divergence analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing Top Divergence: {str(e)}")
