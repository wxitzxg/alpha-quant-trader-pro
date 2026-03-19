#!/usr/bin/env python3
"""财务数据路由 - 提供财务报表和指标数据"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from ..services.financial_service import FinancialService


financial_router = APIRouter()


@financial_router.get("/financial/balance-sheet/{stock_code}", response_model=APIResponse)
async def get_balance_sheet(
    stock_code: str = Path(..., description="股票代码"),
    year: int = Query(..., description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)")
):
    """
    获取资产负债表

    数据包含：
    - 总资产
    - 总负债
    - 股东权益

    Args:
        stock_code: 股票代码
        year: 年份
        quarter: 季度 (1-4)

    Returns:
        资产负债表数据
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_balance_sheet(
            symbol=stock_code,
            year=year,
            quarter=quarter
        )

        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('message', '获取资产负债表失败'))

        return APIResponse(
            data=result.get('data'),
            message="资产负债表获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产负债表失败: {str(e)}")


@financial_router.get("/financial/income-statement/{stock_code}", response_model=APIResponse)
async def get_income_statement(
    stock_code: str = Path(..., description="股票代码"),
    year: int = Query(..., description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)")
):
    """
    获取利润表

    数据包含：
    - 营业收入
    - 净利润
    - 每股收益 (EPS)

    Args:
        stock_code: 股票代码
        year: 年份
        quarter: 季度 (1-4)

    Returns:
        利润表数据
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_income_statement(
            symbol=stock_code,
            year=year,
            quarter=quarter
        )

        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('message', '获取利润表失败'))

        return APIResponse(
            data=result.get('data'),
            message="利润表获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取利润表失败: {str(e)}")


@financial_router.get("/financial/cash-flow/{stock_code}", response_model=APIResponse)
async def get_cash_flow_statement(
    stock_code: str = Path(..., description="股票代码"),
    year: int = Query(..., description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)")
):
    """
    获取现金流量表

    数据包含：
    - 经营活动现金流
    - 投资活动现金流
    - 筹资活动现金流

    Args:
        stock_code: 股票代码
        year: 年份
        quarter: 季度 (1-4)

    Returns:
        现金流量表数据
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_cash_flow_statement(
            symbol=stock_code,
            year=year,
            quarter=quarter
        )

        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('message', '获取现金流量表失败'))

        return APIResponse(
            data=result.get('data'),
            message="现金流量表获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取现金流量表失败: {str(e)}")


@financial_router.get("/financial/indicators/{stock_code}", response_model=APIResponse)
async def get_financial_indicators(
    stock_code: str = Path(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取财务指标数据（分页）

    数据包含：
    - 市盈率 (PE)
    - 市净率 (PB)
    - ROE
    - ROA
    - 资产负债率等

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        财务指标列表（分页）
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_financial_indicators(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取财务指标失败'))

        return APIResponse(
            data={
                "stock_code": stock_code,
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "indicators": result.get('data', []),
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="财务指标获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务指标失败: {str(e)}")


@financial_router.get("/financial/dupont/{stock_code}", response_model=APIResponse)
async def get_dupont_analysis(
    stock_code: str = Path(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取杜邦分析数据（分页）

    杜邦分析将 ROE 拆分为：
    - 净利润率
    - 资产周转率
    - 权益乘数

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        杜邦分析列表（分页）
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_dupont_analysis(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取杜邦分析失败'))

        return APIResponse(
            data={
                "stock_code": stock_code,
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "dupont_data": result.get('data', []),
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="杜邦分析获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取杜邦分析失败: {str(e)}")


@financial_router.get("/financial/per-share/{stock_code}", response_model=APIResponse)
async def get_per_share_indicators(
    stock_code: str = Path(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取每股指标数据（分页）

    数据包含：
    - 每股收益 (EPS)
    - 每股净资产
    - 每股现金流
    - 每股股息等

    Args:
        stock_code: 股票代码
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        每股指标列表（分页）
    """
    try:
        financial_service = FinancialService()
        result = financial_service.get_per_share_indicators(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取每股指标失败'))

        return APIResponse(
            data={
                "stock_code": stock_code,
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "per_share_indicators": result.get('data', []),
                "query_params": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="每股指标获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每股指标失败: {str(e)}")
