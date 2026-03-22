#!/usr/bin/env python3
"""测试新闻搜索相关 API"""

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


class TestNewsSearchAPI:
    """新闻搜索 API 测试"""

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

    def test_search_news_success(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试搜索新闻 - 成功"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.search_news.return_value = {
            "success": True,
            "data": [
                {
                    "news_id": "n1",
                    "title": "股市大涨",
                    "summary": "今日股市大涨",
                    "publish_date": "2024-03-15"
                }
            ],
            "total": 10,
            "total_pages": 1
        }

        response = client.get(f"/api/v1/news/search?query={TEST_STOCK_NAME}&page=1&page_size={PAGE_SIZE_DEFAULT}")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["query"] == TEST_STOCK_NAME
        assert data["data"]["total"] == 10
        assert_pagination_response(data, expected_total=10, expected_page=1)
        assert len(data["data"]["results"]) == 1

    def test_search_news_pagination(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试搜索新闻 - 分页"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.search_news.return_value = {
            "success": True,
            "data": [{"news_id": "n1"}] * 10,
            "total": 50,
            "total_pages": 5
        }

        response = client.get(f"/api/v1/news/search?query={TEST_STOCK_NAME}&page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["page"] == 2
        assert data["data"]["page_size"] == 10
        assert data["data"]["total"] == 50
        assert data["data"]["total_pages"] == 5
        assert len(data["data"]["results"]) == 10

    def test_search_news_empty_result(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试搜索新闻 - 空结果"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.search_news.return_value = {
            "success": True,
            "data": [],
            "total": 0,
            "total_pages": 0
        }

        response = client.get("/api/v1/news/search?query=无效关键词&page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["total"] == 0
        assert len(data["data"]["results"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
