#!/usr/bin/env python3
"""测试新闻资讯服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api_server.services.news_service import NewsService


class TestNewsService:
    """新闻资讯服务层测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return NewsService()

    def test_get_news_list_not_implemented(self, service):
        """测试获取新闻列表 - 未实现"""
        result = service.get_news_list(
            page=1,
            page_size=20,
            category="财经",
            start_date="2024-03-01",
            end_date="2024-03-31"
        )

        assert result["success"] is False
        assert "not yet implemented" in result["message"]

    def test_get_news_detail_not_implemented(self, service):
        """测试获取新闻详情 - 未实现"""
        result = service.get_news_detail(news_id="test_news_001")

        assert result["success"] is False
        assert "not found" in result["message"]
        assert "not yet implemented" in result["message"]

    def test_search_news_not_implemented(self, service):
        """测试搜索新闻 - 未实现"""
        result = service.search_news(query="贵州茅台", page=1, page_size=10)

        assert result["success"] is False
        assert "not yet implemented" in result["message"]
