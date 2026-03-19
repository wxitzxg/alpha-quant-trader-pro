#!/usr/bin/env python3
"""测试财务数据 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


from api_server.main import app


class TestFinancialAPI:
    """财务数据 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 资产负债表测试 ==========
    def test_get_balance_sheet_success(self, client):
        """测试获取资产负债表 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_balance_sheet.return_value = {
                "success": True,
                "data": {
                    "total_assets": 1000000000,
                    "total_liabilities": 400000000,
                    "shareholders_equity": 600000000
                }
            }

            response = client.get(
                "/api/v1/financial/balance-sheet/600519?year=2023&quarter=4"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_assets"] == 1000000000
            assert "资产负债表获取成功" in data["message"]

    def test_get_balance_sheet_not_found(self, client):
        """测试获取资产负债表 - 未找到"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_balance_sheet.return_value = {
                "success": False,
                "message": "数据不存在"
            }

            response = client.get(
                "/api/v1/financial/balance-sheet/600519?year=2023&quarter=4"
            )

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False

    # ========== 利润表测试 ==========
    def test_get_income_statement_success(self, client):
        """测试获取利润表 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_income_statement.return_value = {
                "success": True,
                "data": {
                    "revenue": 100000000,
                    "net_profit": 20000000,
                    "eps": 10.0
                }
            }

            response = client.get(
                "/api/v1/financial/income-statement/600519?year=2023&quarter=4"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["revenue"] == 100000000
            assert data["data"]["eps"] == 10.0

    def test_get_income_statement_validation(self, client):
        """测试获取利润表 - 验证错误"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_income_statement.side_effect = ValueError("Invalid quarter")

            response = client.get(
                "/api/v1/financial/income-statement/600519?year=2023&quarter=5"
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    # ========== 现金流量表测试 ==========
    def test_get_cash_flow_statement_success(self, client):
        """测试获取现金流量表 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_cash_flow_statement.return_value = {
                "success": True,
                "data": {
                    "operating_cash_flow": 50000000,
                    "investing_cash_flow": -20000000,
                    "financing_cash_flow": -10000000
                }
            }

            response = client.get(
                "/api/v1/financial/cash-flow/600519?year=2023&quarter=4"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["operating_cash_flow"] == 50000000

    # ========== 财务指标测试 ==========
    def test_get_financial_indicators_success(self, client):
        """测试获取财务指标 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_financial_indicators.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2023-12-31",
                        "pe_ratio": 20.0,
                        "pb_ratio": 2.5,
                        "roe": 0.15,
                        "roa": 0.08,
                        "debt_ratio": 0.4
                    }
                ],
                "total": 4,
                "total_pages": 1
            }

            response = client.get(
                "/api/v1/financial/indicators/600519?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["stock_code"] == "600519"
            assert data["data"]["total"] == 4
            assert len(data["data"]["indicators"]) == 1

    def test_get_financial_indicators_with_date_range(self, client):
        """测试获取财务指标 - 带日期范围"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_financial_indicators.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get(
                "/api/v1/financial/indicators/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=10"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["query_params"]["start_date"] == "2023-01-01"

    def test_get_financial_indicators_pagination(self, client):
        """测试获取财务指标 - 分页"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_financial_indicators.return_value = {
                "success": True,
                "data": [],
                "total": 100,
                "total_pages": 5
            }

            response = client.get(
                "/api/v1/financial/indicators/600519?page=2&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 20
            assert data["data"]["total_pages"] == 5

    # ========== 杜邦分析测试 ==========
    def test_get_dupont_analysis_success(self, client):
        """测试获取杜邦分析 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_dupont_analysis.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2023-12-31",
                        "roe": 0.15,
                        "profit_margin": 0.2,
                        "asset_turnover": 0.5,
                        "equity_multiplier": 1.5
                    }
                ],
                "total": 4,
                "total_pages": 1
            }

            response = client.get(
                "/api/v1/financial/dupont/600519?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["dupont_data"]) == 1
            assert data["data"]["dupont_data"][0]["roe"] == 0.15

    # ========== 每股指标测试 ==========
    def test_get_per_share_indicators_success(self, client):
        """测试获取每股指标 - 成功"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_per_share_indicators.return_value = {
                "success": True,
                "data": [
                    {
                        "date": "2023-12-31",
                        "eps": 10.0,
                        "book_value_per_share": 50.0,
                        "cash_flow_per_share": 8.0,
                        "dividend_per_share": 2.0
                    }
                ],
                "total": 4,
                "total_pages": 1
            }

            response = client.get(
                "/api/v1/financial/per-share/600519?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["per_share_indicators"][0]["eps"] == 10.0

    # ========== 异常测试 ==========
    def test_get_balance_sheet_exception(self, client):
        """测试获取资产负债表 - 异常"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_balance_sheet.side_effect = Exception("Data error")

            response = client.get(
                "/api/v1/financial/balance-sheet/600519?year=2023&quarter=4"
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_financial_indicators_exception(self, client):
        """测试获取财务指标 - 异常"""
        with patch('api_server.routers.financial.FinancialService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_financial_indicators.side_effect = Exception("Query error")

            response = client.get(
                "/api/v1/financial/indicators/600519?page=1&page_size=20"
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
