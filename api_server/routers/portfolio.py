#!/usr/bin/env python3
"""持仓管理路由 - 集成业务逻辑"""

from fastapi import APIRouter, HTTPException, Path, Query, Body
from datetime import datetime

from ..models.common import APIResponse
from ..models.portfolio import (
    AccountSummary,
    PositionInfo,
    TradeRecord,
    CashOperation,
    TradeRequest,
    TransactionHistory
)
from ..services import PortfolioService

portfolio_router = APIRouter()
service = PortfolioService()

@portfolio_router.get("/portfolio/account/summary", response_model=APIResponse)
async def get_account_summary():
    """获取账户汇总"""
    try:
        result = service.get_account_summary()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get account summary")

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Account summary retrieved successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting account summary: {str(e)}")

@portfolio_router.get("/portfolio/positions", response_model=APIResponse)
async def get_positions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取持仓列表"""
    try:
        result = service.get_all_positions(page=page, page_size=page_size)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get positions")

        return APIResponse(
            data={
                "positions": result.get("data", []),
                "total": result.get("total", 0),
                "page": result.get("page", 1),
                "page_size": result.get("page_size", 20),
                "total_pages": result.get("total_pages", 0)
            },
            message=result.get("message", "Positions retrieved successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")

@portfolio_router.get("/portfolio/positions/{stock_code}", response_model=APIResponse)
async def get_position(
    stock_code: str = Path(..., description="股票代码", example="600519")
):
    """获取单只股票持仓信息"""
    try:
        result = service.get_position(stock_code)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "Position not found"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Position retrieved successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting position: {str(e)}")

@portfolio_router.post("/portfolio/trade/buy", response_model=APIResponse)
async def buy_stock(request: TradeRequest):
    """买入股票"""
    try:
        result = service.record_buy(
            symbol=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            transaction_date=request.transaction_date
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to record buy"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Buy transaction recorded successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording buy: {str(e)}")

@portfolio_router.post("/portfolio/trade/sell", response_model=APIResponse)
async def sell_stock(request: TradeRequest):
    """卖出股票"""
    try:
        result = service.record_sell(
            symbol=request.stock_code,
            quantity=request.quantity,
            price=request.price,
            transaction_date=request.transaction_date
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to record sell"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Sell transaction recorded successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording sell: {str(e)}")

@portfolio_router.post("/portfolio/account/cash/add", response_model=APIResponse)
async def add_cash(operation: CashOperation):
    """充值"""
    try:
        result = service.set_cash_balance(operation.amount)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to add cash"))

        return APIResponse(
            data={"amount": operation.amount},
            message=result.get("message", f"Added {operation.amount} to account")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding cash: {str(e)}")

@portfolio_router.get("/portfolio/account/cash", response_model=APIResponse)
async def get_cash_balance():
    """获取现金余额"""
    try:
        result = service.get_cash_balance()

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get cash balance")

        return APIResponse(
            data=result.get("data"),
            message="Cash balance retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cash balance: {str(e)}")

@portfolio_router.get("/portfolio/transactions", response_model=APIResponse)
async def get_transactions(
    stock_code: str = Query(None, description="股票代码（可选）"),
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取交易历史"""
    try:
        result = service.get_transaction_history(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get transactions")

        return APIResponse(
            data={
                "transactions": result.get("data", []),
                "total": result.get("total", 0),
                "page": result.get("page", 1),
                "page_size": result.get("page_size", 20),
                "total_pages": result.get("total_pages", 0)
            },
            message="Transaction history retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transactions: {str(e)}")
