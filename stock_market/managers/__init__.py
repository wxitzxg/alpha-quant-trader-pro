"""
管理器模块（重构版 - 使用 Service 层）

向后兼容：导出新的 Service 类
"""

# 导出重构后的 Service
from stock_market.services import (
    StockService,
    KLineService
)

# 保持旧的导入路径兼容性
StockDataManager = StockService
KLineDataManager = KLineService

__all__ = [
    'StockService',
    'KLineService',
    'StockDataManager',  # 旧名称，保持兼容
    'KLineDataManager'   # 旧名称，保持兼容
]
