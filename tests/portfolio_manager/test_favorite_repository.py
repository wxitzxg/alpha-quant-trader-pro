# tests/portfolio_manager/test_favorite_repository.py
"""FavoriteRepository 单元测试"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.database import Base, StockFavorite
from portfolio_manager.repositories.favorite_repository import FavoriteRepository


@pytest.fixture
def db_session():
    """创建内存数据库用于测试"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """创建 FavoriteRepository 实例"""
    return FavoriteRepository(db_session)


class TestFavoriteRepository:
    """FavoriteRepository 测试"""

    def test_get_by_symbol_found(self, repository, db_session):
        """测试根据 symbol 查找收藏（找到）"""
        favorite = StockFavorite(symbol="600519", tag="自选股", note="贵州茅台")
        db_session.add(favorite)
        db_session.commit()

        result = repository.get_by_symbol("600519")

        assert result is not None
        assert result.symbol == "600519"
        assert result.tag == "自选股"
        assert result.note == "贵州茅台"

    def test_get_by_symbol_not_found(self, repository):
        """测试根据 symbol 查找收藏（未找到）"""
        result = repository.get_by_symbol("999999")

        assert result is None

    def test_get_all(self, repository, db_session):
        """测试获取所有收藏"""
        favorite1 = StockFavorite(symbol="600519", tag="白酒")
        favorite2 = StockFavorite(symbol="000001", tag="银行")
        db_session.add_all([favorite1, favorite2])
        db_session.commit()

        result = repository.get_all()

        assert len(result) == 2
        symbols = [f.symbol for f in result]
        assert "600519" in symbols
        assert "000001" in symbols

    def test_get_all_order_by_created_at_desc(self, repository, db_session):
        """测试获取所有收藏按创建时间倒序"""
        from datetime import datetime, timedelta

        # 明确设置创建时间，确保时间差异
        now = datetime.now()
        favorite1 = StockFavorite(symbol="600519", tag="白酒")
        favorite1.created_at = now - timedelta(seconds=1)  # 更早的时间
        db_session.add(favorite1)
        db_session.commit()

        favorite2 = StockFavorite(symbol="000001", tag="银行")
        favorite2.created_at = now  # 更晚的时间
        db_session.add(favorite2)
        db_session.commit()

        result = repository.get_all()

        # 后添加的（时间更新）应该在前面（按创建时间倒序）
        assert result[0].symbol == "000001"
        assert result[1].symbol == "600519"

    def test_get_all_paginated(self, repository, db_session):
        """测试分页获取收藏"""
        for i in range(15):
            favorite = StockFavorite(symbol=f"60051{i}", tag=f"tag{i}")
            db_session.add(favorite)
        db_session.commit()

        # 第一页
        result_page1 = repository.get_all_paginated(page=1, page_size=10)
        assert len(result_page1) == 10

        # 第二页
        result_page2 = repository.get_all_paginated(page=2, page_size=10)
        assert len(result_page2) == 5

    def test_count(self, repository, db_session):
        """测试统计收藏数量"""
        favorite1 = StockFavorite(symbol="600519", tag="白酒")
        favorite2 = StockFavorite(symbol="000001", tag="银行")
        db_session.add_all([favorite1, favorite2])
        db_session.commit()

        result = repository.count()

        assert result == 2

    def test_count_empty(self, repository):
        """测试空表统计收藏数量"""
        result = repository.count()

        assert result == 0

    def test_exists_by_symbol_true(self, repository, db_session):
        """测试检查股票是否已收藏（存在）"""
        favorite = StockFavorite(symbol="600519", tag="自选股")
        db_session.add(favorite)
        db_session.commit()

        result = repository.exists_by_symbol("600519")

        assert result is True

    def test_exists_by_symbol_false(self, repository):
        """测试检查股票是否已收藏（不存在）"""
        result = repository.exists_by_symbol("999999")

        assert result is False

    def test_inherited_methods(self, repository, db_session):
        """测试从 BaseRepository 继承的方法"""
        # 测试 add 方法
        favorite = StockFavorite(symbol="600519", tag="自选股", note="测试")
        repository.add(favorite)
        db_session.commit()

        # 测试 get 方法
        result = repository.get(favorite.id)
        assert result is not None
        assert result.symbol == "600519"

        # 测试 delete 方法
        repository.delete(favorite)
        db_session.commit()

        result = repository.get(favorite.id)
        assert result is None
