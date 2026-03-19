"""
数据库连接管理模块

已迁移至 common.database
为保持向后兼容，导出 common.database 的 DatabaseManager
"""

from common.database import DatabaseManager, Base

__all__ = ['DatabaseManager', 'Base']
