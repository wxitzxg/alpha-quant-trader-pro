# 股票市场管理模块设计文档

**日期：** 2026-03-15
**模块名称：** stock_market
**状态：** ✅ 设计完成，等待评审
**依赖模块：** data_sources（数据源聚合模块）

---

## 1. 需求概述

### 1.1 业务背景
股票市场管理模块位于量化交易系统的中层，负责：
1. **股票基础数据管理** - 维护A股市场所有股票的完整信息
2. **K线数据管理** - 存储和管理历史及实时K线数据

### 1.2 设计目标
- ✅ **持久化存储** - 使用 PostgreSQL 存储股票数据，支持历史查询
- ✅ **增量同步** - 按最后同步时间增量补充数据
- ✅ **并发处理** - 线程池并发同步多只股票
- ✅ **版本管理** - 使用 Alembic 管理数据库表结构变更
- ✅ **数据一致性** - 保证基础数据和K线数据的完整性

### 1.3 功能需求

#### 1.3.1 股票基础数据管理
- [x] 同步A股所有股票列表
- [x] 同步股票详细信息（名称、股本、行业、概念等）
- [x] 查询单只股票信息
- [x] 按行业/概念/地区筛选股票
- [x] 管理股票上市/退市状态

#### 1.3.2 K线数据管理
- [x] 同步单只股票K线数据（日线、5日线、10日线、月线）
- [x] 并发同步多只股票K线
- [x] 按时间范围查询K线数据
- [x] 增量补充缺失的K线数据
- [x] 支持不同周期的K线存储

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     量化交易系统 (alpha-quant-trader-pro)        │
│  ┌─────────────┬──────────────┬──────────────────────────────┐  │
│  │  策略引擎    │  回测模块     │  用户股票管理 (未来)           │  │
│  └──────┬──────┴──────┬───────┴────────────────┬─────────────┘  │
│         │              │                        │                │
│         └──────────────┼────────────────────────┘                │
│                        │                                         │
│         ┌──────────────▼─────────────────────────────┐          │
│         │         股票市场管理模块 (stock_market)      │          │
│         │  ┌───────────────────────────────────────┐  │          │
│         │  │        股票基础数据管理                 │  │          │
│         │  │  - 全量同步股票列表                    │  │          │
│         │  │  - 同步详细信息                        │  │          │
│         │  │  - 行业/概念筛选                       │  │          │
│         │  └──────────────┬────────────────────────┘  │          │
│         │                 │                            │          │
│         │  ┌──────────────▼────────────────────────┐  │          │
│         │  │         K线数据管理                    │  │          │
│         │  │  - 单股票同步                          │  │          │
│         │  │  - 多股票并发同步 (ThreadPool)        │  │          │
│         │  │  - 增量补充 (最后同步时间策略)         │  │          │
│         │  │  - 按日期范围查询                      │  │          │
│         │  └──────────────┬────────────────────────┘  │          │
│         │                 │                            │          │
│         │  ┌──────────────▼────────────────────────┐  │          │
│         │  │      数据访问层 (DAO)                   │  │          │
│         │  │  ┌─────────────────────────────────┐  │  │          │
│         │  │  │  SQLAlchemy ORM + Alembic      │  │  │          │
│         │  │  │  - 数据库连接池管理             │  │  │          │
│         │  │  │  - 自动迁移版本管理             │  │  │          │
│         │  │  │  - 数据缓存 (可选)              │  │  │          │
│         │  │  └──────────┬──────────────────────┘  │  │          │
│         │  └─────────────┼─────────────────────────┘  │          │
│         │                │                            │          │
│         └────────────────┼────────────────────────────┘          │
│                          │                                       │
│         ┌────────────────▼────────────────────────────┐         │
│         │      底层数据源 (data_sources)              │         │
│         │  DataSourceAggregator - 统一数据访问接口    │         │
│         │  - Tushare Pro  (优先级1)                   │         │
│         │  - AKShare      (优先级2)                   │         │
│         │  - 新浪财经     (优先级3)                   │         │
│         │  - 自动降级 + 重试机制                      │         │
│         └─────────────────────────────────────────────┘         │
│                                                                  │
│  📦 数据存储: PostgreSQL (SQLAlchemy + Alembic)                 │
│  ⚡ 并发处理: ThreadPoolExecutor (线程池)                         │
│  🔄 同步策略: 按最后同步时间增量同步                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **数据库** | PostgreSQL | 关系型数据库，支持复杂查询 |
| **ORM** | SQLAlchemy | Python ORM，模型定义和查询 |
| **迁移工具** | Alembic | 数据库版本管理和迁移 |
| **并发处理** | concurrent.futures.ThreadPoolExecutor | 线程池并发 |
| **数据源** | data_sources.DataSourceAggregator | 已有模块，统一数据访问 |
| **配置管理** | JSON + 环境变量 | 灵活的配置方式 |

