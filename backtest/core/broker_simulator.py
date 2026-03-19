"""Broker Simulator - 经纪商模拟器"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """订单执行结果"""
    symbol: str
    direction: str  # 'buy' or 'sell'
    quantity: int
    requested_price: float
    actual_price: float
    slippage: float
    commission: float
    total_cost: float


class BrokerSimulator:
    """
    经纪商模拟器
    """

    def __init__(
        self,
        commission_rate: float = 0.00025,  # 万分之2.5
        slippage_rate: float = 0.001,       # 千分之1滑点
        stamp_duty_rate: float = 0.001      # 千分之1印花税 (卖出)
    ):
        """
        初始化经纪商模拟器

        Args:
            commission_rate: 手续费率
            slippage_rate: 滑点率
            stamp_duty_rate: 印花税率
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.stamp_duty_rate = stamp_duty_rate

    def calculate_commission(self, amount: float) -> float:
        """
        计算手续费

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        return amount * self.commission_rate

    def apply_slippage(self, price: float, direction: str) -> float:
        """
        应用滑点

        Args:
            price: 原始价格
            direction: 交易方向 ('buy' or 'sell')

        Returns:
            调整后的价格
        """
        if direction == 'buy':
            return price * (1 + self.slippage_rate)
        elif direction == 'sell':
            return price * (1 - self.slippage_rate)
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def execute_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        direction: str  # 'buy' or 'sell'
    ) -> ExecutionResult:
        """
        执行订单

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            direction: 交易方向

        Returns:
            ExecutionResult: 执行结果
        """
        # 应用滑点
        actual_price = self.apply_slippage(price, direction)
        slippage = abs(actual_price - price)

        # 计算手续费
        amount = actual_price * quantity
        commission = self.calculate_commission(amount)

        # 卖出时计算印花税
        stamp_duty = 0.0
        if direction == 'sell':
            stamp_duty = amount * self.stamp_duty_rate

        # 总成本 (佣金 + 印花税)
        total_cost = commission + stamp_duty

        return ExecutionResult(
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            requested_price=price,
            actual_price=actual_price,
            slippage=slippage,
            commission=commission,
            total_cost=total_cost
        )
