"""
每日报告仓库 - 封装日报数据库操作
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from simulate_trading.models import DailyReport
from datetime import date, timedelta


class DailyReportRepository:
    """每日报告仓库"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, report: DailyReport) -> DailyReport:
        """创建日报"""
        self.session.add(report)
        self.session.flush()
        return report

    def get_by_strategy_and_date(self, strategy_name: str, report_date: date) -> Optional[DailyReport]:
        """根据策略和日期获取日报"""
        return self.session.query(DailyReport)\
            .filter_by(strategy_name=strategy_name, report_date=report_date)\
            .first()

    def get_by_strategy(self, strategy_name: str, days: int = 30) -> List[DailyReport]:
        """获取策略最近N天的日报"""
        since = date.today() - timedelta(days=days)
        return self.session.query(DailyReport)\
            .filter(
                and_(
                    DailyReport.strategy_name == strategy_name,
                    DailyReport.report_date >= since
                )
            )\
            .order_by(DailyReport.report_date.desc())\
            .all()

    def get_latest(self, strategy_name: str) -> Optional[DailyReport]:
        """获取策略最新日报"""
        return self.session.query(DailyReport)\
            .filter_by(strategy_name=strategy_name)\
            .order_by(DailyReport.report_date.desc())\
            .first()

    def get_all_latest(self) -> List[DailyReport]:
        """获取所有策略的最新日报"""
        # 获取每个策略最新的日报日期
        from sqlalchemy import distinct
        strategies = self.session.query(distinct(DailyReport.strategy_name)).all()

        reports = []
        for (strategy_name,) in strategies:
            latest = self.get_latest(strategy_name)
            if latest:
                reports.append(latest)

        return reports
