#!/usr/bin/env python3
"""测试新闻资讯 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


from api_server.main import app


class TestNewsAPI:
    """新闻资讯 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    # ========== 获取新闻列表测试 ==========
    def test_get_news_list_success(self, client):
        """测试获取新闻列表 - 成功"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
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

            response = client.get("/api/v1/news/list?page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == 50
            assert len(data["data"]["news"]) == 1

    def test_get_news_list_with_category(self, client):
        """测试获取新闻列表 - 带分类筛选"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_news_list.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get("/api/v1/news/list?category=股市&page=1&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["query_params"]["category"] == "股市"

    def test_get_news_list_with_date_range(self, client):
        """测试获取新闻列表 - 带日期范围"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_news_list.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get(
                "/api/v1/news/list?start_date=2024-01-01&end_date=2024-03-31&page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["query_params"]["start_date"] == "2024-01-01"
            assert data["data"]["query_params"]["end_date"] == "2024-03-31"

    def test_get_news_list_pagination(self, client):
        """测试获取新闻列表 - 分页"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
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
            assert len(data["data"]["news"]) == 15

    # ========== 获取新闻详情测试 ==========
    def test_get_news_detail_success(self, client):
        """测试获取新闻详情 - 成功"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
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
            assert data["success"] is True
            assert data["data"]["news_id"] == "n1"
            assert data["data"]["title"] == "股市大涨"

    def test_get_news_detail_not_found(self, client):
        """测试获取新闻详情 - 未找到"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_news_detail.return_value = {
                "success": False,
                "message": "news not found"
            }

            response = client.get("/api/v1/news/invalid_id")

            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False

    # ========== 搜索新闻测试 ==========
    def test_search_news_success(self, client):
        """测试搜索新闻 - 成功"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
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

            response = client.get("/api/v1/news/search?query=股市&page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["query"] == "股市"
            assert data["data"]["total"] == 10
            assert len(data["data"]["results"]) == 1

    def test_search_news_pagination(self, client):
        """测试搜索新闻 - 分页"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.search_news.return_value = {
                "success": True,
                "data": [{"news_id": "n1"}] * 10,
                "total": 50,
                "total_pages": 5
            }

            response = client.get("/api/v1/news/search?query=股市&page=2&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["page"] == 2
            assert data["data"]["total_pages"] == 5

    def test_search_news_empty_result(self, client):
        """测试搜索新闻 - 空结果"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.search_news.return_value = {
                "success": True,
                "data": [],
                "total": 0,
                "total_pages": 0
            }

            response = client.get("/api/v1/news/search?query=无效关键词&page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == 0
            assert len(data["data"]["results"]) == 0

    # ========== 异常测试 ==========
    def test_get_news_list_exception(self, client):
        """测试获取新闻列表 - 异常"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.get_news_list.side_effect = Exception("Database error")

            response = client.get("/api/v1/news/list?page=1&page_size=20")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_search_news_validation_error(self, client):
        """测试搜索新闻 - 验证错误"""
        with patch('api_server.routers.news.NewsService') as mock_service:
            mock_service_obj = MagicMock()
            mock_service.return_value = mock_service_obj
            mock_service_obj.search_news.side_effect = ValueError("Invalid query")

            response = client.get("/api/v1/news/search?query=&page=1&page_size=20")

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
