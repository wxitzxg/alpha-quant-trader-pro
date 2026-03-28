"""股票市场数据仓库层"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from common.repositories.base import BaseRepository
from stock_market.models import Stock, KLine, SyncRecord


class StockRepository(BaseRepository[Stock]):
    """股票信息仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Stock)

    def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根据股票代码获取股票信息"""
        return self.get_by(symbol=symbol)

    def get_active(self) -> List[Stock]:
        """获取所有上市股票"""
        stmt = select(Stock).filter_by(is_active=True)
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_by_industry(self, industry: str) -> List[Stock]:
        """根据行业获取股票列表"""
        stmt = select(Stock).filter_by(industry=industry, is_active=True)
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_by_concept(self, concept: str) -> List[Stock]:
        """根据概念获取股票列表"""
        stmt = select(Stock).filter(
            Stock.concept.contains(concept),
            Stock.is_active == True
        )
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def bulk_upsert(self, stocks: List[Stock]) -> int:
        """
        批量插入或更新股票

        Args:
            stocks: 股票列表

        Returns:
            成功处理的数量
        """
        success_count = 0
        for stock in stocks:
            existing = self.get_by(symbol=stock.symbol)
            if existing:
                # 更新现有记录
                for key, value in stock.__dict__.items():
                    if not key.startswith('_') and key not in ['id', 'created_at']:
                        setattr(existing, key, value)
                existing.last_sync_time = datetime.now()
            else:
                # 插入新记录
                stock.last_sync_time = datetime.now()
                self.add(stock)
            success_count += 1

        return success_count


class KLineRepository(BaseRepository[KLine]):
    """K线数据仓库"""

    def __init__(self, session: Session):
        super().__init__(session, KLine)

    def get_by_symbol_and_date(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> List[KLine]:
        """
        根据股票代码和日期范围获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            K线数据列表
        """
        stmt = select(KLine).filter(
            KLine.symbol == symbol,
            KLine.interval == interval,
            KLine.date >= start_date,
            KLine.date <= end_date
        ).order_by(KLine.date)

        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_latest_by_symbol(self, symbol: str, interval: str) -> Optional[KLine]:
        """获取最新K线数据"""
        stmt = select(KLine).filter_by(
            symbol=symbol,
            interval=interval
        ).order_by(KLine.date.desc()).limit(1)

        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def get_last_sync_date(self, symbol: str, interval: str) -> Optional[str]:
        """获取最后同步日期"""
        latest = self.get_latest_by_symbol(symbol, interval)
        return latest.date if latest else None

    def query_klines(self, params) -> List[KLine]:
        """
        根据查询参数获取K线数据

        Args:
            params: KLineQuerySchema 查询参数

        Returns:
            K线数据列表
        """
        stmt = select(KLine).filter(
            KLine.symbol == params.symbol,
            KLine.interval == params.interval
        )

        if params.start_date:
            stmt = stmt.filter(KLine.date >= params.start_date)
        if params.end_date:
            stmt = stmt.filter(KLine.date <= params.end_date)

        stmt = stmt.order_by(KLine.date.desc()).limit(params.limit)

        result = self.session.execute(stmt).scalars().all()
        return list(reversed(list(result)))  # 按时间正序返回

    def get_all_latest_klines(
        self,
        interval: str = "1d",
        limit: int = 5000
    ) -> List[KLine]:
        """
        获取所有股票的最新 K 线数据

        使用子查询获取每只股票的最新日期，然后关联获取完整 K 线

        Args:
            interval: K 线周期
            limit: 最大返回数量

        Returns:
            每只股票最新一天 K 线数据的列表
        """
        from sqlalchemy import func, and_

        # 子查询：获取每只股票的最新日期
        subquery = self.session.query(
            KLine.symbol,
            func.max(KLine.date).label('max_date')
        ).filter(
            KLine.interval == interval
        ).group_by(
            KLine.symbol
        ).subquery()

        # 主查询：关联获取完整 K 线数据
        stmt = select(KLine).join(
            subquery,
            and_(
                KLine.symbol == subquery.c.symbol,
                KLine.date == subquery.c.max_date,
                KLine.interval == interval
            )
        ).limit(limit)

        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def bulk_insert(self, klines: List[KLine]) -> int:
        """
        批量插入K线数据

        Args:
            klines: K线数据列表

        Returns:
            成功插入的数量
        """
        # 过滤已存在的数据
        new_klines = []
        for kline in klines:
            existing = self.session.execute(
                select(KLine).filter_by(
                    symbol=kline.symbol,
                    interval=kline.interval,
                    date=kline.date
                )
            ).scalar_one_or_none()

            if not existing:
                new_klines.append(kline)

        if new_klines:
            self.add_all(new_klines)
            return len(new_klines)
        return 0


class SyncRecordRepository(BaseRepository[SyncRecord]):
    """同步记录仓库"""

    def __init__(self, session: Session):
        super().__init__(session, SyncRecord)

    def get_latest_sync(self, sync_type: str, **kwargs) -> Optional[SyncRecord]:
        """
        获取最新的同步记录

        Args:
            sync_type: 同步类型
            **kwargs: 其他过滤条件

        Returns:
            最新的同步记录
        """
        filters = {"sync_type": sync_type}
        filters.update(kwargs)

        stmt = select(SyncRecord).filter_by(**filters).order_by(
            SyncRecord.sync_time.desc()
        ).limit(1)

        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def get_sync_history(
        self,
        sync_type: str,
        limit: int = 100
    ) -> List[SyncRecord]:
        """
        获取同步历史记录

        Args:
            sync_type: 同步类型
            limit: 限制返回数量

        Returns:
            同步记录列表
        """
        stmt = select(SyncRecord).filter_by(
            sync_type=sync_type
        ).order_by(SyncRecord.sync_time.desc()).limit(limit)

        result = self.session.execute(stmt).scalars().all()
        return list(result)
