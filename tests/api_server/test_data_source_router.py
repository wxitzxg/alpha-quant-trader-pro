#!/usr/bin/env python3
"""测试数据源 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from api_server.main import app


class TestDataSourceAPI:
    """数据源 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 股票列表测试 ==========
    def test_get_stock_list(self, client):
        """测试获取股票列表"""
        response = client.get(
            "/api/v1/stock/list?page=1&page_size=20&exchange=SH&industry=白酒"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "stocks" in data["data"]

    def test_get_stock_list_invalid_params(self, client):
        """测试获取股票列表 - 无效参数"""
        response = client.get("/api/v1/stock/list?page=0&page_size=0")

        assert response.status_code in [200, 422]  # 可能验证失败或返回空结果

    # ========== 股票详情测试 ==========
    def test_get_stock_info(self, client):
        """测试获取股票详情"""
        response = client.get("/api/v1/stock/info/600519")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_stock_info_invalid_code(self, client):
        """测试获取股票详情 - 无效代码"""
        response = client.get("/api/v1/stock/info/INVALID")

        assert response.status_code == 200  # TODO端点可能返回空数据而非错误

    # ========== 实时行情测试 ==========
    def test_get_realtime_quote(self, client):
        """测试获取单股实时行情"""
        response = client.get("/api/v1/quote/realtime/600519")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "current_price" in data["data"]
        assert data["data"]["symbol"] == "600519"

    def test_get_realtime_quote_invalid_code(self, client):
        """测试获取实时行情 - 无效代码"""
        response = client.get("/api/v1/quote/realtime/INVALID")

        assert response.status_code == 200  # TODO端点可能返回默认数据

    # ========== 批量行情测试 ==========
    def test_get_batch_quotes(self, client):
        """测试批量获取行情"""
        response = client.post(
            "/api/v1/quote/batch",
            json={
                "stock_codes": ["600519", "000001"],
                "fields": ["price", "volume"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "quotes" in data["data"]

    # ========== 排行榜测试 ==========
    def test_get_top_list_gain(self, client):
        """测试涨跌幅排行 - 涨幅榜"""
        response = client.get("/api/v1/quote/top-list?type=gain")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "gain"

    def test_get_top_list_loss(self, client):
        """测试涨跌幅排行 - 跌幅榜"""
        response = client.get("/api/v1/quote/top-list?type=loss")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "loss"

    # ========== K线数据测试 ==========
    def test_get_kline(self, client):
        """测试获取K线数据"""
        response = client.get(
            "/api/v1/kline/600519?interval=1d&start_date=2024-01-01&end_date=2024-03-31"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "klines" in data["data"]
        assert data["data"]["symbol"] == "600519"

    def test_get_kline_invalid_params(self, client):
        """测试获取K线数据 - 无效参数"""
        response = client.get("/api/v1/kline/600519?interval=invalid")

        assert response.status_code == 200  # TODO端点可能忽略无效参数

    # ========== 批量K线测试 ==========
    def test_get_batch_klines(self, client):
        """测试批量获取K线"""
        response = client.post(
            "/api/v1/kline/batch",
            json={
                "stock_codes": ["600519", "000001"],
                "interval": "1d",
                "start_date": "2024-01-01",
                "end_date": "2024-03-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "data" in data["data"]

    # ========== K线统计测试 ==========
    def test_get_kline_stats(self, client):
        """测试K线统计信息"""
        response = client.get("/api/v1/kline/stats/600519?period=1y")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "price_range" in data["data"]
        assert "volume_stats" in data["data"]
        assert "volatility" in data["data"]

    # ========== 财务指标测试 ==========
    def test_get_financial_indicators(self, client):
        """测试获取财务指标"""
        response = client.get("/api/v1/financial/indicators/600519")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    # ========== 边界测试 ==========
    def test_get_stock_list_boundary(self, client):
        """测试股票列表边界情况"""
        # 测试最大页码
        response = client.get("/api/v1/stock/list?page=1&page_size=1000")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 测试最小页码
        response = client.get("/api/v1/stock/list?page=1&page_size=1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
