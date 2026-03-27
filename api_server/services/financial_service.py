#!/usr/bin/env python3
"""财务数据服务层 - 支持多数据源"""

import sys
import os
sys.path.insert(0, '.')

from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from data_sources.aggregator import DataSourceAggregator
from data_sources.exceptions import DataSourceError
from common.config import get_config


class FinancialService:
    """财务数据服务"""

    def __init__(self):
        """初始化财务数据服务"""
        # 使用 DataSourceAggregator 支持多数据源
        self.aggregator = DataSourceAggregator()

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
            result = self.aggregator.get_balance_sheet(
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
            result = self.aggregator.get_income_statement(
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
            result = self.aggregator.get_cash_flow_statement(
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
            from datetime import datetime
            import akshare as ak
            
            # 确定要查询的报告期
            if end_date:
                dt = datetime.strptime(end_date, "%Y-%m-%d")
                year = dt.year
                quarter = (dt.month - 1) // 3 + 1
            else:
                dt = datetime.now()
                year = dt.year
                quarter = (dt.month - 1) // 3 + 1
                # 如果是季度初，使用上一季度数据
                if dt.day < 15 and quarter > 1:
                    quarter -= 1

            # 季度对应的报告期日期
            def get_quarter_date(y, q):
                dates = {1: f"{y}0331", 2: f"{y}0630", 3: f"{y}0930", 4: f"{y}1231"}
                return dates.get(q)
            
            report_date = get_quarter_date(year, quarter)
            
            # 尝试获取数据，如果失败或找不到股票则往前推季度
            df = None
            found_year = year
            found_quarter = quarter
            max_retries = 8  # 最多尝试 8 次（往前推 2 年）
            
            for _ in range(max_retries):
                try:
                    test_df = ak.stock_yjbb_em(date=report_date)
                    # 检查是否有足够的数据和目标股票
                    if test_df is not None and len(test_df) > 1000:
                        row = test_df[test_df['股票代码'] == symbol]
                        if not row.empty:
                            df = test_df
                            break
                except:
                    pass
                
                # 往前推一个季度
                quarter -= 1
                if quarter <= 0:
                    quarter = 4
                    year -= 1
                report_date = get_quarter_date(year, quarter)
            
            # 从 DataFrame 中提取指标
            items_list = []
            if df is not None:
                row = df[df['股票代码'] == symbol]
                if not row.empty:
                    r = row.iloc[0]
                    indicators = {}
                    
                    # 提取各项指标
                    roe = r.get('净资产收益率')
                    if roe is not None:
                        indicators['roe'] = float(roe) / 100
                    
                    gross_margin = r.get('销售毛利率')
                    if gross_margin is not None:
                        indicators['gross_margin'] = float(gross_margin) / 100
                    
                    eps = r.get('每股收益')
                    if eps is not None:
                        indicators['eps'] = float(eps)
                    
                    bvps = r.get('每股净资产')
                    if bvps is not None:
                        indicators['bvps'] = float(bvps)
                    
                    ocfps = r.get('每股经营现金流量')
                    if ocfps is not None:
                        indicators['ocfps'] = float(ocfps)
                    
                    net_profit_growth = r.get('净利润-同比增长')
                    if net_profit_growth is not None:
                        indicators['net_profit_growth'] = float(net_profit_growth) / 100
                    
                    revenue_growth = r.get('营业总收入-同比增长')
                    if revenue_growth is not None:
                        indicators['revenue_growth'] = float(revenue_growth) / 100
                    
                    items_list = [{
                        "symbol": symbol,
                        "year": year,
                        "quarter": quarter,
                        **indicators
                    }]

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = items_list[start:end]

            return {
                "success": True,
                "data": paginated_items,
                "total": len(items_list),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(items_list) + page_size - 1) // page_size if len(items_list) > 0 else 0,
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
            all_items = self.aggregator.get_dupont_analysis(
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
            all_items = self.aggregator.get_per_share_indicators(
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
