#!/usr/bin/env python3
"""
健康检查路由
"""

from fastapi import APIRouter
from ..models.common import APIResponse

health_router = APIRouter()


@health_router.get("/health", response_model=APIResponse)
async def health_check():
    """健康检查"""
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={"status": "ok"}
    )
