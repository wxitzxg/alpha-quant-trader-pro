#!/usr/bin/env python3
"""VCP 形态检测路由 - 波动收缩形态识别"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from technical_analysis.indicators.vcp_detector import VCPDetector
from technical_analysis.indicators.base_indicators import BaseIndicators
from ..services.stock_market_service import StockMarketService


vcp_router = APIRouter()


@vcp_router.post("/indicators/vcp", response_model=APIResponse)
async def detect_vcp_pattern(
    stock_code: str,
    days: int = 120,
    min_drops: int = 2,
    max_drops: int = 4
):
    """
    检测 VCP 形态（波动收缩形态）

    VCP 特征：
    1. 2-4 次回调，幅度依次减小 (如 -20% → -10% → -5%)
    2. 成交量逐级萎缩
    3. 最后一次回调的高点为枢轴点 (Pivot)
    4. 突破确认：股价放量 (>1.5 倍均量) 突破枢轴点

    Args:
        stock_code: 股票代码
        days: 回溯天数 (默认120)
        min_drops: 最少回调次数 (默认2)
        max_drops: 最多回调次数 (默认4)

    Returns:
        VCP 形态检测结果
    """
    try:
        # 获取K线数据
        klines = StockMarketService.get_kline(
            stock_code=stock_code,
            start_date=None,
            end_date=None,
            limit=days
        )

        if not klines or len(klines) < 60:
            raise HTTPException(status_code=400, detail="K线数据不足，至少需要60个交易日")

        # 转换为DataFrame格式
        import pandas as pd
        df = pd.DataFrame(klines)

        # 计算成交量移动平均（用于突破检测）
        indicator_calculator = BaseIndicators(df)
        df_with_vol = indicator_calculator.calculate_volume_indicators()

        # 检测 VCP 形态
        vcp_detector = VCPDetector(
            df=df_with_vol,
            min_drops=min_drops,
            max_drops=max_drops
        )
        vcp_result = vcp_detector.detect_vcp()

        # 准备返回数据
        result = {
            "stock_code": stock_code,
            "days": days,
            "analysis_date": datetime.now().isoformat(),
            "is_vcp": vcp_result.get('is_vcp', False),
            "stage": vcp_result.get('stage', 'unknown'),
            "stage_description": vcp_result.get('message', '未知阶段'),
            "contraction_ratio": vcp_result.get('contraction_ratio', 0),
            "drop_count": vcp_result.get('drop_count', 0),
            "breakout_detected": vcp_result.get('breakout_detected', False),
            "breakout_price": vcp_result.get('breakout_price'),
            "breakout_volume": vcp_result.get('breakout_volume', False),
            "current_price": vcp_result.get('current_price'),
            "drops": vcp_result.get('drops', [])
        }

        return APIResponse(
            data=result,
            message="VCP 形态检测完成"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VCP 形态检测失败: {str(e)}")
