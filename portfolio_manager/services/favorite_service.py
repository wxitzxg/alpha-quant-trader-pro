"""
股票收藏管理服务
"""

from typing import List, Tuple, Optional
from datetime import datetime
from portfolio_manager.database import StockFavorite
from portfolio_manager.schemas.favorite_schemas import FavoriteResponse
from common.exceptions import NotFoundError, BusinessError
import math


class FavoriteService:
    """股票收藏管理服务"""

    def __init__(self, repository):
        """
        初始化收藏服务

        Args:
            repository: FavoriteRepository 实例（依赖注入）
        """
        self.repo = repository

    def add_favorite(
        self,
        symbol: str,
        tag: Optional[str] = None,
        note: Optional[str] = None
    ) -> FavoriteResponse:
        """
        添加收藏

        Args:
            symbol: 股票代码
            tag: 标签（可选）
            note: 备注（可选）

        Returns:
            FavoriteResponse

        Raises:
            BusinessError: 股票已收藏
        """
        # 检查是否已收藏
        if self.repo.exists_by_symbol(symbol):
            raise BusinessError(f"股票 {symbol} 已收藏", context={"symbol": symbol})

        # 创建收藏记录
        favorite = StockFavorite(
            symbol=symbol,
            tag=tag,
            note=note
        )

        # 保存到数据库
        self.repo.add(favorite)

        # 重新获取以获取完整数据（包括时间戳）
        saved = self.repo.get_by_symbol(symbol)
        return self._to_response(saved)

    def remove_favorite(self, symbol: str) -> None:
        """
        移除收藏

        Args:
            symbol: 股票代码

        Raises:
            NotFoundError: 收藏不存在
        """
        favorite = self.repo.get_by_symbol(symbol)
        if not favorite:
            raise NotFoundError("Favorite", symbol)

        self.repo.delete(favorite)

    def update_favorite(
        self,
        symbol: str,
        tag: Optional[str] = None,
        note: Optional[str] = None
    ) -> FavoriteResponse:
        """
        更新收藏

        Args:
            symbol: 股票代码
            tag: 新标签（None 表示不修改）
            note: 新备注（None 表示不修改）

        Returns:
            FavoriteResponse

        Raises:
            NotFoundError: 收藏不存在
            BusinessError: 未提供任何更新字段
        """
        # 检查是否提供了更新字段
        if tag is None and note is None:
            raise BusinessError("至少提供一个更新字段（tag 或 note）")

        # 查找收藏
        favorite = self.repo.get_by_symbol(symbol)
        if not favorite:
            raise NotFoundError("Favorite", symbol)

        # 更新字段
        if tag is not None:
            favorite.tag = tag
        if note is not None:
            favorite.note = note

        return self._to_response(favorite)

    def get_all(self) -> List[FavoriteResponse]:
        """
        获取所有收藏

        Returns:
            FavoriteResponse 列表
        """
        favorites = self.repo.get_all()
        return [self._to_response(f) for f in favorites]

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FavoriteResponse], int, int]:
        """
        分页获取收藏

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (favorites, total, total_pages)
        """
        favorites = self.repo.get_all_paginated(page=page, page_size=page_size)
        total = self.repo.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return [self._to_response(f) for f in favorites], total, total_pages

    def _to_response(self, favorite: StockFavorite) -> FavoriteResponse:
        """转换为响应模型"""
        return FavoriteResponse(
            symbol=favorite.symbol,
            tag=favorite.tag,
            note=favorite.note,
            created_at=favorite.created_at or datetime.now(),
            updated_at=favorite.updated_at or datetime.now()
        )
