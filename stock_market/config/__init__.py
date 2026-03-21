"""
股票市场模块配置模块
统一从 common.config 获取配置
Configuration module for stock market module
Unified configuration loading from common.config
"""

from common.config import get_config


def get_stock_market_config():
    """
    获取股票市场配置
    Get stock market configuration

    Returns:
        StockMarketConfig: 股票市场配置对象
    """
    return get_config().stock_market


def get_sync_config():
    """
    获取同步配置
    Get sync configuration

    Returns:
        SyncConfig: 同步配置对象
    """
    return get_config().stock_market.sync


def get_trading_hours():
    """
    获取交易时间配置
    Get trading hours configuration

    Returns:
        TradingHoursConfig: 交易时间配置对象
    """
    return get_config().stock_market.trading_hours


def get_data_retention_config():
    """
    获取数据保留配置
    Get data retention configuration

    Returns:
        DataRetentionConfig: 数据保留配置对象
    """
    return get_config().stock_market.data_retention


__all__ = [
    'get_stock_market_config',
    'get_sync_config',
    'get_trading_hours',
    'get_data_retention_config',
]
