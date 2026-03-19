#!/usr/bin/env python3
"""背离检测路由 - 检测价格与指标背离"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from technical_analysis.indicators.divergence_check import DivergenceCheck
from technical_analysis.indicators.base_indicators import BaseIndicators
from ..services.stock_market_service import StockMarketService


divergence_router = APIRouter()


@divergence_router.post("/indicators/divergence", response_model=APIResponse)
async def detect_divergence(
    stock_code: str,
    days: int = 60,
    indicator: str = "macd"
):
    """
    检测背离信号

    背离类型：
    - 顶背离：价格创新高，但指标未创新高 (看跌信号)
    - 底背离：价格创新低，但指标未创新低 (看涨信号)

    Args:
        stock_code: 股票代码
        days: 回溯天数 (默认60)
        indicator: 指标类型 (目前支持: macd)

    Returns:
        背离检测结果和详细信息
    """
    try:
        # 获取K线数据
        klines = StockMarketService.get_kline(
            stock_code=stock_code,
            start_date=None,
            end_date=None,
            limit=days
        )

        if not klines or len(klines) < 30:
            raise HTTPException(status_code=400, detail="K线数据不足，至少需要30个交易日")

        # 转换为DataFrame格式
        import pandas as pd
        df = pd.DataFrame(klines)

        # 计算MACD指标
        indicator_calculator = BaseIndicators(df)
        df_with_indicators = indicator_calculator.calculate_trend_indicators()

        # 检测背离
        divergence_checker = DivergenceCheck(df_with_indicators)
        divergence_result = divergence_checker.detect_macd_divergence(lookback=days)

        # 准备返回数据
        result = {
            "stock_code": stock_code,
            "days": days,
            "indicator": indicator,
            "analysis_date": datetime.now().isoformat(),
            "divergences": divergence_result
        }

        # 检查是否有背离信号
        has_signal = False
        if divergence_result.get('bullish_divergence', {}).get('detected', False):
            has_signal = True
        if divergence_result.get('bearish_divergence', {}).get('detected', False):
            has_signal = True

        message = "发现背离信号" if has_signal else "未检测到背离"

        return APIResponse(
            data=result,
            message=message
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"背离检测失败: {str(e)}")
