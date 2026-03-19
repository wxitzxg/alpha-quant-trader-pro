"""Backtest Exceptions - 回测异常"""


class BacktestError(Exception):
    """回测基础异常"""
    pass


class InsufficientDataError(BacktestError):
    """数据不足异常"""
    pass


class InsufficientFundsError(BacktestError):
    """资金不足异常"""
    pass


class InsufficientSharesError(BacktestError):
    """持仓不足异常"""
    pass


class InvalidConfigError(BacktestError):
    """配置无效异常"""
    pass
