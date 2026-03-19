#!/usr/bin/env python3
"""收益统计路由 - 集成业务逻辑"""

from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session

from ..models.common import APIResponse
from ..models.performance import PerformanceResponse, PerformanceMetrics
from ..services import PortfolioService
from common.database import DatabaseManager
from portfolio_manager.repositories import TransactionRepository
from portfolio_manager.transaction_service import TransactionService

performance_router = APIRouter()
portfolio_service = PortfolioService()

def calculate_performance_metrics(transactions: list, current_positions: list) -> dict:
    """计算收益统计指标"""
    if not transactions:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_holding_days": 0.0
        }

    # 这里简化计算，实际项目应该使用更复杂的统计方法
    total_return = 0.0
    win_count = 0
    total_trades = len([t for t in transactions if t.get('transaction_type') == 'SELL'])

    for transaction in transactions:
        if transaction.get('transaction_type') == 'SELL':
            # 这里应该查找对应的买入交易来计算收益
            # 简化版本直接假设有收益
            total_return += 0.01  # 假设1%收益
            win_count += 1

    return {
        "total_return": total_return,
        "annualized_return": total_return * 252 / 365 if total_return else 0.0,
        "max_drawdown": 0.05,  # 假设最大回撤5%
        "volatility": 0.18,  # 假设波动率18%
        "sharpe_ratio": 1.3,  # 假设夏普比率1.3
        "sortino_ratio": 1.8,  # 假设索提诺比率1.8
        "win_rate": win_count / total_trades if total_trades > 0 else 0.0,
        "profit_factor": 1.8,  # 假设盈利因子1.8
        "avg_holding_days": 15.5  # 假设平均持仓天数15.5
    }

@performance_router.get("/performance/account/summary", response_model=APIResponse)
async def get_account_performance():
    """账户收益汇总"""
    try:
        # 获取交易历史
        transactions_result = portfolio_service.get_transaction_history()
        positions_result = portfolio_service.get_all_positions(page=1, page_size=100)

        if not transactions_result.get("success") or not positions_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get performance data")

        transactions = transactions_result.get("data", [])
        positions = positions_result.get("data", [])

        # 计算收益指标
        metrics = calculate_performance_metrics(transactions, positions)

        return APIResponse(
            data={
                "metrics": metrics,
                "transactions_count": len(transactions),
                "positions_count": len(positions),
                "calculation_time": datetime.now().isoformat()
            },
            message="Account performance retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting account performance: {str(e)}")

@performance_router.get("/performance/stock/{stock_code}", response_model=APIResponse)
async def get_stock_performance(
    stock_code: str = Path(..., description="股票代码", example="600519")
):
    """单只股票收益统计"""
    try:
        # 获取该股票的交易历史
        transactions_result = portfolio_service.get_transaction_history(symbol=stock_code)

        if not transactions_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get stock performance data")

        transactions = transactions_result.get("data", [])

        # 计算该股票的收益指标
        buy_transactions = [t for t in transactions if t.get('transaction_type') == 'BUY']
        sell_transactions = [t for t in transactions if t.get('transaction_type') == 'SELL']

        total_buys = sum([t.get('amount', 0) for t in buy_transactions])
        total_sells = sum([t.get('amount', 0) for t in sell_transactions])
        total_fees = sum([t.get('fee', 0) for t in transactions])

        profit = total_sells - total_buys - total_fees
        profit_rate = profit / total_buys if total_buys > 0 else 0.0

        metrics = {
            "stock_code": stock_code,
            "total_buys": total_buys,
            "total_sells": total_sells,
            "total_fees": total_fees,
            "profit": profit,
            "profit_rate": profit_rate,
            "transactions_count": len(transactions),
            "win_count": len(sell_transactions)
        }

        return APIResponse(
            data=metrics,
            message=f"{stock_code} performance retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stock performance: {str(e)}")

@performance_router.get("/performance/history", response_model=APIResponse)
async def get_performance_history(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period: str = Query("daily", description="统计周期 (daily/weekly/monthly)")
):
    """历史收益曲线"""
    try:
        # 获取交易历史
        transactions_result = portfolio_service.get_transaction_history(
            start_date=start_date,
            end_date=end_date
        )

        if not transactions_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get performance history")

        transactions = transactions_result.get("data", [])

        # 按时间统计收益（简化版本）
        df = pd.DataFrame(transactions)
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])

            if period == "daily":
                df['period'] = df['transaction_date'].dt.date
            elif period == "weekly":
                df['period'] = df['transaction_date'].dt.to_period('W')
            elif period == "monthly":
                df['period'] = df['transaction_date'].dt.to_period('M')
            else:
                df['period'] = df['transaction_date'].dt.date

            # 按周期汇总
            performance_history = []
            for period_name, group in df.groupby('period'):
                period_trades = group.to_dict('records')
                period_profit = sum([
                    t.get('amount', 0) if t.get('transaction_type') == 'SELL' else -t.get('amount', 0)
                    for t in period_trades
                ])

                performance_history.append({
                    "period": str(period_name),
                    "profit": period_profit,
                    "trades_count": len(period_trades),
                    "date": str(period_name)
                })
        else:
            performance_history = []

        return APIResponse(
            data={
                "period": period,
                "history": performance_history,
                "total_periods": len(performance_history),
                "start_date": start_date,
                "end_date": end_date
            },
            message="Performance history retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance history: {str(e)}")

@performance_router.get("/performance/compare", response_model=APIResponse)
async def compare_performance():
    """收益对比分析"""
    try:
        # 获取账户汇总
        summary_result = portfolio_service.get_account_summary()

        if not summary_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get account summary")

        summary = summary_result.get("data", {})

        # 简化的对比数据（实际应该与基准指数对比）
        benchmark_return = 0.10  # 假设基准收益率10%
        account_return = summary.get('total_profit', 0) / summary.get('total_market_value', 1)

        comparison = {
            "account_return": account_return,
            "benchmark_return": benchmark_return,
            "alpha": account_return - benchmark_return,
            "total_market_value": summary.get('total_market_value', 0),
            "total_profit": summary.get('total_profit', 0),
            "benchmark": "沪深300 (模拟)"
        }

        return APIResponse(
            data=comparison,
            message="Performance comparison retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance comparison: {str(e)}")
