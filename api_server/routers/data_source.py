#!/usr/bin/env python3
"""数据源聚合路由"""

from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional, List
from datetime import datetime

from ..models.common import APIResponse
from ..models.stock import StockListResponse
from ..models.quote import (
    RealtimeQuote,
    BatchQuoteRequest,
    BatchQuoteResponse,
    TopListResponse
)
from ..models.kline import (
    KLineResponse,
    KLine,
    BatchKLineRequest,
    BatchKLineResponse,
    KLineStats
)
from ..services.data_source_service import DataSourceService

data_source_router = APIRouter()


# ========== 股票基础数据 ==========
@data_source_router.get("/stock/list", response_model=APIResponse[StockListResponse])
async def get_stock_list(
    exchange: Optional[str] = Query(None, description="交易所 (SH/SZ)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取股票列表"""
    result = DataSourceService.get_stock_list(
        page=page, page_size=page_size, exchange=exchange
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=StockListResponse(**result["data"]),
        message="Stock list retrieved successfully"
    )


@data_source_router.get("/stock/info/{stock_code}", response_model=APIResponse)
async def get_stock_info(stock_code: str = Path(..., description="股票代码")):
    """获取股票详情"""
    result = DataSourceService.get_stock_info(stock_code)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return APIResponse(data=result["data"], message="Stock info retrieved successfully")


# ========== 行情数据 ==========
@data_source_router.get("/quote/realtime/{stock_code}", response_model=APIResponse[RealtimeQuote])
async def get_realtime_quote(stock_code: str = Path(..., description="股票代码")):
    """获取单股实时行情"""
    quote_data = DataSourceService.get_realtime_quote(stock_code)
    if not quote_data:
        raise HTTPException(status_code=404, detail=f"Quote not found for {stock_code}")
    return APIResponse(
        data=RealtimeQuote(**quote_data),
        message="Realtime quote retrieved successfully"
    )


@data_source_router.post("/quote/batch", response_model=APIResponse[BatchQuoteResponse])
async def get_batch_quotes(request: BatchQuoteRequest):
    """批量获取行情"""
    try:
        quotes_data = DataSourceService.get_batch_quotes(request.symbols)
        quotes = [RealtimeQuote(**q) for q in quotes_data.values() if q]
        return APIResponse(
            data=BatchQuoteResponse(quotes=quotes, timestamp=datetime.now()),
            message="Batch quotes retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch quotes: {e}")


@data_source_router.get("/quote/top-list", response_model=APIResponse[TopListResponse])
async def get_top_list(
    type: str = Query("gain", description="排行类型 (gain/loss)"),
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)")
):
    """涨跌幅排行"""
    result = DataSourceService.get_top_list(type=type, date=date)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=TopListResponse(**result["data"]),
        message="Top list retrieved successfully"
    )


# ========== K线数据 ==========
@data_source_router.get("/kline/{stock_code}", response_model=APIResponse[KLineResponse])
async def get_kline(
    stock_code: str = Path(..., description="股票代码"),
    interval: str = Query("1d", description="K线周期"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    limit: int = Query(120, ge=1, le=1000, description="数据条数")
):
    """获取K线数据"""
    klines_data = DataSourceService.get_kline(
        stock_code, interval, start_date, end_date, limit
    )
    if klines_data is None:
        raise HTTPException(status_code=404, detail=f"KLine data not found for {stock_code}")
    klines = [KLine(**k) for k in klines_data] if klines_data else []
    return APIResponse(
        data=KLineResponse(
            symbol=stock_code,
            name="",
            interval=interval,
            klines=klines,
            total=len(klines),
            start_date=start_date,
            end_date=end_date
        ),
        message="KLine data retrieved successfully"
    )


@data_source_router.post("/kline/batch", response_model=APIResponse[BatchKLineResponse])
async def get_batch_klines(request: BatchKLineRequest):
    """批量获取K线"""
    try:
        result = DataSourceService.get_batch_klines(request.symbols, request.interval)
        return APIResponse(
            data=BatchKLineResponse(data=result, timestamp=datetime.now()),
            message="Batch KLine data retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch klines: {e}")


@data_source_router.get("/kline/stats/{stock_code}", response_model=APIResponse[KLineStats])
async def get_kline_stats(
    stock_code: str = Path(..., description="股票代码"),
    period: str = Query("1y", description="统计周期 (1y/6m/3m/1m)")
):
    """K线统计信息"""
    result = DataSourceService.get_kline_stats(stock_code, period)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=KLineStats(**result["data"]),
        message="KLine stats retrieved successfully"
    )


# ========== 财务数据 ==========
@data_source_router.get("/financial/indicators/{stock_code}", response_model=APIResponse)
async def get_financial_indicators(stock_code: str = Path(..., description="股票代码")):
    """获取财务指标"""
    result = DataSourceService.get_financial_indicators(stock_code)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return APIResponse(
        data=result["data"],
        message="Financial indicators retrieved successfully"
    )
