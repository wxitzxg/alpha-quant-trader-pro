#!/usr/bin/env python3
"""测试 ZigZag 之字转向指标 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestZigZagAPI:
    """ZigZag 指标 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== ZigZag 计算测试 ==========
    def test_calculate_zigzag_success(self, client):
        """测试计算 ZigZag - 成功"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service, \
             patch('api_server.routers.zigzag.ZigZag') as mock_zigzag:

            # 模拟K线数据
            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
                {"date": "2024-03-16", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200000},
                {"date": "2024-03-17", "open": 106, "high": 110, "low": 104, "close": 108, "volume": 1100000},
            ] * 10  # 30天数据

            # 模拟 ZigZag 计算
            mock_zigzag_obj = MagicMock()
            mock_zigzag.return_value = mock_zigzag_obj
            mock_zigzag_obj.get_zigzag_signal.return_value = {
                "trend": "up",
                "trend_strength": 0.8,
                "is_uptrend": True,
                "is_downtrend": False,
                "last_change_date": "2024-03-10",
                "zigzag_points_count": 5,
                "current_price": 108
            }
            mock_zigzag_obj.get_recent_pivots.return_value = [
                {"date": "2024-03-01", "price": 95, "type": "low"},
                {"date": "2024-03-10", "price": 110, "type": "high"}
            ]

            response = client.post(
                "/api/v1/indicators/zigzag",
                params={"stock_code": "600519", "days": 120, "threshold": 0.05}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["trend"] == "up"
            assert data["data"]["trend_strength"] == 0.8
            assert data["data"]["is_uptrend"] is True
            assert len(data["data"]["recent_pivots"]) > 0

    def test_calculate_zigzag_downtrend(self, client):
        """测试计算 ZigZag - 下降趋势"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service, \
             patch('api_server.routers.zigzag.ZigZag') as mock_zigzag:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_zigzag_obj = MagicMock()
            mock_zigzag.return_value = mock_zigzag_obj
            mock_zigzag_obj.get_zigzag_signal.return_value = {
                "trend": "down",
                "trend_strength": 0.7,
                "is_uptrend": False,
                "is_downtrend": True,
                "zigzag_points_count": 4,
                "current_price": 95
            }
            mock_zigzag_obj.get_recent_pivots.return_value = [
                {"date": "2024-03-05", "price": 110, "type": "high"},
                {"date": "2024-03-15", "price": 95, "type": "low"}
            ]

            response = client.post(
                "/api/v1/indicators/zigzag",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["trend"] == "down"
            assert data["data"]["is_downtrend"] is True

    def test_calculate_zigzag_neutral(self, client):
        """测试计算 ZigZag - 横盘整理"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service, \
             patch('api_server.routers.zigzag.ZigZag') as mock_zigzag:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_zigzag_obj = MagicMock()
            mock_zigzag.return_value = mock_zigzag_obj
            mock_zigzag_obj.get_zigzag_signal.return_value = {
                "trend": "neutral",
                "trend_strength": 0.3,
                "is_uptrend": False,
                "is_downtrend": False,
                "zigzag_points_count": 3,
                "current_price": 100
            }

            response = client.post(
                "/api/v1/indicators/zigzag",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["trend"] == "neutral"
            assert data["data"]["trend_strength"] == 0.3

    def test_calculate_zigzag_insufficient_data(self, client):
        """测试计算 ZigZag - 数据不足"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service:
            mock_service.get_kline.return_value = [{"close": 100}] * 10  # 不足30天

            response = client.post(
                "/api/v1/indicators/zigzag",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 边界测试 ==========
    def test_calculate_zigzag_with_different_threshold(self, client):
        """测试计算 ZigZag - 不同阈值"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service, \
             patch('api_server.routers.zigzag.ZigZag') as mock_zigzag:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_zigzag_obj = MagicMock()
            mock_zigzag.return_value = mock_zigzag_obj
            mock_zigzag_obj.get_zigzag_signal.return_value = {
                "trend": "up",
                "current_price": 105
            }
            mock_zigzag_obj.get_recent_pivots.return_value = []

            # 测试更大的阈值
            response = client.post(
                "/api/v1/indicators/zigzag",
                json={"stock_code": "600519", "days": 120, "threshold": 0.1}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["threshold"] == 0.1

    # ========== 异常测试 ==========
    def test_calculate_zigzag_exception(self, client):
        """测试计算 ZigZag - 异常"""
        with patch('api_server.routers.zigzag.StockMarketService') as mock_service:
            mock_service.get_kline.side_effect = Exception("Data fetch error")

            response = client.post(
                "/api/v1/indicators/zigzag",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
