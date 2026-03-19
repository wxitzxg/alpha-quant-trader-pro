"""
模拟交易模块异常
"""

from common.exceptions import BusinessError


class StrategyExecutionError(BusinessError):
    """策略执行错误"""
    pass


class InsufficientCashError(BusinessError):
    """现金不足错误"""

    def __init__(self, required: float, available: float):
        message = f"现金不足: 需要 {required:.2f}, 实际 {available:.2f}"
        super().__init__(message, context={"required": required, "available": available})


class InvalidStrategyConfigError(BusinessError):
    """策略配置错误"""
    pass
