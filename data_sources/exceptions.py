"""
异常模块

定义数据源相关的异常类型
"""

from typing import Optional


class DataSourceError(Exception):
    """
    数据源异常基类

    所有数据源适配器抛出的异常都应该继承此类
    """

    def __init__(
        self,
        source: str,
        message: str,
        original_error: Optional[Exception] = None
    ):
        """
        Args:
            source: 数据源名称 (如 "tushare", "akshare")
            message: 错误描述
            original_error: 原始异常 (可选)
        """
        self.source = source
        self.message = message
        self.original_error = original_error

        full_message = f"[{source}] {message}"
        if original_error:
            full_message += f" | Original error: {original_error}"

        super().__init__(full_message)


class DataSourceTimeoutError(DataSourceError):
    """数据源超时异常"""
    pass


class DataSourceNotFoundError(DataSourceError):
    """数据未找到异常"""
    pass


class DataSourceConfigError(DataSourceError):
    """配置错误异常"""
    pass
