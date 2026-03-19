#!/usr/bin/env python3
"""风险提示模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AlertConfig(BaseModel):
    """预警配置"""
    alert_type: str = Field(..., description="预警类型 (price/technical/risk)")
    stock_code: str = Field(..., description="股票代码")
    condition: str = Field(..., description="触发条件")
    threshold: float = Field(..., description="阈值")
    is_active: bool = Field(True, description="是否启用")


class AlertTrigger(BaseModel):
    """预警触发"""
    alert_id: str = Field(..., description="预警ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    alert_type: str = Field(..., description="预警类型")
    trigger_time: datetime = Field(default_factory=datetime.now, description="触发时间")
    current_value: float = Field(..., description="当前值")
    threshold_value: float = Field(..., description="阈值")
    message: str = Field(..., description="预警消息")


class WebhookConfig(BaseModel):
    """Webhook 配置"""
    url: str = Field(..., description="回调URL")
    events: List[str] = Field(..., description="监听事件")
    secret: Optional[str] = Field(None, description="签名密钥")


class AlertsResponse(BaseModel):
    """预警响应"""
    alerts: Optional[List[AlertTrigger]] = None
    configs: Optional[List[AlertConfig]] = None
    total: Optional[int] = None
