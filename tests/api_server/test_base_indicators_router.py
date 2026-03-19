#!/usr/bin/env python3
"""测试基础技术指标 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestBaseIndicatorsAPI:
    """基础技术指标 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 计算基础指标测试 ==========
    def test_calculate_base_indicators_success(self, client):
        """测试计算基础技术指标 - 成功"""
        with patch('api_server.routers.base_indicators.StockMarketService') as mock_service, \
             patch('api_server.routers.base_indicators.BaseIndicators') as mock_indicators:

            # 模拟K线数据
            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
                {"date": "2024-03-16", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200000},
                {"date": "2024-03-17", "open": 106, "high": 110, "low": 104, "close": 108, "volume": 1100000},
            ] * 40  # 120天数据

            # 模拟指标计算
            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_all_indicators.return_value = MagicMock()
            mock_indicator_obj.get_latest_signals.return_value = {
                "trend": "BULLISH",
                "rsi_status": "NEUTRAL"
            }

            response = client.post(
                "/api/v1/indicators/base",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["stock_code"] == "600519"
            assert "indicators" in data["data"]

    def test_calculate_base_indicators_insufficient_data(self, client):
        """测试计算基础技术指标 - 数据不足"""
        with patch('api_server.routers.base_indicators.StockMarketService') as mock_service:
            mock_service.get_kline.return_value = [{"close": 100}] * 10  # 不足20天

            response = client.post(
                "/api/v1/indicators/base",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 500  # 内部抛出异常后被500捕获
            data = response.json()
            assert "detail" in data

    # ========== GET方式获取指标测试 ==========
    def test_get_base_indicators_success(self, client):
        """测试 GET 方式获取基础指标 - 成功"""
        with patch('api_server.routers.base_indicators.StockMarketService') as mock_service, \
             patch('api_server.routers.base_indicators.BaseIndicators') as mock_indicators:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
            ] * 40

            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_all_indicators.return_value = MagicMock()
            mock_indicator_obj.get_latest_signals.return_value = {"trend": "BULLISH"}

            response = client.get("/api/v1/indicators/base/600519?days=60")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["days"] == 60

    # ========== 异常测试 ==========
    def test_calculate_base_indicators_exception(self, client):
        """测试计算基础指标 - 异常"""
        with patch('api_server.routers.base_indicators.StockMarketService') as mock_service:
            mock_service.get_kline.side_effect = Exception("Data error")

            response = client.post(
                "/api/v1/indicators/base",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
