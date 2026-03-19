#!/usr/bin/env python3
"""测试 VCP 形态检测 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestVCPAPI:
    """VCP 形态检测 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== VCP 形态检测测试 ==========
    def test_detect_vcp_pattern_success(self, client):
        """测试 VCP 形态检测 - 成功"""
        with patch('api_server.routers.vcp.StockMarketService') as mock_service, \
             patch('api_server.routers.vcp.BaseIndicators') as mock_indicators, \
             patch('api_server.routers.vcp.VCPDetector') as mock_detector:

            # 模拟K线数据
            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
                {"date": "2024-03-16", "open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200000},
                {"date": "2024-03-17", "open": 106, "high": 110, "low": 104, "close": 108, "volume": 1100000},
            ] * 40  # 120天数据

            # 模拟成交量指标计算
            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_volume_indicators.return_value = MagicMock()

            # 模拟 VCP 检测
            mock_detector_obj = MagicMock()
            mock_detector.return_value = mock_detector_obj
            mock_detector_obj.detect_vcp.return_value = {
                "is_vcp": True,
                "stage": "final_contraction",
                "message": "阶段3完成，即将突破",
                "contraction_ratio": 0.3,
                "drop_count": 3,
                "breakout_detected": False,
                "current_price": 108
            }

            response = client.post(
                "/api/v1/indicators/vcp",
                params={
                    "stock_code": "600519",
                    "days": 120,
                    "min_drops": 2,
                    "max_drops": 4
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["is_vcp"] is True
            assert data["data"]["stage"] == "final_contraction"
            assert data["data"]["drop_count"] == 3

    def test_detect_vcp_pattern_no_vcp(self, client):
        """测试 VCP 形态检测 - 无 VCP 形态"""
        with patch('api_server.routers.vcp.StockMarketService') as mock_service, \
             patch('api_server.routers.vcp.BaseIndicators') as mock_indicators, \
             patch('api_server.routers.vcp.VCPDetector') as mock_detector:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100},
            ] * 40

            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_volume_indicators.return_value = MagicMock()

            mock_detector_obj = MagicMock()
            mock_detector.return_value = mock_detector_obj
            mock_detector_obj.detect_vcp.return_value = {
                "is_vcp": False,
                "stage": "unknown",
                "message": "未检测到 VCP 形态",
                "contraction_ratio": 0,
                "drop_count": 0
            }

            response = client.post(
                "/api/v1/indicators/vcp",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["is_vcp"] is False
            assert data["data"]["stage"] == "unknown"

    def test_detect_vcp_pattern_breakout_detected(self, client):
        """测试 VCP 形态检测 - 突破确认"""
        with patch('api_server.routers.vcp.StockMarketService') as mock_service, \
             patch('api_server.routers.vcp.BaseIndicators') as mock_indicators, \
             patch('api_server.routers.vcp.VCPDetector') as mock_detector:

            mock_service.get_kline.return_value = [
                {"date": "2024-03-15", "close": 100, "volume": 1000000},
            ] * 40

            mock_indicator_obj = MagicMock()
            mock_indicators.return_value = mock_indicator_obj
            mock_indicator_obj.calculate_volume_indicators.return_value = MagicMock()

            mock_detector_obj = MagicMock()
            mock_detector.return_value = mock_detector_obj
            mock_detector_obj.detect_vcp.return_value = {
                "is_vcp": True,
                "stage": "breakout_confirmed",
                "message": "VCP 突破确认！",
                "contraction_ratio": 0.25,
                "drop_count": 3,
                "breakout_detected": True,
                "breakout_price": 110,
                "breakout_volume": True,
                "current_price": 112
            }

            response = client.post(
                "/api/v1/indicators/vcp",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["is_vcp"] is True
            assert data["data"]["breakout_detected"] is True
            assert data["data"]["breakout_volume"] is True

    def test_detect_vcp_pattern_insufficient_data(self, client):
        """测试 VCP 形态检测 - 数据不足"""
        with patch('api_server.routers.vcp.StockMarketService') as mock_service:
            mock_service.get_kline.return_value = [{"close": 100}] * 20  # 不足60天

            response = client.post(
                "/api/v1/indicators/vcp",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 异常测试 ==========
    def test_detect_vcp_pattern_exception(self, client):
        """测试 VCP 形态检测 - 异常"""
        with patch('api_server.routers.vcp.StockMarketService') as mock_service:
            mock_service.get_kline.side_effect = Exception("Data fetch error")

            response = client.post(
                "/api/v1/indicators/vcp",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