---

## 3. 数据库设计

### 3.1 表结构

#### 3.1.1 股票基础信息表 (stocks)

```python
from sqlalchemy import Column, Integer, String, Date, Boolean, BigInteger, Numeric
from sqlalchemy.sql import func
from database import Base

class Stock(Base):
    """股票基础信息表"""
    __tablename__ = 'stocks'

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)  # 股票代码 (如: 600519)
    name = Column(String(50), nullable=False)                             # 股票名称 (如: 贵州茅台)
    exchange = Column(String(10), nullable=False)                         # 交易所 (SH: 上交所, SZ: 深交所)

    # 上市信息
    list_date = Column(Date, nullable=False)                              # 上市日期
    delist_date = Column(Date, nullable=True)                             # 退市日期 (未退市为 NULL)

    # 基本面信息
    total_shares = Column(BigInteger, nullable=True)                      # 总股本 (股)
    float_shares = Column(BigInteger, nullable=True)                      # 流通股本 (股)
    industry = Column(String(50), nullable=True)                          # 所属行业 (如: 食品饮料)
    concept = Column(String(200), nullable=True)                          # 概念板块 (逗号分隔: 白酒,央企改革)
    region = Column(String(50), nullable=True)                            # 所属地区 (如: 贵州)

    # 同步信息
    last_sync_time = Column(DateTime, nullable=True)                      # 最后同步时间
    is_active = Column(Boolean, default=True, nullable=False)             # 是否上市 (True: 上市, False: 退市)

    # 索引
    __table_args__ = (
        Index('idx_exchange', 'exchange'),
        Index('idx_industry', 'industry'),
        Index('idx_is_active', 'is_active'),
    )
```

**字段说明：**
- `symbol`: 股票代码，唯一索引，用于快速查询
- `exchange`: 区分沪市/深市，便于分类查询
- `concept`: 存储多个概念标签，逗号分隔
- `is_active`: 标记股票是否上市，退市股票标记为 False

---

#### 3.1.2 K线数据表 (klines)

```python
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey
from sqlalchemy import Index, UniqueConstraint, func
from sqlalchemy.sql import func
from database import Base

class KLine(Base):
    """K线数据表"""
    __tablename__ = 'klines'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)  # 关联股票ID
    symbol = Column(String(10), nullable=False, index=True)               # 股票代码 (冗余字段，加速查询)

    # 时间信息
    date = Column(Date, nullable=False, index=True)                       # 交易日期
    interval = Column(String(10), nullable=False, index=True)             # 周期: 1d, 5d, 10d, 1M

    # 价格信息
    open = Column(Numeric(10, 2), nullable=False)                         # 开盘价
    high = Column(Numeric(10, 2), nullable=False)                         # 最高价
    low = Column(Numeric(10, 2), nullable=False)                          # 最低价
    close = Column(Numeric(10, 2), nullable=False)                        # 收盘价

    # 成交量和成交额
    volume = Column(BigInteger, nullable=False)                           # 成交量 (股)
    amount = Column(Numeric(15, 2), nullable=True)                        # 成交额 (元)

    # 技术指标 (可选)
    ma5 = Column(Numeric(10, 2), nullable=True)                           # 5日均线
    ma10 = Column(Numeric(10, 2), nullable=True)                          # 10日均线
    turnover = Column(Numeric(8, 4), nullable=True)                       # 换手率 (%)

    # 数据源信息
    source = Column(String(20), nullable=True)                            # 数据源 (tushare/akshare/sina)

    # 同步信息
    sync_time = Column(DateTime, nullable=False, default=func.now())     # 同步时间

    # 约束
    __table_args__ = (
        UniqueConstraint('symbol', 'date', 'interval', name='uix_symbol_date_interval'),
        Index('idx_symbol_interval', 'symbol', 'interval'),
        Index('idx_date_interval', 'date', 'interval'),
    )
```

**字段说明：**
- `interval`: 支持的周期类型
  - `"1d"`: 日线
  - `"5d"`: 5日线（5日移动平均）
  - `"10d"`: 10日线（10日移动平均）
  - `"1M"`: 月线
- `stock_id`: 外键关联，保证数据完整性
- `symbol`: 冗余字段，避免频繁 JOIN 操作，提升查询性能
- `ma5/ma10`: 可选字段，可在同步时计算或后续批量计算

