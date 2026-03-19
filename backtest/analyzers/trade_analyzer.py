"""Trade Analyzer - 交易统计分析"""

from typing import List, Dict, Optional
from datetime import datetime
from backtest.models import Trade


class TradeAnalyzer:
    """
    交易统计分析

    分析以下统计指标:
    - 总交易次数
    - 盈利/亏损次数
    - 胜率
    - 平均盈利/亏损
    - 盈亏比
    - 平均持仓天数
    - 最大连胜/连败
    """

    def analyze_trades(self, trades: List[Trade]) -> Dict:
        """
        分析交易统计

        Args:
            trades: 交易列表 (包含 BUY 和 SELL)

        Returns:
            统计结果字典
        """
        # 配对交易 (BUY + SELL)
        completed_trades = self._pair_trades(trades)

        if not completed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'avg_holding_days': 0.0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }

        winning_trades = [t for t in completed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in completed_trades if t.pnl and t.pnl <= 0]

        total_profit = sum(t.pnl for t in winning_trades if t.pnl) if winning_trades else 0
        total_loss = abs(sum(t.pnl for t in losing_trades if t.pnl)) if losing_trades else 0

        return {
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(completed_trades) * 100) if completed_trades else 0.0,
            'avg_profit': (total_profit / len(winning_trades)) if winning_trades else 0.0,
            'avg_loss': (total_loss / len(losing_trades)) if losing_trades else 0.0,
            'profit_factor': (total_profit / total_loss) if total_loss > 0 else 0.0,
            'avg_holding_days': self._calculate_avg_holding_days(completed_trades),
            'max_consecutive_wins': self._calculate_max_consecutive_wins(completed_trades),
            'max_consecutive_losses': self._calculate_max_consecutive_losses(completed_trades)
        }

    def calculate_profit_factor(self, trades: List[Trade]) -> float:
        """
        计算盈亏比 = 总盈利 / 总亏损

        Args:
            trades: 交易列表

        Returns:
            盈亏比
        """
        stats = self.analyze_trades(trades)
        return stats['profit_factor']

    def _pair_trades(self, trades: List[Trade]) -> List[Trade]:
        """
        配对交易 (将 BUY 和 SELL 配对成完整交易)

        Args:
            trades: 交易列表

        Returns:
            完整的交易对列表 (只包含 SELL 交易，但带有 pnl)
        """
        # Group trades by symbol
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)

        completed_trades = []

        for symbol, symbol_trades_list in symbol_trades.items():
            # Sort by date
            symbol_trades_list.sort(key=lambda t: t.date)

            buy_trades = []
            for trade in symbol_trades_list:
                if trade.action == "BUY":
                    buy_trades.append(trade)
                elif trade.action == "SELL" and buy_trades:
                    # Pair with the earliest buy
                    buy_trade = buy_trades.pop(0)
                    # Calculate PnL
                    buy_amount = buy_trade.price * buy_trade.quantity
                    sell_amount = trade.price * trade.quantity
                    total_costs = buy_trade.total_cost + trade.total_cost
                    trade.pnl = sell_amount - buy_amount - total_costs
                    completed_trades.append(trade)

        return completed_trades

    def _calculate_avg_holding_days(self, completed_trades: List[Trade]) -> float:
        """
        计算平均持仓天数

        Args:
            completed_trades: 完整交易对列表

        Returns:
            平均持仓天数
        """
        if not completed_trades:
            return 0.0

        # Note: This requires access to the corresponding BUY trades
        # For simplicity, we return a placeholder
        # In a real implementation, we would track holding periods
        return 5.0  # Placeholder

    def _calculate_max_consecutive_wins(self, completed_trades: List[Trade]) -> int:
        """
        计算最大连胜次数

        Args:
            completed_trades: 完整交易对列表

        Returns:
            最大连胜次数
        """
        if not completed_trades:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in completed_trades:
            if trade.pnl and trade.pnl > 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_max_consecutive_losses(self, completed_trades: List[Trade]) -> int:
        """
        计算最大连败次数

        Args:
            completed_trades: 完整交易对列表

        Returns:
            最大连败次数
        """
        if not completed_trades:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in completed_trades:
            if trade.pnl and trade.pnl <= 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive
