"""统一的异常处理体系"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ErrorDetail:
    """错误详情"""
    code: str
    message: str
    field: Optional[str] = None
    original_error: Optional[Exception] = None


class TradingSystemError(Exception):
    """
    量化交易系统基础异常

    所有自定义异常的基类
    """

    def __init__(self, message: str, code: str = "GENERAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"


class DatabaseError(TradingSystemError):
    """数据库相关异常"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, code="DATABASE_ERROR")
        self.original_error = original_error


class ValidationError(TradingSystemError):
    """数据验证异常"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field

    def __str__(self):
        if self.field:
            return f"[{self.code}] Field '{self.field}': {self.message}"
        return f"[{self.code}] {self.message}"


class ConfigurationError(TradingSystemError):
    """配置相关异常"""

    def __init__(self, message: str, key: Optional[str] = None):
        super().__init__(message, code="CONFIG_ERROR")
        self.key = key


class DataSourceError(TradingSystemError):
    """数据源相关异常"""

    def __init__(self, message: str, source: Optional[str] = None):
        super().__init__(message, code="DATA_SOURCE_ERROR")
        self.source = source

    def __str__(self):
        if self.source:
            return f"[{self.code}] Source '{self.source}': {self.message}"
        return f"[{self.code}] {self.message}"


class BusinessError(TradingSystemError):
    """业务逻辑异常"""

    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message, code="BUSINESS_ERROR")
        self.context = context or {}


class NotFoundError(TradingSystemError):
    """资源未找到异常"""

    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} not found: {identifier}"
        super().__init__(message, code="NOT_FOUND")
        self.resource_type = resource_type
        self.identifier = identifier


class InsufficientFundsError(BusinessError):
    """资金不足异常"""

    def __init__(self, required: float, available: float):
        message = f"Insufficient funds. Required: {required}, Available: {available}"
        super().__init__(message, context={"required": required, "available": available})
        self.code = "INSUFFICIENT_FUNDS"


class InsufficientSharesError(BusinessError):
    """股票数量不足异常"""

    def __init__(self, required: int, available: int):
        message = f"Insufficient shares. Required: {required}, Available: {available}"
        super().__init__(message, context={"required": required, "available": available})
        self.code = "INSUFFICIENT_SHARES"


# ========== 装饰器：统一异常处理 ==========

def handle_exceptions(func):
    """
    统一异常处理装饰器

    将底层异常转换为系统异常，并记录日志

    示例：
        @handle_exceptions
        def my_function():
            # 业务逻辑
            pass
    """
    import logging
    from functools import wraps

    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TradingSystemError:
            # 已经是系统异常，直接抛出
            raise
        except Exception as e:
            # 其他异常转换为系统异常
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise TradingSystemError(
                message=f"Unexpected error: {str(e)}",
                code="UNEXPECTED_ERROR"
            ) from e

    return wrapper


# ========== 工具函数 ==========

def format_error(error: Exception) -> dict:
    """
    格式化异常为字典

    Args:
        error: 异常对象

    Returns:
        错误信息字典
    """
    if isinstance(error, TradingSystemError):
        result = {
            "code": error.code,
            "message": error.message,
            "type": error.__class__.__name__
        }

        # 添加特定异常的额外信息
        if hasattr(error, 'field') and error.field:
            result['field'] = error.field
        if hasattr(error, 'resource_type'):
            result['resource_type'] = error.resource_type
            result['identifier'] = error.identifier
        if hasattr(error, 'context'):
            result['context'] = error.context

        return result
    else:
        return {
            "code": "UNEXPECTED_ERROR",
            "message": str(error),
            "type": error.__class__.__name__
        }
