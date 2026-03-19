"""
增量同步策略模块
"""
import logging
from typing import List, Dict, Optional
from datetime import date, timedelta
from stock_market.database import DatabaseManager
from stock_market.models import KLine

logger = logging.getLogger(__name__)


class IncrementalSyncStrategy:
    """增量同步策略"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_missing_dates(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[date]:
        """
        获取缺失的交易日期

        用于检测数据完整性，找出缺失的K线日期

        Args:
            symbol: 股票代码
            interval: 周期
            start_date: 检查开始日期
            end_date: 检查结束日期

        Returns:
            缺失的日期列表
        """
        with self.db.get_session() as session:
            # 查询已有的日期
            query = session.query(KLine.date).filter_by(
                symbol=symbol,
                interval=interval
            )

            if start_date:
                query = query.filter(KLine.date >= start_date)
            if end_date:
                query = query.filter(KLine.date <= end_date)

            existing_dates = {row[0] for row in query.all()}

            # 生成期望的所有日期范围
            if not start_date:
                # 查询股票上市日期
                from stock_market.models import Stock
                stock = session.query(Stock).filter_by(symbol=symbol).first()
                start_date = stock.list_date if stock else date(2010, 1, 1)

            if not end_date:
                end_date = date.today()

            # 生成所有交易日期（跳过周末）
            expected_dates = []
            current = start_date

            while current <= end_date:
                # 周一到周五为交易日
                if current.weekday() < 5:
                    expected_dates.append(current)
                current += timedelta(days=1)

            # 找出缺失的日期
            missing_dates = [d for d in expected_dates if d not in existing_dates]

            return missing_dates

    def get_sync_gaps(
        self,
        symbol: str,
        interval: str
    ) -> List[Dict[str, date]]:
        """
        获取同步缺口（连续的缺失日期段）

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            [{"start": date, "end": date}] 列表
        """
        missing_dates = self.get_missing_dates(symbol, interval)

        if not missing_dates:
            return []

        gaps = []
        current_gap = {"start": missing_dates[0], "end": missing_dates[0]}

        for i in range(1, len(missing_dates)):
            if missing_dates[i] == missing_dates[i-1] + timedelta(days=1):
                # 连续日期
                current_gap["end"] = missing_dates[i]
            else:
                # 新的缺口
                gaps.append(current_gap)
                current_gap = {"start": missing_dates[i], "end": missing_dates[i]}

        gaps.append(current_gap)

        return gaps
