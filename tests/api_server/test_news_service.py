#!/usr/bin/env python3
"""测试新闻资讯服务层"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from datetime import datetime

from api_server.services.news_service import NewsService
from .test_utils import (
    TEST_STOCK_NAME,
    PAGE_SIZE_DEFAULT,
    TEST_START_DATE,
    TEST_END_DATE,
    assert_error_response
)


class TestNewsService:
    """新闻资讯服务层测试"""

    @pytest.fixture
    def service(self) -> NewsService:
        """创建服务实例"""
        return NewsService()

    def test_get_news_list_not_implemented(self, service: NewsService) -> None:
        """测试获取新闻列表 - 未实现"""
        result = service.get_news_list(
            page=1,
            page_size=PAGE_SIZE_DEFAULT,
            category="财经",
            start_date="2024-03-01",
            end_date="2024-03-31"
        )

        assert result["success"] is False
        assert result["message"] == "News list feature not yet implemented"

    def test_get_news_detail_not_implemented(self, service: NewsService) -> None:
        """测试获取新闻详情 - 未实现"""
        result = service.get_news_detail(news_id="test_news_001")

        assert result["success"] is False
        assert result["message"] == "News detail feature not yet implemented"

    def test_search_news_not_implemented(self, service: NewsService) -> None:
        """测试搜索新闻 - 未实现"""
        result = service.search_news(query=TEST_STOCK_NAME, page=1, page_size=10)

        assert result["success"] is False
        assert result["message"] == "News search feature not yet implemented"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
