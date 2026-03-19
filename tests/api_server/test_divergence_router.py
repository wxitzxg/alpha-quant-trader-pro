#!/usr/bin/env python3
"""测试背离检测 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestDivergenceAPI:
    """背离检测 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 背离检测测试 ==========
    def test_detect_divergence_success(self, client):
        """测试背离检测 - 成功"""
        with patch('api_server.routers.divergence.StockMarketService') as mock_service, \
             patch('api_server.routers.divergence.BaseIndicators') as mock_indicators, \
             patch('api_server.routers.divergence.DivergenceCheck') as mock_checker:

            # 模拟K线数据
            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
                {"date": "2024-03-16", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200000},
                {"date": "2024-03-17", "open": 106, "high": 110, "low": 104, "close": 108, "volume": 1100000},
            ] * 20  # 60天数据

            # 模拟指标计算
            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_trend_indicators.return_value = MagicMock()

            # 模拟背离检测
            mock_checker_obj = MagicMock()
            mock_checker.return_value = mock_checker_obj
            mock_checker_obj.detect_macd_divergence.return_value = {
                "bullish_divergence": {"detected": False},
                "bearish_divergence": {"detected": True, "points": [{"date": "2024-03-10"}]}
            }

            response = client.post(
                "/api/v1/indicators/divergence",
                params={"stock_code": "600519", "days": 60, "indicator": "macd"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert "divergences" in data["data"]
            assert data["data"]["indicator"] == "macd"

    def test_detect_divergence_no_signal(self, client):
        """测试背离检测 - 无信号"""
        with patch('api_server.routers.divergence.StockMarketService') as mock_service, \
             patch('api_server.routers.divergence.BaseIndicators') as mock_indicators, \
             patch('api_server.routers.divergence.DivergenceCheck') as mock_checker:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_trend_indicators.return_value = MagicMock()

            mock_checker_obj = MagicMock()
            mock_checker.return_value = mock_checker_obj
            mock_checker_obj.detect_macd_divergence.return_value = {
                "bullish_divergence": {"detected": False},
                "bearish_divergence": {"detected": False}
            }

            response = client.post(
                "/api/v1/indicators/divergence",
                json={"stock_code": "600519", "days": 60}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "divergences" in data["data"]

    def test_detect_divergence_insufficient_data(self, client):
        """测试背离检测 - 数据不足"""
        with patch('api_server.routers.divergence.StockMarketService') as mock_service:
            mock_service.get_kline.return_value = [{"close": 100}] * 10  # 不足30天

            response = client.post(
                "/api/v1/indicators/divergence",
                json={"stock_code": "600519", "days": 60}
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 异常测试 ==========
    def test_detect_divergence_exception(self, client):
        """测试背离检测 - 异常"""
        with patch('api_server.routers.divergence.StockMarketService') as mock_service:
            mock_service.get_kline.side_effect = Exception("Data fetch error")

            response = client.post(
                "/api/v1/indicators/divergence",
                json={"stock_code": "600519", "days": 60}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
