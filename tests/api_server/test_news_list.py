#!/usr/bin/env python3
"""测试新闻列表相关 API"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from api_server.main import app
from .test_utils import (
    PAGE_SIZE_DEFAULT,
    TEST_STOCK_NAME,
    assert_success_response,
    assert_error_response,
    assert_pagination_response
)


class TestNewsListAPI:
    """新闻列表 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    @pytest.fixture
    def mock_news_service(self):
        """Mock 新闻服务"""
        with patch('api_server.routers.news.NewsService') as mock:
            yield mock

    def test_get_news_list_success(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻列表 - 成功"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_list.return_value = {
            "success": True,
            "data": [
                {
                    "news_id": "n1",
                    "title": "股市大涨",
                    "summary": "今日股市大涨",
                    "publish_date": "2024-03-15",
                    "source": "新浪财经"
                }
            ],
            "total": 50,
            "total_pages": 3
        }

        response = client.get(f"/api/v1/news/list?page=1&page_size={PAGE_SIZE_DEFAULT}")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert_pagination_response(data, expected_total=50, expected_page=1)
        assert len(data["data"]["news"]) == 1

    def test_get_news_list_with_category(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻列表 - 带分类筛选"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_list.return_value = {
            "success": True,
            "data": [],
            "total": 0,
            "total_pages": 0
        }

        response = client.get(f"/api/v1/news/list?category=股市&page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["query_params"]["category"] == "股市"

    def test_get_news_list_with_date_range(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻列表 - 带日期范围"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_list.return_value = {
            "success": True,
            "data": [],
            "total": 0,
            "total_pages": 0
        }

        response = client.get(
            "/api/v1/news/list?start_date=2024-01-01&end_date=2024-03-31"
            f"&page=1&page_size={PAGE_SIZE_DEFAULT}"
        )

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["query_params"]["start_date"] == "2024-01-01"
        assert data["data"]["query_params"]["end_date"] == "2024-03-31"

    def test_get_news_list_pagination(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻列表 - 分页"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_list.return_value = {
            "success": True,
            "data": [{"news_id": "n1"}] * 15,
            "total": 100,
            "total_pages": 7
        }

        response = client.get("/api/v1/news/list?page=3&page_size=15")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 3
        assert data["data"]["page_size"] == 15
        assert data["data"]["total"] == 100
        assert len(data["data"]["news"]) == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
