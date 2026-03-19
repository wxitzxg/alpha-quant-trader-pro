#!/usr/bin/env python3
"""新闻资讯路由 - 提供新闻资讯服务"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..models.common import APIResponse
from ..services.news_service import NewsService


news_router = APIRouter()


@news_router.get("/news/list", response_model=APIResponse)
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="新闻分类"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
):
    """
    获取新闻列表（分页）

    Args:
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)
        category: 分类（可选）
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)

    Returns:
        新闻列表（分页）
    """
    try:
        news_service = NewsService()
        result = news_service.get_news_list(
            page=page,
            page_size=page_size,
            category=category,
            start_date=start_date,
            end_date=end_date
        )

        if not result.get('success'):
            message = result.get('message', '获取新闻列表失败')
            if "not yet implemented" in message:
                return APIResponse(
                    data={
                        "news": [],
                        "page": page,
                        "page_size": page_size,
                        "total": 0,
                        "total_pages": 0,
                        "status": "news_service_unavailable"
                    },
                    message="⚠️ 新闻服务暂未启用，请配置新闻数据源"
                )
            raise HTTPException(status_code=400, detail=message)

        return APIResponse(
            data={
                "news": result.get('data', []),
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "query_params": {
                    "category": category,
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            message="新闻列表获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻列表失败: {str(e)}")


@news_router.get("/news/{news_id}", response_model=APIResponse)
async def get_news_detail(news_id: str):
    """
    获取新闻详情

    Args:
        news_id: 新闻ID

    Returns:
        新闻详情
    """
    try:
        news_service = NewsService()
        result = news_service.get_news_detail(news_id=news_id)

        if not result.get('success'):
            message = result.get('message', '获取新闻详情失败')
            if "not found" in message.lower():
                raise HTTPException(status_code=404, detail=message)
            raise HTTPException(status_code=400, detail=message)

        return APIResponse(
            data=result.get('data', {}),
            message="新闻详情获取成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻详情失败: {str(e)}")


@news_router.get("/news/search", response_model=APIResponse)
async def search_news(
    query: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    搜索新闻

    Args:
        query: 搜索关键词
        page: 页码 (默认1)
        page_size: 每页数量 (默认20)

    Returns:
        搜索结果
    """
    try:
        news_service = NewsService()
        result = news_service.search_news(
            query=query,
            page=page,
            page_size=page_size
        )

        if not result.get('success'):
            message = result.get('message', '搜索新闻失败')
            if "not yet implemented" in message:
                return APIResponse(
                    data={
                        "results": [],
                        "page": page,
                        "page_size": page_size,
                        "total": 0,
                        "total_pages": 0,
                        "query": query,
                        "status": "news_service_unavailable"
                    },
                    message="⚠️ 暂未启用新闻搜索功能"
                )
            raise HTTPException(status_code=400, detail=message)

        return APIResponse(
            data={
                "results": result.get('data', []),
                "page": page,
                "page_size": page_size,
                "total": result.get('total', 0),
                "total_pages": result.get('total_pages', 0),
                "query": query
            },
            message=f"搜索 '{query}' 完成"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索新闻失败: {str(e)}")
