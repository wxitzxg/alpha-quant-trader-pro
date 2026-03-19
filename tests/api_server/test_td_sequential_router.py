#!/usr/bin/env python3
"""测试 TD 序列（神奇九转）API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestTDSequentialAPI:
    """TD 序列 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== TD 序列计算测试 ==========
    def test_calculate_td_sequential_success(self, client):
        """测试计算 TD 序列 - 成功"""
        with patch('api_server.routers.td_sequential.StockMarketService') as mock_service, \
             patch('api_server.routers.td_sequential.TDSequential') as mock_td:

            # 模拟K线数据
            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
                {"date": "2024-03-16", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200000},
                {"date": "2024-03-17", "open": 106, "high": 110, "low": 104, "close": 108, "volume": 1100000},
            ] * 10  # 30天数据

            # 模拟TD序列计算
            mock_td_obj = MagicMock()
            mock_td.return_value = mock_td_obj
            mock_td_obj.get_td_sequential.return_value = {
                "td_buy_count": 5,
                "td_sell_count": 0,
                "td_buy_signal": False,
                "td_sell_signal": False,
                "status": "counting_low_5"
            }

            response = client.post(
                "/api/v1/indicators/td-sequential",
                params={
                    "stock_code": "600519",
                    "days": 30,
                    "period": 9,
                    "compare_period": 4
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["td_buy_count"] == 5
            assert data["data"]["status"] == "counting_low_5"

    def test_calculate_td_sequential_low_nine_complete(self, client):
        """测试计算 TD 序列 - 低九完成（买入信号）"""
        with patch('api_server.routers.td_sequential.StockMarketService') as mock_service, \
             patch('api_server.routers.td_sequential.TDSequential') as mock_td:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_td_obj = MagicMock()
            mock_td.return_value = mock_td_obj
            mock_td_obj.get_td_sequential.return_value = {
                "td_buy_count": 9,
                "td_sell_count": 0,
                "td_buy_signal": True,
                "td_sell_signal": False,
                "status": "low_nine_complete"
            }

            response = client.post(
                "/api/v1/indicators/td-sequential",
                json={"stock_code": "600519", "days": 30}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["td_buy_signal"] is True
            assert data["data"]["status"] == "low_nine_complete"

    def test_calculate_td_sequential_high_nine_complete(self, client):
        """测试计算 TD 序列 - 高九完成（卖出信号）"""
        with patch('api_server.routers.td_sequential.StockMarketService') as mock_service, \
             patch('api_server.routers.td_sequential.TDSequential') as mock_td:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 20

            mock_td_obj = MagicMock()
            mock_td.return_value = mock_td_obj
            mock_td_obj.get_td_sequential.return_value = {
                "td_buy_count": 0,
                "td_sell_count": 9,
                "td_buy_signal": False,
                "td_sell_signal": True,
                "status": "high_nine_complete"
            }

            response = client.post(
                "/api/v1/indicators/td-sequential",
                json={"stock_code": "600519", "days": 30}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["td_sell_signal"] is True
            assert data["data"]["status"] == "high_nine_complete"

    def test_calculate_td_sequential_insufficient_data(self, client):
        """测试计算 TD 序列 - 数据不足"""
        with patch('api_server.routers.td_sequential.StockMarketService') as mock_service:
            mock_service.get_kline.return_value = [{"close": 100}] * 5  # 不足13天

            response = client.post(
                "/api/v1/indicators/td-sequential",
                json={"stock_code": "600519", "days": 30, "period": 9, "compare_period": 4}
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 异常测试 ==========
    def test_calculate_td_sequential_exception(self, client):
        """测试计算 TD 序列 - 异常"""
        with patch('api_server.routers.td_sequential.StockMarketService') as mock_service:
            mock_service.get_kline.side_effect = Exception("Data fetch error")

            response = client.post(
                "/api/v1/indicators/td-sequential",
                json={"stock_code": "600519", "days": 30}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
