#!/usr/bin/env python3
"""ZigZag 指标路由 - 之字转向指标"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime

from ..models.common import APIResponse
from technical_analysis.indicators.zigzag import ZigZag
from ..services.stock_market_service import StockMarketService


zigzag_router = APIRouter()


@zigzag_router.post("/indicators/zigzag", response_model=APIResponse)
async def calculate_zigzag(
    stock_code: str,
    days: int = 120,
    threshold: float = 0.05
):
    """
    计算 ZigZag 之字转向指标

    功能：
    - 识别价格的主要转折点
    - 过滤噪音，只保留重要的价格转折
    - 判断当前趋势方向

    Args:
        stock_code: 股票代码
        days: 回溯天数 (默认120)
        threshold: 转折点阈值 (默认5%)

    Returns:
        ZigZag 转折点和趋势信息
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

        # 计算 ZigZag
        zigzag_calculator = ZigZag(df, threshold=threshold)
        signal = zigzag_calculator.get_zigzag_signal()
        recent_pivots = zigzag_calculator.get_recent_pivots(count=5)

        # 准备返回数据
        result = {
            "stock_code": stock_code,
            "days": days,
            "threshold": threshold,
            "analysis_date": datetime.now().isoformat(),
            "trend": signal.get('trend', 'neutral'),
            "trend_strength": signal.get('trend_strength', 0),
            "trend_direction": get_trend_direction(signal.get('trend', 'neutral')),
            "is_uptrend": signal.get('is_uptrend', False),
            "is_downtrend": signal.get('is_downtrend', False),
            "last_change_date": signal.get('last_change_date'),
            "zigzag_points_count": signal.get('zigzag_points_count', 0),
            "current_price": signal.get('current_price'),
            "recent_pivots": recent_pivots
        }

        return APIResponse(
            data=result,
            message="ZigZag 计算成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZigZag 计算失败: {str(e)}")


def get_trend_direction(trend: str) -> str:
    """获取趋势方向描述"""
    directions = {
        'up': '📈 上升趋势',
        'down': '📉 下降趋势',
        'neutral': '⚪ 横盘整理'
    }
    return directions.get(trend, '未知')
