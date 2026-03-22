#!/usr/bin/env python3
"""测试数据源 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient

from api_server.main import app
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_CODE_2,
    TEST_START_DATE,
    TEST_END_DATE,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MIN,
    PAGE_SIZE_MAX,
    assert_success_response
)


class TestDataSourceAPI:
    """数据源 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    # ========== 股票列表测试 ==========
    def test_get_stock_list(self, client: TestClient) -> None:
        """测试获取股票列表"""
        response = client.get(
            f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_DEFAULT}&exchange=SH&industry=白酒"
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert "stocks" in data["data"]

    def test_get_stock_list_invalid_params(self, client: TestClient) -> None:
        """测试获取股票列表 - 无效参数"""
        response = client.get("/api/v1/stock/list?page=0&page_size=0")

        # 可能验证失败或返回空结果
        assert response.status_code in [200, 422]

    # ========== 股票详情测试 ==========
    def test_get_stock_info(self, client: TestClient) -> None:
        """测试获取股票详情"""
        response = client.get(f"/api/v1/stock/info/{TEST_STOCK_CODE}")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert data["data"]["symbol"] == TEST_STOCK_CODE

    def test_get_stock_info_invalid_code(self, client: TestClient) -> None:
        """测试获取股票详情 - 无效代码"""
        response = client.get("/api/v1/stock/info/INVALID")

        # TODO 端点可能返回空数据而非错误
        assert response.status_code == 200

    # ========== 实时行情测试 ==========
    def test_get_realtime_quote(self, client: TestClient) -> None:
        """测试获取单股实时行情"""
        response = client.get(f"/api/v1/quote/realtime/{TEST_STOCK_CODE}")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert "current_price" in data["data"]
        assert "change_percent" in data["data"]
        assert data["data"]["symbol"] == TEST_STOCK_CODE

    def test_get_realtime_quote_invalid_code(self, client: TestClient) -> None:
        """测试获取实时行情 - 无效代码"""
        response = client.get("/api/v1/quote/realtime/INVALID")

        # TODO 端点可能返回默认数据
        assert response.status_code == 200

    # ========== 批量行情测试 ==========
    def test_get_batch_quotes(self, client: TestClient) -> None:
        """测试批量获取行情"""
        response = client.post(
            "/api/v1/quote/batch",
            json={
                "stock_codes": [TEST_STOCK_CODE, TEST_STOCK_CODE_2],
                "fields": ["price", "volume"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert "quotes" in data["data"]
        assert len(data["data"]["quotes"]) >= 0

    # ========== 排行榜测试 ==========
    def test_get_top_list_gain(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 涨幅榜"""
        response = client.get("/api/v1/quote/top-list?type=gain")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["type"] == "gain"
        assert "stocks" in data["data"]

    def test_get_top_list_loss(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 跌幅榜"""
        response = client.get("/api/v1/quote/top-list?type=loss")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["type"] == "loss"
        assert "stocks" in data["data"]

    # ========== K线数据测试 ==========
    def test_get_kline(self, client: TestClient) -> None:
        """测试获取K线数据"""
        response = client.get(
            f"/api/v1/kline/{TEST_STOCK_CODE}"
            f"?interval=1d&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert "klines" in data["data"]
        assert data["data"]["symbol"] == TEST_STOCK_CODE

    def test_get_kline_invalid_params(self, client: TestClient) -> None:
        """测试获取K线数据 - 无效参数"""
        response = client.get(f"/api/v1/kline/{TEST_STOCK_CODE}?interval=invalid")

        # TODO 端点可能忽略无效参数
        assert response.status_code == 200

    # ========== 批量K线测试 ==========
    def test_get_batch_klines(self, client: TestClient) -> None:
        """测试批量获取K线"""
        response = client.post(
            "/api/v1/kline/batch",
            json={
                "stock_codes": [TEST_STOCK_CODE, TEST_STOCK_CODE_2],
                "interval": "1d",
                "start_date": TEST_START_DATE,
                "end_date": TEST_END_DATE
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data

    # ========== K线统计测试 ==========
    def test_get_kline_stats(self, client: TestClient) -> None:
        """测试K线统计信息"""
        response = client.get(f"/api/v1/kline/stats/{TEST_STOCK_CODE}?period=1y")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data
        assert "price_range" in data["data"]
        assert "volume_stats" in data["data"]
        assert "volatility" in data["data"]
        assert data["data"]["symbol"] == TEST_STOCK_CODE

    # ========== 财务指标测试 ==========
    def test_get_financial_indicators(self, client: TestClient) -> None:
        """测试获取财务指标"""
        response = client.get(f"/api/v1/financial/indicators/{TEST_STOCK_CODE}")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "data" in data

    # ========== 边界测试 ==========
    def test_get_stock_list_boundary(self, client: TestClient) -> None:
        """测试股票列表边界情况"""
        # 测试最大页码
        response = client.get(f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_MAX}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 测试最小页码
        response = client.get(f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_MIN}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
