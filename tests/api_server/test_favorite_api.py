#!/usr/bin/env python3
"""股票收藏 API 集成测试"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from api_server.main import app
from tests.api_server.test_utils import (
    TEST_STOCK_CODE,
    assert_success_response
)


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端"""
    test_client = TestClient(app)
    test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
    return test_client


def create_mock_favorite(
    symbol: str = "600519",
    tag: str = None,
    note: str = None
) -> Mock:
    """创建收藏数据的 mock"""
    mock_favorite = Mock()
    mock_favorite.symbol = symbol
    mock_favorite.tag = tag
    mock_favorite.note = note
    mock_favorite.created_at = datetime.now()
    mock_favorite.updated_at = datetime.now()
    mock_favorite.model_dump = lambda: {
        "symbol": symbol,
        "tag": tag,
        "note": note,
        "created_at": mock_favorite.created_at.isoformat(),
        "updated_at": mock_favorite.updated_at.isoformat()
    }
    return mock_favorite


class TestFavoriteAPI:
    """收藏 API 测试"""

    # ========== 获取收藏列表测试 ==========
    def test_get_favorites_success(self, client: TestClient) -> None:
        """测试获取收藏列表 - 成功"""
        mock_favorite = create_mock_favorite(symbol="600519", tag="自选股")

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_paginated.return_value = ([mock_favorite], 1, 1)
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/portfolio/favorites")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert "favorites" in data["data"]
            assert data["data"]["total"] == 1
            assert data["data"]["page"] == 1
            assert data["data"]["total_pages"] == 1

    def test_get_favorites_empty(self, client: TestClient) -> None:
        """测试获取收藏列表 - 空列表"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_paginated.return_value = ([], 0, 0)
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/portfolio/favorites")

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["total"] == 0
            assert len(data["data"]["favorites"]) == 0

    def test_get_favorites_pagination(self, client: TestClient) -> None:
        """测试获取收藏列表 - 分页"""
        favorites = [
            create_mock_favorite(symbol=f"60051{i}", tag=f"标签{i}")
            for i in range(10)
        ]

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_paginated.return_value = (favorites, 50, 5)
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/portfolio/favorites?page=2&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 50
            assert data["data"]["page"] == 2
            assert data["data"]["total_pages"] == 5
            assert len(data["data"]["favorites"]) == 10

    # ========== 添加收藏测试 ==========
    def test_add_favorite_success(self, client: TestClient) -> None:
        """测试添加收藏 - 成功"""
        mock_favorite = create_mock_favorite(symbol="600519", tag="自选股", note="测试备注")

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.add_favorite.return_value = mock_favorite
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/add",
                json={"symbol": "600519", "tag": "自选股", "note": "测试备注"}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == "600519"
            assert data["data"]["tag"] == "自选股"
            assert data["data"]["note"] == "测试备注"

    def test_add_duplicate_favorite(self, client: TestClient) -> None:
        """测试重复添加收藏"""
        from common.exceptions import BusinessError

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.add_favorite.side_effect = BusinessError("股票已收藏")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/add",
                json={"symbol": "600519"}
            )

            assert response.status_code == 400

    def test_add_favorite_minimal(self, client: TestClient) -> None:
        """测试添加收藏 - 最小参数"""
        mock_favorite = create_mock_favorite(symbol="600519")

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.add_favorite.return_value = mock_favorite
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/add",
                json={"symbol": "600519"}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == "600519"

    # ========== 移除收藏测试 ==========
    def test_remove_favorite_success(self, client: TestClient) -> None:
        """测试移除收藏 - 成功"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.remove_favorite.return_value = None
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/remove",
                json={"symbol": "600519"}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == "600519"

    def test_remove_favorite_not_found(self, client: TestClient) -> None:
        """测试移除不存在的收藏"""
        from common.exceptions import NotFoundError

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.remove_favorite.side_effect = NotFoundError("Favorite", "999999")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/remove",
                json={"symbol": "999999"}
            )

            assert response.status_code == 404

    # ========== 更新收藏测试 ==========
    def test_update_favorite_success(self, client: TestClient) -> None:
        """测试更新收藏 - 成功"""
        mock_favorite = create_mock_favorite(symbol="600519", tag="新标签", note="新备注")

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.update_favorite.return_value = mock_favorite
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/update",
                json={"symbol": "600519", "tag": "新标签", "note": "新备注"}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == "600519"
            assert data["data"]["tag"] == "新标签"
            assert data["data"]["note"] == "新备注"

    def test_update_favorite_not_found(self, client: TestClient) -> None:
        """测试更新不存在的收藏"""
        from common.exceptions import NotFoundError

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.update_favorite.side_effect = NotFoundError("Favorite", "999999")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/update",
                json={"symbol": "999999", "tag": "新标签"}
            )

            assert response.status_code == 404

    def test_update_favorite_business_error(self, client: TestClient) -> None:
        """测试更新收藏 - 业务错误"""
        from common.exceptions import BusinessError

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.update_favorite.side_effect = BusinessError("无效的标签")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/update",
                json={"symbol": "600519", "tag": "无效标签"}
            )

            assert response.status_code == 400

    def test_update_favorite_partial(self, client: TestClient) -> None:
        """测试更新收藏 - 部分更新"""
        mock_favorite = create_mock_favorite(symbol="600519", tag="新标签", note=None)

        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.update_favorite.return_value = mock_favorite
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/update",
                json={"symbol": "600519", "tag": "新标签"}
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == "600519"
            assert data["data"]["tag"] == "新标签"

    # ========== 异常处理测试 ==========
    def test_get_favorites_exception(self, client: TestClient) -> None:
        """测试获取收藏列表 - 异常"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Database error")

            response = client.get("/api/v1/portfolio/favorites")

            assert response.status_code == 500

    def test_add_favorite_exception(self, client: TestClient) -> None:
        """测试添加收藏 - 异常"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.add_favorite.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/add",
                json={"symbol": "600519"}
            )

            assert response.status_code == 500

    def test_remove_favorite_exception(self, client: TestClient) -> None:
        """测试移除收藏 - 异常"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.remove_favorite.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/remove",
                json={"symbol": "600519"}
            )

            assert response.status_code == 500

    def test_update_favorite_exception(self, client: TestClient) -> None:
        """测试更新收藏 - 异常"""
        with patch('api_server.routers.portfolio._get_favorite_service') as mock_get_service:
            mock_service = Mock()
            mock_service.update_favorite.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/portfolio/favorites/update",
                json={"symbol": "600519", "tag": "新标签"}
            )

            assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
