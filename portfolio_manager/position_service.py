# portfolio_manager/position_service.py
"""
持仓管理服务（重构版 - 使用 Repository 模式）
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from portfolio_manager.database import Position
from portfolio_manager.models import PositionModel
from portfolio_manager.repositories import PositionRepository
from common.exceptions import NotFoundError, BusinessError


class PositionService:
    """持仓管理服务"""

    def __init__(self, repository: PositionRepository, data_source_aggregator=None):
        """
        初始化持仓服务

        Args:
            repository: 持仓仓库（依赖注入）
            data_source_aggregator: 底层数据源聚合器（可选）
        """
        self.repo = repository
        self.data_source = data_source_aggregator

    def add_position(
        self,
        symbol: str,
        quantity: int,
        cost_price: float,
        current_price: Optional[float] = None
    ) -> PositionModel:
        """
        新增持仓股

        成本价支持负数：高位卖出留底仓时，盈利收入可能大于成本，
        导致剩余仓位成本为负

        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价（支持负数）
            current_price: 当前价格（可选，未提供则从数据源获取）

        Returns:
            PositionModel

        Raises:
            BusinessError: 持仓已存在
        """
        # 检查是否已存在
        existing = self.repo.get_by_symbol(symbol)
        if existing:
            raise BusinessError(f"持仓 {symbol} 已存在", context={"symbol": symbol})

        # 如果未提供现价，从数据源获取
        if current_price is None and self.data_source:
            try:
                quote = self.data_source.get_realtime(symbol)
                if quote:
                    current_price = quote.price
            except Exception as e:
                # 数据源异常，使用 None
                pass

        # 创建持仓记录
        position = Position(
            symbol=symbol,
            quantity=quantity,
            cost_price=Decimal(str(cost_price)),
            current_price=Decimal(str(current_price)) if current_price else None
        )

        # 计算指标
        position.calculate_metrics()

        # 保存到数据库
        self.repo.add(position)

        return self._to_pydantic(position)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> PositionModel:
        """
        更新持仓股（支持部分字段更新）

        Args:
            symbol: 股票代码
            quantity: 持仓数量（可选）
            cost_price: 成本价（可选）
            current_price: 当前价格（可选）

        Returns:
            PositionModel

        Raises:
            NotFoundError: 持仓不存在
        """
        position = self.repo.get_by_symbol(symbol)
        if not position:
            raise NotFoundError("Position", symbol)

        # 更新字段
        if quantity is not None:
            position.quantity = quantity
        if cost_price is not None:
            position.cost_price = Decimal(str(cost_price))
        if current_price is not None:
            position.current_price = Decimal(str(current_price))

        # 重新计算指标
        position.calculate_metrics()

        return self._to_pydantic(position)

    def get_position(self, symbol: str) -> Optional[PositionModel]:
        """
        获取单只持仓股

        Args:
            symbol: 股票代码

        Returns:
            PositionModel 或 None
        """
        position = self.repo.get_by_symbol(symbol)
        if not position:
            return None

        # 刷新现价（如果数据源可用）
        if self.data_source:
            try:
                quote = self.data_source.get_realtime(symbol)
                if quote and quote.price:
                    position.current_price = Decimal(str(quote.price))
                    position.calculate_metrics()
            except Exception:
                # 数据源异常，使用现有价格
                pass

        return self._to_pydantic(position)

    def get_all_positions(self) -> List[PositionModel]:
        """
        获取持仓股列表

        Returns:
            PositionModel 列表
        """
        positions = self.repo.get_all_active()

        # 如果有数据源，批量刷新现价
        if self.data_source and positions:
            symbols = [p.symbol for p in positions]
            try:
                quotes = self.data_source.batch_get_realtime(symbols)
                quote_map = {q.symbol: q.price for q in quotes}

                for position in positions:
                    if position.symbol in quote_map and quote_map[position.symbol]:
                        position.current_price = Decimal(str(quote_map[position.symbol]))
                        position.calculate_metrics()
            except Exception:
                # 批量获取失败，使用现有价格
                pass

        return [self._to_pydantic(p) for p in positions]

    def _to_pydantic(self, position: Position) -> PositionModel:
        """转换为 Pydantic 模型"""
        return PositionModel(
            symbol=position.symbol,
            quantity=position.quantity,
            cost_price=float(position.cost_price),
            current_price=float(position.current_price) if position.current_price else None,
            market_value=float(position.market_value),
            cost_value=float(position.cost_value),
            floating_pl=float(position.floating_pl),
            position_ratio=0.0,  # 需要在 AccountService 中计算
            last_updated=position.last_updated
        )
