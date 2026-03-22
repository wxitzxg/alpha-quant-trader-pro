#!/usr/bin/env python3
"""测试新闻详情相关 API"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from api_server.main import app
from .test_utils import assert_success_response, assert_error_response


class TestNewsDetailAPI:
    """新闻详情 API 测试"""

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

    def test_get_news_detail_success(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻详情 - 成功"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_detail.return_value = {
            "success": True,
            "data": {
                "news_id": "n1",
                "title": "股市大涨",
                "content": "详细内容...",
                "publish_date": "2024-03-15",
                "source": "新浪财经",
                "url": "http://example.com/news/1"
            }
        }

        response = client.get("/api/v1/news/n1")

        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["data"]["news_id"] == "n1"
        assert data["data"]["title"] == "股市大涨"
        assert "content" in data["data"]

    def test_get_news_detail_not_found(self, client: TestClient, mock_news_service: Mock) -> None:
        """测试获取新闻详情 - 未找到"""
        mock_service_obj = MagicMock()
        mock_news_service.return_value = mock_service_obj
        mock_service_obj.get_news_detail.return_value = {
            "success": False,
            "message": "news not found"
        }

        response = client.get("/api/v1/news/invalid_id")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
