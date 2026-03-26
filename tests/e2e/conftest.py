"""E2E 测试 pytest fixtures"""

import pytest
import httpx

from .config import E2E_CONFIG


@pytest.fixture(scope="session")
def api_base_url():
    """API 基础 URL"""
    return E2E_CONFIG["api_base_url"]


@pytest.fixture(scope="session")
def client(api_base_url):
    """HTTP 客户端"""
    with httpx.Client(base_url=api_base_url, timeout=E2E_CONFIG["timeout"]) as c:
        yield c


@pytest.fixture(scope="session")
def test_stocks():
    """测试股票代码列表"""
    return E2E_CONFIG["test_stocks"]


@pytest.fixture(scope="session")
def default_stock():
    """默认测试股票代码"""
    return E2E_CONFIG["default_stock"]


def assert_success_response(response, expected_status=200):
    """断言成功响应"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("success") is True, f"Expected success=true, got: {data}"
    return data


def assert_response_structure(data, required_fields):
    """断言响应数据结构"""
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
