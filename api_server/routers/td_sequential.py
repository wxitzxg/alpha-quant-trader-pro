#!/usr/bin/env python3
"""TD 序列路由 - 神奇九转指标"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from technical_analysis.indicators.td_sequential import TDSequential
from ..services.stock_market_service import StockMarketService


td_sequential_router = APIRouter()


@td_sequential_router.post("/indicators/td-sequential", response_model=APIResponse)
async def calculate_td_sequential(
    stock_code: str,
    days: int = 30,
    period: int = 9,
    compare_period: int = 4
):
    """
    计算 TD 序列（神奇九转）

    信号说明：
    - 低九：连续 9 日收盘价 < 4 日前收盘价 (下跌衰竭，买入信号)
    - 高九：连续 9 日收盘价 > 4 日前收盘价 (上涨衰竭，卖出信号)

    Args:
        stock_code: 股票代码
        days: 回溯天数 (默认30)
        period: 九转周期 (默认9)
        compare_period: 比较周期 (默认4)

    Returns:
        TD 计数和信号状态
    """
    try:
        # 获取K线数据
        klines = StockMarketService.get_kline(
            stock_code=stock_code,
            start_date=None,
            end_date=None,
            limit=days
        )

        if not klines or len(klines) < period + compare_period:
            raise HTTPException(status_code=400, detail=f"K线数据不足，至少需要{period + compare_period}个交易日")

        # 转换为DataFrame格式
        import pandas as pd
        df = pd.DataFrame(klines)

        # 计算 TD 序列
        td_calculator = TDSequential(df, period=period, compare_period=compare_period)
        td_result = td_calculator.get_td_sequential()

        # 准备返回数据
        result = {
            "stock_code": stock_code,
            "days": days,
            "period": period,
            "compare_period": compare_period,
            "analysis_date": datetime.now().isoformat(),
            "td_buy_count": td_result.get('td_buy_count', 0),
            "td_sell_count": td_result.get('td_sell_count', 0),
            "td_buy_signal": td_result.get('td_buy_signal', False),
            "td_sell_signal": td_result.get('td_sell_signal', False),
            "status": td_result.get('status', 'neutral'),
            "interpretation": get_td_interpretation(td_result)
        }

        return APIResponse(
            data=result,
            message="TD 序列计算成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TD 序列计算失败: {str(e)}")


def get_td_interpretation(td_result: dict) -> str:
    """获取 TD 序列解读"""
    status = td_result.get('status', 'neutral')

    interpretations = {
        'low_nine_complete': '✅ 低九完成！下跌衰竭，潜在买入点',
        'high_nine_complete': '⚠️ 高九完成！上涨衰竭，潜在卖出点',
        'counting_low_1': '📉 正在计数低九 (1/9)',
        'counting_low_2': '📉 正在计数低九 (2/9)',
        'counting_low_3': '📉 正在计数低九 (3/9)',
        'counting_low_4': '📉 正在计数低九 (4/9)',
        'counting_low_5': '📉 正在计数低九 (5/9)',
        'counting_low_6': '📉 正在计数低九 (6/9)',
        'counting_low_7': '📉 正在计数低九 (7/9)',
        'counting_low_8': '📉 正在计数低九 (8/9)',
        'counting_high_1': '📈 正在计数高九 (1/9)',
        'counting_high_2': '📈 正在计数高九 (2/9)',
        'counting_high_3': '📈 正在计数高九 (3/9)',
        'counting_high_4': '📈 正在计数高九 (4/9)',
        'counting_high_5': '📈 正在计数高九 (5/9)',
        'counting_high_6': '📈 正在计数高九 (6/9)',
        'counting_high_7': '📈 正在计数高九 (7/9)',
        'counting_high_8': '📈 正在计数高九 (8/9)',
        'neutral': '⚪ 无信号'
    }

    return interpretations.get(status, '无明确信号')
