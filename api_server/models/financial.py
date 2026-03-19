#!/usr/bin/env python3
"""财务数据模型"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FinancialStatementBase(BaseModel):
    """财务报表基类"""
    ts_code: str = Field(..., description="TS代码")
    symbol: str = Field(..., description="股票代码")
    ann_date: Optional[date] = Field(None, description="公告日期")
    f_ann_date: Optional[date] = Field(None, description="实际公告日期")
    end_date: date = Field(..., description="报告期")
    report_type: Optional[str] = Field(None, description="报告类型")
    comp_type: Optional[str] = Field(None, description="公司类型")


class IncomeStatement(FinancialStatementBase):
    """利润表"""
    total_revenue: Optional[float] = Field(None, description="营业总收入")
    operating_profit: Optional[float] = Field(None, description="营业利润")
    total_profit: Optional[float] = Field(None, description="利润总额")
    net_profit: Optional[float] = Field(None, description="净利润")
    net_profit_cut: Optional[float] = Field(None, description="扣非净利润")
    eps: Optional[float] = Field(None, description="每股收益")
    eps_cut: Optional[float] = Field(None, description="扣非每股收益")
    roe: Optional[float] = Field(None, description="净资产收益率")


class BalanceSheet(FinancialStatementBase):
    """资产负债表"""
    total_assets: Optional[float] = Field(None, description="资产总计")
    total_liab: Optional[float] = Field(None, description="负债总计")
    total_hldr_eqy: Optional[float] = Field(None, description="股东权益合计")
    cash_and_equiv: Optional[float] = Field(None, description="货币资金")
    accounts_receiv: Optional[float] = Field(None, description="应收账款")
    inventory: Optional[float] = Field(None, description="存货")
    fixed_assets: Optional[float] = Field(None, description="固定资产")
    intangible_assets: Optional[float] = Field(None, description="无形资产")
    goodwill: Optional[float] = Field(None, description="商誉")


class CashFlowStatement(FinancialStatementBase):
    """现金流量表"""
    cashflow_from_operating: Optional[float] = Field(None, description="经营活动现金流")
    cashflow_from_investing: Optional[float] = Field(None, description="投资活动现金流")
    cashflow_from_financing: Optional[float] = Field(None, description="筹资活动现金流")
    net_increase_cash: Optional[float] = Field(None, description="现金净增加额")
    final_balance_cash: Optional[float] = Field(None, description="期末现金余额")


class FinancialIndicator(BaseModel):
    """财务指标"""
    ts_code: str
    symbol: str
    end_date: date
    eps: Optional[float] = Field(None, description="每股收益")
    dt_eps: Optional[float] = Field(None, description="稀释每股收益")
    total_revenue_ps: Optional[float] = Field(None, description="每股营业收入")
    revenue_ps: Optional[float] = Field(None, description="每股销售收入")
    pe: Optional[float] = Field(None, description="市盈率")
    pe_ttm: Optional[float] = Field(None, description="市盈率TTM")
    pb: Optional[float] = Field(None, description="市净率")
    ps: Optional[float] = Field(None, description="市销率")
    ps_ttm: Optional[float] = Field(None, description="市销率TTM")
    roe: Optional[float] = Field(None, description="净资产收益率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    roic: Optional[float] = Field(None, description="投入资本回报率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    debt_to_assets: Optional[float] = Field(None, description="资产负债率")


class FinancialReportResponse(BaseModel):
    """财务报告响应基类"""
    symbol: str
    name: str
    statements: List[FinancialStatementBase]
    total: int
    page: int
    page_size: int
