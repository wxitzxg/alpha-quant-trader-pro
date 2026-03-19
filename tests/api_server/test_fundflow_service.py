#!/usr/bin/env python3
"""测试资金流向服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api_server.services.fundflow_service import FundFlowService


class TestFundFlowService:
    """资金流向服务层测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return FundFlowService()

    def test_get_fund_flows_success(self, service):
        """测试获取资金流向成功（分页）"""
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_data = [
                {
                    "symbol": "600519",
                    "trade_date": "2024-03-15",
                    "main_net_inflow": 5000.0,
                    "main_net_inflow_rate": 0.05,
                    "retail_net_inflow": 1000.0,
                    "retail_net_inflow_rate": 0.01,
                    "super_large_net_inflow": 3000.0,
                    "large_net_inflow": 2000.0,
                    "medium_net_inflow": 500.0,
                    "small_net_inflow": 500.0
                },
                {
                    "symbol": "600519",
                    "trade_date": "2024-03-14",
                    "main_net_inflow": 3000.0,
                    "main_net_inflow_rate": 0.03,
                    "retail_net_inflow": 800.0,
                    "retail_net_inflow_rate": 0.008,
                    "super_large_net_inflow": 2000.0,
                    "large_net_inflow": 1000.0,
                    "medium_net_inflow": 400.0,
                    "small_net_inflow": 400.0
                }
            ]
            mock_get.return_value = mock_data

            result = service.get_fund_flows(
                symbol="600519",
                start_date="2024-03-14",
                end_date="2024-03-15",
                page=1,
                page_size=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["total"] == 2
            assert result["data"][0]["main_net_inflow"] == 5000.0
            assert result["data"][0]["retail_net_inflow"] == 1000.0

    def test_get_fund_flows_empty(self, service):
        """测试获取资金流向 - 空数据"""
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_get.return_value = []

            result = service.get_fund_flows(
                symbol="600000",
                page=1,
                page_size=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 0
            assert result["total"] == 0

    def test_get_fund_flows_error(self, service):
        """测试获取资金流向 - 错误"""
        from data_sources.exceptions import DataSourceError
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_get.side_effect = DataSourceError("investoday", "API error")

            result = service.get_fund_flows(symbol="600519", page=1, page_size=10)

            assert result["success"] is False
            assert "error" in result

    def test_get_dragon_tiger_success(self, service):
        """测试获取龙虎榜成功（分页）"""
        with patch.object(service.data_source, 'get_dragon_tiger') as mock_get:
            mock_data = [
                {
                    "symbol": "600519",
                    "trade_date": "2024-03-15",
                    "change_percent": 9.98,
                    "buy_institution_amount": 500000000.0,
                    "sell_institution_amount": 100000000.0,
                    "net_institution_amount": 400000000.0,
                    "buy_broker_amount": 200000000.0,
                    "sell_broker_amount": 50000000.0,
                    "net_broker_amount": 150000000.0
                }
            ]
            mock_get.return_value = mock_data

            result = service.get_dragon_tiger(
                symbol="600519",
                start_date="2024-03-15",
                end_date="2024-03-15",
                page=1,
                page_size=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 1
            assert result["data"][0]["buy_institution_amount"] == 500000000.0
            assert result["data"][0]["net_institution_amount"] == 400000000.0

    def test_get_dragon_tiger_paginated(self, service):
        """测试获取龙虎榜 - 分页"""
        with patch.object(service.data_source, 'get_dragon_tiger') as mock_get:
            mock_data = [
                {"symbol": "600519", "trade_date": f"2024-03-{day:02d}", "change_percent": 9.98}
                for day in range(1, 21)  # 20条数据
            ]
            mock_get.return_value = mock_data

            # 第一页
            result = service.get_dragon_tiger(symbol="600519", page=1, page_size=10)
            assert result["success"] is True
            assert len(result["data"]) == 10
            assert result["total"] == 20
            assert result["page"] == 1
            assert result["total_pages"] == 2

            # 第二页
            result = service.get_dragon_tiger(symbol="600519", page=2, page_size=10)
            assert len(result["data"]) == 10
