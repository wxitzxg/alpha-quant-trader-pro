#!/usr/bin/env python3
"""模拟交易路由"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from datetime import datetime

from ..models.common import APIResponse
from ..models.simulation import (
    SimulationAccountCreate,
    TradeOrder,
    SimulationAccount,
    PositionsResponse,
    TradeResult
)
from ..services.simulation_service import SimulationService

simulation_router = APIRouter()

# 全局服务实例（生产环境应该用依赖注入）
SIMULATION_SERVICE = SimulationService()


@simulation_router.post("/simulation/account", response_model=APIResponse)
async def create_simulation_account(request: SimulationAccountCreate):
    """创建模拟账户"""
    try:
        account = SIMULATION_SERVICE.create_account(
            account_name=request.account_name,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )

        return APIResponse(
            data=account.to_dict(),
            message="账户创建成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建账户失败: {str(e)}")


@simulation_router.get("/simulation/account/{account_id}", response_model=APIResponse)
async def get_simulation_account(account_id: str):
    """获取账户信息"""
    try:
        account = SIMULATION_SERVICE.get_account(account_id)
        return APIResponse(
            data=account.to_dict(SIMULATION_SERVICE.market_prices),
            message="账户信息获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@simulation_router.get("/simulation/accounts", response_model=APIResponse)
async def list_simulation_accounts():
    """获取所有账户"""
    try:
        accounts = SIMULATION_SERVICE.list_accounts()
        return APIResponse(
            data=[acc.to_dict(SIMULATION_SERVICE.market_prices) for acc in accounts],
            message="账户列表获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")


@simulation_router.post("/simulation/buy", response_model=APIResponse)
async def buy_stock(request: TradeOrder):
    """买入股票"""
    try:
        trade = SIMULATION_SERVICE.buy(
            account_id=request.account_id,
            symbol=request.symbol,
            price=request.price,
            quantity=request.quantity
        )

        account = SIMULATION_SERVICE.get_account(request.account_id)

        return APIResponse(
            data=TradeResult(
                trade_id=trade.trade_id,
                account_id=request.account_id,
                symbol=request.symbol,
                action="buy",
                price=request.price,
                quantity=request.quantity,
                amount=trade.amount,
                commission=trade.commission,
                total_cost=trade.amount + trade.commission,
                timestamp=trade.timestamp,
                account_balance=account.current_balance
            ),
            message="买入成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"买入失败: {str(e)}")


@simulation_router.post("/simulation/sell", response_model=APIResponse)
async def sell_stock(request: TradeOrder):
    """卖出股票"""
    try:
        trade = SIMULATION_SERVICE.sell(
            account_id=request.account_id,
            symbol=request.symbol,
            price=request.price,
            quantity=request.quantity
        )

        account = SIMULATION_SERVICE.get_account(request.account_id)

        return APIResponse(
            data=TradeResult(
                trade_id=trade.trade_id,
                account_id=request.account_id,
                symbol=request.symbol,
                action="sell",
                price=request.price,
                quantity=request.quantity,
                amount=trade.amount,
                commission=trade.commission,
                pnl=trade.pnl,
                total_revenue=trade.amount - trade.commission,
                timestamp=trade.timestamp,
                account_balance=account.current_balance
            ),
            message="卖出成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卖出失败: {str(e)}")


@simulation_router.get("/simulation/positions/{account_id}", response_model=APIResponse)
async def get_positions(account_id: str):
    """获取持仓列表"""
    try:
        positions_data = SIMULATION_SERVICE.get_positions(account_id)
        return APIResponse(
            data=positions_data,
            message="持仓列表获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@simulation_router.get("/simulation/trades/{account_id}", response_model=APIResponse)
async def get_trades(account_id: str, limit: int = 20):
    """获取交易历史"""
    try:
        trades_data = SIMULATION_SERVICE.get_trades(account_id, limit=limit)
        return APIResponse(
            data=trades_data,
            message="交易历史获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易历史失败: {str(e)}")


@simulation_router.delete("/simulation/account/{account_id}", response_model=APIResponse)
async def delete_simulation_account(account_id: str):
    """删除账户"""
    try:
        SIMULATION_SERVICE.delete_account(account_id)
        return APIResponse(
            data={"account_id": account_id, "deleted_at": datetime.now().isoformat()},
            message="账户删除成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除账户失败: {str(e)}")
