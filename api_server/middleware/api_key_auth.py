#!/usr/bin/env python3
"""
API Key 认证中间件
验证所有请求的 API Key 和签名
"""

from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from datetime import datetime

from ..auth import verify_api_request


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求

        Args:
            request: HTTP 请求
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP 响应
        """
        # 跳过健康检查和文档路径
        skip_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in skip_paths or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            return await call_next(request)

        # 获取请求头
        api_key = request.headers.get("X-API-Key")
        signature = request.headers.get("X-API-Signature")
        timestamp = request.headers.get("X-Timestamp")

        # 读取请求体（用于签名验证）
        body = ""
        if signature and timestamp:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode('utf-8') if body_bytes else ""

                # 重新设置请求体以便后续使用
                receive = request._receive

                async def new_receive():
                    return {'type': 'http.request', 'body': body_bytes, 'more_body': False}

                request._receive = new_receive
            except Exception:
                body = ""

        # 验证 API 请求
        try:
            verify_api_request(
                api_key=api_key,
                signature=signature,
                timestamp=timestamp,
                body=body
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "code": 401,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # 继续处理请求
        response = await call_next(request)
        return response
