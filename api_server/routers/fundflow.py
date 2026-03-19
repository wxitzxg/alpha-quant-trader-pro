#!/usr/bin/env python3
"""资金流向路由 - 提供资金流向和龙虎榜数据"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from ..services.fundflow_service import FundFlowService


fundflow_router = APIRouter()


@fundflow_router.get("/fundflow/{stock_code}", response_model=APIResponse)
async def get_fund_flow(
    stock_code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取资金流向数据

    数据包含：
    - 主力资金净流入
    - 散户资金净流入
    - 资金流向趋势

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        资金流向数据列表（分页）
    """
    try:
        fundflow_service = FundFlowService()
        result = fundflow_service.get_fund_flows(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取资金流向失败'))

        return APIResponse(
            data={
                "stock_code": stock_code,
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "fund_flows": result.get('data', []),
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="资金流向获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资金流向失败: {str(e)}")


@fundflow_router.get("/fundflow/dragon-tiger/{stock_code}", response_model=APIResponse)
async def get_dragon_tiger(
    stock_code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取龙虎榜数据

    数据包含：
    - 买入/卖出营业部
    - 成交金额
    - 买卖净额

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        龙虎榜数据列表（分页）
    """
    try:
        fundflow_service = FundFlowService()
        result = fundflow_service.get_dragon_tiger(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取龙虎榜失败'))

        return APIResponse(
            data={
                "stock_code": stock_code,
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "dragon_tiger_data": result.get('data', []),
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="龙虎榜数据获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取龙虎榜失败: {str(e)}")
