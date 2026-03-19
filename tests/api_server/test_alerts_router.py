#!/usr/bin/env python3
"""测试风险提示 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestAlertsAPI:
    """风险提示 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 触发的告警测试 ==========
    def test_get_triggered_alerts_success(self, client):
        """测试获取触发的告警 - 成功"""
        with patch('api_server.routers.alerts.check_price_alerts') as mock_price, \
             patch('api_server.routers.alerts.check_technical_alerts') as mock_tech, \
             patch('api_server.routers.alerts.check_portfolio_risk_alerts') as mock_portfolio:

            mock_price.return_value = [
                {
                    "type": "PRICE_ABOVE_THRESHOLD",
                    "stock_code": "600519",
                    "message": "Price exceeded threshold",
                    "trigger_time": datetime.now().isoformat()
                }
            ]
            mock_tech.return_value = []
            mock_portfolio.return_value = []

            response = client.get("/api/v1/alerts/triggered")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alerts" in data["data"]
            assert len(data["data"]["alerts"]) > 0
            assert data["data"]["alerts"][0]["type"] == "PRICE_ABOVE_THRESHOLD"

    # ========== 股票告警测试 ==========
    def test_get_stock_alerts_success(self, client):
        """测试获取股票告警 - 成功"""
        with patch('api_server.routers.alerts.check_price_alerts') as mock_price, \
             patch('api_server.routers.alerts.check_technical_alerts') as mock_tech:

            mock_price.return_value = [
                {
                    "type": "PRICE_HIGH_RISK",
                    "stock_code": "600519",
                    "message": "High price risk",
                    "trigger_time": datetime.now().isoformat()
                }
            ]
            mock_tech.return_value = [
                {
                    "type": "TECHNICAL_OVERBOUGHT",
                    "stock_code": "600519",
                    "message": "RSI overbought",
                    "trigger_time": datetime.now().isoformat()
                }
            ]

            response = client.get("/api/v1/alerts/stock/600519")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alerts" in data["data"]
            assert "risk_level" in data["data"]
            assert len(data["data"]["alerts"]) >= 2

    def test_get_stock_alerts_no_alerts(self, client):
        """测试获取股票告警 - 无告警"""
        with patch('api_server.routers.alerts.check_price_alerts') as mock_price, \
             patch('api_server.routers.alerts.check_technical_alerts') as mock_tech:

            mock_price.return_value = []
            mock_tech.return_value = []

            response = client.get("/api/v1/alerts/stock/000001")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["alerts"]) == 0
            assert data["data"]["risk_level"] == "LOW"

    # ========== 监控组合风险测试 ==========
    def test_monitor_portfolio_risks_success(self, client):
        """测试监控组合风险 - 成功"""
        with patch('api_server.routers.alerts.check_portfolio_risk_alerts') as mock_portfolio, \
             patch('api_server.routers.alerts.PortfolioService') as mock_service:

            mock_portfolio.return_value = [
                {
                    "type": "CONCENTRATION_RISK",
                    "message": "Portfolio too concentrated",
                    "severity": "HIGH",
                    "trigger_time": datetime.now().isoformat()
                }
            ]

            mock_portfolio_service = MagicMock()
            mock_service.return_value = mock_portfolio_service
            mock_portfolio_service.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {"symbol": "600519", "market_value": 50000},
                    {"symbol": "000001", "market_value": 30000},
                ]
            }

            response = client.post("/api/v1/alerts/portfolio/monitor")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alerts" in data["data"]
            assert "portfolio_metrics" in data["data"]
            assert data["data"]["portfolio_metrics"]["positions_count"] == 2

    def test_monitor_portfolio_risks_empty(self, client):
        """测试监控组合风险 - 空持仓"""
        with patch('api_server.routers.alerts.check_portfolio_risk_alerts') as mock_portfolio, \
             patch('api_server.routers.alerts.PortfolioService') as mock_service:

            mock_portfolio.return_value = []

            mock_portfolio_service = MagicMock()
            mock_service.return_value = mock_portfolio_service
            mock_portfolio_service.get_all_positions.return_value = {
                "success": True,
                "data": []
            }

            response = client.post("/api/v1/alerts/portfolio/monitor")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["alerts"]) == 0
            assert data["data"]["portfolio_metrics"]["positions_count"] == 0

    # ========== 边界测试 ==========
    def test_get_stock_alerts_invalid_code(self, client):
        """测试获取股票告警 - 无效代码"""
        with patch('api_server.routers.alerts.check_price_alerts') as mock_price, \
             patch('api_server.routers.alerts.check_technical_alerts') as mock_tech:

            mock_price.return_value = []
            mock_tech.return_value = []

            response = client.get("/api/v1/alerts/stock/INVALID_CODE")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # ========== 异常测试 ==========
    def test_get_triggered_alerts_exception(self, client):
        """测试触发的告警 - 异常"""
        with patch('api_server.routers.alerts.check_price_alerts') as mock_price:

            mock_price.side_effect = Exception("Alert check error")

            response = client.get("/api/v1/alerts/triggered")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    def test_monitor_portfolio_exception(self, client):
        """测试监控组合风险 - 异常"""
        with patch('api_server.routers.alerts.check_portfolio_risk_alerts') as mock_portfolio, \
             patch('api_server.routers.alerts.PortfolioService') as mock_service:

            mock_portfolio.side_effect = Exception("Portfolio check error")

            response = client.post("/api/v1/alerts/portfolio/monitor")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
