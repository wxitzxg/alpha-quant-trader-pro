"""
数据库同步功能测试
"""

import pytest
from common.database import Base


def test_base_consistency():
    """测试所有模块使用统一的 Base"""
    from common.database import Base as common_base
    from stock_market.database import Base as stock_base
    from portfolio_manager.database import Base as portfolio_base

    assert common_base is stock_base is portfolio_base, "所有模块应该使用同一个 Base 类"


def test_tables_registered():
    """测试所有表都已注册到 metadata"""
    table_names = set(Base.metadata.tables.keys())

    expected_tables = {
        'stocks',        # 股票基础信息
        'klines',        # K线数据
        'sync_records',  # 同步记录
        'positions',     # 持仓
        'transactions',  # 交易记录
        'cash_balance'   # 现金余额
    }

    assert expected_tables.issubset(table_names), f"缺失表: {expected_tables - table_names}"


def test_all_models_imported():
    """测试所有模型都能正确导入"""
    # 这个测试确保所有模型文件都能被导入（触发注册）
    from stock_market.models import Stock, KLine, SyncRecord
    from portfolio_manager.database import Position, Transaction, CashBalance

    assert Stock is not None
    assert KLine is not None
    assert SyncRecord is not None
    assert Position is not None
    assert Transaction is not None
    assert CashBalance is not None
