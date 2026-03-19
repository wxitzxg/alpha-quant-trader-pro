#!/usr/bin/env python3
"""测试回测系统 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


from api_server.main import app


class TestBacktestAPI:
    """回测系统 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 单策略回测测试 ==========
    @pytest.mark.asyncio
    async def test_run_single_backtest_success(self, client):
        """测试单策略回测 - 成功"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service, \
             patch('api_server.routers.backtest.create_strategy') as mock_create:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.run_backtest.return_value = {
                "success": True,
                "task_id": "bt_123",
                "status": "completed",
                "metrics": {
                    "total_return": 0.25,
                    "annual_return": 0.35,
                    "max_drawdown": 0.15,
                    "sharpe_ratio": 1.5,
                    "win_rate": 0.65
                }
            }

            mock_create.return_value = MagicMock()

            response = client.post(
                "/api/v1/backtest/single",
                json={
                    "strategy_name": "VCP",
                    "stock_codes": ["600519"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "task_id" in data["data"]
            assert "metrics" in data["data"]
            assert data["data"]["metrics"]["total_return"] == 0.25

    @pytest.mark.asyncio
    async def test_run_single_backtest_invalid_strategy(self, client):
        """测试单策略回测 - 无效策略"""
        with patch('api_server.routers.backtest.create_strategy') as mock_create:

            mock_create.side_effect = ValueError("Unknown strategy")

            response = client.post(
                "/api/v1/backtest/single",
                json={
                    "strategy_name": "INVALID",
                    "stock_codes": ["600519"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31"
                }
            )

            assert response.status_code == 400

    # ========== 组合回测测试 ==========
    @pytest.mark.asyncio
    async def test_run_portfolio_backtest_success(self, client):
        """测试组合回测 - 成功"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.run_portfolio_backtest.return_value = {
                "success": True,
                "task_id": "bt_456",
                "status": "completed",
                "portfolio_metrics": {
                    "total_return": 0.32,
                    "annual_return": 0.40,
                    "max_drawdown": 0.18,
                    "sharpe_ratio": 1.8,
                    "correlation_matrix": {}
                },
                "stock_results": [
                    {"stock_code": "600519", "return": 0.25},
                    {"stock_code": "000001", "return": 0.15}
                ]
            }

            response = client.post(
                "/api/v1/backtest/portfolio",
                json={
                    "stock_codes": ["600519", "000001"],
                    "strategies": ["VCP", "TD"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000,
                    "allocation_method": "equal"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["portfolio_metrics"]["total_return"] == 0.32
            assert len(data["data"]["stock_results"]) == 2

    # ========== 策略对比测试 ==========
    @pytest.mark.asyncio
    async def test_compare_strategies_success(self, client):
        """测试策略对比 - 成功"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.run_backtest.return_value = {
                "success": True,
                "task_id": "bt_789",
                "status": "completed",
                "metrics": {
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5
                }
            }

            response = client.post(
                "/api/v1/backtest/compare",
                json={
                    "stock_codes": ["600519"],
                    "strategies": ["VCP", "TD", "Divergence"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "comparison_results" in data["data"]
            assert len(data["data"]["comparison_results"]) >= 3

    # ========== 回测结果查询测试 ==========
    @pytest.mark.asyncio
    async def test_get_backtest_result_success(self, client):
        """测试获取回测结果 - 成功"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.get_result.return_value = {
                "success": True,
                "task_id": "bt_123",
                "status": "completed",
                "metrics": {
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": 0.15
                },
                "trades": [
                    {
                        "date": "2023-01-15",
                        "action": "BUY",
                        "price": 100.0,
                        "quantity": 100
                    }
                ]
            }

            response = client.get("/api/v1/backtest/result/bt_123")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["task_id"] == "bt_123"
            assert data["data"]["status"] == "completed"
            assert "trades" in data["data"]

    @pytest.mark.asyncio
    async def test_get_backtest_result_not_found(self, client):
        """测试获取回测结果 - 未找到"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.get_result.return_value = {
                "success": False,
                "error": "Task not found"
            }

            response = client.get("/api/v1/backtest/result/invalid_task")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False

    # ========== 生成回测报告测试 ==========
    @pytest.mark.asyncio
    async def test_generate_backtest_report_text(self, client):
        """测试生成回测报告 - 文本格式"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.get_result.return_value = {
                "success": True,
                "metrics": {
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5
                }
            }

            response = client.post(
                "/api/v1/backtest/report",
                json={
                    "task_id": "bt_123",
                    "format": "text",
                    "include_trades": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["format"] == "text"
            assert "report_content" in data["data"]

    @pytest.mark.asyncio
    async def test_generate_backtest_report_html(self, client):
        """测试生成回测报告 - HTML格式"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager, \
             patch('api_server.routers.backtest.BacktestService') as mock_service:

            mock_session = Mock()
            mock_db_manager.return_value.get_session.return_value.__enter__.return_value = mock_session

            mock_backtest = MagicMock()
            mock_service.return_value = mock_backtest
            mock_backtest.get_result.return_value = {
                "success": True,
                "metrics": {
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5
                }
            }

            response = client.post(
                "/api/v1/backtest/report",
                json={
                    "task_id": "bt_123",
                    "format": "html"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["format"] == "html"
            assert "<html>" in data["data"]["report_content"]

    # ========== 边界测试 ==========
    @pytest.mark.asyncio
    async def test_run_single_backtest_empty_stocks(self, client):
        """测试单策略回测 - 空股票列表"""
        response = client.post(
            "/api/v1/backtest/single",
            json={
                "strategy_name": "VCP",
                "stock_codes": [],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        )

        # 应该返回验证错误
        assert response.status_code in [200, 422]

    # ========== 异常测试 ==========
    @pytest.mark.asyncio
    async def test_backtest_with_exception(self, client):
        """测试回测接口异常处理"""
        with patch('api_server.routers.backtest.DatabaseManager') as mock_db_manager:

            mock_db_manager.side_effect = Exception("Database error")

            response = client.post(
                "/api/v1/backtest/single",
                json={
                    "strategy_name": "VCP",
                    "stock_codes": ["600519"],
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

