#!/usr/bin/env python3
"""股票市场管理路由 - 同步股票列表和K线数据"""

from fastapi import APIRouter, HTTPException, Path
from datetime import datetime

from ..models.common import APIResponse
from ..models.stock_market import (
    StockSyncParams,
    KLineSyncParams,
    SyncStatusResponse
)
from ..services import StockMarketService

stock_market_router = APIRouter()
service = StockMarketService()


@stock_market_router.post("/market/stock/sync", response_model=APIResponse[SyncStatusResponse])
async def sync_stock_list(params: StockSyncParams):
    """同步股票列表"""
    try:
        result = service.sync_all_stocks(force_update=params.force_update)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to sync stocks"))

        return APIResponse(
            data=SyncStatusResponse(
                task_id=f"stock_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                sync_type="stock",
                status={
                    "status": "completed",
                    "progress": 100,
                    "total_count": result.get("count", 0),
                    "completed_count": result.get("count", 0),
                    "failed_count": 0,
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "error_message": None
                }
            ),
            message=result.get("message", "Stock sync completed")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing stocks: {str(e)}")


@stock_market_router.get("/market/stock/sync-status", response_model=APIResponse)
async def get_stock_sync_status():
    """获取股票同步状态"""
    try:
        result = service.get_sync_status(sync_type="stocks")

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to get sync status"))

        return APIResponse(
            data=result.get("data", {}),
            message="Sync status retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")


@stock_market_router.post("/market/kline/sync/{stock_code}", response_model=APIResponse[SyncStatusResponse])
async def sync_kline(
    stock_code: str = Path(..., description="股票代码"),
    params: KLineSyncParams = None
):
    """同步单股K线"""
    if params is None:
        params = KLineSyncParams(stock_code=stock_code)

    try:
        result = service.sync_single_kline(
            stock_code=stock_code,
            interval=params.interval,
            start_date=params.start_date,
            end_date=params.end_date,
            force_update=params.force_update
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to sync kline"))

        return APIResponse(
            data=SyncStatusResponse(
                task_id=f"kline_sync_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                sync_type="kline",
                status={
                    "status": "completed",
                    "progress": 100,
                    "total_count": result.get("count", 0),
                    "completed_count": result.get("count", 0),
                    "failed_count": 0,
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "error_message": None
                }
            ),
            message=result.get("message", f"KLine sync completed for {stock_code}")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing kline: {str(e)}")
