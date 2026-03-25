#!/usr/bin/env python3
"""股票市场管理模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StockSyncParams(BaseModel):
    """股票同步参数"""
    force_update: bool = Field(False, description="强制更新")


class KLineSyncParams(BaseModel):
    """K线同步参数"""
    interval: str = Field("1d", description="周期 (1d/1w/1m)")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    force_update: bool = Field(False, description="强制更新")


class SyncStatus(BaseModel):
    """同步状态"""
    status: str = Field(..., description="状态 (pending/running/completed/failed)")
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    total_count: int = Field(0, description="总数")
    completed_count: int = Field(0, description="已完成数")
    failed_count: int = Field(0, description="失败数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")


class SyncStatusResponse(BaseModel):
    """同步状态响应"""
    task_id: str = Field(..., description="任务ID")
    sync_type: str = Field(..., description="同步类型 (stock/kline)")
    status: SyncStatus
