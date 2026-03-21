#!/usr/bin/env python3
"""资金流向服务层 - 集成 Investoday 数据源"""

import sys
import os
sys.path.insert(0, '.')

from typing import Optional, List, Dict
from datetime import datetime

from data_sources.adapters.investoday_adapter import InvestodayAdapter
from data_sources.exceptions import DataSourceError
from common.config import get_config


class FundFlowService:
    """资金流向服务"""

    def __init__(self):
        """初始化资金流向服务"""
        config = get_config()
        # 获取 Investoday 数据源的超时配置
        fund_flows_config = None
        for source in config.data_sources.sources.fund_flows:
            if source.name == "investoday":
                fund_flows_config = source
                break

        timeout = fund_flows_config.timeout if fund_flows_config else config.data_sources.timeout

        self.data_source = InvestodayAdapter(timeout=timeout)

    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取资金流向数据（分页）

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            page_size: 每页数量

        Returns:
            资金流向列表
        """
        try:
            all_items = self.data_source.get_fund_flows(
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
                "message": f"Retrieved {len(paginated_items)} fund flow records for {symbol}"
            }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get fund flows: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving fund flows: {str(e)}"
            }

    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取龙虎榜数据（分页）

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码
            page_size: 每页数量

        Returns:
            龙虎榜列表
        """
        try:
            all_items = self.data_source.get_dragon_tiger(
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
                "message": f"Retrieved {len(paginated_items)} dragon tiger records for {symbol}"
            }
        except DataSourceError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get dragon tiger data: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error retrieving dragon tiger data: {str(e)}"
            }
