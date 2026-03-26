#!/usr/bin/env python3
"""实时K线同步接口测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api_server.main import app

client = TestClient(app)


class TestRealtimeKLineSync:
    """实时K线同步接口测试"""

    def test_sync_realtime_kline_single_stock(self):
        """测试单只股票同步成功"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 1,
                "failed_count": 0,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 1
        assert data["data"]["success_count"] == 1

    def test_sync_realtime_kline_multiple_stocks(self):
        """测试多只股票批量同步"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 2,
                "success_count": 2,
                "failed_count": 0,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None},
                    {"symbol": "000001", "status": "updated", "reason": None}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 2
        assert data["data"]["success_count"] == 2

    def test_sync_realtime_kline_empty_list(self):
        """测试空列表返回422错误"""
        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": [], "interval": "1d"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_sync_realtime_kline_invalid_interval(self):
        """测试无效interval返回400错误"""
        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": ["600519"], "interval": "1w"}
        )

        assert response.status_code == 400

    def test_sync_realtime_kline_partial_failure(self):
        """测试部分失败响应"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 3,
                "success_count": 2,
                "failed_count": 1,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None},
                    {"symbol": "000001", "status": "updated", "reason": None},
                    {"symbol": "999999", "status": "failed", "reason": "stock_not_found"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001", "999999"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["failed_count"] == 1
        assert data["data"]["success_count"] == 2

    def test_sync_realtime_kline_max_limit(self):
        """测试超过100只返回422错误"""
        stock_codes = [f"600{i:03d}" for i in range(101)]

        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": stock_codes, "interval": "1d"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_sync_realtime_kline_data_source_error(self):
        """测试数据源不可用"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 2,
                "success_count": 0,
                "failed_count": 2,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "failed", "reason": "data_source_error"},
                    {"symbol": "000001", "status": "failed", "reason": "data_source_error"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["failed_count"] == 2
        assert data["data"]["details"][0]["reason"] == "data_source_error"

    def test_sync_realtime_kline_db_error(self):
        """测试数据库写入失败"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 0,
                "failed_count": 1,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "failed", "reason": "db_error"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["details"][0]["reason"] == "db_error"

    def test_sync_realtime_kline_no_ohlc_data(self):
        """测试数据源不支持OHLC时跳过"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 1,
                "details": [
                    {"symbol": "600519", "status": "skipped", "reason": "no_ohlc_data"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["skipped_count"] == 1
        assert data["data"]["details"][0]["reason"] == "no_ohlc_data"
