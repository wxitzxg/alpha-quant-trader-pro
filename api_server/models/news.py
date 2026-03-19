#!/usr/bin/env python3
"""新闻资讯模型"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NewsArticle(BaseModel):
    """新闻文章"""
    news_id: str = Field(..., description="新闻ID")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    source: str = Field(..., description="来源")
    publish_time: datetime = Field(..., description="发布时间")
    url: Optional[str] = Field(None, description="原文链接")
    related_stocks: Optional[list[str]] = Field(None, description="相关股票代码")


class NewsListResponse(BaseModel):
    """新闻列表响应"""
    news: list[NewsArticle]
    total: int
    page: int
    page_size: int
    timestamp: datetime
