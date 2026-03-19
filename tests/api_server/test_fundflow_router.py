#!/usr/bin/env python3
"""测试资金流向数据 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


from api_server.main import app


class TestFundFlowAPI:
    """资金流向数据 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 资金流向测试 ==========
    def test_get_fund_flow_success(self, client):
        """测试获取资金流向 - 成功"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_fund_flows.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2024-03-15",
                        "main_net_inflow": 50000000,
                        "retail_net_inflow": -10000000,
                        "trend": "positive"
                    }
                ],
                "total": 10,
                "total_pages": 1
            }

            response = client.get(
                "/api/v1/fundflow/600519?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["total"] == 10
            assert len(data["data"]["fund_flows"]) == 1

    def test_get_fund_flow_with_date_range(self, client):
        """测试获取资金流向 - 带日期范围"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_fund_flows.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get(
                "/api/v1/fundflow/600519?start_date=2024-01-01&end_date=2024-03-31&page=1&page_size=10"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["query_params"]["start_date"] == "2024-01-01"
            assert data["data"]["query_params"]["end_date"] == "2024-03-31"

    def test_get_fund_flow_pagination(self, client):
        """测试获取资金流向 - 分页"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_fund_flows.return_value = {
                "success": True,
                "data": [{"date": "2024-03-15"}] * 15,
                "total": 100,
                "total_pages": 7
            }

            response = client.get(
                "/api/v1/fundflow/600519?page=2&page_size=15"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 15
            assert len(data["data"]["fund_flows"]) == 15

    # ========== 龙虎榜测试 ==========
    def test_get_dragon_tiger_success(self, client):
        """测试获取龙虎榜 - 成功"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_dragon_tiger.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2024-03-15",
                        "buy_side": [
                            {"broker": "中信证券", "amount": 50000000},
                            {"broker": "华泰证券", "amount": 30000000}
                        ],
                        "sell_side": [
                            {"broker": "国泰君安", "amount": 20000000}
                        ],
                        "net_amount": 60000000
                    }
                ],
                "total": 5,
                "total_pages": 1
            }

            response = client.get(
                "/api/v1/fundflow/dragon-tiger/600519?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert len(data["data"]["dragon_tiger_data"]) == 1
            assert data["data"]["dragon_tiger_data"][0]["net_amount"] == 60000000

    def test_get_dragon_tiger_with_date_range(self, client):
        """测试获取龙虎榜 - 带日期范围"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_dragon_tiger.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get(
                "/api/v1/fundflow/dragon-tiger/600519?start_date=2024-01-01&end_date=2024-03-31"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_get_dragon_tiger_pagination(self, client):
        """测试获取龙虎榜 - 分页"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_dragon_tiger.return_value = {
                "success": True,
                "data": [{"date": "2024-03-15"}] * 10,
                "total": 50,
                "total_pages": 5
            }

            response = client.get(
                "/api/v1/fundflow/dragon-tiger/600519?page=3&page_size=10"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 3
            assert data["data"]["total_pages"] == 5

    # ========== 异常测试 ==========
    def test_get_fund_flow_not_found(self, client):
        """测试获取资金流向 - 未找到"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_fund_flows.return_value = {
                "success": False,
                "message": "数据不存在"
            }

            response = client.get(
                "/api/v1/fundflow/600519?page=1&page_size=20"
            )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False

    def test_get_dragon_tiger_exception(self, client):
        """测试获取龙虎榜 - 异常"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_dragon_tiger.side_effect = Exception("Data error")

            response = client.get(
                "/api/v1/fundflow/dragon-tiger/600519?page=1&page_size=20"
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_fund_flow_validation_error(self, client):
        """测试获取资金流向 - 验证错误"""
        with patch('api_server.routers.fundflow.FundFlowService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_fund_flows.side_effect = ValueError("Invalid date format")

            response = client.get(
                "/api/v1/fundflow/600519?start_date=invalid&page=1&page_size=20"
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
