#!/usr/bin/env python3
"""
限流中间件
基于 slowapi 实现请求限流
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime

from ..config import settings


# 创建限流器
limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware:
    """限流中间件包装类"""

    @staticmethod
    def get_limiter():
        """获取限流器实例"""
        return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    限流异常处理器

    Args:
        request: HTTP 请求
        exc: 限流异常
    """
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "code": 429,
            "message": "Too many requests",
            "details": f"Rate limit exceeded. Retry after {exc.limit.limit} seconds.",
            "retry_after": exc.limit.limit,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers={"Retry-After": str(exc.limit.limit)}
    )
