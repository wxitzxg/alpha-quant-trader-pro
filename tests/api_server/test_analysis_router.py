#!/usr/bin/env python3
"""测试技术分析 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api_server.main import app


class TestAnalysisAPI:
    """技术分析 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 五维分析测试 ==========
    @pytest.mark.asyncio
    async def test_analyze_five_dimension_success(self, client):
        """测试五维共振分析 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_stock.return_value = {
                "stock_code": "600519",
                "interval": "1d",
                "days": 120,
                "five_dimension": {
                    "trend": "BULLISH",
                    "momentum": "STRONG",
                    "volatility": "MEDIUM",
                    "volume": "INCREASING",
                    "pattern": "VCP"
                },
                "score": 85,
                "signals": ["BUY"],
                "risk_level": "LOW"
            }

            response = client.post(
                "/api/v1/analysis/five-dimension",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["score"] == 85

    @pytest.mark.asyncio
    async def test_analyze_five_dimension_error(self, client):
        """测试五维共振分析 - 错误"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_stock.return_value = {
                "error": True,
                "message": "Stock not found"
            }

            response = client.post(
                "/api/v1/analysis/five-dimension",
                json={"stock_code": "INVALID", "days": 120}
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 策略分析测试 ==========
    @pytest.mark.asyncio
    async def test_analyze_with_strategies_success(self, client):
        """测试三大策略分析 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_with_strategies.return_value = {
                "stock_code": "600519",
                "strategies": {
                    "vcp_breakout": {
                        "signal": "BUY",
                        "score": 80,
                        "confidence": 0.85,
                        "details": {"phases": 3, "breakout_price": 1750}
                    },
                    "td_golden_pit": {
                        "signal": "HOLD",
                        "score": 65,
                        "td_count": 7,
                        "details": {}
                    },
                    "top_divergence": {
                        "signal": "SELL",
                        "score": 55,
                        "divergence_type": "BEARISH",
                        "details": {}
                    }
                }
            }

            response = client.get(
                "/api/v1/analysis/strategies/600519?interval=1d&days=120"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "strategies" in data["data"]
            assert data["data"]["strategies"]["vcp_breakout"]["signal"] == "BUY"

    # ========== 技术指标测试 ==========
    @pytest.mark.asyncio
    async def test_get_indicator_success(self, client):
        """测试获取技术指标 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.get_technical_indicators.return_value = {
                "current_price": 1710.0,
                "latest_signals": ["MA_GOLDEN_CROSS"],
                "data_points": [
                    {"date": "2024-03-15", "ma5": 1700, "ma10": 1690, "ma20": 1680}
                ]
            }

            response = client.get(
                "/api/v1/analysis/indicator/600519?indicator_name=ma"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["indicator_name"] == "ma"
            assert data["data"]["current_price"] == 1710.0

    # ========== VCP 策略分析测试 ==========
    @pytest.mark.asyncio
    async def test_analyze_vcp_success(self, client):
        """测试 VCP 策略分析 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_with_strategies.return_value = {
                "strategies": {
                    "vcp_breakout": {
                        "signal": "BUY",
                        "score": 82,
                        "confidence": 0.88,
                        "details": {"phases": 4, "volume_increase": True}
                    }
                }
            }

            response = client.get(
                "/api/v1/analysis/strategy/vcp/600519?days=120"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["strategy_name"] == "VCP"
            assert data["data"]["signal"] == "BUY"

    # ========== TD 黄金坑策略分析测试 ==========
    @pytest.mark.asyncio
    async def test_analyze_td_golden_pit_success(self, client):
        """测试九转黄金坑策略分析 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_with_strategies.return_value = {
                "strategies": {
                    "td_golden_pit": {
                        "signal": "BUY",
                        "score": 78,
                        "td_count": 9,
                        "details": {"setup_count": 9, "intersection_count": 13}
                    }
                }
            }

            response = client.get(
                "/api/v1/analysis/strategy/td/600519?days=120"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["strategy_name"] == "TD Golden Pit"
            assert data["data"]["td_count"] == 9

    # ========== 背离策略分析测试 ==========
    @pytest.mark.asyncio
    async def test_analyze_top_divergence_success(self, client):
        """测试顶部背离策略分析 - 成功"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.analysis.AnalysisService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_analysis = MagicMock()
            mock_service.return_value = mock_analysis
            mock_analysis.analyze_with_strategies.return_value = {
                "strategies": {
                    "top_divergence": {
                        "signal": "SELL",
                        "score": 75,
                        "divergence_type": "BEARISH",
                        "details": {"price_high": 1800, "indicator_high": 1750}
                    }
                }
            }

            response = client.get(
                "/api/v1/analysis/strategy/divergence/600519?days=120"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["strategy_name"] == "Top Divergence"
            assert data["data"]["divergence_type"] == "BEARISH"

    # ========== 异常测试 ==========
    @pytest.mark.asyncio
    async def test_analysis_with_exception(self, client):
        """测试分析接口异常处理"""
        with patch('api_server.routers.analysis.DatabaseManager') as mock_db_manager:
            mock_db_manager.side_effect = Exception("Database error")

            response = client.post(
                "/api/v1/analysis/five-dimension",
                json={"stock_code": "600519", "days": 120}
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

