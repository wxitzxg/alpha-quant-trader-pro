#!/usr/bin/env python3
"""收益统计服务"""

from typing import Dict, List
from datetime import datetime
from .simulation_service import SimulationAccount, SimulationService


class PerformanceService:
    """收益统计服务"""

    def __init__(self, simulation_service: SimulationService):
        self.simulation_service = simulation_service

    def calculate_metrics(self, account: SimulationAccount) -> Dict:
        """计算绩效指标"""
        # 总收益
        total_return = account.current_balance - account.initial_capital
        total_return_pct = (total_return / account.initial_capital) * 100 if account.initial_capital > 0 else 0

        # 年化收益
        days = (datetime.now() - account.created_at).days
        if days < 1:
            days = 1  # 避免除零
        annualized_return = total_return_pct * (365 / days)

        # 交易统计
        sell_trades = [t for t in account.trades if t.action == "sell"]
        total_trades = len(sell_trades)

        winning_trades = sum(1 for t in sell_trades if t.pnl and t.pnl > 0)
        losing_trades = sum(1 for t in sell_trades if t.pnl and t.pnl < 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 盈亏比
        profits = [t.pnl for t in sell_trades if t.pnl and t.pnl > 0]
        losses = [abs(t.pnl) for t in sell_trades if t.pnl and t.pnl < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = avg_profit / avg_loss if avg_loss > 0 else 0

        # 持仓市值和浮动盈亏
        market_prices = self.simulation_service.market_prices
        total_market_value = 0
        total_floating_pl = 0

        for symbol, pos in account.positions.items():
            market_price = market_prices.get(symbol, pos.cost_price)
            market_value = market_price * pos.quantity
            floating_pl = (market_price - pos.cost_price) * pos.quantity
            total_market_value += market_value
            total_floating_pl += floating_pl

        total_value = account.available_cash + total_market_value

        return {
            "total_return": total_return_pct,
            "total_return_amount": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": 0.0,  # 需要历史数据计算
            "volatility": 0.0,     # 需要历史数据计算
            "sharpe_ratio": 0.0,   # 需要历史数据计算
            "sortino_ratio": 0.0,  # 需要历史数据计算
            "calmar_ratio": 0.0,   # 需要历史数据计算
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_holding_days": 0.0,  # 需要持仓历史计算
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_value": total_value,
            "total_market_value": total_market_value,
            "total_floating_pl": total_floating_pl
        }

    def get_account_performance(self, account_id: str) -> Dict:
        """获取账户收益汇总"""
        try:
            account = self.simulation_service.get_account(account_id)
            metrics = self.calculate_metrics(account)

            return {
                "account_id": account_id,
                "metrics": metrics,
                "time_period": {
                    "start_date": account.created_at.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "days": (datetime.now() - account.created_at).days
                }
            }
        except ValueError as e:
            raise ValueError(f"获取账户失败: {str(e)}")

    def get_positions_performance(self, account_id: str) -> Dict:
        """获取持仓收益分析"""
        try:
            account = self.simulation_service.get_account(account_id)
            market_prices = self.simulation_service.market_prices

            positions_analysis = []
            total_cost_basis = 0
            total_current_value = 0

            for symbol, pos in account.positions.items():
                market_price = market_prices.get(symbol, pos.cost_price)
                cost_basis = pos.cost_price * pos.quantity
                current_value = market_price * pos.quantity
                unrealized_pl = (market_price - pos.cost_price) * pos.quantity
                unrealized_pl_pct = (unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0
                days_held = (datetime.now() - datetime.fromisoformat(pos.entry_date)).days or 1
                annualized_return = unrealized_pl_pct * (365 / days_held)

                positions_analysis.append({
                    "symbol": symbol,
                    "quantity": pos.quantity,
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "unrealized_pl": unrealized_pl,
                    "unrealized_pl_pct": unrealized_pl_pct,
                    "days_held": days_held,
                    "annualized_return": annualized_return
                })

                total_cost_basis += cost_basis
                total_current_value += current_value

            total_unrealized_pl = total_current_value - total_cost_basis
            total_unrealized_pl_pct = (total_unrealized_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0

            return {
                "account_id": account_id,
                "positions_analysis": positions_analysis,
                "summary": {
                    "total_cost_basis": total_cost_basis,
                    "total_current_value": total_current_value,
                    "total_unrealized_pl": total_unrealized_pl,
                    "total_unrealized_pl_pct": total_unrealized_pl_pct
                }
            }
        except ValueError as e:
            raise ValueError(f"获取持仓分析失败: {str(e)}")

    def get_trades_performance(self, account_id: str) -> Dict:
        """获取交易绩效分析"""
        try:
            account = self.simulation_service.get_account(account_id)
            sell_trades = [t for t in account.trades if t.action == "sell"]

            if not sell_trades:
                return {
                    "account_id": account_id,
                    "trade_analysis": {
                        "total_trades": 0,
                        "buy_trades": len([t for t in account.trades if t.action == "buy"]),
                        "sell_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "avg_win": 0.0,
                        "avg_loss": 0.0,
                        "profit_factor": 0.0,
                        "largest_win": 0.0,
                        "largest_loss": 0.0,
                        "avg_holding_days": 0.0,
                        "total_commission": sum(t.commission for t in account.trades)
                    },
                    "realized_pl": 0.0,
                    "commission_paid": sum(t.commission for t in account.trades),
                    "net_profit": 0.0
                }

            # 统计
            winning_trades = [t for t in sell_trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in sell_trades if t.pnl and t.pnl < 0]

            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(abs(t.pnl) for t in losing_trades) / len(losing_trades) if losing_trades else 0
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

            largest_win = max((t.pnl for t in sell_trades if t.pnl), default=0)
            largest_loss = min((t.pnl for t in sell_trades if t.pnl), default=0)

            total_commission = sum(t.commission for t in account.trades)
            realized_pl = sum(t.pnl for t in sell_trades if t.pnl)
            net_profit = realized_pl - total_commission

            return {
                "account_id": account_id,
                "trade_analysis": {
                    "total_trades": len(sell_trades),
                    "buy_trades": len([t for t in account.trades if t.action == "buy"]),
                    "sell_trades": len(sell_trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(losing_trades),
                    "win_rate": (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss,
                    "profit_factor": profit_factor,
                    "largest_win": largest_win,
                    "largest_loss": largest_loss,
                    "avg_holding_days": 0.0,  # 需要更复杂的逻辑
                    "total_commission": total_commission
                },
                "realized_pl": realized_pl,
                "commission_paid": total_commission,
                "net_profit": net_profit
            }
        except ValueError as e:
            raise ValueError(f"获取交易分析失败: {str(e)}")
