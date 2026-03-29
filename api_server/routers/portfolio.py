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
    PositionSyncRequest,
    TransactionHistory
)
from ..services import PortfolioService
from portfolio_manager.schemas.favorite_schemas import (
    AddFavoriteRequest,
    RemoveFavoriteRequest,
    UpdateFavoriteRequest,
    FavoriteResponse
)
from portfolio_manager.schemas.capital_schemas import (
    CapitalAdjustRequest
)
from portfolio_manager.services.favorite_service import FavoriteService
from common.exceptions import BusinessError, NotFoundError

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


# ==================== 资金调整管理 ====================


@portfolio_router.post("/portfolio/account/capital/adjust", response_model=APIResponse)
async def adjust_capital(request: CapitalAdjustRequest):
    """
    调整初始资金

    支持转入(deposit)和转出(withdraw)操作。
    大额操作（>=10万）需要设置 confirm=true 确认。
    """
    try:
        result = service.adjust_capital(request)

        # 如果需要确认
        if not result.get("success") and result.get("data", {}).get("require_confirmation"):
            return APIResponse(
                success=False,
                data=result.get("data"),
                message=result.get("message", "Confirmation required")
            )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to adjust capital"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Capital adjusted successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adjusting capital: {str(e)}")


@portfolio_router.get("/portfolio/account/capital/history", response_model=APIResponse)
async def get_capital_history(
    limit: int = Query(20, ge=1, le=100, description="限制返回数量")
):
    """获取资金调整历史"""
    try:
        result = service.get_capital_history(limit=limit)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get capital history")

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Capital history retrieved successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting capital history: {str(e)}")

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


@portfolio_router.post("/portfolio/positions/sync", response_model=APIResponse)
async def sync_position(request: PositionSyncRequest):
    """同步持仓信息（存在则覆盖，不存在则新增）"""
    try:
        result = service.sync_position(
            symbol=request.stock_code,
            quantity=request.quantity,
            cost_price=request.cost_price,
            current_price=request.current_price
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to sync position"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Position synced successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing position: {str(e)}")


# ==================== 股票收藏管理 ====================


def _get_favorite_service():
    """获取收藏服务实例，返回 (service, session) 元组"""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from portfolio_manager.repositories.favorite_repository import FavoriteRepository
    from portfolio_manager.services.favorite_service import FavoriteService

    # 从环境变量获取数据库 URL，或使用默认配置
    db_url = os.environ.get(
        "DATABASE__URL",
        "postgresql://alpha_quant_trader_pro:alpha_quant_trader_pro@alpha-quant-db:5432/alpha_quant_trader_pro"
    )

    # 创建引擎和 session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = FavoriteRepository(session)
    return FavoriteService(repo), session


@portfolio_router.get("/portfolio/favorites", response_model=APIResponse)
async def get_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取收藏列表（分页）"""
    try:
        service, session = _get_favorite_service()
        favorites, total, total_pages = service.get_paginated(page=page, page_size=page_size)

        return APIResponse(
            data={
                "favorites": [f.model_dump() for f in favorites],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="Favorites retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting favorites: {str(e)}")
    finally:
        session.close()


@portfolio_router.post("/portfolio/favorites/add", response_model=APIResponse)
async def add_favorite(request: AddFavoriteRequest):
    """添加收藏"""
    try:
        service, session = _get_favorite_service()
        result = service.add_favorite(
            symbol=request.symbol,
            tag=request.tag,
            note=request.note
        )
        session.commit()  # 提交事务

        return APIResponse(
            data=result.model_dump(),
            message=f"Stock {request.symbol} added to favorites"
        )
    except BusinessError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")
    finally:
        session.close()


@portfolio_router.post("/portfolio/favorites/remove", response_model=APIResponse)
async def remove_favorite(request: RemoveFavoriteRequest):
    """移除收藏"""
    try:
        service, session = _get_favorite_service()
        service.remove_favorite(symbol=request.symbol)
        session.commit()

        return APIResponse(
            data={"symbol": request.symbol},
            message=f"Stock {request.symbol} removed from favorites"
        )
    except NotFoundError as e:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")
    finally:
        session.close()


@portfolio_router.post("/portfolio/favorites/update", response_model=APIResponse)
async def update_favorite(request: UpdateFavoriteRequest):
    """更新收藏"""
    try:
        service, session = _get_favorite_service()
        result = service.update_favorite(
            symbol=request.symbol,
            tag=request.tag,
            note=request.note
        )
        session.commit()

        return APIResponse(
            data=result.model_dump(),
            message=f"Favorite {request.symbol} updated successfully"
        )
    except NotFoundError as e:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating favorite: {str(e)}")
    finally:
        session.close()
