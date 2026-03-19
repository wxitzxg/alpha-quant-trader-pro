"""
日期处理工具模块
"""
from datetime import date, datetime, timedelta
from typing import List, Optional


def get_trade_days(start_date: date, end_date: date) -> List[date]:
    """
    获取交易日列表（跳过周末）

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        交易日列表
    """
    trade_days = []
    current = start_date

    while current <= end_date:
        # 周一到周五为交易日
        if current.weekday() < 5:
            trade_days.append(current)
        current += timedelta(days=1)

    return trade_days


def format_date(date_obj: date) -> str:
    """格式化日期为 YYYY-MM-DD"""
    return date_obj.strftime("%Y-%m-%d")


def parse_date(date_str: str) -> date:
    """解析日期字符串为 date 对象"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_month_range(year: int, month: int) -> tuple[date, date]:
    """
    获取指定月份的起止日期

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        (start_date, end_date)
    """
    start_date = date(year, month, 1)

    # 计算下个月第一天
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    end_date = next_month - timedelta(days=1)

    return start_date, end_date