---

#### 3.1.3 同步记录表 (sync_records)

```python
class SyncRecord(Base):
    """同步记录表 - 记录每次同步操作"""
    __tablename__ = 'sync_records'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 同步类型
    sync_type = Column(String(20), nullable=False)                        # stocks: 股票列表, klines: K线数据
    symbol = Column(String(10), nullable=True)                            # 股票代码 (kline同步时)
    interval = Column(String(10), nullable=True)                          # K线周期 (kline同步时)

    # 时间范围
    start_date = Column(Date, nullable=True)                              # 同步开始日期
    end_date = Column(Date, nullable=True)                                # 同步结束日期

    # 执行结果
    status = Column(String(20), nullable=False)                           # success/failed/partial
    records_count = Column(Integer, default=0, nullable=False)           # 同步记录数
    error_message = Column(Text, nullable=True)                           # 错误信息 (失败时)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # 索引
    __table_args__ = (
        Index('idx_sync_type_created', 'sync_type', 'created_at'),
        Index('idx_symbol_interval', 'symbol', 'interval'),
    )
```

**字段说明：**
- `status`: 同步状态
  - `"success"`: 完全成功
  - `"failed"`: 完全失败
  - `"partial"`: 部分成功（如多股票同步时部分失败）
- `records_count`: 本次同步的数据条数
- 用于监控和调试同步任务

---

### 3.2 数据库迁移

使用 Alembic 管理数据库版本：

```bash
# 初始化迁移
alembic init migrations

# 生成初始迁移脚本
alembic revision --autogenerate -m "Initial schema"

# 应用迁移
alembic upgrade head
```

**迁移文件结构：**
```
migrations/
├── env.py                    # Alembic 环境配置
├── script.py.mako            # 迁移脚本模板
└── versions/
    ├── xxx_initial_schema.py        # 初始表结构
    ├── yyy_add_ma_columns.py        # 添加均线字段
    └── zzz_add_sync_records.py      # 添加同步记录表
```

---

## 4. 详细设计

