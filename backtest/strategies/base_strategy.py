"""Base Strategy - 策略基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Signal:
    """
    交易信号

    Attributes:
        symbol: 股票代码
        date: 信号日期
        action: 交易动作 ("BUY", "SELL", "HOLD", "COVER")
        price: 交易价格
        quantity: 交易数量 (可选)
        position_size: 仓位比例 (0-1) (可选)
        reason: 信号原因 (可选)
    """
    symbol: str
    date: str
    action: str  # "BUY", "SELL", "HOLD", "COVER"
    price: float
    quantity: Optional[int] = None
    position_size: Optional[float] = None  # 仓位比例 (0-1)
    reason: Optional[str] = None  # 信号原因

    def __post_init__(self):
        """设置默认值"""
        if self.position_size is None:
            self.position_size = 0.1  # Default position size 10%


class BaseStrategy(ABC):
    """
    策略基类

    所有策略必须继承此类并实现 on_data 方法
    """

    @abstractmethod
    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        处理当日数据，生成交易信号

        Args:
            symbol: 股票代码
            data: K线数据 {open, high, low, close, volume, ...}
            date: 日期

        Returns:
            Signal: 交易信号
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取策略名称

        Returns:
            策略名称
        """
        pass

    def get_position_size(self, total_capital: float) -> float:
        """
        计算建议仓位 (0-1)

        Args:
            total_capital: 总资金

        Returns:
            仓位比例
        """
        # 默认返回 10% 仓位
        return 0.1

    def __str__(self) -> str:
        """字符串表示"""
        return self.get_name()

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"<{self.__class__.__name__}: {self.get_name()}>"
