#!/usr/bin/env python3
"""模拟交易服务"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


class Position:
    """持仓类"""

    def __init__(self, symbol: str, quantity: int, cost_price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.cost_price = cost_price
        self.entry_date = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self, market_price: float):
        """转换为字典"""
        market_value = market_price * self.quantity
        floating_pl = (market_price - self.cost_price) * self.quantity
        floating_pl_pct = (floating_pl / (self.cost_price * self.quantity)) * 100 if self.quantity > 0 else 0

        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "cost_price": self.cost_price,
            "market_price": market_price,
            "market_value": market_value,
            "floating_pl": floating_pl,
            "floating_pl_pct": floating_pl_pct,
            "entry_date": self.entry_date
        }


class Trade:
    """交易类"""

    def __init__(
        self,
        account_id: str,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        commission: float,
        pnl: Optional[float] = None
    ):
        self.trade_id = f"trade_{uuid.uuid4().hex[:8]}"
        self.account_id = account_id
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.amount = price * quantity
        self.commission = commission
        self.pnl = pnl
        self.timestamp = datetime.now()

    def to_dict(self):
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "account_id": self.account_id,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "amount": self.amount,
            "commission": self.commission,
            "pnl": self.pnl,
            "timestamp": self.timestamp.isoformat()
        }


class SimulationAccount:
    """模拟账户类"""

    def __init__(
        self,
        account_name: str,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025
    ):
        self.account_id = f"sim_{int(datetime.now().timestamp())}"
        self.account_name = account_name
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.available_cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def buy(self, symbol: str, price: float, quantity: int) -> Trade:
        """买入"""
        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_cost = total_amount + commission

        if self.available_cash < total_cost:
            raise ValueError(
                f"余额不足，需要 {total_cost:.2f}，当前可用 {self.available_cash:.2f}"
            )

        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_cost_price = (pos.cost_price * pos.quantity + total_amount) / new_quantity
            pos.quantity = new_quantity
            pos.cost_price = new_cost_price
        else:
            self.positions[symbol] = Position(symbol, quantity, price)

        # 更新账户
        self.available_cash -= total_cost
        self.current_balance -= total_cost

        # 记录交易
        trade = Trade(self.account_id, symbol, "buy", price, quantity, commission)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

    def sell(self, symbol: str, price: float, quantity: int) -> Trade:
        """卖出"""
        if symbol not in self.positions:
            raise ValueError(f"没有持仓 {symbol}")

        pos = self.positions[symbol]
        if pos.quantity < quantity:
            raise ValueError(f"持仓不足，当前 {pos.quantity}，卖出 {quantity}")

        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_revenue = total_amount - commission

        # 计算盈亏
        pnl = (price - pos.cost_price) * quantity

        # 更新持仓
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]

        # 更新账户
        self.available_cash += total_revenue
        self.current_balance += total_revenue

        # 记录交易
        trade = Trade(self.account_id, symbol, "sell", price, quantity, commission, pnl)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

    def get_positions(self, market_prices: Dict[str, float]) -> dict:
        """获取持仓列表"""
        positions = []
        total_market_value = 0
        total_floating_pl = 0

        for symbol, pos in self.positions.items():
            market_price = market_prices.get(symbol, pos.cost_price)
            pos_dict = pos.to_dict(market_price)
            positions.append(pos_dict)
            total_market_value += pos_dict["market_value"]
            total_floating_pl += pos_dict["floating_pl"]

        total_floating_pl_pct = (
            (total_floating_pl / self.initial_capital) * 100
            if self.initial_capital > 0 else 0
        )

        return {
            "account_id": self.account_id,
            "positions": positions,
            "total_market_value": total_market_value,
            "total_floating_pl": total_floating_pl,
            "total_floating_pl_pct": total_floating_pl_pct
        }

    def to_dict(self, market_prices: Dict[str, float] = None) -> dict:
        """转换为字典"""
        # 计算总市值和浮动盈亏
        total_market_value = 0
        total_floating_pl = 0

        if market_prices:
            for symbol, pos in self.positions.items():
                market_price = market_prices.get(symbol, pos.cost_price)
                market_value = market_price * pos.quantity
                floating_pl = (market_price - pos.cost_price) * pos.quantity
                total_market_value += market_value
                total_floating_pl += floating_pl

        total_value = self.available_cash + total_market_value
        floating_pl = total_floating_pl
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100

        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "initial_capital": self.initial_capital,
            "current_balance": self.current_balance,
            "available_cash": self.available_cash,
            "total_value": total_value,
            "floating_pl": floating_pl,
            "total_return": total_return,
            "positions_count": len(self.positions),
            "commission_rate": self.commission_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SimulationService:
    """模拟交易服务"""

    def __init__(self):
        self.accounts: Dict[str, SimulationAccount] = {}
        # 模拟市场价格（实际应该从数据源获取）
        self.market_prices: Dict[str, float] = {}

    def set_market_price(self, symbol: str, price: float):
        """设置市场价格（测试用）"""
        self.market_prices[symbol] = price

    def create_account(
        self,
        account_name: str,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025
    ) -> SimulationAccount:
        """创建账户"""
        account = SimulationAccount(account_name, initial_capital, commission_rate)
        self.accounts[account.account_id] = account
        return account

    def get_account(self, account_id: str) -> SimulationAccount:
        """获取账户"""
        if account_id not in self.accounts:
            raise ValueError(f"账户 {account_id} 不存在")
        return self.accounts[account_id]

    def list_accounts(self) -> List[SimulationAccount]:
        """获取所有账户"""
        return list(self.accounts.values())

    def delete_account(self, account_id: str):
        """删除账户"""
        if account_id in self.accounts:
            del self.accounts[account_id]

    def buy(
        self,
        account_id: str,
        symbol: str,
        price: float,
        quantity: int
    ) -> Trade:
        """买入"""
        account = self.get_account(account_id)
        # 如果没有设置市场价格，使用交易价格
        if symbol not in self.market_prices:
            self.market_prices[symbol] = price
        return account.buy(symbol, price, quantity)

    def sell(
        self,
        account_id: str,
        symbol: str,
        price: float,
        quantity: int
    ) -> Trade:
        """卖出"""
        account = self.get_account(account_id)
        if symbol not in self.market_prices:
            self.market_prices[symbol] = price
        return account.sell(symbol, price, quantity)

    def get_positions(self, account_id: str) -> dict:
        """获取持仓"""
        account = self.get_account(account_id)
        return account.get_positions(self.market_prices)

    def get_trades(self, account_id: str, limit: int = 20) -> dict:
        """获取交易历史"""
        account = self.get_account(account_id)
        trades = [t.to_dict() for t in account.trades[-limit:]]

        # 统计
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losing_trades = sum(1 for t in trades if t.get("pnl", 0) < 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)

        return {
            "account_id": account_id,
            "trades": trades,
            "total_count": len(account.trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_pnl": total_pnl
        }