### 4.1 数据库连接管理

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, db_url: str, pool_size: int = 10, max_overflow: int = 20):
        """
        初始化数据库连接

        Args:
            db_url: PostgreSQL 连接字符串
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
        """
        self.engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,      # 连接前检查可用性
            pool_recycle=3600,       # 1小时回收连接
            echo=False
        )

        self.session_factory = sessionmaker(bind=self.engine)
        self.scoped_session = scoped_session(self.session_factory)

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.scoped_session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def create_all(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    def drop_all(self):
        """删除所有表（测试用）"""
        Base.metadata.drop_all(self.engine)
```

---

### 4.2 股票基础数据管理

```python
# managers/stock_manager.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_
from models import Stock, SyncRecord
from database import DatabaseManager
from data_sources import DataSourceAggregator

class StockDataManager:
    """股票基础数据管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.aggregator = DataSourceAggregator()  # 复用已有数据源模块

    def sync_all_stocks(self, force_update: bool = False) -> int:
        """
        同步所有股票列表（全量）

        Args:
            force_update: 是否强制更新（覆盖现有数据）

        Returns:
            成功同步的股票数量
        """
        with self.db.get_session() as session:
            # 从数据源获取股票列表
            stock_list = self.aggregator.get_stock_list()

            success_count = 0
            for stock_data in stock_list:
                try:
                    # 检查是否已存在
                    existing = session.query(Stock).filter_by(
                        symbol=stock_data['symbol']
                    ).first()

                    if existing:
                        if force_update:
                            # 更新现有记录
                            for key, value in stock_data.items():
                                setattr(existing, key, value)
                            existing.last_sync_time = datetime.now()
                            success_count += 1
                    else:
                        # 新增股票
                        new_stock = Stock(**stock_data)
                        new_stock.last_sync_time = datetime.now()
                        session.add(new_stock)
                        success_count += 1

                except Exception as e:
                    logger.error(f"Failed to sync stock {stock_data.get('symbol')}: {e}")
                    continue

            # 记录同步日志
            self._log_sync(
                sync_type="stocks",
                status="success",
                records_count=success_count
            )

            return success_count

    def sync_stock_details(self, symbols: List[str]) -> int:
        """
        同步股票详细信息

        Args:
            symbols: 股票代码列表

        Returns:
            成功同步的数量
        """
        with self.db.get_session() as session:
            success_count = 0

            for symbol in symbols:
                try:
                    # 获取股票详细信息
                    detail = self.aggregator.get_stock_detail(symbol)

                    if detail:
                        stock = session.query(Stock).filter_by(symbol=symbol).first()
                        if stock:
                            # 更新详细信息
                            for key, value in detail.items():
                                setattr(stock, key, value)
                            stock.last_sync_time = datetime.now()
                            success_count += 1

                except Exception as e:
                    logger.error(f"Failed to sync detail for {symbol}: {e}")
                    continue

            return success_count

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """
        获取单只股票信息

        Args:
            symbol: 股票代码

        Returns:
            Stock 对象或 None
        """
        with self.db.get_session() as session:
            return session.query(Stock).filter_by(symbol=symbol).first()

    def get_stocks_by_industry(self, industry: str) -> List[Stock]:
        """
        按行业查询股票

        Args:
            industry: 行业名称

        Returns:
            股票列表
        """
        with self.db.get_session() as session:
            return session.query(Stock).filter_by(
                industry=industry,
                is_active=True
            ).all()

    def get_stocks_by_concept(self, concept: str) -> List[Stock]:
        """
        按概念查询股票

        Args:
            concept: 概念名称 (如: "白酒")

        Returns:
            股票列表
        """
        with self.db.get_session() as session:
            return session.query(Stock).filter(
                Stock.concept.contains(concept),
                Stock.is_active == True
            ).all()

    def get_active_stocks(self) -> List[Stock]:
        """
        获取所有上市股票

        Returns:
            股票列表
        """
        with self.db.get_session() as session:
            return session.query(Stock).filter_by(is_active=True).all()

    def _log_sync(self, sync_type: str, status: str, records_count: int, **kwargs):
        """记录同步日志"""
        with self.db.get_session() as session:
            record = SyncRecord(
                sync_type=sync_type,
                status=status,
                records_count=records_count,
                **kwargs
            )
            session.add(record)
```

---

### 4.3 K线数据管理

```python
# managers/kline_manager.py
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func
from models import KLine, SyncRecord
from database import DatabaseManager
from data_sources import DataSourceAggregator

class KLineDataManager:
    """K线数据管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.aggregator = DataSourceAggregator()

    def sync_single_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_update: bool = False
    ) -> int:
        """
        同步单只股票K线数据

        Args:
            symbol: 股票代码
            interval: 周期 (1d, 5d, 10d, 1M)
            start_date: 开始日期 (YYYY-MM-DD)，None 表示从最后同步时间开始
            end_date: 结束日期 (YYYY-MM-DD)，None 表示到今天
            force_update: 是否强制更新已存在的数据

        Returns:
            成功同步的K线数量
        """
        with self.db.get_session() as session:
            # 确定同步时间范围
            if start_date is None:
                # 增量同步：从最后同步时间开始
                start_date, end_date = self._get_incremental_range(session, symbol, interval)
            else:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()

            if start_date > end_date:
                logger.info(f"No data to sync for {symbol} {interval}")
                return 0

            # 从数据源获取K线数据
            klines = self.aggregator.get_kline(
                symbol=symbol,
                interval=interval,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            if not klines:
                logger.warning(f"No kline data returned for {symbol}")
                return 0

            success_count = 0
            for kline in klines:
                try:
                    # 检查是否已存在
                    existing = session.query(KLine).filter_by(
                        symbol=symbol,
                        date=kline.datetime.date(),
                        interval=interval
                    ).first()

                    if existing:
                        if force_update:
                            # 更新现有记录
                            existing.open = kline.open
                            existing.high = kline.high
                            existing.low = kline.low
                            existing.close = kline.close
                            existing.volume = kline.volume
                            existing.amount = kline.amount
                            existing.sync_time = datetime.now()
                            success_count += 1
                    else:
                        # 新增K线
                        new_kline = KLine(
                            symbol=symbol,
                            date=kline.datetime.date(),
                            interval=interval,
                            open=kline.open,
                            high=kline.high,
                            low=kline.low,
                            close=kline.close,
                            volume=kline.volume,
                            amount=kline.amount,
                            source=kline.source if hasattr(kline, 'source') else None,
                            sync_time=datetime.now()
                        )
                        session.add(new_kline)
                        success_count += 1

                except Exception as e:
                    logger.error(f"Failed to save kline for {symbol} on {kline.datetime}: {e}")
                    continue

            # 记录同步日志
            self._log_sync(
                sync_type="klines",
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
                status="success" if success_count > 0 else "failed",
                records_count=success_count
            )

            return success_count

    def _get_incremental_range(
        self,
        session,
        symbol: str,
        interval: str
    ) -> Tuple[date, date]:
        """
        获取增量同步的时间范围

        策略：
        1. 查询数据库中该股票+周期的最后同步时间
        2. 从最后同步时间的下一天开始同步
        3. 同步到当前日期

        Returns:
            (start_date, end_date)
        """
        # 查询最后一条记录
        last_kline = session.query(KLine).filter_by(
            symbol=symbol,
            interval=interval
        ).order_by(KLine.date.desc()).first()

        if last_kline:
            # 从最后一天的下一天开始
            start_date = last_kline.date + timedelta(days=1)
        else:
            # 首次同步，查询股票上市日期
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if stock and stock.list_date:
                start_date = stock.list_date
            else:
                # 默认从2010年1月1日开始
                start_date = date(2010, 1, 1)

        end_date = date.today()

        return start_date, end_date

    def query_klines(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: str = "asc"
    ) -> List[KLine]:
        """
        查询K线数据

        Args:
            symbol: 股票代码
            interval: 周期
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数量限制
            order_by: 排序 (asc: 升序, desc: 降序)

        Returns:
            KLine 对象列表
        """
        with self.db.get_session() as session:
            query = session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            )

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(KLine.date >= start)

            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(KLine.date <= end)

            if order_by == "desc":
                query = query.order_by(KLine.date.desc())
            else:
                query = query.order_by(KLine.date.asc())

            if limit:
                query = query.limit(limit)

            return query.all()

    def get_latest_kline(self, symbol: str, interval: str = "1d") -> Optional[KLine]:
        """
        获取最新的K线数据

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            最新的 KLine 对象或 None
        """
        with self.db.get_session() as session:
            return session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            ).order_by(KLine.date.desc()).first()

    def get_kline_count(self, symbol: str, interval: str = "1d") -> int:
        """
        获取K线数据条数

        Args:
            symbol: 股票代码
            interval: 周期

        Returns:
            K线数量
        """
        with self.db.get_session() as session:
            return session.query(KLine).filter_by(
                symbol=symbol,
                interval=interval
            ).count()

    def _log_sync(self, sync_type: str, status: str, records_count: int, **kwargs):
        """记录同步日志"""
        with self.db.get_session() as session:
            record = SyncRecord(
                sync_type=sync_type,
                status=status,
                records_count=records_count,
                **kwargs
            )
            session.add(record)
