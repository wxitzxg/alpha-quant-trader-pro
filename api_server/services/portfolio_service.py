#!/usr/bin/env python3
"""持仓管理服务层 - 连接 API Router 和现有 portfolio_manager 模块"""

import sys
import os
sys.path.insert(0, '.')

from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from contextlib import contextmanager

from common.database import DatabaseManager
from portfolio_manager.repositories import (
    PositionRepository,
    TransactionRepository,
    CashBalanceRepository,
    CapitalAdjustmentRepository
)
from portfolio_manager.position_service import PositionService
from portfolio_manager.transaction_service import TransactionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.capital_service import CapitalService
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.models import (
    PositionModel,
    TransactionModel,
    AccountSummary
)
from portfolio_manager.schemas.capital_schemas import CapitalAdjustRequest


class PortfolioService:
    """持仓管理服务"""

    def __init__(self, db_url: Optional[str] = None):
        """
        初始化持仓管理服务

        Args:
            db_url: 数据库连接字符串
        """
        self.db_url = db_url or os.getenv("DATABASE__URL", "postgresql://localhost/stock_market")
        self.db_manager = DatabaseManager(self.db_url)

    @contextmanager
    def _get_services(self):
        """获取服务实例（上下文管理器）"""
        with self.db_manager.get_session() as session:
            # 初始化 repositories
            position_repo = PositionRepository(session)
            transaction_repo = TransactionRepository(session)
            cash_repo = CashBalanceRepository(session)
            capital_repo = CapitalAdjustmentRepository(session)

            # 初始化 services
            position_service = PositionService(position_repo)
            capital_service = CapitalService(session, capital_repo, cash_repo)
            account_service = AccountService(cash_repo, position_service, capital_service)
            fee_calculator = FeeCalculator()
            transaction_service = TransactionService(
                transaction_repo=transaction_repo,
                position_repo=position_repo,
                position_service=position_service,
                account_service=account_service,
                fee_calculator=fee_calculator
            )

            yield (
                session,
                position_service,
                transaction_service,
                account_service,
                fee_calculator,
                capital_service
            )

    def get_account_summary(self) -> Dict:
        """
        获取账户汇总信息

        Returns:
            账户汇总响应
        """
        try:
            with self._get_services() as (_, _, _, account_service, _, _):
                summary = account_service.get_account_summary()

                return {
                    "success": True,
                    "data": {
                        "total_market_value": summary.total_market_value,
                        "stock_market_value": summary.stock_market_value,
                        "cash": summary.cash,
                        "initial_capital": summary.initial_capital,
                        "total_floating_pl": summary.total_floating_pl,
                        "total_realized_pl": summary.total_realized_pl,
                        "positions_count": summary.positions_count
                    },
                    "message": "Account summary retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get account summary: {str(e)}"
            }

    def get_position(self, symbol: str) -> Dict:
        """
        获取单只股票持仓信息

        Args:
            symbol: 股票代码

        Returns:
            持仓信息
        """
        try:
            with self._get_services() as (_, position_service, _, _, _, _):
                position = position_service.get_position(symbol)

                if not position:
                    return {
                        "success": False,
                        "message": f"Position {symbol} not found"
                    }

                return {
                    "success": True,
                    "data": {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "cost_price": position.cost_price,
                        "current_price": position.current_price,
                        "market_value": position.market_value,
                        "cost_value": position.cost_value,
                        "floating_pl": position.floating_pl,
                        "position_ratio": position.position_ratio,
                        "last_updated": position.last_updated.isoformat()
                    },
                    "message": "Position retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get position: {str(e)}"
            }

    def get_all_positions(self, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取持仓列表（分页）

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            持仓列表
        """
        try:
            with self._get_services() as (_, position_service, _, _, _, _):
                positions = position_service.get_all_positions()

                # 分页
                start = (page - 1) * page_size
                end = start + page_size
                paginated_positions = positions[start:end]

                return {
                    "success": True,
                    "data": [
                        {
                            "symbol": p.symbol,
                            "quantity": p.quantity,
                            "cost_price": p.cost_price,
                            "current_price": p.current_price,
                            "market_value": p.market_value,
                            "cost_value": p.cost_value,
                            "floating_pl": p.floating_pl,
                            "position_ratio": p.position_ratio,
                            "last_updated": p.last_updated.isoformat()
                        }
                        for p in paginated_positions
                    ],
                    "total": len(positions),
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (len(positions) + page_size - 1) // page_size,
                    "message": "Positions retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get positions: {str(e)}"
            }

    def add_position(
        self,
        symbol: str,
        quantity: int,
        cost_price: float,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        新增持仓

        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价
            current_price: 当前价格（可选）

        Returns:
            持仓信息
        """
        try:
            with self._get_services() as (_, position_service, _, _, _, _):
                position = position_service.add_position(
                    symbol=symbol,
                    quantity=quantity,
                    cost_price=cost_price,
                    current_price=current_price
                )

                return {
                    "success": True,
                    "data": {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "cost_price": position.cost_price,
                        "current_price": position.current_price,
                        "market_value": position.market_value,
                        "cost_value": position.cost_value,
                        "floating_pl": position.floating_pl,
                        "last_updated": position.last_updated.isoformat()
                    },
                    "message": f"Position {symbol} added successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add position: {str(e)}"
            }

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        更新持仓

        Args:
            symbol: 股票代码
            quantity: 持仓数量（可选）
            cost_price: 成本价（可选）
            current_price: 当前价格（可选）

        Returns:
            持仓信息
        """
        try:
            with self._get_services() as (_, position_service, _, _, _, _):
                position = position_service.update_position(
                    symbol=symbol,
                    quantity=quantity,
                    cost_price=cost_price,
                    current_price=current_price
                )

                return {
                    "success": True,
                    "data": {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "cost_price": position.cost_price,
                        "current_price": position.current_price,
                        "market_value": position.market_value,
                        "cost_value": position.cost_value,
                        "floating_pl": position.floating_pl,
                        "last_updated": position.last_updated.isoformat()
                    },
                    "message": f"Position {symbol} updated successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update position: {str(e)}"
            }

    def sync_position(
        self,
        symbol: str,
        quantity: int,
        cost_price: float,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        同步持仓信息（存在则覆盖，不存在则新增）

        Args:
            symbol: 股票代码（必填）
            quantity: 持仓数量（必填）
            cost_price: 成本价（必填）
            current_price: 当前价格（可选）

        Returns:
            {
                "success": bool,
                "data": PositionInfo | None,
                "message": str
            }
        """
        try:
            with self._get_services() as (_, position_service, _, _, _, _):
                position = position_service.sync_position(
                    symbol=symbol,
                    quantity=quantity,
                    cost_price=cost_price,
                    current_price=current_price
                )

                return {
                    "success": True,
                    "data": {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "cost_price": position.cost_price,
                        "current_price": position.current_price,
                        "market_value": position.market_value,
                        "cost_value": position.cost_value,
                        "floating_pl": position.floating_pl,
                        "last_updated": position.last_updated.isoformat()
                    },
                    "message": f"Position {symbol} synced successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to sync position: {str(e)}"
            }

    def record_buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[str] = None
    ) -> Dict:
        """
        记录买入交易

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（YYYY-MM-DD HH:MM:SS 格式）

        Returns:
            交易记录
        """
        try:
            with self._get_services() as (_, _, transaction_service, _, _, _):
                # 转换日期格式
                date_obj = None
                if transaction_date:
                    date_obj = datetime.fromisoformat(transaction_date)

                transaction = transaction_service.record_buy(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    transaction_date=date_obj
                )

                return {
                    "success": True,
                    "data": {
                        "symbol": transaction.symbol,
                        "transaction_type": transaction.transaction_type,
                        "quantity": transaction.quantity,
                        "price": transaction.price,
                        "amount": transaction.amount,
                        "fee": transaction.fee,
                        "transaction_date": transaction.transaction_date.isoformat()
                    },
                    "message": f"Buy transaction for {symbol} recorded successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to record buy transaction: {str(e)}"
            }

    def record_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[str] = None
    ) -> Dict:
        """
        记录卖出交易

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（YYYY-MM-DD HH:MM:SS 格式）

        Returns:
            交易记录
        """
        try:
            with self._get_services() as (_, _, transaction_service, _, _, _):
                # 转换日期格式
                date_obj = None
                if transaction_date:
                    date_obj = datetime.fromisoformat(transaction_date)

                transaction = transaction_service.record_sell(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    transaction_date=date_obj
                )

                return {
                    "success": True,
                    "data": {
                        "symbol": transaction.symbol,
                        "transaction_type": transaction.transaction_type,
                        "quantity": transaction.quantity,
                        "price": transaction.price,
                        "amount": transaction.amount,
                        "fee": transaction.fee,
                        "transaction_date": transaction.transaction_date.isoformat()
                    },
                    "message": f"Sell transaction for {symbol} recorded successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to record sell transaction: {str(e)}"
            }

    def get_transaction_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取交易历史

        Args:
            symbol: 股票代码（可选）
            start_date: 开始日期（YYYY-MM-DD 格式）
            end_date: 结束日期（YYYY-MM-DD 格式）
            page: 页码
            page_size: 每页数量

        Returns:
            交易历史列表
        """
        try:
            with self._get_services() as (_, _, transaction_service, _, _, _):
                # 转换日期格式
                start_date_obj = None
                end_date_obj = None
                if start_date:
                    start_date_obj = datetime.fromisoformat(start_date)
                if end_date:
                    end_date_obj = datetime.fromisoformat(end_date)

                transactions = transaction_service.get_transaction_history(
                    symbol=symbol,
                    start_date=start_date_obj,
                    end_date=end_date_obj
                )

                # 分页
                start = (page - 1) * page_size
                end = start + page_size
                paginated_transactions = transactions[start:end]

                return {
                    "success": True,
                    "data": [
                        {
                            "symbol": t.symbol,
                            "transaction_type": t.transaction_type,
                            "quantity": t.quantity,
                            "price": t.price,
                            "amount": t.amount,
                            "fee": t.fee,
                            "transaction_date": t.transaction_date.isoformat()
                        }
                        for t in paginated_transactions
                    ],
                    "total": len(transactions),
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (len(transactions) + page_size - 1) // page_size,
                    "message": "Transaction history retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get transaction history: {str(e)}"
            }

    def get_cash_balance(self) -> Dict:
        """
        获取现金余额

        Returns:
            现金余额
        """
        try:
            with self._get_services() as (_, _, _, account_service, _, _):
                cash = account_service.get_cash_balance()

                return {
                    "success": True,
                    "data": {
                        "cash": cash
                    },
                    "message": "Cash balance retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get cash balance: {str(e)}"
            }

    def set_cash_balance(self, amount: float) -> Dict:
        """
        设置现金余额（覆盖）

        Args:
            amount: 新的余额

        Returns:
            操作结果
        """
        try:
            with self._get_services() as (_, _, _, account_service, _, _):
                account_service.set_cash_balance(amount)

                return {
                    "success": True,
                    "data": {
                        "amount": amount
                    },
                    "message": f"Cash balance set to {amount}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to set cash balance: {str(e)}"
            }

    def adjust_capital(self, request: CapitalAdjustRequest) -> Dict:
        """
        调整初始资金

        Args:
            request: 资金调整请求

        Returns:
            调整结果
        """
        try:
            with self._get_services() as (_, _, _, _, _, capital_service):
                response, confirmation = capital_service.adjust_capital(request)

                # 如果需要确认
                if confirmation:
                    return {
                        "success": False,
                        "data": confirmation,
                        "message": confirmation.get("message", "Confirmation required")
                    }

                return {
                    "success": True,
                    "data": {
                        "adjustment_id": response.adjustment_id,
                        "new_initial_capital": response.new_initial_capital,
                        "adjustment_type": response.adjustment_type.value,
                        "amount": response.amount,
                        "new_cash_balance": response.new_cash_balance
                    },
                    "message": "Capital adjusted successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to adjust capital: {str(e)}"
            }

    def get_capital_history(self, limit: int = 20) -> Dict:
        """
        获取资金调整历史

        Args:
            limit: 限制返回数量

        Returns:
            调整历史
        """
        try:
            with self._get_services() as (_, _, _, _, _, capital_service):
                history = capital_service.get_adjustment_history(limit)

                return {
                    "success": True,
                    "data": {
                        "items": [
                            {
                                "id": item.id,
                                "amount": item.amount,
                                "adjustment_type": item.adjustment_type.value,
                                "reason": item.reason,
                                "created_at": item.created_at.isoformat()
                            }
                            for item in history.items
                        ],
                        "total": history.total
                    },
                    "message": "Capital adjustment history retrieved successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get capital history: {str(e)}"
            }
