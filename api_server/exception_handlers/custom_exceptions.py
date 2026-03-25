#!/usr/bin/env python3
"""
自定义异常和异常处理器
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime
import logging

from ..config import settings

logger = logging.getLogger(__name__)


def _error_response(code: int, message: str, details: Optional[str] = None) -> dict:
    """Create a JSON-serializable error response dict"""
    return {
        "success": False,
        "code": code,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }


def register_exception_handlers(app: FastAPI):
    """注册所有异常处理器"""

    # Pydantic 验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_response(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Validation error",
                details=str(exc.errors())
            )
        )

    # Pydantic 模型验证错误
    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
        logger.error(f"Pydantic validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_response(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Data validation error",
                details=str(exc.errors())
            )
        )

    # SQLAlchemy 错误
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_response(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error",
                details="Internal database error occurred"
            )
        )

    # 通用异常（生产环境不泄露详细信息）
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        error_msg = str(exc)
        logger.error(f"Unhandled exception: {error_msg}", exc_info=True)

        # 生产环境隐藏详细错误
        details = error_msg if settings.DEBUG else "Internal server error"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_response(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Internal server error",
                details=details
            )
        )


class APIException(Exception):
    """API 自定义异常基类"""

    def __init__(self, message: str, code: int = 400, details: Optional[str] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundException(APIException):
    """未找到异常"""

    def __init__(self, message: str = "Resource not found", details: Optional[str] = None):
        super().__init__(message, 404, details)


class BadRequestException(APIException):
    """请求错误异常"""

    def __init__(self, message: str = "Bad request", details: Optional[str] = None):
        super().__init__(message, 400, details)


class UnauthorizedException(APIException):
    """未授权异常"""

    def __init__(self, message: str = "Unauthorized", details: Optional[str] = None):
        super().__init__(message, 401, details)


class ForbiddenException(APIException):
    """禁止访问异常"""

    def __init__(self, message: str = "Forbidden", details: Optional[str] = None):
        super().__init__(message, 403, details)
