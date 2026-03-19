"""测试 Tushare 适配器"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from data_sources.adapters.tushare_adapter import TushareAdapter


@pytest.fixture
def mock_tushare_adapter():
    """创建模拟的 TushareAdapter"""
    with patch('data_sources.adapters.tushare_adapter.ts') as mock_ts:
        mock_pro = Mock()
        mock_ts.pro_api.return_value = mock_pro

        adapter = TushareAdapter(token="test_token", timeout=1)
        adapter.pro = mock_pro

        return adapter, mock_pro


def test_tushare_adapter_name():
    """测试适配器名称"""
    adapter = TushareAdapter(token="test", timeout=1)
    assert adapter.name == "tushare"


def test_tushare_adapter_priority():
    """测试适配器优先级"""
    adapter = TushareAdapter(token="test", timeout=1)
    assert adapter.priority == 30


@patch('data_sources.adapters.tushare_adapter.ts')
def test_format_symbol_shanghai(mock_ts):
    """测试沪市股票代码格式化"""
    adapter = TushareAdapter(token="test", timeout=1)

    assert adapter._format_symbol("600519") == "600519.SH"
    assert adapter._format_symbol("601318") == "601318.SH"


@patch('data_sources.adapters.tushare_adapter.ts')
def test_format_symbol_shenzhen(mock_ts):
    """测试深市股票代码格式化"""
    adapter = TushareAdapter(token="test", timeout=1)

    assert adapter._format_symbol("000001") == "000001.SZ"
    assert adapter._format_symbol("300750") == "300750.SZ"


@patch('data_sources.adapters.tushare_adapter.ts')
def test_parse_symbol(mock_ts):
    """测试从 Tushare 代码解析股票代码"""
    adapter = TushareAdapter(token="test", timeout=1)

    assert adapter._parse_symbol("600519.SH") == "600519"
    assert adapter._parse_symbol("000001.SZ") == "000001"
