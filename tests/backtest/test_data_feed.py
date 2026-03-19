"""Test Data Feed"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
import pandas as pd


def test_data_feed_import():
    """测试数据源适配器导入"""
    from backtest.core.data_feed import DataFeed
    assert DataFeed is not None


def test_data_feed_initialization():
    """测试数据源适配器初始化"""
    mock_session = Mock(spec=Session)
    from backtest.core.data_feed import DataFeed
    data_feed = DataFeed(mock_session)
    assert data_feed.session is not None


@patch('backtest.core.data_feed.KLineRepository')
def test_get_stock_data(mock_kline_repo_class):
    """测试获取股票数据"""
    from backtest.core.data_feed import DataFeed

    mock_session = Mock(spec=Session)
    data_feed = DataFeed(mock_session)

    # Create mock kline data
    mock_kline1 = Mock()
    mock_kline1.open_price = 1500.0
    mock_kline1.high_price = 1520.0
    mock_kline1.low_price = 1490.0
    mock_kline1.close_price = 1510.0
    mock_kline1.volume = 1000000
    mock_kline1.timestamp = "2024-01-01"

    mock_kline2 = Mock()
    mock_kline2.open_price = 1515.0
    mock_kline2.high_price = 1530.0
    mock_kline2.low_price = 1510.0
    mock_kline2.close_price = 1525.0
    mock_kline2.volume = 1200000
    mock_kline2.timestamp = "2024-01-02"

    mock_kline_repo_instance = Mock()
    mock_kline_repo_instance.query_klines.return_value = [mock_kline1, mock_kline2]
    mock_kline_repo_class.return_value = mock_kline_repo_instance

    df = data_feed.get_stock_data("600519", "2024-01-01", "2024-01-31")

    assert len(df) == 2
    assert df['open'].iloc[0] == 1500.0
    assert df['close'].iloc[0] == 1510.0
    assert df.index[0] == "2024-01-01"
    assert isinstance(df, pd.DataFrame)


@patch('backtest.core.data_feed.KLineRepository')
def test_get_stock_data_no_data(mock_kline_repo_class):
    """测试获取空数据"""
    from backtest.core.data_feed import DataFeed

    mock_session = Mock(spec=Session)
    data_feed = DataFeed(mock_session)

    mock_kline_repo_instance = Mock()
    mock_kline_repo_instance.query_klines.return_value = []
    mock_kline_repo_class.return_value = mock_kline_repo_instance

    with pytest.raises(ValueError, match="No data found"):
        data_feed.get_stock_data("600519", "2024-01-01", "2024-01-31")


@patch('backtest.core.data_feed.KLineRepository')
def test_get_multi_stock_data(mock_kline_repo_class):
    """测试获取多股票数据"""
    from backtest.core.data_feed import DataFeed

    mock_session = Mock(spec=Session)
    data_feed = DataFeed(mock_session)

    mock_kline = Mock()
    mock_kline.open_price = 1500.0
    mock_kline.high_price = 1520.0
    mock_kline.low_price = 1490.0
    mock_kline.close_price = 1510.0
    mock_kline.volume = 1000000
    mock_kline.timestamp = "2024-01-01"

    mock_kline_repo_instance = Mock()
    mock_kline_repo_instance.query_klines.return_value = [mock_kline]
    mock_kline_repo_class.return_value = mock_kline_repo_instance

    result = data_feed.get_multi_stock_data(
        ["600519", "000001"],
        "2024-01-01",
        "2024-01-31"
    )

    assert len(result) == 2
    assert "600519" in result
    assert "000001" in result
    assert len(result["600519"]) == 1
