#!/usr/bin/env python3
"""财务数据服务层 - 集成 Investoday 数据源"""

import sys
import os
sys.path.insert(0, '.')

from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from data_sources.adapters.investoday_adapter import InvestodayAdapter
from data_sources.exceptions import DataSourceError
from common.config import get_config


class FinancialService:
    """财务数据服务"""

    def __init__(self):
        """初始化财务数据服务"""
        config = get_config()
        # 获取 Investoday 数据源的超时配置
        fund_flows_config = None
        for source in config.data_sources.sources.fund_flows:
            if source.name == "investoday":
                fund_flows_config = source
                break

        timeout = fund_flows_config.timeout if fund_flows_config else config.data_sources.timeout

        self.data_source = InvestodayAdapter(timeout=timeout)

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict:
        """
        获取资产负债表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            资产负债表数据
        """
        try:
            result = self.data_source.get_balance_sheet(
                symbol=symbol,
                year=year,
                quarter=quarter
            )

            if result:
                return {
                    "success": True,
                    "data": {
                        "symbol": result.symbol,
                        "year": result.year,
                        "quarter": result.quarter,
                        "report_date": result.report_date,
                        "total_assets": float(result.total_assets),
                        "total_liabilities": float(result.total_liabilities),
                        "shareholders_equity": float(result.shareholders_equity)
                    },
                    "message": f"Balance sheet for {symbol} {year}Q{quarter} retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"No balance sheet data found for {symbol} {year}Q{quarter}"
                }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get balance sheet: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving balance sheet: {str(e)}"
            }

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict:
        """
        获取利润表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            利润表数据
        """
        try:
            result = self.data_source.get_income_statement(
                symbol=symbol,
                year=year,
                quarter=quarter
            )

            if result:
                return {
                    "success": True,
                    "data": {
                        "symbol": result.symbol,
                        "year": result.year,
                        "quarter": result.quarter,
                        "report_date": result.report_date,
                        "revenue": float(result.revenue),
                        "net_profit": float(result.net_profit),
                        "eps": float(result.eps)
                    },
                    "message": f"Income statement for {symbol} {year}Q{quarter} retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"No income statement data found for {symbol} {year}Q{quarter}"
                }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get income statement: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving income statement: {str(e)}"
            }

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict:
        """
        获取现金流量表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            现金流量表数据
        """
        try:
            result = self.data_source.get_cash_flow_statement(
                symbol=symbol,
                year=year,
                quarter=quarter
            )

            if result:
                return {
                    "success": True,
                    "data": {
                        "symbol": result.symbol,
                        "year": result.year,
                        "quarter": result.quarter,
                        "report_date": result.report_date,
                        "operating_cash_flow": float(result.operating_cash_flow),
                        "investing_cash_flow": float(result.investing_cash_flow),
                        "financing_cash_flow": float(result.financing_cash_flow)
                    },
                    "message": f"Cash flow statement for {symbol} {year}Q{quarter} retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"No cash flow data found for {symbol} {year}Q{quarter}"
                }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get cash flow statement: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving cash flow statement: {str(e)}"
            }

    def get_financial_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取财务指标数据（分页）

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            page_size: 每页数量

        Returns:
            财务指标列表
        """
        try:
            all_items = self.data_source.get_financial_indicators(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = all_items[start:end]

            return {
                "success": True,
                "data": paginated_items,
                "total": len(all_items),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(all_items) + page_size - 1) // page_size,
                "message": f"Retrieved {len(paginated_items)} financial indicators for {symbol}"
            }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get financial indicators: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving financial indicators: {str(e)}"
            }

    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取杜邦分析数据（分页）

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            page_size: 每页数量

        Returns:
            杜邦分析列表
        """
        try:
            all_items = self.data_source.get_dupont_analysis(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = all_items[start:end]

            return {
                "success": True,
                "data": paginated_items,
                "total": len(all_items),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(all_items) + page_size - 1) // page_size,
                "message": f"Retrieved {len(paginated_items)} Dupont analysis records for {symbol}"
            }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get Dupont analysis: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving Dupont analysis: {str(e)}"
            }

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取每股指标数据（分页）

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            page_size: 每页数量

        Returns:
            每股指标列表
        """
        try:
            all_items = self.data_source.get_per_share_indicators(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = all_items[start:end]

            return {
                "success": True,
                "data": paginated_items,
                "total": len(all_items),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(all_items) + page_size - 1) // page_size,
                "message": f"Retrieved {len(paginated_items)} per-share indicators for {symbol}"
            }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get per-share indicators: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving per-share indicators: {str(e)}"
            }
