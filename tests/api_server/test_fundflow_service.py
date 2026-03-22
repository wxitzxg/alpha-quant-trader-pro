#!/usr/bin/env python3
"""测试资金流向服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from api_server.services.fundflow_service import FundFlowService
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_START_DATE,
    TEST_END_DATE,
    PAGE_SIZE_DEFAULT,
    TEST_MAIN_NET_INFLOW,
    TEST_RETAIL_NET_INFLOW,
    assert_success_response,
    assert_error_response,
    assert_pagination_response
)


class TestFundFlowService:
    """资金流向服务层测试"""

    @pytest.fixture
    def service(self) -> FundFlowService:
        """创建服务实例"""
        return FundFlowService()

    def test_get_fund_flows_success(self, service: FundFlowService) -> None:
        """测试获取资金流向成功（分页）"""
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_data = [
                {
                    "symbol": TEST_STOCK_CODE,
                    "trade_date": "2024-03-15",
                    "main_net_inflow": TEST_MAIN_NET_INFLOW,
                    "main_net_inflow_rate": 0.05,
                    "retail_net_inflow": TEST_RETAIL_NET_INFLOW,
                    "retail_net_inflow_rate": 0.01,
                    "super_large_net_inflow": 3000.0,
                    "large_net_inflow": 2000.0,
                    "medium_net_inflow": 500.0,
                    "small_net_inflow": 500.0
                },
                {
                    "symbol": TEST_STOCK_CODE,
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
                symbol=TEST_STOCK_CODE,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                page=1,
                page_size=PAGE_SIZE_DEFAULT
            )

            assert_success_response(result)
            assert_pagination_response(result, expected_total=2, expected_page=1)
            assert len(result["data"]) == 2
            assert result["data"][0]["main_net_inflow"] == TEST_MAIN_NET_INFLOW
            assert result["data"][0]["retail_net_inflow"] == TEST_RETAIL_NET_INFLOW

    def test_get_fund_flows_empty(self, service: FundFlowService) -> None:
        """测试获取资金流向 - 空数据"""
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_get.return_value = []

            result = service.get_fund_flows(
                symbol="600000",
                page=1,
                page_size=PAGE_SIZE_DEFAULT
            )

            assert_success_response(result)
            assert_pagination_response(result, expected_total=0, expected_page=1)
            assert len(result["data"]) == 0

    def test_get_fund_flows_error(self, service: FundFlowService) -> None:
        """测试获取资金流向 - 错误"""
        from data_sources.exceptions import DataSourceError
        with patch.object(service.data_source, 'get_fund_flows') as mock_get:
            mock_get.side_effect = DataSourceError("investoday", "API error")

            result = service.get_fund_flows(
                symbol=TEST_STOCK_CODE,
                page=1,
                page_size=PAGE_SIZE_DEFAULT
            )

            assert_error_response(result, "error")
            assert result["success"] is False

    def test_get_dragon_tiger_success(self, service: FundFlowService) -> None:
        """测试获取龙虎榜成功（分页）"""
        with patch.object(service.data_source, 'get_dragon_tiger') as mock_get:
            mock_data = [
                {
                    "symbol": TEST_STOCK_CODE,
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
                symbol=TEST_STOCK_CODE,
                start_date=TEST_START_DATE,
                end_date=TEST_END_DATE,
                page=1,
                page_size=PAGE_SIZE_DEFAULT
            )

            assert_success_response(result)
            assert_pagination_response(result, expected_total=1, expected_page=1)
            assert len(result["data"]) == 1
            assert result["data"][0]["buy_institution_amount"] == 500000000.0
            assert result["data"][0]["net_institution_amount"] == 400000000.0

    def test_get_dragon_tiger_paginated(self, service: FundFlowService) -> None:
        """测试获取龙虎榜 - 分页"""
        with patch.object(service.data_source, 'get_dragon_tiger') as mock_get:
            mock_data = [
                {
                    "symbol": TEST_STOCK_CODE,
                    "trade_date": f"2024-03-{day:02d}",
                    "change_percent": 9.98,
                    "buy_institution_amount": 100000000.0 * day,
                    "net_institution_amount": 50000000.0 * day
                }
                for day in range(1, 21)  # 20条数据
            ]
            mock_get.return_value = mock_data

            # 第一页
            result = service.get_dragon_tiger(
                symbol=TEST_STOCK_CODE,
                page=1,
                page_size=10
            )
            assert_success_response(result)
            assert_pagination_response(result, expected_total=20, expected_page=1)
            assert len(result["data"]) == 10
            assert result["total_pages"] == 2

            # 第二页
            result = service.get_dragon_tiger(
                symbol=TEST_STOCK_CODE,
                page=2,
                page_size=10
            )
            assert_success_response(result)
            assert len(result["data"]) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
