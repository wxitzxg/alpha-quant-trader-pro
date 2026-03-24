"""
数据库模型定义
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Date, Boolean, BigInteger,
    Numeric, DateTime, ForeignKey, Index, UniqueConstraint, Text
)
from sqlalchemy.sql import func
from stock_market.database import Base

class Stock(Base):
    """股票基础信息表"""
    __tablename__ = 'stocks'

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)  # 股票代码
    name = Column(String(50), nullable=False)                             # 股票名称
    exchange = Column(String(10), nullable=False)                         # 交易所

    # 上市信息
    list_date = Column(Date, nullable=False)                              # 上市日期
    delist_date = Column(Date, nullable=True)                             # 退市日期

    # 基本面信息
    total_shares = Column(BigInteger, nullable=True)                      # 总股本
    float_shares = Column(BigInteger, nullable=True)                      # 流通股本
    industry = Column(String(50), nullable=True)                          # 所属行业
    concept = Column(String(200), nullable=True)                          # 概念板块
    region = Column(String(50), nullable=True)                            # 所属地区

    # 同步信息
    last_sync_time = Column(DateTime, nullable=True)                      # 最后同步时间
    is_active = Column(Boolean, default=True, nullable=False)             # 是否上市

    # 索引
    __table_args__ = (
        Index('idx_exchange', 'exchange'),
        Index('idx_industry', 'industry'),
        Index('idx_is_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Stock({self.symbol}, {self.name})>"


class KLine(Base):
    """K线数据表"""
    __tablename__ = 'klines'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    symbol = Column(String(10), nullable=False, index=True)               # 股票代码（冗余）

    # 时间信息
    date = Column(Date, nullable=False, index=True)                       # 交易日期
    interval = Column(String(10), nullable=False, index=True)             # 周期

    # 价格信息
    open = Column(Numeric(10, 2), nullable=False)
    high = Column(Numeric(10, 2), nullable=False)
    low = Column(Numeric(10, 2), nullable=False)
    close = Column(Numeric(10, 2), nullable=False)

    # 成交量和成交额
    volume = Column(BigInteger, nullable=False)
    amount = Column(Numeric(15, 2), nullable=True)

    # 技术指标
    ma5 = Column(Numeric(10, 2), nullable=True)                           # 5日均线
    ma10 = Column(Numeric(10, 2), nullable=True)                          # 10日均线
    turnover = Column(Numeric(8, 4), nullable=True)                       # 换手率

    # 数据源信息
    source = Column(String(20), nullable=True)                            # 数据源

    # 同步信息
    sync_time = Column(DateTime, nullable=False, default=func.now())

    # 约束
    __table_args__ = (
        UniqueConstraint('symbol', 'date', 'interval', name='uix_symbol_date_interval'),
        Index('idx_kline_symbol_interval', 'symbol', 'interval'),
        Index('idx_date_interval', 'date', 'interval'),
    )

    def __repr__(self):
        return f"<KLine({self.symbol}, {self.date}, {self.interval})>"


class SyncRecord(Base):
    """同步记录表"""
    __tablename__ = 'sync_records'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 同步类型
    sync_type = Column(String(20), nullable=False)
    symbol = Column(String(10), nullable=True)
    interval = Column(String(10), nullable=True)

    # 时间范围
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # 执行结果
    status = Column(String(20), nullable=False)
    records_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # 索引
    __table_args__ = (
        Index('idx_sync_type_created', 'sync_type', 'created_at'),
        Index('idx_sync_symbol_interval', 'symbol', 'interval'),
    )

    def __repr__(self):
        return f"<SyncRecord({self.sync_type}, {self.status})>"
