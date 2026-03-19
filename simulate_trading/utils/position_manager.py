"""
持仓管理辅助类 - 用于策略内部管理虚拟持仓
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
import json
import os


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: int
    cost_price: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price

    @property
    def cost_value(self) -> float:
        """持仓成本"""
        return self.quantity * self.cost_price

    @property
    def profit(self) -> float:
        """浮动盈亏"""
        return self.market_value - self.cost_value

    @property
    def profit_pct(self) -> float:
        """盈亏比例"""
        if self.cost_value == 0:
            return 0.0
        return self.profit / self.cost_value


class PositionManager:
    """
    持仓管理器 - 在内存中管理策略的虚拟持仓

    注意：这只是一个辅助类，真实持仓应使用 portfolio_manager
    """

    def __init__(self, strategy_name: str, storage_path: Optional[str] = None):
        self.strategy_name = strategy_name
        self.positions: Dict[str, Position] = {}
        self.storage_path = storage_path or f".positions_{strategy_name}.json"
        self._load_positions()

    def add_position(self, symbol: str, quantity: int, price: float):
        """新增或增加持仓"""
        if symbol in self.positions:
            # 已有持仓，计算加权平均成本
            old_pos = self.positions[symbol]
            old_value = old_pos.cost_value
            new_value = quantity * price
            total_quantity = old_pos.quantity + quantity
            total_value = old_value + new_value

            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=total_quantity,
                cost_price=total_value / total_quantity,
                current_price=price
            )
        else:
            # 新增持仓
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=price,
                current_price=price
            )

    def reduce_position(self, symbol: str, quantity: int):
        """减少持仓"""
        if symbol not in self.positions:
            raise ValueError(f"持仓 {symbol} 不存在")

        position = self.positions[symbol]

        if position.quantity <= quantity:
            # 全部卖出
            del self.positions[symbol]
        else:
            # 部分卖出（成本价不变）
            position.quantity -= quantity
            self.positions[symbol] = position

    def update_price(self, symbol: str, price: float):
        """更新持仓价格"""
        if symbol in self.positions:
            self.positions[symbol].current_price = price

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """获取所有持仓"""
        return self.positions.copy()

    def get_total_value(self) -> float:
        """获取总持仓市值"""
        return sum(pos.market_value for pos in self.positions.values())

    def get_position_count(self) -> int:
        """获取持仓数量"""
        return len(self.positions)

    def _load_positions(self):
        """从文件加载持仓"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for symbol, pos_data in data.items():
                        self.positions[symbol] = Position(**pos_data)
            except Exception as e:
                print(f"加载持仓失败: {e}")

    def _save_positions(self):
        """保存持仓到文件"""
        try:
            data = {
                symbol: {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'cost_price': pos.cost_price,
                    'current_price': pos.current_price
                }
                for symbol, pos in self.positions.items()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存持仓失败: {e}")

    def clear(self):
        """清空所有持仓"""
        self.positions.clear()
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