```

---

### 4.4 并发同步管理

```python
# sync/concurrent_sync.py
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime
import logging
from models import SyncRecord
from database import DatabaseManager

logger = logging.getLogger(__name__)

class ConcurrentSyncManager:
    """并发同步管理器"""

    def __init__(self, db_manager: DatabaseManager, max_workers: int = 5):
        """
        初始化并发同步管理器

        Args:
            db_manager: 数据库管理器
            max_workers: 线程池大小
        """
        self.db = db_manager
        self.max_workers = max_workers

    def sync_klines_concurrently(
        self,
        symbols: List[str],
        interval: str = "1d",
        max_workers: Optional[int] = None,
        **sync_kwargs
    ) -> Dict[str, dict]:
        """
        并发同步多只股票K线

        Args:
            symbols: 股票代码列表
            interval: 周期
            max_workers: 线程池大小（覆盖默认值）
            **sync_kwargs: 传递给 sync_single_kline 的参数

        Returns:
            {symbol: {"status": "success/failed", "count": int, "error": str}}
        """
        from managers.kline_manager import KLineDataManager

        max_workers = max_workers or self.max_workers
        results = {}
        manager = KLineDataManager(self.db)

        logger.info(f"Starting concurrent sync for {len(symbols)} stocks with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures: Dict[Future, str] = {}

            for symbol in symbols:
                future = executor.submit(
                    self._sync_single_kline_task,
                    manager,
                    symbol,
                    interval,
                    **sync_kwargs
                )
                futures[future] = symbol

            # 收集结果
            success_count = 0
            failed_count = 0

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    results[symbol] = result

                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failed_count += 1

                    logger.info(
                        f"[{success_count + failed_count}/{len(symbols)}] "
                        f"{symbol}: {result['status']} ({result.get('count', 0)} records)"
                    )

                except Exception as e:
                    failed_count += 1
                    results[symbol] = {
                        "status": "failed",
                        "error": str(e),
                        "count": 0
                    }
                    logger.error(f"Exception for {symbol}: {e}")

        # 记录总体同步日志
        self._log_batch_sync(
            sync_type="klines_batch",
            interval=interval,
            total_count=len(symbols),
            success_count=success_count,
            failed_count=failed_count,
            status="partial" if failed_count > 0 else "success"
        )

        logger.info(
            f"Concurrent sync completed: "
            f"{success_count} success, {failed_count} failed"
        )

        return results

    def _sync_single_kline_task(
        self,
        manager: KLineDataManager,
        symbol: str,
        interval: str,
        **sync_kwargs
    ) -> dict:
        """
        单个股票同步任务（线程池中执行）

        Args:
            manager: KLineDataManager 实例
            symbol: 股票代码
            interval: 周期
            **sync_kwargs: 同步参数

        Returns:
            {"status": "success/failed", "count": int, "error": str}
        """
        try:
            count = manager.sync_single_kline(
                symbol=symbol,
                interval=interval,
                **sync_kwargs
            )

            return {
                "status": "success",
                "count": count
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "count": 0
            }

    def _log_batch_sync(
        self,
        sync_type: str,
        interval: str,
        total_count: int,
        success_count: int,
        failed_count: int,
        status: str
    ):
        """记录批量同步日志"""
        with self.db.get_session() as session:
            record = SyncRecord(
                sync_type=sync_type,
                interval=interval,
                status=status,
                records_count=success_count,
                error_message=f"Failed: {failed_count}/{total_count}" if failed_count > 0 else None,
                created_at=datetime.now()
            )
            session.add(record)
```

---

### 4.5 增量同步策略

```python
# sync/incremental_sync.py
from typing import List, Dict, Optional
from datetime import date, timedelta
from models import KLine
from database import DatabaseManager

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
                from models import Stock
                stock = session.query(Stock).filter_by(symbol=symbol).first()
                start_date = stock.list_date if stock else date(2010, 1, 1)

            if not end_date:
                end_date = date.today()

            # 生成所有交易日期（跳过周末）
            expected_dates = []
            current = start_date

            while current <= end_date:
                # 跳过周末
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
```

---

### 4.6 工具函数

```python
# utils/date_utils.py
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
```

---

## 5. 使用示例

### 5.1 初始化模块

```python
# 初始化数据库
from database import DatabaseManager
from managers.stock_manager import StockDataManager
from managers.kline_manager import KLineDataManager
from sync.concurrent_sync import ConcurrentSyncManager

# 数据库连接
db_manager = DatabaseManager(
    db_url="postgresql://user:password@localhost:5432/stock_db",
    pool_size=10
)

# 创建表
db_manager.create_all()

# 初始化管理器
stock_manager = StockDataManager(db_manager)
kline_manager = KLineDataManager(db_manager)
sync_manager = ConcurrentSyncManager(db_manager, max_workers=5)
```

---

### 5.2 同步股票基础数据

```python
# 全量同步所有股票
count = stock_manager.sync_all_stocks(force_update=False)
print(f"Synced {count} stocks")

# 同步股票详细信息
stocks = stock_manager.get_active_stocks()
symbols = [s.symbol for s in stocks[:100]]  # 前100只
count = stock_manager.sync_stock_details(symbols)
print(f"Synced details for {count} stocks")

# 按行业查询
bank_stocks = stock_manager.get_stocks_by_industry("银行")
print(f"Found {len(bank_stocks)} bank stocks")
```

---

### 5.3 同步K线数据

```python
# 单只股票同步
count = kline_manager.sync_single_kline(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
print(f"Synced {count} klines for 600519")

# 增量同步（从最后同步时间到今天）
count = kline_manager.sync_single_kline(symbol="600519", interval="1d")
print(f"Synced {count} klines (incremental)")

# 并发同步多只股票
symbols = ["600519", "000001", "601318", "300750", "688981"]
results = sync_manager.sync_klines_concurrently(
    symbols=symbols,
    interval="1d",
    max_workers=3
)

for symbol, result in results.items():
    print(f"{symbol}: {result['status']} ({result.get('count', 0)} records)")
```

---

### 5.4 查询K线数据

```python
# 查询日线数据
klines = kline_manager.query_klines(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
print(f"Found {len(klines)} klines")

# 查询最新K线
latest = kline_manager.get_latest_kline("600519", "1d")
print(f"Latest close: {latest.close}")

# 查询月线数据
monthly_klines = kline_manager.query_klines(
    symbol="600519",
    interval="1M",
    start_date="2020-01-01"
)
```

---

### 5.5 数据完整性检查

```python
from sync.incremental_sync import IncrementalSyncStrategy

strategy = IncrementalSyncStrategy(db_manager)

# 检查缺失的日期
missing_dates = strategy.get_missing_dates(
    symbol="600519",
    interval="1d",
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

print(f"Missing {len(missing_dates)} dates")
for d in missing_dates[:10]:  # 打印前10个
    print(f"  - {d}")

# 获取同步缺口
gaps = strategy.get_sync_gaps("600519", "1d")
for gap in gaps:
    print(f"Gap: {gap['start']} to {gap['end']}")
```

---

## 6. 目录结构

```
stock_market/
├── __init__.py
├── database.py                  # 数据库连接管理
├── models.py                    # SQLAlchemy 模型
├── config/
│   └── database.json            # 数据库配置
├── managers/                    # 数据管理器
│   ├── __init__.py
│   ├── stock_manager.py        # 股票基础数据管理
│   └── kline_manager.py        # K线数据管理
├── sync/                        # 同步模块
│   ├── __init__.py
│   ├── concurrent_sync.py      # 并发同步管理
│   └── incremental_sync.py     # 增量同步策略
├── utils/                       # 工具函数
│   ├── __init__.py
│   └── date_utils.py           # 日期处理
├── migrations/                  # Alembic 迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── xxx_initial_schema.py
└── examples/                    # 使用示例
    └── usage_example.py

tests/                           # 测试
├── __init__.py
├── test_models.py
├── test_stock_manager.py
├── test_kline_manager.py
└── test_concurrent_sync.py

scripts/                         # 运维脚本
├── sync_all_stocks.py          # 全量同步股票列表
├── sync_all_klines.py          # 全量同步所有K线
└── check_data_integrity.py     # 检查数据完整性
```

---

## 7. 配置文件

### 7.1 数据库配置 (config/database.json)

```json
{
  "database": {
    "url": "postgresql://stock_user:password@localhost:5432/stock_db",
    "pool_size": 10,
    "max_overflow": 20,
    "echo": false,
    "pool_pre_ping": true,
    "pool_recycle": 3600
  },
  "sync": {
    "kline": {
      "max_workers": 5,
      "batch_size": 1000,
      "retry_times": 3,
      "retry_delay": 1
    },
    "stock": {
      "batch_size": 500
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/stock_market.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

---

### 7.2 Alembic 配置 (migrations/alembic.ini)

```ini
[alembic]
script_location = migrations
prepend_sys_path = .

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualName =

[logger_sqlalchemy]
level = WARN
handlers =
qualName = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualName = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

## 8. 测试策略

### 8.1 单元测试

```python
# tests/test_models.py
def test_stock_model_creation():
    """测试股票模型创建"""
    stock = Stock(
        symbol="600519",
        name="贵州茅台",
        exchange="SH",
        list_date=date(2001, 8, 27),
        industry="食品饮料",
        is_active=True
    )
    assert stock.symbol == "600519"
    assert stock.name == "贵州茅台"

# tests/test_kline_manager.py
def test_sync_single_kline():
    """测试单只股票K线同步"""
    manager = KLineDataManager(mock_db)
    count = manager.sync_single_kline("600519", interval="1d")
    assert count > 0
```

### 8.2 集成测试

```python
def test_concurrent_sync():
    """测试并发同步"""
    manager = ConcurrentSyncManager(mock_db, max_workers=3)
    symbols = ["600519", "000001", "601318"]
    results = manager.sync_klines_concurrently(symbols, interval="1d")

    assert len(results) == 3
    assert all(r["status"] in ["success", "failed"] for r in results.values())
```

### 8.3 测试覆盖率目标

- **单元测试覆盖率**: 80%+
- **关键路径**: 增量同步、并发同步、数据库操作
- **边界测试**: 空数据、异常日期、超大数据量

---

## 9. 部署和运维

### 9.1 数据库初始化

```bash
# 创建数据库
createdb -U postgres stock_db

# 应用初始迁移
cd stock_market
alembic upgrade head

# 或者直接创建表
python -c "from database import DatabaseManager; db = DatabaseManager('postgresql://...'); db.create_all()"
```

---

### 9.2 定时同步任务

```python
# scripts/sync_daily.py
"""每日定时同步脚本"""

from managers.stock_manager import StockDataManager
from managers.kline_manager import KLineDataManager
from database import DatabaseManager
import schedule
import time

db_manager = DatabaseManager("postgresql://...")
stock_manager = StockDataManager(db_manager)
kline_manager = KLineDataManager(db_manager)

def sync_stocks():
    """同步股票列表"""
    count = stock_manager.sync_all_stocks()
    print(f"Synced {count} stocks")

def sync_latest_klines():
    """同步最新K线数据"""
    stocks = stock_manager.get_active_stocks()
    symbols = [s.symbol for s in stocks]

    for symbol in symbols:
        try:
            count = kline_manager.sync_single_kline(symbol, interval="1d")
            if count > 0:
                print(f"Synced {count} klines for {symbol}")
        except Exception as e:
            print(f"Failed to sync {symbol}: {e}")

# 每天 9:00 同步股票列表
schedule.every().day.at("09:00").do(sync_stocks)

# 每天 18:00 同步最新K线
schedule.every().day.at("18:00").do(sync_latest_klines)

# 运行定时任务
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

### 9.3 监控和告警

```python
# 监控同步失败率
def check_sync_health():
    """检查同步健康度"""
    from models import SyncRecord

    with db_manager.get_session() as session:
        # 查询最近24小时的同步记录
        yesterday = datetime.now() - timedelta(hours=24)
        records = session.query(SyncRecord).filter(
            SyncRecord.created_at >= yesterday
        ).all()

        total = len(records)
        failed = sum(1 for r in records if r.status == "failed")

        failure_rate = failed / total if total > 0 else 0

        if failure_rate > 0.1:  # 失败率超过10%
            send_alert(f"Sync failure rate: {failure_rate:.2%}")
```

---

## 10. 性能优化建议

### 10.1 数据库优化

- **索引优化**:
  - `symbol + date + interval` 联合唯一索引
  - `symbol + interval` 查询索引
  - `date + interval` 范围查询索引

- **分区表** (大数据量时):
  - 按年份或月份分区 KLine 表
  - 提升查询性能和维护效率

### 10.2 缓存策略

- **Redis 缓存**:
  - 缓存热门股票的最新K线（TTL 5分钟）
  - 缓存股票基础信息（TTL 1小时）
  - 减少数据库查询压力

### 10.3 批量操作

- **批量插入**:
  ```python
  session.bulk_insert_mappings(KLine, kline_dicts)
  session.commit()
  ```

- **批量更新**:
  ```python
  session.bulk_update_mappings(KLine, update_dicts)
  ```

---

## 11. 扩展性设计

### 11.1 新增K线周期

只需在同步时指定新的 `interval` 值，数据库自动支持：

```python
# 支持周线
kline_manager.sync_single_kline(symbol="600519", interval="1w")
```

### 11.2 新增技术指标

在 `KLine` 模型中添加字段，然后：

1. 生成 Alembic 迁移：`alembic revision --autogenerate -m "Add technical indicators"`
2. 应用迁移：`alembic upgrade head`
3. 在同步时计算并保存指标

### 11.3 数据源扩展

复用 `data_sources` 模块，新增数据源只需：

1. 在 `data_sources/adapters/` 添加新的适配器
2. 在 `config/sources.json` 配置优先级
3. 无需修改 `stock_market` 模块

---

## 12. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| **数据库连接耗尽** | 高 | 连接池管理 + 超时控制 + 重试机制 |
| **数据源API限流** | 高 | 自动降级 + 指数退避重试 + 多源备份 |
| **数据不一致** | 中 | 唯一约束 + 事务管理 + 数据校验 |
| **并发冲突** | 中 | 数据库锁 + 乐观锁 + 幂等设计 |
| **大表性能** | 中 | 索引优化 + 分区表 + 定期清理 |
| **同步失败** | 中 | 失败重试 + 增量补偿 + 监控告警 |

---

## 13. 实施计划

### Phase 1: 基础框架 (1-2天)
- [ ] 创建项目结构
- [ ] 实现数据库模型
- [ ] 配置 Alembic 迁移
- [ ] 实现数据库连接管理

### Phase 2: 核心功能 (3-4天)
- [ ] 实现 StockDataManager
- [ ] 实现 KLineDataManager
- [ ] 实现增量同步策略
- [ ] 实现并发同步管理

### Phase 3: 工具和优化 (2-3天)
- [ ] 实现工具函数（日期处理等）
- [ ] 添加日志和监控
- [ ] 性能优化（索引、缓存）
- [ ] 编写使用文档

### Phase 4: 测试和部署 (2-3天)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 数据完整性检查
- [ ] 部署脚本

**总预计时间**: 8-12 天

---

## 14. 设计审批

- [x] 架构设计 ✓
- [x] 数据库设计 ✓
- [x] 接口设计 ✓
- [x] 并发策略 ✓
- [x] 增量同步策略 ✓
- [x] 扩展性设计 ✓

**审批人**: _________________
**日期**: _________________

---

## 附录

### A. 依赖包

```txt
sqlalchemy>=2.0.0
alembic>=1.10.0
psycopg2-binary>=2.9.0
pandas>=2.0.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
schedule>=1.1.0
```

### B. 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/stock_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/stock_market.log

# 并发配置
SYNC_MAX_WORKERS=5
```

### C. 参考资料

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
