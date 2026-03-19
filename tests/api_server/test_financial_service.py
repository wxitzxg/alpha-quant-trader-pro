#!/usr/bin/env python3
"""测试财务数据服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api_server.services.financial_service import FinancialService


class TestFinancialService:
    """财务数据服务层测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return FinancialService()

    def test_get_balance_sheet_success(self, service):
        """测试获取资产负债表成功"""
        with patch.object(service.data_source, 'get_balance_sheet') as mock_get:
            mock_result = Mock()
            mock_result.symbol = "600519"
            mock_result.year = 2023
            mock_result.quarter = 4
            mock_result.report_date = "2023-12-31"
            mock_result.total_assets = 2000000000.0
            mock_result.total_liabilities = 500000000.0
            mock_result.shareholders_equity = 1500000000.0
            mock_get.return_value = mock_result

            result = service.get_balance_sheet(symbol="600519", year=2023, quarter=4)

            assert result["success"] is True
            assert result["data"]["symbol"] == "600519"
            assert result["data"]["total_assets"] == 2000000000.0
            assert result["data"]["shareholders_equity"] == 1500000000.0

    def test_get_balance_sheet_not_found(self, service):
        """测试获取资产负债表 - 未找到"""
        with patch.object(service.data_source, 'get_balance_sheet') as mock_get:
            mock_get.return_value = None

            result = service.get_balance_sheet(symbol="600000", year=2023, quarter=4)

            assert result["success"] is False
            assert "not found" in result["message"]

    def test_get_balance_sheet_error(self, service):
        """测试获取资产负债表 - 错误"""
        from data_sources.exceptions import DataSourceError
        with patch.object(service.data_source, 'get_balance_sheet') as mock_get:
            mock_get.side_effect = DataSourceError("investoday", "API error")

            result = service.get_balance_sheet(symbol="600519", year=2023, quarter=4)

            assert result["success"] is False
            assert "error" in result

    def test_get_income_statement_success(self, service):
        """测试获取利润表成功"""
        with patch.object(service.data_source, 'get_income_statement') as mock_get:
            mock_result = Mock()
            mock_result.symbol = "600519"
            mock_result.year = 2023
            mock_result.quarter = 4
            mock_result.report_date = "2023-12-31"
            mock_result.revenue = 1000000000.0
            mock_result.net_profit = 500000000.0
            mock_result.eps = 40.0
            mock_get.return_value = mock_result

            result = service.get_income_statement(symbol="600519", year=2023, quarter=4)

            assert result["success"] is True
            assert result["data"]["revenue"] == 1000000000.0
            assert result["data"]["net_profit"] == 500000000.0
            assert result["data"]["eps"] == 40.0

    def test_get_cash_flow_statement_success(self, service):
        """测试获取现金流量表成功"""
        with patch.object(service.data_source, 'get_cash_flow_statement') as mock_get:
            mock_result = Mock()
            mock_result.symbol = "600519"
            mock_result.year = 2023
            mock_result.quarter = 4
            mock_result.report_date = "2023-12-31"
            mock_result.operating_cash_flow = 600000000.0
            mock_result.investing_cash_flow = -200000000.0
            mock_result.financing_cash_flow = -100000000.0
            mock_get.return_value = mock_result

            result = service.get_cash_flow_statement(symbol="600519", year=2023, quarter=4)

            assert result["success"] is True
            assert result["data"]["operating_cash_flow"] == 600000000.0
            assert result["data"]["investing_cash_flow"] == -200000000.0

    def test_get_financial_indicators_success(self, service):
        """测试获取财务指标成功（分页）"""
        with patch.object(service.data_source, 'get_financial_indicators') as mock_get:
            mock_data = [
                {"symbol": "600519", "report_date": "2023-12-31", "roe": 0.30, "pe": 30.0},
                {"symbol": "600519", "report_date": "2023-09-30", "roe": 0.28, "pe": 28.0},
                {"symbol": "600519", "report_date": "2023-06-30", "roe": 0.25, "pe": 25.0},
            ]
            mock_get.return_value = mock_data

            result = service.get_financial_indicators(
                symbol="600519",
                start_date="2023-01-01",
                end_date="2023-12-31",
                page=1,
                page_size=2
            )

            assert result["success"] is True
            assert len(result["data"]) == 2  # 第一页2条
            assert result["total"] == 3
            assert result["page"] == 1
            assert result["total_pages"] == 2

    def test_get_dupont_analysis_success(self, service):
        """测试获取杜邦分析成功（分页）"""
        with patch.object(service.data_source, 'get_dupont_analysis') as mock_get:
            mock_data = [
                {"symbol": "600519", "report_date": "2023-12-31", "roe": 0.30, "profit_margin": 0.50},
                {"symbol": "600519", "report_date": "2023-09-30", "roe": 0.28, "profit_margin": 0.48},
            ]
            mock_get.return_value = mock_data

            result = service.get_dupont_analysis(
                symbol="600519",
                page=1,
                page_size=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["total"] == 2

    def test_get_per_share_indicators_success(self, service):
        """测试获取每股指标成功（分页）"""
        with patch.object(service.data_source, 'get_per_share_indicators') as mock_get:
            mock_data = [
                {"symbol": "600519", "report_date": "2023-12-31", "eps": 40.0, "bps": 200.0},
                {"symbol": "600519", "report_date": "2023-09-30", "eps": 38.0, "bps": 195.0},
            ]
            mock_get.return_value = mock_data

            result = service.get_per_share_indicators(
                symbol="600519",
                page=1,
                page_size=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["data"][0]["eps"] == 40.0
