#!/usr/bin/env python3
"""测试工具和辅助函数"""

import sys
import os
sys.path.insert(0, '.')

from unittest.mock import Mock
from datetime import datetime
from decimal import Decimal


# ==================== 常量定义 ====================
# 分页参数
PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MIN = 1
PAGE_SIZE_MAX = 1000

# 测试用股票代码
TEST_STOCK_CODE = "600519"
TEST_STOCK_CODE_2 = "000001"
TEST_STOCK_NAME = "贵州茅台"
TEST_STOCK_INDUSTRY = "白酒"

# 日期常量
TEST_START_DATE = "2024-01-01"
TEST_END_DATE = "2024-03-31"
TEST_DATE_STR = "2024-03-15"

# 价格常量
TEST_PRICE_OPEN = 1700.0
TEST_PRICE_HIGH = 1720.0
TEST_PRICE_LOW = 1690.0
TEST_PRICE_CLOSE = 1710.0
TEST_PRICE_COST = 1500.0

# 数量常量
TEST_QUANTITY = 100
TEST_QUANTITY_2 = 50

# 资金流向
TEST_MAIN_NET_INFLOW = 5000.0
TEST_RETAIL_NET_INFLOW = 1000.0


# ==================== Mock 工厂函数 ====================
def create_mock_stock(
    ts_code: str = "600519.SH",
    symbol: str = "600519",
    name: str = "贵州茅台",
    industry: str = "白酒",
    market: str = "主板"
) -> Mock:
    """创建股票数据的 mock"""
    mock_stock = Mock()
    mock_stock.ts_code = ts_code
    mock_stock.symbol = symbol
    mock_stock.name = name
    mock_stock.industry = industry
    mock_stock.market = market
    mock_stock.list_date = datetime(2001, 8, 27)
    return mock_stock


def create_mock_position(
    symbol: str = "600519",
    quantity: int = 100,
    cost_price: float = 1500.0,
    current_price: float = 1700.0,
    position_ratio: float = 0.0
) -> Mock:
    """创建持仓数据的 mock"""
    mock_position = Mock()
    mock_position.symbol = symbol
    mock_position.quantity = quantity
    mock_position.cost_price = cost_price
    mock_position.current_price = current_price
    mock_position.market_value = current_price * quantity
    mock_position.cost_value = cost_price * quantity
    mock_position.floating_pl = (current_price - cost_price) * quantity
    mock_position.position_ratio = position_ratio
    mock_position.last_updated = datetime.now()
    return mock_position


def create_mock_kline(
    symbol: str = "600519",
    date: datetime = None,
    open_price: float = 1700.0,
    high_price: float = 1720.0,
    low_price: float = 1690.0,
    close_price: float = 1710.0,
    volume: int = 100000
) -> Mock:
    """创建K线数据的 mock"""
    if date is None:
        date = datetime(2024, 3, 15)

    mock_kline = Mock()
    mock_kline.symbol = symbol
    mock_kline.date = date
    mock_kline.open = open_price
    mock_kline.high = high_price
    mock_kline.low = low_price
    mock_kline.close = close_price
    mock_kline.volume = volume
    mock_kline.amount = close_price * volume
    return mock_kline


def create_mock_summary(
    total_market_value: float = 100000.0,
    stock_market_value: float = 80000.0,
    cash: float = 20000.0,
    total_floating_pl: float = 5000.0,
    total_realized_pl: float = 3000.0,
    positions_count: int = 5
) -> Mock:
    """创建账户汇总的 mock"""
    mock_summary = Mock()
    mock_summary.total_market_value = total_market_value
    mock_summary.stock_market_value = stock_market_value
    mock_summary.cash = cash
    mock_summary.total_floating_pl = total_floating_pl
    mock_summary.total_realized_pl = total_realized_pl
    mock_summary.positions_count = positions_count
    return mock_summary


def create_mock_transaction(
    symbol: str = "600519",
    transaction_type: str = "buy",
    quantity: int = 100,
    price: float = 1700.0,
    fee: float = 200.0,
    transaction_date: datetime = None
) -> Mock:
    """创建交易记录的 mock"""
    if transaction_date is None:
        transaction_date = datetime(2024, 3, 15, 10, 30, 0)

    mock_transaction = Mock()
    mock_transaction.symbol = symbol
    mock_transaction.transaction_type = transaction_type
    mock_transaction.quantity = quantity
    mock_transaction.price = price
    mock_transaction.amount = price * quantity - fee
    mock_transaction.fee = fee
    mock_transaction.transaction_date = transaction_date
    return mock_transaction


def create_mock_sync_record(
    sync_type: str = "stocks",
    status: str = "completed",
    records_count: int = 5000,
    start_time: datetime = None,
    end_time: datetime = None
) -> Mock:
    """创建同步记录的 mock"""
    if start_time is None:
        start_time = datetime(2024, 3, 15, 10, 0, 0)
    if end_time is None:
        end_time = datetime(2024, 3, 15, 10, 5, 0)

    mock_sync_record = Mock()
    mock_sync_record.sync_type = sync_type
    mock_sync_record.status = status
    mock_sync_record.records_count = records_count
    mock_sync_record.start_time = start_time
    mock_sync_record.end_time = end_time
    mock_sync_record.error_message = None
    return mock_sync_record


# ==================== 断言辅助函数 ====================
def assert_success_response(data: dict) -> None:
    """断言成功响应"""
    assert data["success"] is True, f"Expected success but got: {data}"


def assert_error_response(data: dict, expected_message: str = None) -> None:
    """断言错误响应"""
    assert data["success"] is False, f"Expected error but got success: {data}"
    assert "message" in data or "error" in data, f"No error message in response: {data}"

    if expected_message:
        error_msg = data.get("message", data.get("error", ""))
        assert expected_message in str(error_msg).lower(), \
            f"Expected '{expected_message}' in error message, got: {error_msg}"


def assert_pagination_response(data: dict, expected_total: int, expected_page: int = 1) -> None:
    """断言分页响应"""
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert data["total"] == expected_total
    assert data["page"] == expected_page

    if expected_total > 0:
        assert len(data["data"]) > 0
    else:
        assert len(data["data"]) == 0


def assert_stock_data(data: dict, expected_symbol: str = "600519") -> None:
    """断言股票数据结构"""
    assert "symbol" in data
    assert data["symbol"] == expected_symbol
    assert "name" in data


def assert_position_data(data: dict, expected_symbol: str = "600519") -> None:
    """断言持仓数据结构"""
    assert "symbol" in data
    assert data["symbol"] == expected_symbol
    assert "quantity" in data
    assert "current_price" in data
    assert "floating_pl" in data


def assert_kline_data(data: dict, expected_symbol: str = "600519") -> None:
    """断言K线数据结构"""
    assert "symbol" in data
    assert data["symbol"] == expected_symbol
    assert "open" in data
    assert "high" in data
    assert "low" in data
    assert "close" in data
    assert "volume" in data
