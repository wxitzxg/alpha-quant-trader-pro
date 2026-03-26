"""股票收藏数据仓库层"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from common.repositories.base import BaseRepository
from portfolio_manager.database import StockFavorite


class FavoriteRepository(BaseRepository[StockFavorite]):
    """股票收藏仓库"""

    def __init__(self, session: Session):
        super().__init__(session, StockFavorite)

    def get_by_symbol(self, symbol: str) -> Optional[StockFavorite]:
        """根据股票代码获取收藏"""
        return self.get_by(symbol=symbol)

    def get_all(self) -> List[StockFavorite]:
        """获取所有收藏（按创建时间倒序）"""
        stmt = select(StockFavorite).order_by(StockFavorite.created_at.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> List[StockFavorite]:
        """分页获取收藏（按创建时间倒序）"""
        offset = (page - 1) * page_size
        stmt = (
            select(StockFavorite)
            .order_by(StockFavorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def count(self) -> int:
        """获取收藏总数"""
        stmt = select(func.count(StockFavorite.id))
        result = self.session.execute(stmt).scalar()
        return result or 0

    def exists(self, symbol: str) -> bool:
        """检查股票是否已收藏"""
        return self.get_by_symbol(symbol) is not None
