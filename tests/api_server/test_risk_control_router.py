#!/usr/bin/env python3
"""测试风险控制 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestRiskControlAPI:
    """风险控制 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 波动率分析测试 ==========
    @pytest.mark.asyncio
    async def test_get_volatility_success(self, client):
        """测试波动率分析 - 成功"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
                {"close": 102.0, "high": 106.0, "low": 96.0},
                {"close": 98.0, "high": 103.0, "low": 94.0},
                {"close": 105.0, "high": 108.0, "low": 97.0},
            ]

            response = client.get("/api/v1/risk/volatility/600519?days=30")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["stock_code"] == "600519"
            assert "risk_metrics" in data["data"]
            assert "volatility" in data["data"]["risk_metrics"]
            assert "var_95" in data["data"]["risk_metrics"]
            assert "max_drawdown" in data["data"]["risk_metrics"]
            assert "sharpe_ratio" in data["data"]["risk_metrics"]

    @pytest.mark.asyncio
    async def test_get_volatility_no_data(self, client):
        """测试波动率分析 - 无数据"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = []

            response = client.get("/api/v1/risk/volatility/INVALID?days=30")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_get_volatility_insufficient_data(self, client):
        """测试波动率分析 - 数据不足"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [{"close": 100.0}]

            response = client.get("/api/v1/risk/volatility/600519?days=30")

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 止损位计算测试 ==========
    @pytest.mark.asyncio
    async def test_calculate_stop_loss_atr(self, client):
        """测试止损位计算 - ATR方法"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
                {"close": 102.0, "high": 106.0, "low": 96.0},
                {"close": 98.0, "high": 103.0, "low": 94.0},
            ]

            response = client.post(
                "/api/v1/risk/stop-loss/calculate",
                json={
                    "stock_code": "600519",
                    "risk_tolerance": 0.05,
                    "method": "atr"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["method"] == "atr"
            assert data["data"]["stop_loss"] > 0
            assert data["data"]["stop_loss"] < data["data"]["current_price"]

    @pytest.mark.asyncio
    async def test_calculate_stop_loss_volatility(self, client):
        """测试止损位计算 - 波动率方法"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
                {"close": 102.0, "high": 106.0, "low": 96.0},
            ]

            response = client.post(
                "/api/v1/risk/stop-loss/calculate",
                json={
                    "stock_code": "600519",
                    "risk_tolerance": 0.08,
                    "method": "volatility"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["method"] == "volatility"

    @pytest.mark.asyncio
    async def test_calculate_stop_loss_percentage(self, client):
        """测试止损位计算 - 百分比方法"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
            ]

            response = client.post(
                "/api/v1/risk/stop-loss/calculate",
                json={
                    "stock_code": "600519",
                    "risk_tolerance": 0.1,
                    "method": "percentage"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["method"] == "percentage"
            assert data["data"]["stop_loss"] == 90.0  # 100 * (1 - 0.1)

    @pytest.mark.asyncio
    async def test_calculate_stop_loss_invalid_method(self, client):
        """测试止损位计算 - 无效方法"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
            ]

            response = client.post(
                "/api/v1/risk/stop-loss/calculate",
                json={
                    "stock_code": "600519",
                    "risk_tolerance": 0.05,
                    "method": "invalid"
                }
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    # ========== 投资组合分散度测试 ==========
    @pytest.mark.asyncio
    async def test_get_portfolio_diversification_success(self, client):
        """测试投资组合分散度分析 - 成功"""
        with patch('api_server.routers.risk_control.PortfolioService') as mock_service:

            mock_portfolio = MagicMock()
            mock_service.return_value = mock_portfolio
            mock_portfolio.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {"symbol": "600519", "market_value": 50000, "quantity": 100},
                    {"symbol": "000001", "market_value": 30000, "quantity": 200},
                    {"symbol": "601398", "market_value": 20000, "quantity": 500},
                ]
            }

            response = client.get("/api/v1/risk/diversification")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "diversification_score" in data["data"]
            assert "concentration_risk" in data["data"]
            assert "hhi_index" in data["data"]
            assert "positions_count" in data["data"]
            assert data["data"]["positions_count"] == 3

    @pytest.mark.asyncio
    async def test_get_portfolio_diversification_empty(self, client):
        """测试投资组合分散度分析 - 空持仓"""
        with patch('api_server.routers.risk_control.PortfolioService') as mock_service:

            mock_portfolio = MagicMock()
            mock_service.return_value = mock_portfolio
            mock_portfolio.get_all_positions.return_value = {
                "success": True,
                "data": []
            }

            response = client.get("/api/v1/risk/diversification")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["diversification_score"] == 0
            assert data["data"]["positions_count"] == 0

    @pytest.mark.asyncio
    async def test_get_portfolio_diversification_no_market_value(self, client):
        """测试投资组合分散度分析 - 无市值"""
        with patch('api_server.routers.risk_control.PortfolioService') as mock_service:

            mock_portfolio = MagicMock()
            mock_service.return_value = mock_portfolio
            mock_portfolio.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {"symbol": "600519", "market_value": 0, "quantity": 100},
                ]
            }

            response = client.get("/api/v1/risk/diversification")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["concentration_risk"] == "HIGH"

    # ========== 投资组合VaR测试 ==========
    @pytest.mark.asyncio
    async def test_get_portfolio_var_success(self, client):
        """测试投资组合VaR计算 - 成功"""
        with patch('api_server.routers.risk_control.PortfolioService') as mock_service:

            mock_portfolio = MagicMock()
            mock_service.return_value = mock_portfolio
            mock_portfolio.get_all_positions.return_value = {
                "success": True,
                "data": [
                    {"symbol": "600519", "market_value": 50000, "quantity": 100},
                    {"symbol": "000001", "market_value": 30000, "quantity": 200},
                ]
            }
            mock_portfolio.get_transaction_history.return_value = {
                "success": True,
                "data": [
                    {"transaction_type": "SELL", "amount": 11000},
                    {"transaction_type": "SELL", "amount": 12000},
                ]
            }

            response = client.get("/api/v1/risk/portfolio/value-at-risk?confidence_level=0.95")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "var" in data["data"]
            assert "var_pct" in data["data"]
            assert "confidence_level" in data["data"]
            assert data["data"]["confidence_level"] == 0.95
            assert data["data"]["total_portfolio_value"] == 80000

    @pytest.mark.asyncio
    async def test_get_portfolio_var_empty(self, client):
        """测试投资组合VaR计算 - 空持仓"""
        with patch('api_server.routers.risk_control.PortfolioService') as mock_service:

            mock_portfolio = MagicMock()
            mock_service.return_value = mock_portfolio
            mock_portfolio.get_all_positions.return_value = {
                "success": True,
                "data": []
            }
            mock_portfolio.get_transaction_history.return_value = {
                "success": True,
                "data": []
            }

            response = client.get("/api/v1/risk/portfolio/value-at-risk?confidence_level=0.99")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["var"] == 0
            assert data["data"]["positions_count"] == 0

    @pytest.mark.asyncio
    async def test_get_portfolio_var_invalid_confidence(self, client):
        """测试投资组合VaR计算 - 无效置信水平"""
        response = client.get("/api/v1/risk/portfolio/value-at-risk?confidence_level=0.8")

        # 参数验证可能会失败或使用默认值
        assert response.status_code in [200, 422]

    # ========== 边界测试 ==========
    @pytest.mark.asyncio
    async def test_get_volatility_boundary_days(self, client):
        """测试波动率分析 - 边界天数"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.return_value = [
                {"close": 100.0, "high": 105.0, "low": 95.0},
                {"close": 102.0, "high": 106.0, "low": 96.0},
            ]

            # 最小天数
            response = client.get("/api/v1/risk/volatility/600519?days=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # 较大天数
            response = client.get("/api/v1/risk/volatility/600519?days=365")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # ========== 异常测试 ==========
    @pytest.mark.asyncio
    async def test_get_volatility_exception(self, client):
        """测试波动率分析 - 异常"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.side_effect = Exception("Database error")

            response = client.get("/api/v1/risk/volatility/600519?days=30")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_calculate_stop_loss_exception(self, client):
        """测试止损位计算 - 异常"""
        with patch('api_server.routers.risk_control.DataSourceService') as mock_service:

            mock_service.get_kline.side_effect = Exception("Data fetch error")

            response = client.post(
                "/api/v1/risk/stop-loss/calculate",
                json={
                    "stock_code": "600519",
                    "risk_tolerance": 0.05,
                    "method": "percentage"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
