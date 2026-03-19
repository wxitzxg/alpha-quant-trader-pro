"""测试新浪财经适配器"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from data_sources.adapters.sina_adapter import SinaAdapter


def test_sina_adapter_name():
    """测试适配器名称"""
    adapter = SinaAdapter(timeout=1)
    assert adapter.name == "sina"


def test_sina_adapter_priority():
    """测试适配器优先级"""
    adapter = SinaAdapter(timeout=1)
    assert adapter.priority == 10  # 高优先级


def test_format_symbol_shanghai():
    """测试沪市股票代码格式化"""
    adapter = SinaAdapter(timeout=1)

    assert adapter._format_symbol("600519") == "sh600519"
    assert adapter._format_symbol("601318") == "sh601318"


def test_format_symbol_shenzhen():
    """测试深市股票代码格式化"""
    adapter = SinaAdapter(timeout=1)

    assert adapter._format_symbol("000001") == "sz000001"
    assert adapter._format_symbol("300750") == "sz300750"


def test_parse_symbol():
    """测试从新浪代码解析股票代码"""
    adapter = SinaAdapter(timeout=1)

    assert adapter._parse_symbol("sh600519") == "600519"
    assert adapter._parse_symbol("sz000001") == "000001"
