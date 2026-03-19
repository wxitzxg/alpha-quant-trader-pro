"""Position Tracker - 持仓跟踪器"""

from typing import Dict, Optional
from dataclasses import dataclass
from backtest.exceptions import InsufficientFundsError, InsufficientSharesError


@dataclass
class Position:
    """持仓信息 (内部使用)"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float = 0.0
    entry_date: Optional[str] = None


class PositionTracker:
    """
    持仓跟踪器 - 复用 PortfolioCommands 逻辑
    """

    def __init__(self, initial_capital: float):
        """
        初始化持仓跟踪器

        Args:
            initial_capital: 初始资金
        """
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}

    def buy(self, symbol: str, quantity: int, price: float) -> bool:
        """
        买入股票

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格

        Returns:
            bool: 是否成功

        Raises:
            InsufficientFundsError: 资金不足
        """
        total_cost = quantity * price

        if self.cash < total_cost:
            raise InsufficientFundsError(
                f"Insufficient funds: need {total_cost}, have {self.cash}"
            )

        if symbol in self.positions:
            # 加仓 - 更新成本价 (加权平均)
            existing = self.positions[symbol]
            new_cost_price = (
                existing.cost_price * existing.quantity + price * quantity
            ) / (existing.quantity + quantity)

            existing.quantity += quantity
            existing.cost_price = new_cost_price
        else:
            # 新建持仓
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=price
            )

        self.cash -= total_cost
        return True

    def sell(self, symbol: str, quantity: int, price: float) -> bool:
        """
        卖出股票

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            bool: 是否成功

        Raises:
            InsufficientSharesError: 持仓不足
        """
        if symbol not in self.positions:
            raise InsufficientSharesError(f"No position for {symbol}")

        position = self.positions[symbol]

        if position.quantity < quantity:
            raise InsufficientSharesError(
                f"Insufficient shares: need {quantity}, have {position.quantity}"
            )

        # 更新持仓
        position.quantity -= quantity
        if position.quantity == 0:
            del self.positions[symbol]

        # 增加现金
        self.cash += quantity * price
        return True

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            Position or None
        """
        return self.positions.get(symbol)

    def update_market_value(self, symbol: str, current_price: float):
        """
        更新持仓市值

        Args:
            symbol: 股票代码
            current_price: 当前价格
        """
        if symbol in self.positions:
            self.positions[symbol].market_price = current_price

    def get_total_value(self) -> float:
        """
        获取总资产 (现金 + 股票市值)

        Returns:
            总资产
        """
        stock_value = sum(
            p.market_price * p.quantity if p.market_price > 0 else p.cost_price * p.quantity
            for p in self.positions.values()
        )
        return self.cash + stock_value

    def get_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓

        Returns:
            持仓字典
        """
        return self.positions.copy()
