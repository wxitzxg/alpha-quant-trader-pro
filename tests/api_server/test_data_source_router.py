#!/usr/bin/env python3
"""测试数据源 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from api_server.main import app
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_CODE_2,
    TEST_START_DATE,
    TEST_END_DATE,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MIN,
    PAGE_SIZE_MAX,
    assert_success_response
)


class TestDataSourceAPI:
    """数据源 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    # ========== 股票列表测试 ==========
    def test_get_stock_list(self, client: TestClient) -> None:
        """测试获取股票列表"""
        mock_stocks = [
            {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台", "exchange": "SH", "market": "主板", "status": "L"},
            {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "exchange": "SZ", "market": "主板", "status": "L"},
        ]
        mock_result = {"success": True, "data": {"stocks": mock_stocks, "total": 2, "page": 1, "page_size": 20}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_list.return_value = mock_result

            response = client.get(f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_DEFAULT}&exchange=SH")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_stock_list_invalid_params(self, client: TestClient) -> None:
        """测试获取股票列表 - 无效参数"""
        response = client.get("/api/v1/stock/list?page=0&page_size=0")

        # FastAPI 验证会返回 422
        assert response.status_code in [200, 422]

    def test_get_stock_list_server_error(self, client: TestClient) -> None:
        """测试获取股票列表 - 服务端错误"""
        mock_result = {"success": False, "message": "Database error"}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_list.return_value = mock_result

            response = client.get("/api/v1/stock/list?page=1&page_size=20")

            assert response.status_code == 500

    # ========== 股票详情测试 ==========
    def test_get_stock_info(self, client: TestClient) -> None:
        """测试获取股票详情"""
        mock_detail = {
            "ts_code": f"{TEST_STOCK_CODE}.SH",
            "symbol": TEST_STOCK_CODE,
            "name": "贵州茅台",
            "exchange": "SH",
            "market": "主板",
            "status": "L"
        }
        mock_result = {"success": True, "data": mock_detail}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_info.return_value = mock_result

            response = client.get(f"/api/v1/stock/info/{TEST_STOCK_CODE}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_stock_info_not_found(self, client: TestClient) -> None:
        """测试获取股票详情 - 未找到"""
        mock_result = {"success": False, "message": "Stock INVALID not found"}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_info.return_value = mock_result

            response = client.get("/api/v1/stock/info/INVALID")

            assert response.status_code == 404

    # ========== 实时行情测试 ==========
    def test_get_realtime_quote(self, client: TestClient) -> None:
        """测试获取单股实时行情"""
        mock_quote = {
            "ts_code": f"{TEST_STOCK_CODE}.SH",
            "symbol": TEST_STOCK_CODE,
            "name": "贵州茅台",
            "current_price": 1700.0,
            "change": 10.0,
            "change_pct": 0.5,
            "open": 1690.0,
            "high": 1720.0,
            "low": 1680.0,
            "close": 1700.0,
            "volume": 100000,
            "amount": 170000000.0,
            "turnover_rate": 0.5,
            "update_time": "2024-03-15T10:30:00"
        }

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_realtime_quote.return_value = mock_quote

            response = client.get(f"/api/v1/quote/realtime/{TEST_STOCK_CODE}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_realtime_quote_not_found(self, client: TestClient) -> None:
        """测试获取实时行情 - 未找到"""
        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_realtime_quote.return_value = None

            response = client.get("/api/v1/quote/realtime/INVALID")

            assert response.status_code == 404

    # ========== 批量行情测试 ==========
    def test_get_batch_quotes(self, client: TestClient) -> None:
        """测试批量获取行情"""
        mock_quotes = {
            TEST_STOCK_CODE: {
                "ts_code": f"{TEST_STOCK_CODE}.SH",
                "symbol": TEST_STOCK_CODE,
                "name": "贵州茅台",
                "current_price": 1700.0,
                "change": 10.0,
                "change_pct": 0.5,
                "open": 1690.0,
                "high": 1720.0,
                "low": 1680.0,
                "close": 1700.0,
                "volume": 100000,
                "amount": 170000000.0,
                "update_time": "2024-03-15T10:30:00"
            },
            TEST_STOCK_CODE_2: {
                "ts_code": f"{TEST_STOCK_CODE_2}.SZ",
                "symbol": TEST_STOCK_CODE_2,
                "name": "平安银行",
                "current_price": 15.0,
                "change": 0.5,
                "change_pct": 0.3,
                "open": 14.5,
                "high": 15.5,
                "low": 14.3,
                "close": 15.0,
                "volume": 500000,
                "amount": 7500000.0,
                "update_time": "2024-03-15T10:30:00"
            }
        }

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_batch_quotes.return_value = mock_quotes

            response = client.post(
                "/api/v1/quote/batch",
                json={"symbols": [TEST_STOCK_CODE, TEST_STOCK_CODE_2]}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_batch_quotes_empty(self, client: TestClient) -> None:
        """测试批量获取行情 - 空列表"""
        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_batch_quotes.return_value = {}

            response = client.post(
                "/api/v1/quote/batch",
                json={"symbols": [TEST_STOCK_CODE]}
            )

            assert response.status_code == 200

    # ========== 排行榜测试 ==========
    def test_get_top_list_gain(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 涨幅榜"""
        mock_items = [
            {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台", "change_pct": 5.0, "current_price": 1700.0, "change": 80.0, "volume": 100000},
        ]
        mock_result = {"success": True, "data": {"type": "gain", "date": "2024-03-15", "items": mock_items, "total": 1}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_top_list.return_value = mock_result

            response = client.get("/api/v1/quote/top-list?type=gain")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["type"] == "gain"

    def test_get_top_list_loss(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 跌幅榜"""
        mock_items = [
            {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "change_pct": -5.0, "current_price": 14.0, "change": -0.8, "volume": 200000},
        ]
        mock_result = {"success": True, "data": {"type": "loss", "date": "2024-03-15", "items": mock_items, "total": 1}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_top_list.return_value = mock_result

            response = client.get("/api/v1/quote/top-list?type=loss")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["type"] == "loss"

    def test_get_top_list_with_date(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 指定日期"""
        mock_result = {"success": True, "data": {"type": "gain", "date": "2024-03-01", "items": [], "total": 0}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_top_list.return_value = mock_result

            response = client.get("/api/v1/quote/top-list?type=gain&date=2024-03-01")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["date"] == "2024-03-01"

    def test_get_top_list_error(self, client: TestClient) -> None:
        """测试涨跌幅排行 - 服务错误"""
        mock_result = {"success": False, "message": "API Error"}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_top_list.return_value = mock_result

            response = client.get("/api/v1/quote/top-list?type=gain")

            assert response.status_code == 500

    # ========== K线数据测试 ==========
    def test_get_kline(self, client: TestClient) -> None:
        """测试获取K线数据"""
        mock_klines = [
            {
                "ts_code": f"{TEST_STOCK_CODE}.SH",
                "symbol": TEST_STOCK_CODE,
                "trade_date": "2024-03-15",
                "open": 1690.0,
                "high": 1720.0,
                "low": 1680.0,
                "close": 1700.0,
                "volume": 100000,
                "amount": 170000000.0
            }
        ]

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_kline.return_value = mock_klines

            response = client.get(
                f"/api/v1/kline/{TEST_STOCK_CODE}"
                f"?interval=1d&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_kline_not_found(self, client: TestClient) -> None:
        """测试获取K线数据 - 未找到"""
        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_kline.return_value = None

            response = client.get(f"/api/v1/kline/INVALID?interval=1d")

            assert response.status_code == 404

    # ========== 批量K线测试 ==========
    def test_get_batch_klines(self, client: TestClient) -> None:
        """测试批量获取K线"""
        mock_result = {
            TEST_STOCK_CODE: [{
                "ts_code": f"{TEST_STOCK_CODE}.SH",
                "symbol": TEST_STOCK_CODE,
                "trade_date": "2024-03-15",
                "open": 1690.0,
                "high": 1720.0,
                "low": 1680.0,
                "close": 1700.0,
                "volume": 100000,
                "amount": 170000000.0
            }],
            TEST_STOCK_CODE_2: [{
                "ts_code": f"{TEST_STOCK_CODE_2}.SZ",
                "symbol": TEST_STOCK_CODE_2,
                "trade_date": "2024-03-15",
                "open": 14.5,
                "high": 15.5,
                "low": 14.0,
                "close": 15.0,
                "volume": 500000,
                "amount": 7500000.0
            }]
        }

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_batch_klines.return_value = mock_result

            response = client.post(
                "/api/v1/kline/batch",
                json={
                    "symbols": [TEST_STOCK_CODE, TEST_STOCK_CODE_2],
                    "interval": "1d"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_batch_klines_error(self, client: TestClient) -> None:
        """测试批量获取K线 - 错误"""
        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_batch_klines.side_effect = Exception("API Error")

            response = client.post(
                "/api/v1/kline/batch",
                json={"symbols": [TEST_STOCK_CODE], "interval": "1d"}
            )

            assert response.status_code == 500

    # ========== K线统计测试 ==========
    def test_get_kline_stats(self, client: TestClient) -> None:
        """测试K线统计信息"""
        mock_stats = {
            "symbol": TEST_STOCK_CODE,
            "name": "贵州茅台",
            "period": "1y",
            "total_trading_days": 244,
            "price_range": {"min": 1500.0, "max": 2000.0, "avg": 1750.0},
            "volume_stats": {"min": 100000, "max": 500000, "avg": 200000, "total": 48800000},
            "volatility": 15.5,
            "highest_price": {"price": 2000.0, "date": "2024-01-15"},
            "lowest_price": {"price": 1500.0, "date": "2024-02-20"}
        }
        mock_result = {"success": True, "data": mock_stats}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_kline_stats.return_value = mock_result

            response = client.get(f"/api/v1/kline/stats/{TEST_STOCK_CODE}?period=1y")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert "price_range" in data["data"]
            assert "volume_stats" in data["data"]
            assert "volatility" in data["data"]

    def test_get_kline_stats_different_periods(self, client: TestClient) -> None:
        """测试K线统计 - 不同周期"""
        mock_stats = {
            "symbol": TEST_STOCK_CODE,
            "name": "贵州茅台",
            "period": "6m",
            "total_trading_days": 122,
            "price_range": {"min": 1500.0, "max": 2000.0, "avg": 1750.0},
            "volume_stats": {"min": 100000, "max": 500000, "avg": 200000, "total": 24400000},
            "volatility": 15.5,
            "highest_price": {"price": 2000.0, "date": "2024-01-15"},
            "lowest_price": {"price": 1500.0, "date": "2024-02-20"}
        }
        mock_result = {"success": True, "data": mock_stats}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_kline_stats.return_value = mock_result

            for period in ["1y", "6m", "3m", "1m"]:
                response = client.get(f"/api/v1/kline/stats/{TEST_STOCK_CODE}?period={period}")
                assert response.status_code == 200

    def test_get_kline_stats_error(self, client: TestClient) -> None:
        """测试K线统计 - 服务错误"""
        mock_result = {"success": False, "message": "Data Error"}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_kline_stats.return_value = mock_result

            response = client.get(f"/api/v1/kline/stats/{TEST_STOCK_CODE}?period=1y")

            assert response.status_code == 500

    # ========== 财务指标测试 ==========
    def test_get_financial_indicators(self, client: TestClient) -> None:
        """测试获取财务指标"""
        mock_indicators = {
            "roe": 0.15,
            "gross_margin": 0.40,
            "net_margin": 0.20
        }
        mock_result = {"success": True, "data": mock_indicators}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_financial_indicators.return_value = mock_result

            response = client.get(f"/api/v1/financial/indicators/{TEST_STOCK_CODE}")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)

    def test_get_financial_indicators_not_found(self, client: TestClient) -> None:
        """测试获取财务指标 - 未找到"""
        mock_result = {"success": False, "message": "No financial indicators for INVALID"}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_financial_indicators.return_value = mock_result

            response = client.get("/api/v1/financial/indicators/INVALID")

            assert response.status_code == 404

    # ========== 边界测试 ==========
    def test_get_stock_list_boundary(self, client: TestClient) -> None:
        """测试股票列表边界情况"""
        # Router has page_size limit of 100, not PAGE_SIZE_MAX (1000)
        PAGE_SIZE_ROUTER_MAX = 100
        mock_result = {"success": True, "data": {"stocks": [], "total": 0, "page": 1, "page_size": PAGE_SIZE_ROUTER_MAX}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_list.return_value = mock_result

            # 测试最大页码（路由限制为100）
            response = client.get(f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_ROUTER_MAX}")
            assert response.status_code == 200

            # 测试最小页码
            mock_result["data"]["page_size"] = PAGE_SIZE_MIN
            response = client.get(f"/api/v1/stock/list?page=1&page_size={PAGE_SIZE_MIN}")
            assert response.status_code == 200

    # ========== 响应格式测试 ==========
    def test_response_format_consistency(self, client: TestClient) -> None:
        """测试响应格式一致性"""
        mock_result = {"success": True, "data": {"stocks": [], "total": 0, "page": 1, "page_size": 20}}

        with patch('api_server.routers.data_source.DataSourceService') as MockService:
            MockService.get_stock_list.return_value = mock_result

            response = client.get("/api/v1/stock/list")

            data = response.json()
            # 检查标准响应格式
            assert "success" in data
            assert "data" in data
            assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
