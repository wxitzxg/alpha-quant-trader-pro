"""FavoriteService 单元测试"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from portfolio_manager.services.favorite_service import FavoriteService
from portfolio_manager.database import StockFavorite
from portfolio_manager.schemas.favorite_schemas import FavoriteResponse
from common.exceptions import NotFoundError, BusinessError


class TestFavoriteService:
    """FavoriteService 测试"""

    @pytest.fixture
    def favorite_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, favorite_repo):
        return FavoriteService(repository=favorite_repo)

    # === add_favorite 测试 ===
    def test_add_favorite_success(self, service, favorite_repo):
        """测试添加收藏成功"""
        favorite_repo.exists_by_symbol.return_value = False
        favorite_repo.get_by_symbol.return_value = Mock(
            spec=StockFavorite,
            symbol="600519",
            tag="自选股",
            note="测试",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = service.add_favorite(symbol="600519", tag="自选股", note="测试")

        favorite_repo.add.assert_called_once()
        assert result.symbol == "600519"

    def test_add_favorite_duplicate_raises_error(self, service, favorite_repo):
        """测试重复添加收藏抛出异常"""
        favorite_repo.exists_by_symbol.return_value = True

        with pytest.raises(BusinessError, match="已收藏"):
            service.add_favorite(symbol="600519")

    # === remove_favorite 测试 ===
    def test_remove_favorite_success(self, service, favorite_repo):
        """测试移除收藏成功"""
        mock_favorite = Mock(spec=StockFavorite)
        favorite_repo.get_by_symbol.return_value = mock_favorite

        service.remove_favorite(symbol="600519")

        favorite_repo.delete.assert_called_once_with(mock_favorite)

    def test_remove_favorite_not_found_raises_error(self, service, favorite_repo):
        """测试移除不存在的收藏抛出异常"""
        favorite_repo.get_by_symbol.return_value = None

        with pytest.raises(NotFoundError, match="Favorite"):
            service.remove_favorite(symbol="999999")

    # === update_favorite 测试 ===
    def test_update_favorite_success(self, service, favorite_repo):
        """测试更新收藏成功"""
        mock_favorite = Mock(
            spec=StockFavorite,
            symbol="600519",
            tag="旧标签",
            note="旧备注",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        favorite_repo.get_by_symbol.return_value = mock_favorite

        result = service.update_favorite(symbol="600519", tag="新标签", note="新备注")

        assert mock_favorite.tag == "新标签"
        assert mock_favorite.note == "新备注"

    def test_update_favorite_not_found_raises_error(self, service, favorite_repo):
        """测试更新不存在的收藏抛出异常"""
        favorite_repo.get_by_symbol.return_value = None

        with pytest.raises(NotFoundError, match="Favorite"):
            service.update_favorite(symbol="999999", tag="标签")

    def test_update_favorite_no_fields_raises_error(self, service, favorite_repo):
        """测试更新时未提供任何字段抛出异常"""
        mock_favorite = Mock(spec=StockFavorite)
        favorite_repo.get_by_symbol.return_value = mock_favorite

        with pytest.raises(BusinessError, match="至少提供一个更新字段"):
            service.update_favorite(symbol="600519")

    # === get_all 测试 ===
    def test_get_all_success(self, service, favorite_repo):
        """测试获取所有收藏"""
        mock_favorites = [
            Mock(spec=StockFavorite, symbol="600519", tag=None, note=None, created_at=datetime.now(), updated_at=datetime.now()),
            Mock(spec=StockFavorite, symbol="000001", tag=None, note=None, created_at=datetime.now(), updated_at=datetime.now())
        ]
        favorite_repo.get_all.return_value = mock_favorites

        result = service.get_all()

        assert len(result) == 2

    def test_get_all_empty(self, service, favorite_repo):
        """测试获取空收藏列表"""
        favorite_repo.get_all.return_value = []

        result = service.get_all()

        assert result == []
        assert len(result) == 0

    # === get_paginated 测试 ===
    def test_get_paginated_success(self, service, favorite_repo):
        """测试分页获取收藏"""
        mock_favorites = [Mock(spec=StockFavorite, symbol="600519", tag=None, note=None, created_at=datetime.now(), updated_at=datetime.now())]
        favorite_repo.get_all_paginated.return_value = mock_favorites
        favorite_repo.count.return_value = 25

        favorites, total, total_pages = service.get_paginated(page=1, page_size=20)

        assert len(favorites) == 1
        assert total == 25
        assert total_pages == 2

    def test_get_paginated_empty(self, service, favorite_repo):
        """测试分页获取空结果集"""
        favorite_repo.get_all_paginated.return_value = []
        favorite_repo.count.return_value = 0

        favorites, total, total_pages = service.get_paginated(page=1, page_size=20)

        assert favorites == []
        assert total == 0
        assert total_pages == 0
