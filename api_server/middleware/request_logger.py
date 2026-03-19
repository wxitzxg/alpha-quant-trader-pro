#!/usr/bin/env python3
"""
请求日志中间件
记录所有 API 请求和响应
"""

import time
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        记录请求和响应

        Args:
            request: HTTP 请求
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP 响应
        """
        # 记录请求
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        # 读取请求体（仅用于日志，不影响后续处理）
        body = ""
        try:
            body_bytes = await request.body()
            body = body_bytes.decode('utf-8') if body_bytes else ""

            # 重新设置请求体
            async def receive():
                return {'type': 'http.request', 'body': body_bytes, 'more_body': False}

            request._receive = receive
        except Exception:
            pass

        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_host} "
            f"headers={dict(request.headers)} "
            f"body={body[:500]}"  # 限制日志长度
        )

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"from {client_host} "
                f"elapsed={elapsed_time:.3f}s "
                f"error={str(e)}"
            )
            raise

        # 记录响应
        elapsed_time = time.time() - start_time

        # 对于 StreamingResponse，无法直接读取响应体
        if isinstance(response, StreamingResponse):
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"from {client_host} "
                f"status={response.status_code} "
                f"elapsed={elapsed_time:.3f}s"
            )
        else:
            # 读取响应体
            resp_body = b""
            async for chunk in response.body_iterator:
                resp_body += chunk

            # 重新设置响应体
            response.body_iterator = iterate_in_threadpool(iter([resp_body]))

            try:
                resp_text = resp_body.decode('utf-8')
                logger.info(
                    f"Response: {request.method} {request.url.path} "
                    f"from {client_host} "
                    f"status={response.status_code} "
                    f"elapsed={elapsed_time:.3f}s "
                    f"body={resp_text[:500]}"
                )
            except Exception:
                logger.info(
                    f"Response: {request.method} {request.url.path} "
                    f"from {client_host} "
                    f"status={response.status_code} "
                    f"elapsed={elapsed_time:.3f}s"
                )

        return response
