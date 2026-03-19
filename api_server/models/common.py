#!/usr/bin/env python3
"""
通用 Pydantic 数据模型
所有 API 响应和请求的基础模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime


T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = Field(True, description="是否成功")
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[T] = Field(None, description="数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    code: int
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    success: bool = True
    data: List[T]
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class TimeRangeParams(BaseModel):
    """时间范围参数"""
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")


class SortParams(BaseModel):
    """排序参数"""
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序顺序")
