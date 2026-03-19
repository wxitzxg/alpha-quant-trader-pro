#!/usr/bin/env python3
"""资金流向模型"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FundFlow(BaseModel):
    """资金流向"""
    ts_code: str = Field(..., description="TS代码")
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    trade_date: str = Field(..., description="交易日期")
    main_net_inflow: float = Field(..., description="主力净流入（万元）")
    main_net_inflow_rate: float = Field(..., description="主力净流入率")
    retail_net_inflow: float = Field(..., description="散户净流入（万元）")
    retail_net_inflow_rate: float = Field(..., description="散户净流入率")
    super_large_net_inflow: float = Field(..., description="超大单净流入")
    large_net_inflow: float = Field(..., description="大单净流入")
    medium_net_inflow: float = Field(..., description="中单净流入")
    small_net_inflow: float = Field(..., description="小单净流入")


class FundFlowResponse(BaseModel):
    """资金流向响应"""
    symbol: str
    name: str
    fundflow: list[FundFlow]
    total: int
