#!/usr/bin/env python3
"""基础技术指标路由 - 提供各类技术指标计算"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from datetime import datetime

from ..models.common import APIResponse
from ..models.analysis import AnalysisRequest, IndicatorResult
from technical_analysis.indicators.base_indicators import BaseIndicators
from ..services.stock_market_service import StockMarketService


base_indicators_router = APIRouter()


@base_indicators_router.post("/indicators/base", response_model=APIResponse)
async def calculate_base_indicators(request: AnalysisRequest):
    """
    计算基础技术指标

    支持的指标类型：
    - 趋势指标：MA5/10/20/50/200, EMA, MACD, ADX
    - 动量指标：RSI, Stochastic, CCI, Williams %R
    - 波动率指标：布林带, ATR, 标准差
    - 成交量指标：OBV, 量比

    Args:
        stock_code: 股票代码
        days: 分析天数 (默认120，范围1-365)
        indicators: 指标列表 (可选，默认全部)

    Returns:
        包含所有技术指标数据和最新信号的响应
    """
    try:
        # 获取K线数据
        service = StockMarketService()
        result = service.get_kline_data(
            stock_code=request.stock_code,
            interval="1d",
            limit=request.days
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "获取K线数据失败"))

        klines = result.get("data", [])
        
        if not klines or len(klines) < 20:
            raise HTTPException(status_code=400, detail="K线数据不足，至少需要20个交易日")

        # 转换为DataFrame格式
        import pandas as pd
        df = pd.DataFrame(klines)
        
        # 设置日期为索引
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        df = df.sort_index()  # 按日期升序排列

        # 计算基础指标
        indicator_calculator = BaseIndicators(df)
        df_with_indicators = indicator_calculator.calculate_all_indicators()

        # 获取最新的技术信号
        latest_signals = indicator_calculator.get_latest_signals()

        # 准备返回数据
        result = {
            "stock_code": request.stock_code,
            "days": request.days,
            "data_points": len(df_with_indicators),
            "latest_date": df_with_indicators.index[-1].strftime('%Y-%m-%d') if hasattr(df_with_indicators.index[-1], 'strftime') else str(df_with_indicators.index[-1]),
            "latest_price": float(df_with_indicators['close'].iloc[-1]),
            "signals": latest_signals,
            "indicators": {
                # 趋势指标
                "ma5": float(df_with_indicators['ma5'].iloc[-1]) if 'ma5' in df_with_indicators.columns else None,
                "ma10": float(df_with_indicators['ma10'].iloc[-1]) if 'ma10' in df_with_indicators.columns else None,
                "ma20": float(df_with_indicators['ma20'].iloc[-1]) if 'ma20' in df_with_indicators.columns else None,
                "ma50": float(df_with_indicators['ma50'].iloc[-1]) if 'ma50' in df_with_indicators.columns else None,
                "ma200": float(df_with_indicators['ma200'].iloc[-1]) if 'ma200' in df_with_indicators.columns else None,
                "macd": float(df_with_indicators['macd'].iloc[-1]) if 'macd' in df_with_indicators.columns else None,
                "macd_signal": float(df_with_indicators['macd_signal'].iloc[-1]) if 'macd_signal' in df_with_indicators.columns else None,
                "macd_histogram": float(df_with_indicators['macd_histogram'].iloc[-1]) if 'macd_histogram' in df_with_indicators.columns else None,
                "adx": float(df_with_indicators['adx'].iloc[-1]) if 'adx' in df_with_indicators.columns else None,
                # 动量指标
                "rsi": float(df_with_indicators['rsi'].iloc[-1]) if 'rsi' in df_with_indicators.columns else None,
                "stoch_k": float(df_with_indicators['stoch_k'].iloc[-1]) if 'stoch_k' in df_with_indicators.columns else None,
                "stoch_d": float(df_with_indicators['stoch_d'].iloc[-1]) if 'stoch_d' in df_with_indicators.columns else None,
                "cci": float(df_with_indicators['cci'].iloc[-1]) if 'cci' in df_with_indicators.columns else None,
                "williams_r": float(df_with_indicators['williams_r'].iloc[-1]) if 'williams_r' in df_with_indicators.columns else None,
                # 波动率指标
                "bb_upper": float(df_with_indicators['bb_upper'].iloc[-1]) if 'bb_upper' in df_with_indicators.columns else None,
                "bb_middle": float(df_with_indicators['bb_middle'].iloc[-1]) if 'bb_middle' in df_with_indicators.columns else None,
                "bb_lower": float(df_with_indicators['bb_lower'].iloc[-1]) if 'bb_lower' in df_with_indicators.columns else None,
                "bb_width": float(df_with_indicators['bb_width'].iloc[-1]) if 'bb_width' in df_with_indicators.columns else None,
                "atr": float(df_with_indicators['atr'].iloc[-1]) if 'atr' in df_with_indicators.columns else None,
                # 成交量指标
                "obv": float(df_with_indicators['obv'].iloc[-1]) if 'obv' in df_with_indicators.columns else None,
                "volume_ratio": float(df_with_indicators['volume_ratio'].iloc[-1]) if 'volume_ratio' in df_with_indicators.columns else None,
            }
        }

        return APIResponse(
            data=result,
            message="基础技术指标计算成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算基础指标失败: {str(e)}")


@base_indicators_router.get("/indicators/base/{stock_code}", response_model=APIResponse)
async def get_base_indicators(
    stock_code: str,
    days: int = 120
):
    """
    获取指定股票的基础技术指标（GET版本）

    Args:
        stock_code: 股票代码
        days: 分析天数 (默认120)

    Returns:
        技术指标数据
    """
    request = AnalysisRequest(stock_code=stock_code, days=days)
    return await calculate_base_indicators(request)
