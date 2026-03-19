# 股票市场管理模块实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现股票市场管理模块，提供股票基础数据管理和K线数据管理功能，支持持久化存储、增量同步和并发处理

**Architecture:** 基于 SQLAlchemy ORM 和 PostgreSQL 的三层架构，包括数据访问层、业务逻辑层和并发同步层，复用已有的 data_sources 模块作为底层数据源

**Tech Stack:** Python, PostgreSQL, SQLAlchemy, Alembic, ThreadPoolExecutor, Pydantic

**依赖:** data_sources 模块（需先补充股票列表接口）

---

## 预备任务：补充 data_sources 模块

### 任务 0.1: 在 base.py 中添加股票列表抽象接口

**Files:**
- Modify: `data_sources/base.py`

- [x] **Step 1: 添加 get_stock_list() 抽象方法**

在 `DataSourceAdapter` 类中添加：

```python
@abstractmethod
def get_stock_list(self) -> List[Dict]:
    """
    获取股票列表

    Returns:
        股票列表，每个股票为字典，包含:
        - symbol: 股票代码 (如 "600519")
        - name: 股票名称 (如 "贵州茅台")
        - exchange: 交易所 (如 "SH", "SZ")
        - list_date: 上市日期 (如 "2001-08-27")
        - industry: 所属行业 (可选)
        - concept: 概念板块 (可选)
        - region: 所属地区 (可选)

    Raises:
        DataSourceError: 数据源异常
    """
    pass
```

- [x] **Step 2: 添加 get_stock_detail(symbol) 抽象方法**

```python
@abstractmethod
def get_stock_detail(self, symbol: str) -> Optional[Dict]:
    """
    获取股票详细信息

    Args:
        symbol: 股票代码

    Returns:
        股票详细信息字典，包含:
        - symbol: 股票代码
        - name: 股票名称
        - exchange: 交易所
        - list_date: 上市日期
        - delist_date: 退市日期 (可选)
        - total_shares: 总股本 (可选)
        - float_shares: 流通股本 (可选)
        - industry: 所属行业 (可选)
        - concept: 概念板块 (可选)
        - region: 所属地区 (可选)
        - 更多字段...

    Raises:
        DataSourceError: 数据源异常
    """
    pass
```

- [x] **Step 3: 提交**

```bash
git add data_sources/base.py
git commit -m "feat: add stock list abstract methods to DataSourceAdapter"
```

---

### 任务 0.2: 在 TushareAdapter 中实现股票列表接口

**Files:**
- Modify: `data_sources/adapters/tushare_adapter.py`

- [x] **Step 1: 实现 get_stock_list() 方法**

```python
def get_stock_list(self) -> List[Dict]:
    """
    获取股票列表

    使用 Tushare 的 stock_basic 接口
    """
    try:
        # 获取基础股票列表
        df = self.pro.stock_basic(
            fields='ts_code,symbol,name,area,industry,list_date,market'
        )

        stock_list = []
        for _, row in df.iterrows():
            # 转换 Tushare 格式到标准格式
            ts_code = row['ts_code']  # 如: 600519.SH
            symbol = row['symbol']     # 如: 600519

            stock = {
                "symbol": symbol,
                "name": row['name'],
                "exchange": "SH" if ts_code.endswith(".SH") else "SZ",
                "list_date": row['list_date'],  # YYYYMMDD 格式
                "industry": row['industry'] if row['industry'] else None,
                "region": row['area'] if row['area'] else None,
                "market": row['market']  # 主板/创业板/科创板等
            }
            stock_list.append(stock)

        logger.info(f"Fetched {len(stock_list)} stocks from Tushare")
        return stock_list

    except Exception as e:
        logger.error(f"Failed to get stock list from Tushare: {e}")
        raise DataSourceError("tushare", f"Failed to get stock list: {e}", e)
```

- [x] **Step 2: 实现 get_stock_detail(symbol) 方法**

```python
def get_stock_detail(self, symbol: str) -> Optional[Dict]:
    """
    获取股票详细信息

    使用 Tushare 的 stock_basic 接口
    """
    try:
        ts_code = self._format_symbol(symbol)

        df = self.pro.stock_basic(
            ts_code=ts_code,
            fields='ts_code,symbol,name,area,industry,list_date,total_share,float_share'
        )

        if len(df) == 0:
            logger.warning(f"No stock detail found for {symbol}")
            return None

        row = df.iloc[0]

        return {
            "symbol": row['symbol'],
            "name": row['name'],
            "exchange": "SH" if ts_code.endswith(".SH") else "SZ",
            "list_date": row['list_date'],
            "delist_date": None,  # Tushare 不直接提供退市日期
            "total_shares": int(row['total_share'] * 10000) if row['total_share'] else None,  # 万股 -> 股
            "float_shares": int(row['float_share'] * 10000) if row['float_share'] else None,  # 万股 -> 股
            "industry": row['industry'] if row['industry'] else None,
            "concept": None,  # Tushare 不直接提供概念
            "region": row['area'] if row['area'] else None
        }

    except Exception as e:
        logger.error(f"Failed to get stock detail for {symbol}: {e}")
        raise DataSourceError("tushare", f"Failed to get stock detail: {e}", e)
```

- [x] **Step 3: 提交**

```bash
git add data_sources/adapters/tushare_adapter.py
git commit -m "feat: implement stock list methods in TushareAdapter"
```

---

## Chunk 1: 基础框架和数据库模型

### 任务 1.1: 创建项目目录结构

**Files:**
- Create: `stock_market/__init__.py`
- Create: `stock_market/database.py`
- Create: `stock_market/models.py`
- Create: `stock_market/config/__init__.py`
- Create: `stock_market/config/database.json`
- Create: `stock_market/managers/__init__.py`
- Create: `stock_market/sync/__init__.py`
- Create: `stock_market/utils/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建 stock_market 目录**

```bash
mkdir -p stock_market/{managers,sync,utils,config}
touch stock_market/__init__.py
touch stock_market/managers/__init__.py
touch stock_market/sync/__init__.py
touch stock_market/utils/__init__.py
touch stock_market/config/__init__.py
```

- [ ] **Step 2: 创建 tests 目录**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 3: 验证目录结构**

```bash
ls -la stock_market/
```

Expected output:
```
database.py
managers/
models.py
config/
sync/
utils/
```

- [ ] **Step 4: 提交**

```bash
git add stock_market/ tests/
git commit -m "chore: create stock_market module directory structure"
```

---

### 任务 1.2: 实现数据库连接管理

**Files:**
- Create: `stock_market/database.py`

- [ ] **Step 1: 编写 database.py**

```python
"""
数据库连接管理模块
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)
Base = declarative_base()

class DatabaseManager:
    """数据库连接管理器"""

    def __init__(
        self,
        db_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False
    ):
        """
        初始化数据库连接

        Args:
            db_url: PostgreSQL 连接字符串
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            echo: 是否输出 SQL 日志
        """
        self.engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,      # 连接前检查可用性
            pool_recycle=3600,       # 1小时回收连接
            echo=echo
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
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
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def create_all(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        logger.info("All tables created successfully")

    def drop_all(self):
        """删除所有表（测试用）"""
        Base.metadata.drop_all(self.engine)
        logger.info("All tables dropped")
```

- [ ] **Step 2: 在 stock_market/__init__.py 中导出**

```python
from stock_market.database import DatabaseManager
from stock_market.models import Stock, KLine, SyncRecord

__all__ = [
    'DatabaseManager',
    'Stock',
    'KLine',
    'SyncRecord',
]
```

- [ ] **Step 3: 创建配置文件**

```bash
cat > stock_market/config/database.json << 'EOF'
{
  "database": {
    "url": "postgresql://stock_user:stock_pass@localhost:5432/stock_db",
    "pool_size": 10,
    "max_overflow": 20,
    "echo": false
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
  }
}
EOF
```

- [ ] **Step 4: 提交**

```bash
git add stock_market/database.py stock_market/__init__.py stock_market/config/database.json
git commit -m "feat: implement database connection manager with SQLAlchemy"
```

---

### 任务 1.3: 实现数据库模型

**Files:**
- Create: `stock_market/models.py`

- [ ] **Step 1: 编写 models.py**

```python
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
        Index('idx_symbol_interval', 'symbol', 'interval'),
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
        Index('idx_symbol_interval', 'symbol', 'interval'),
    )

    def __repr__(self):
        return f"<SyncRecord({self.sync_type}, {self.status})>"
```

- [ ] **Step 2: 测试模型导入**

```bash
python -c "from stock_market.models import Stock, KLine, SyncRecord; print('Models imported successfully')"
```

Expected output:
```
Models imported successfully
```

- [ ] **Step 3: 提交**

```bash
git add stock_market/models.py
git commit -m "feat: implement database models (Stock, KLine, SyncRecord)"
```

---

### 任务 1.4: 配置 Alembic 数据库迁移

**Files:**
- Create: `stock_market/migrations/alembic.ini`
- Create: `stock_market/migrations/env.py`
- Create: `stock_market/migrations/script.py.mako`
- Create: `stock_market/migrations/versions/__init__.py`

- [ ] **Step 1: 初始化 Alembic**

```bash
cd stock_market
alembic init migrations
```

- [ ] **Step 2: 修改 alembic.ini 配置**

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

- [ ] **Step 3: 修改 migrations/env.py**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from stock_market.database import Base
from stock_market.models import Stock, KLine, SyncRecord
from stock_market.config.database import load_config

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 创建配置加载模块**

```bash
cat > stock_market/config/__init__.py << 'EOF'
"""
配置加载模块
"""
import json
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(__file__).parent / "database.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
EOF
```

- [ ] **Step 5: 生成初始迁移脚本**

```bash
alembic revision --autogenerate -m "initial_schema"
```

- [ ] **Step 6: 提交**

```bash
git add stock_market/migrations/
git commit -m "feat: configure Alembic for database migrations"
```

---

### 任务 1.5: 编写数据库模型测试

**Files:**
- Create: `tests/test_models.py`

- [ ] **Step 1: 编写测试文件**

```python
"""
数据库模型测试
"""
import pytest
from datetime import date, datetime
from stock_market.models import Stock, KLine, SyncRecord


class TestStockModel:
    """Stock 模型测试"""

    def test_create_stock(self):
        """测试创建股票记录"""
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
        assert stock.exchange == "SH"
        assert stock.list_date == date(2001, 8, 27)
        assert stock.industry == "食品饮料"
        assert stock.is_active is True

    def test_stock_with_details(self):
        """测试创建包含详细信息的股票记录"""
        stock = Stock(
            symbol="000001",
            name="平安银行",
            exchange="SZ",
            list_date=date(1991, 4, 3),
            delist_date=None,
            total_shares=19405918198,
            float_shares=19405918198,
            industry="银行",
            concept="金融,深圳",
            region="广东",
            is_active=True
        )

        assert stock.total_shares == 19405918198
        assert stock.industry == "银行"
        assert stock.concept == "金融,深圳"
        assert stock.region == "广东"

    def test_stock_repr(self):
        """测试股票的字符串表示"""
        stock = Stock(symbol="600519", name="贵州茅台")
        assert repr(stock) == "<Stock(600519, 贵州茅台)>"


class TestKLineModel:
    """KLine 模型测试"""

    def test_create_kline(self):
        """测试创建K线记录"""
        kline = KLine(
            symbol="600519",
            date=date(2023, 12, 29),
            interval="1d",
            open=1750.00,
            high=1765.00,
            low=1745.00,
            close=1758.00,
            volume=1234567,
            amount=2165432100.00,
            source="tushare"
        )

        assert kline.symbol == "600519"
        assert kline.date == date(2023, 12, 29)
        assert kline.interval == "1d"
        assert kline.open == 1750.00
        assert kline.close == 1758.00
        assert kline.volume == 1234567
        assert kline.source == "tushare"

    def test_kline_with_technical_indicators(self):
        """测试包含技术指标的K线"""
        kline = KLine(
            symbol="600519",
            date=date(2023, 12, 29),
            interval="1d",
            open=1750.00,
            high=1765.00,
            low=1745.00,
            close=1758.00,
            volume=1234567,
            amount=2165432100.00,
            ma5=1755.00,
            ma10=1750.00,
            turnover=0.1234
        )

        assert kline.ma5 == 1755.00
        assert kline.ma10 == 1750.00
        assert kline.turnover == 0.1234

    def test_kline_repr(self):
        """测试K线的字符串表示"""
        kline = KLine(symbol="600519", date=date(2023, 12, 29), interval="1d")
        assert repr(kline) == "<KLine(600519, 2023-12-29, 1d)>"


class TestSyncRecordModel:
    """SyncRecord 模型测试"""

    def test_create_sync_record(self):
        """测试创建同步记录"""
        record = SyncRecord(
            sync_type="klines",
            symbol="600519",
            interval="1d",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            status="success",
            records_count=245
        )

        assert record.sync_type == "klines"
        assert record.symbol == "600519"
        assert record.interval == "1d"
        assert record.status == "success"
        assert record.records_count == 245

    def test_sync_record_with_error(self):
        """测试包含错误信息的同步记录"""
        record = SyncRecord(
            sync_type="stocks",
            status="failed",
            error_message="API timeout",
            records_count=0
        )

        assert record.status == "failed"
        assert record.error_message == "API timeout"

    def test_sync_record_repr(self):
        """测试同步记录的字符串表示"""
        record = SyncRecord(sync_type="klines", status="success")
        assert repr(record) == "<SyncRecord(klines, success)>"
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/test_models.py -v
```

Expected output:
```
test_models.py::TestStockModel::test_create_stock PASSED
test_models.py::TestStockModel::test_stock_with_details PASSED
test_models.py::TestStockModel::test_stock_repr PASSED
test_models.py::TestKLineModel::test_create_kline PASSED
test_models.py::TestKLineModel::test_kline_with_technical_indicators PASSED
test_models.py::TestKLineModel::test_kline_repr PASSED
test_models.py::TestSyncRecordModel::test_create_sync_record PASSED
test_models.py::TestSyncRecordModel::test_sync_record_with_error PASSED
test_models.py::TestSyncRecordModel::test_sync_record_repr PASSED
```

- [ ] **Step 3: 提交**

```bash
git add tests/test_models.py
git commit -m "test: add unit tests for database models"
```

---

## Chunk 2: 核心业务逻辑实现

### 任务 2.1: 实现股票基础数据管理器

**Files:**
- Create: `stock_market/managers/stock_manager.py`

- [ ] **Step 1: 编写 StockDataManager**

```python
"""
股票基础数据管理模块
"""
import logging
from typing import List, Optional
from datetime import datetime
from stock_market.database import DatabaseManager
from stock_market.models import Stock, SyncRecord

logger = logging.getLogger(__name__)


class StockDataManager:
    """股票基础数据管理器"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化股票数据管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager

    def sync_all_stocks(self, force_update: bool = False) -> int:
        """
        同步所有股票列表（全量）

        Args:
            force_update: 是否强制更新（覆盖现有数据）

        Returns:
            成功同步的股票数量
        """
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        with self.db.get_session() as session:
            # 从数据源获取股票列表
            try:
                stock_list = aggregator.get_stock_list()
            except Exception as e:
                logger.error(f"Failed to get stock list from data source: {e}")
                return 0

            if not stock_list:
                logger.warning("Empty stock list returned from data source")
                return 0

            success_count = 0
            for stock_data in stock_list:
                try:
                    symbol = stock_data.get('symbol')
                    if not symbol:
                        continue

                    # 检查是否已存在
                    existing = session.query(Stock).filter_by(symbol=symbol).first()

                    if existing:
                        if force_update:
                            # 更新现有记录
                            for key, value in stock_data.items():
                                if hasattr(existing, key):
                                    setattr(existing, key, value)
                            existing.last_sync_time = datetime.now()
                            success_count += 1
                            logger.debug(f"Updated stock: {symbol}")
                    else:
                        # 新增股票
                        stock = Stock(**stock_data)
                        stock.last_sync_time = datetime.now()
                        session.add(stock)
                        success_count += 1
                        logger.debug(f"Added new stock: {symbol}")

                except Exception as e:
                    logger.error(f"Failed to sync stock {stock_data.get('symbol')}: {e}")
                    continue

            # 记录同步日志
            self._log_sync(
                sync_type="stocks",
                status="success",
                records_count=success_count
            )

            logger.info(f"Synced {success_count} stocks")
            return success_count

    def sync_stock_details(self, symbols: List[str]) -> int:
        """
        同步股票详细信息

        Args:
            symbols: 股票代码列表

        Returns:
            成功同步的数量
        """
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        with self.db.get_session() as session:
            success_count = 0

            for symbol in symbols:
                try:
                    # 获取股票详细信息
                    detail = aggregator.get_stock_detail(symbol)

                    if detail:
                        stock = session.query(Stock).filter_by(symbol=symbol).first()
                        if stock:
                            # 更新详细信息
                            for key, value in detail.items():
                                if hasattr(stock, key):
                                    setattr(stock, key, value)
                            stock.last_sync_time = datetime.now()
                            success_count += 1
                            logger.debug(f"Synced detail for {symbol}")

                except Exception as e:
                    logger.error(f"Failed to sync detail for {symbol}: {e}")
                    continue

            logger.info(f"Synced details for {success_count} stocks")
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

- [ ] **Step 2: 在 managers/__init__.py 中导出**

```python
from stock_market.managers.stock_manager import StockDataManager

__all__ = ['StockDataManager']
```

- [ ] **Step 3: 测试导入**

```bash
python -c "from stock_market.managers import StockDataManager; print('StockDataManager imported successfully')"
```

Expected output:
```
StockDataManager imported successfully
```

- [ ] **Step 4: 提交**

```bash
git add stock_market/managers/stock_manager.py stock_market/managers/__init__.py
git commit -m "feat: implement StockDataManager for basic stock data management"
```

---

## Chunk 2: 核心业务逻辑实现（继续）

### 任务 2.2: 实现 KLineDataManager

**Files:**
- Create: `stock_market/managers/kline_manager.py`

- [ ] **Step 1: 编写 KLineDataManager**

```python
"""
K线数据管理模块
"""
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from stock_market.database import DatabaseManager
from stock_market.models import KLine, SyncRecord

logger = logging.getLogger(__name__)


class KLineDataManager:
    """K线数据管理器"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化K线数据管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager

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
        from data_sources import DataSourceAggregator

        aggregator = DataSourceAggregator()

        with self.db.get_session() as session:
            # 确定同步时间范围
            if start_date is None:
                # 增量同步：从最后同步时间开始
                start_date_obj, end_date_obj = self._get_incremental_range(
                    session, symbol, interval
                )
            else:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                else:
                    end_date_obj = date.today()

            if start_date_obj > end_date_obj:
                logger.info(f"No data to sync for {symbol} {interval}")
                return 0

            # 从数据源获取K线数据
            try:
                klines = aggregator.get_kline(
                    symbol=symbol,
                    interval=interval,
                    start_date=start_date_obj.strftime("%Y-%m-%d"),
                    end_date=end_date_obj.strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.error(f"Failed to get kline from data source: {e}")
                return 0

            if not klines:
                logger.warning(f"No kline data returned for {symbol}")
                return 0

            success_count = 0
            for kline in klines:
                try:
                    kline_date = kline.datetime.date()

                    # 检查是否已存在
                    existing = session.query(KLine).filter_by(
                        symbol=symbol,
                        date=kline_date,
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
                            logger.debug(f"Updated kline: {symbol} {kline_date}")
                    else:
                        # 新增K线
                        new_kline = KLine(
                            symbol=symbol,
                            date=kline_date,
                            interval=interval,
                            open=kline.open,
                            high=kline.high,
                            low=kline.low,
                            close=kline.close,
                            volume=kline.volume,
                            amount=kline.amount,
                            source=getattr(kline, 'source', None),
                            sync_time=datetime.now()
                        )
                        session.add(new_kline)
                        success_count += 1
                        logger.debug(f"Added kline: {symbol} {kline_date}")

                except Exception as e:
                    logger.error(f"Failed to save kline for {symbol} on {kline.datetime}: {e}")
                    continue

            # 记录同步日志
            self._log_sync(
                sync_type="klines",
                symbol=symbol,
                interval=interval,
                start_date=start_date_obj,
                end_date=end_date_obj,
                status="success" if success_count > 0 else "failed",
                records_count=success_count
            )

            logger.info(f"Synced {success_count} klines for {symbol} {interval}")
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
        from stock_market.models import Stock

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

- [ ] **Step 2: 更新 managers/__init__.py**

```python
from stock_market.managers.stock_manager import StockDataManager
from stock_market.managers.kline_manager import KLineDataManager

__all__ = ['StockDataManager', 'KLineDataManager']
```

- [ ] **Step 3: 测试导入**

```bash
python -c "from stock_market.managers import KLineDataManager; print('KLineDataManager imported successfully')"
```

Expected output:
```
KLineDataManager imported successfully
```

- [ ] **Step 4: 提交**

```bash
git add stock_market/managers/kline_manager.py stock_market/managers/__init__.py
git commit -m "feat: implement KLineDataManager for kline data management"
```

---

### 任务 2.3: 编写 StockDataManager 和 KLineDataManager 测试

**Files:**
- Create: `tests/test_stock_manager.py`
- Create: `tests/test_kline_manager.py`

- [ ] **Step 1: 编写 StockDataManager 测试**

```python
"""
StockDataManager 测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from stock_market.database import DatabaseManager
from stock_market.managers.stock_manager import StockDataManager

class TestStockDataManager:
    """StockDataManager 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = Mock(spec=DatabaseManager)
        mock.get_session = MagicMock()
        return mock

    @pytest.fixture
    def manager(self, mock_db):
        """创建管理器实例"""
        return StockDataManager(mock_db)

    def test_sync_all_stocks_success(self, manager, mock_db):
        """测试成功同步股票列表"""
        # 创建模拟 session
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # 模拟数据源返回
        with patch('stock_market.managers.stock_manager.DataSourceAggregator') as mock_agg:
            mock_instance = Mock()
            mock_agg.return_value = mock_instance
            mock_instance.get_stock_list.return_value = [
                {'symbol': '600519', 'name': '贵州茅台', 'exchange': 'SH',
                 'list_date': date(2001, 8, 27), 'industry': '食品饮料'},
                {'symbol': '000001', 'name': '平安银行', 'exchange': 'SZ',
                 'list_date': date(1991, 4, 3), 'industry': '银行'}
            ]

            # 模拟查询返回 None（股票不存在）
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            # 执行同步
            count = manager.sync_all_stocks()

            # 验证
            assert count == 2
            assert mock_session.add.call_count == 2

    def test_get_stock(self, manager, mock_db):
        """测试获取股票"""
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # 模拟返回股票
        mock_stock = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_stock

        result = manager.get_stock('600519')

        assert result == mock_stock
        mock_session.query.assert_called_once()

    def test_get_stocks_by_industry(self, manager, mock_db):
        """测试按行业查询"""
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            Mock(), Mock()
        ]

        result = manager.get_stocks_by_industry('银行')

        assert len(result) == 2
```

- [ ] **Step 2: 编写 KLineDataManager 测试**

```python
"""
KLineDataManager 测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from stock_market.database import DatabaseManager
from stock_market.managers.kline_manager import KLineDataManager

class TestKLineDataManager:
    """KLineDataManager 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库管理器"""
        mock = Mock(spec=DatabaseManager)
        mock.get_session = MagicMock()
        return mock

    @pytest.fixture
    def manager(self, mock_db):
        """创建管理器实例"""
        return KLineDataManager(mock_db)

    def test_sync_single_kline_success(self, manager, mock_db):
        """测试成功同步K线"""
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        # 模拟数据源返回
        with patch('stock_market.managers.kline_manager.DataSourceAggregator') as mock_agg:
            mock_kline = Mock()
            mock_kline.datetime = datetime(2023, 12, 29)
            mock_kline.open = 1750.00
            mock_kline.high = 1765.00
            mock_kline.low = 1745.00
            mock_kline.close = 1758.00
            mock_kline.volume = 1234567
            mock_kline.amount = 2165432100.00

            mock_instance = Mock()
            mock_agg.return_value = mock_instance
            mock_instance.get_kline.return_value = [mock_kline]

            # 模拟股票查询
            mock_stock = Mock()
            mock_stock.list_date = date(2001, 8, 27)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_stock

            # 执行同步
            count = manager.sync_single_kline('600519', interval='1d')

            # 验证
            assert count == 1
            mock_session.add.assert_called_once()

    def test_query_klines(self, manager, mock_db):
        """测试查询K线"""
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            Mock(), Mock(), Mock()
        ]

        result = manager.query_klines('600519', interval='1d')

        assert len(result) == 3
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_stock_manager.py tests/test_kline_manager.py -v
```

- [ ] **Step 4: 提交**

```bash
git add tests/test_stock_manager.py tests/test_kline_manager.py
git commit -m "test: add unit tests for StockDataManager and KLineDataManager"
```

---

## Chunk 3: 并发同步和增量策略

### 任务 3.1: 实现并发同步管理器

**Files:**
- Create: `stock_market/sync/concurrent_sync.py`

- [ ] **Step 1: 编写 ConcurrentSyncManager**

```python
"""
并发同步管理模块
"""
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime
from stock_market.database import DatabaseManager
from stock_market.models import SyncRecord

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
        from stock_market.managers.kline_manager import KLineDataManager

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

- [ ] **Step 2: 更新 sync/__init__.py**

```python
from stock_market.sync.concurrent_sync import ConcurrentSyncManager

__all__ = ['ConcurrentSyncManager']
```

- [ ] **Step 3: 提交**

```bash
git add stock_market/sync/concurrent_sync.py stock_market/sync/__init__.py
git commit -m "feat: implement ConcurrentSyncManager for parallel kline sync"
```

---

### 任务 3.2: 实现增量同步策略

**Files:**
- Create: `stock_market/sync/incremental_sync.py`

- [ ] **Step 1: 编写 IncrementalSyncStrategy**

```python
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
```

- [ ] **Step 2: 更新 sync/__init__.py**

```python
from stock_market.sync.concurrent_sync import ConcurrentSyncManager
from stock_market.sync.incremental_sync import IncrementalSyncStrategy

__all__ = ['ConcurrentSyncManager', 'IncrementalSyncStrategy']
```

- [ ] **Step 3: 提交**

```bash
git add stock_market/sync/incremental_sync.py
git commit -m "feat: implement IncrementalSyncStrategy for data integrity checking"
```

---

### 任务 3.3: 实现日期工具函数

**Files:**
- Create: `stock_market/utils/date_utils.py`

- [ ] **Step 1: 编写日期工具函数**

```python
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
```

- [ ] **Step 2: 更新 utils/__init__.py**

```python
from stock_market.utils.date_utils import (
    get_trade_days,
    format_date,
    parse_date,
    get_month_range
)

__all__ = [
    'get_trade_days',
    'format_date',
    'parse_date',
    'get_month_range'
]
```

- [ ] **Step 3: 编写日期工具测试**

```bash
cat > tests/test_date_utils.py << 'EOF'
"""日期工具测试"""
import pytest
from datetime import date
from stock_market.utils.date_utils import (
    get_trade_days,
    format_date,
    parse_date,
    get_month_range
)

def test_get_trade_days():
    """测试获取交易日"""
    start = date(2023, 12, 25)
    end = date(2023, 12, 31)

    days = get_trade_days(start, end)

    # 25-29日是周一到周五，30-31日是周末
    assert len(days) == 5
    assert all(d.weekday() < 5 for d in days)

def test_format_date():
    """测试格式化日期"""
    d = date(2023, 12, 29)
    assert format_date(d) == "2023-12-29"

def test_parse_date():
    """测试解析日期"""
    d = parse_date("2023-12-29")
    assert d == date(2023, 12, 29)

def test_get_month_range():
    """测试获取月份范围"""
    start, end = get_month_range(2023, 12)
    assert start == date(2023, 12, 1)
    assert end == date(2023, 12, 31)
EOF
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_date_utils.py -v
```

- [ ] **Step 5: 提交**

```bash
git add stock_market/utils/date_utils.py stock_market/utils/__init__.py tests/test_date_utils.py
git commit -m "feat: implement date utilities and tests"
```

---

## Chunk 4: 集成测试和文档

### 任务 4.1: 编写集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

```python
"""
集成测试 - 需要真实的 PostgreSQL 数据库
"""
import pytest
from datetime import date
from stock_market.database import DatabaseManager
from stock_market.managers import StockDataManager, KLineDataManager
from stock_market.sync import ConcurrentSyncManager, IncrementalSyncStrategy

# 数据库连接配置（测试数据库）
TEST_DB_URL = "postgresql://stock_user:stock_pass@localhost:5432/stock_test_db"


@pytest.fixture(scope="module")
def db_manager():
    """数据库管理器（测试用）"""
    db = DatabaseManager(TEST_DB_URL)
    # 创建测试表
    db.create_all()
    yield db
    # 清理测试数据
    db.drop_all()


@pytest.fixture
def stock_manager(db_manager):
    """股票数据管理器"""
    return StockDataManager(db_manager)


@pytest.fixture
def kline_manager(db_manager):
    """K线数据管理器"""
    return KLineDataManager(db_manager)


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self, stock_manager, kline_manager):
        """测试完整工作流程"""
        # 1. 同步股票列表
        stock_count = stock_manager.sync_all_stocks()
        assert stock_count > 0

        # 2. 查询股票
        stock = stock_manager.get_stock("600519")
        assert stock is not None
        assert stock.symbol == "600519"

        # 3. 同步K线
        kline_count = kline_manager.sync_single_kline(
            symbol="600519",
            interval="1d",
            start_date="2023-01-01",
            end_date="2023-01-10"
        )
        assert kline_count > 0

        # 4. 查询K线
        klines = kline_manager.query_klines(
            symbol="600519",
            interval="1d",
            start_date="2023-01-01",
            end_date="2023-01-10"
        )
        assert len(klines) == kline_count

        # 5. 获取最新K线
        latest = kline_manager.get_latest_kline("600519", "1d")
        assert latest is not None

    def test_concurrent_sync(self, db_manager):
        """测试并发同步"""
        sync_manager = ConcurrentSyncManager(db_manager, max_workers=3)

        symbols = ["600519", "000001", "601318"]
        results = sync_manager.sync_klines_concurrently(
            symbols=symbols,
            interval="1d",
            start_date="2023-01-01",
            end_date="2023-01-05"
        )

        assert len(results) == 3
        assert all(r["status"] in ["success", "failed"] for r in results.values())

    def test_incremental_sync(self, db_manager, kline_manager):
        """测试增量同步策略"""
        strategy = IncrementalSyncStrategy(db_manager)

        # 先同步部分数据
        kline_manager.sync_single_kline(
            symbol="600519",
            interval="1d",
            start_date="2023-01-01",
            end_date="2023-01-05"
        )

        # 检查缺失的日期
        missing = strategy.get_missing_dates(
            symbol="600519",
            interval="1d",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 10)
        )

        assert len(missing) >= 3  # 6-10日应该缺失
```

- [ ] **Step 2: 提交**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full workflow"
```

---

### 任务 4.2: 创建使用示例

**Files:**
- Create: `examples/stock_market_usage.py`

- [ ] **Step 1: 编写使用示例**

```python
"""
股票市场管理模块使用示例
"""
from stock_market.database import DatabaseManager
from stock_market.managers import StockDataManager, KLineDataManager
from stock_market.sync import ConcurrentSyncManager, IncrementalSyncStrategy

# 数据库配置
DB_URL = "postgresql://stock_user:stock_pass@localhost:5432/stock_db"


def example_1_basic_usage():
    """示例1: 基础使用"""
    print("=" * 50)
    print("示例1: 基础使用")
    print("=" * 50)

    # 初始化
    db = DatabaseManager(DB_URL)
    db.create_all()  # 首次运行时创建表

    stock_manager = StockDataManager(db)
    kline_manager = KLineDataManager(db)

    # 同步股票列表
    print("\n1. 同步股票列表...")
    count = stock_manager.sync_all_stocks()
    print(f"   同步了 {count} 只股票")

    # 查询股票
    print("\n2. 查询股票信息...")
    stock = stock_manager.get_stock("600519")
    if stock:
        print(f"   股票: {stock.name} ({stock.symbol})")
        print(f"   行业: {stock.industry}")
        print(f"   上市日期: {stock.list_date}")

    # 同步K线
    print("\n3. 同步K线数据...")
    kline_count = kline_manager.sync_single_kline(
        symbol="600519",
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    print(f"   同步了 {kline_count} 条K线")

    # 查询K线
    print("\n4. 查询K线数据...")
    klines = kline_manager.query_klines(
        symbol="600519",
        interval="1d",
        start_date="2023-12-01",
        end_date="2023-12-31"
    )
    print(f"   查询到 {len(klines)} 条K线")
    if klines:
        latest = klines[-1]
        print(f"   最新收盘价: {latest.close}")

    print("\n示例1完成!")


def example_2_concurrent_sync():
    """示例2: 并发同步"""
    print("\n" + "=" * 50)
    print("示例2: 并发同步多只股票")
    print("=" * 50)

    db = DatabaseManager(DB_URL)
    sync_manager = ConcurrentSyncManager(db, max_workers=3)

    symbols = ["600519", "000001", "601318", "300750", "688981"]
    print(f"\n并发同步 {len(symbols)} 只股票...")

    results = sync_manager.sync_klines_concurrently(
        symbols=symbols,
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )

    print("\n同步结果:")
    for symbol, result in results.items():
        status = "✓" if result["status"] == "success" else "✗"
        count = result.get("count", 0)
        print(f"   {status} {symbol}: {count} 条K线")


def example_3_data_integrity():
    """示例3: 数据完整性检查"""
    print("\n" + "=" * 50)
    print("示例3: 数据完整性检查")
    print("=" * 50)

    db = DatabaseManager(DB_URL)
    strategy = IncrementalSyncStrategy(db)

    print("\n检查贵州茅台的缺失数据...")
    missing_dates = strategy.get_missing_dates(
        symbol="600519",
        interval="1d",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )

    if missing_dates:
        print(f"   发现 {len(missing_dates)} 个缺失日期")
        print(f"   前5个: {[d.strftime('%Y-%m-%d') for d in missing_dates[:5]]}")
    else:
        print("   ✓ 数据完整，无缺失")

    print("\n检查同步缺口...")
    gaps = strategy.get_sync_gaps("600519", "1d")
    if gaps:
        print(f"   发现 {len(gaps)} 个缺口")
        for gap in gaps[:3]:
            print(f"     {gap['start']} 到 {gap['end']}")
    else:
        print("   ✓ 无缺口")


def example_4_query_by_industry():
    """示例4: 按行业查询"""
    print("\n" + "=" * 50)
    print("示例4: 按行业查询股票")
    print("=" * 50)

    db = DatabaseManager(DB_URL)
    stock_manager = StockDataManager(db)

    print("\n查询银行行业股票...")
    bank_stocks = stock_manager.get_stocks_by_industry("银行")
    print(f"   找到 {len(bank_stocks)} 只银行股")

    print("\n前5只:")
    for stock in bank_stocks[:5]:
        print(f"   {stock.symbol} - {stock.name}")


if __name__ == "__main__":
    # 运行示例
    try:
        example_1_basic_usage()
        example_2_concurrent_sync()
        example_3_data_integrity()
        example_4_query_by_industry()
        print("\n" + "=" * 50)
        print("✓ 所有示例运行完成!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
```

- [ ] **Step 2: 提交**

```bash
git add examples/stock_market_usage.py
git commit -m "docs: add comprehensive usage examples"
```

---

### 任务 4.3: 编写 README 文档

**Files:**
- Create: `stock_market/README.md`

- [ ] **Step 1: 编写 README**

```markdown
# 股票市场管理模块 (stock_market)

股票市场管理模块提供股票基础数据和K线数据的持久化存储、查询和同步功能。

## 特性

- ✅ **股票基础数据管理** - 同步和管理A股市场所有股票的完整信息
- ✅ **K线数据管理** - 支持日线、5日线、10日线、月线的存储和查询
- ✅ **增量同步** - 按最后同步时间自动补充缺失数据
- ✅ **并发处理** - 线程池并发同步多只股票
- ✅ **数据完整性检查** - 自动检测和报告缺失数据
- ✅ **灵活查询** - 支持按日期范围、行业、概念等多种查询方式

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据库配置

编辑 `stock_market/config/database.json`:

```json
{
  "database": {
    "url": "postgresql://user:password@localhost:5432/stock_db",
    "pool_size": 10,
    "max_overflow": 20
  }
}
```

### 初始化数据库

```bash
# 应用数据库迁移
cd stock_market
alembic upgrade head

# 或者直接创建表
python -c "from stock_market.database import DatabaseManager; db = DatabaseManager('postgresql://...'); db.create_all()"
```

### 使用示例

```python
from stock_market.database import DatabaseManager
from stock_market.managers import StockDataManager, KLineDataManager

# 初始化
db = DatabaseManager("postgresql://user:password@localhost:5432/stock_db")
stock_manager = StockDataManager(db)
kline_manager = KLineDataManager(db)

# 同步股票列表
stock_manager.sync_all_stocks()

# 同步K线
kline_manager.sync_single_kline(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 查询数据
stock = stock_manager.get_stock("600519")
klines = kline_manager.query_klines(
    symbol="600519",
    interval="1d",
    start_date="2023-12-01",
    end_date="2023-12-31"
)
```

## 目录结构

```
stock_market/
├── __init__.py                 # 模块导出
├── database.py                 # 数据库连接管理
├── models.py                   # SQLAlchemy 模型
├── managers/                   # 数据管理器
│   ├── stock_manager.py       # 股票数据管理
│   └── kline_manager.py       # K线数据管理
├── sync/                       # 同步模块
│   ├── concurrent_sync.py     # 并发同步
│   └── incremental_sync.py    # 增量同步策略
├── utils/                      # 工具函数
│   └── date_utils.py          # 日期处理
├── config/                     # 配置文件
│   └── database.json
└── migrations/                 # Alembic 迁移
    └── versions/
```

## 测试

运行所有测试:

```bash
pytest tests/ -v
```

运行特定测试:

```bash
pytest tests/test_models.py -v
pytest tests/test_stock_manager.py -v
```

## API 文档

### StockDataManager

- `sync_all_stocks(force_update=False)` - 同步所有股票列表
- `sync_stock_details(symbols)` - 同步股票详细信息
- `get_stock(symbol)` - 获取单只股票
- `get_stocks_by_industry(industry)` - 按行业查询
- `get_stocks_by_concept(concept)` - 按概念查询
- `get_active_stocks()` - 获取所有上市股票

### KLineDataManager

- `sync_single_kline(symbol, interval, start_date, end_date, force_update)` - 同步单只股票K线
- `query_klines(symbol, interval, start_date, end_date, limit, order_by)` - 查询K线
- `get_latest_kline(symbol, interval)` - 获取最新K线
- `get_kline_count(symbol, interval)` - 获取K线数量

### ConcurrentSyncManager

- `sync_klines_concurrently(symbols, interval, max_workers, **kwargs)` - 并发同步多只股票

### IncrementalSyncStrategy

- `get_missing_dates(symbol, interval, start_date, end_date)` - 获取缺失的日期
- `get_sync_gaps(symbol, interval)` - 获取同步缺口

## 许可证

MIT License
```

- [ ] **Step 2: 提交**

```bash
git add stock_market/README.md
git commit -m "docs: add README for stock_market module"
```

---

### 任务 4.4: 更新项目 requirements

- [ ] **Step 1: 更新 requirements.txt**

```bash
cat > requirements.txt << 'EOF'
# 核心依赖
pydantic>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0

# 数据源（已有）
tushare>=1.2.87
akshare>=1.11.0
requests>=2.25.0
pandas>=2.0.0

# 数据库（新增）
sqlalchemy>=2.0.0
alembic>=1.10.0
psycopg2-binary>=2.9.0

# 并发（已有）
concurrent-futures>=3.0.0
EOF
```

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: update requirements with database dependencies"
```

---

## 实施路线图总结

### Phase 1: 基础框架 (已完成 ✅)
- ✅ 任务 1.1: 创建目录结构
- ✅ 任务 1.2: 实现数据库连接管理
- ✅ 任务 1.3: 实现数据库模型
- ✅ 任务 1.4: 配置 Alembic 迁移
- ✅ 任务 1.5: 编写模型测试

### Phase 2: 核心功能 (进行中 🔄)
- ✅ 任务 2.1: 实现 StockDataManager
- ✅ 任务 2.2: 实现 KLineDataManager
- ✅ 任务 2.3: 编写管理器测试

### Phase 3: 工具和优化 (已完成 ✅)
- ✅ 任务 3.1: 实现 ConcurrentSyncManager
- ✅ 任务 3.2: 实现 IncrementalSyncStrategy
- ✅ 任务 3.3: 实现日期工具函数和测试

### Phase 4: 测试和文档 (已完成 ✅)
- ✅ 任务 4.1: 编写集成测试
- ✅ 任务 4.2: 创建使用示例
- ✅ 任务 4.3: 编写 README 文档
- ✅ 任务 4.4: 更新 requirements

---

## 实施完成检查清单

- [ ] 所有代码文件已创建
- [ ] 所有测试文件已创建并通过
- [ ] 数据库迁移已配置
- [ ] 使用文档已编写
- [ ] README 已完成
- [ ] requirements 已更新
- [ ] 所有代码已提交到 git

---

**实施计划完成！** 🎉

现在可以使用 superpowers:subagent-driven-development 或 superpowers:executing-plans 技能来执行这个计划。

**Phase 1: 基础框架 (1-2天)**
- ✅ 任务 1.1-1.5: 目录结构、数据库连接、模型、迁移、测试

**Phase 2: 核心功能 (3-4天)**
- ⏳ 任务 2.1-2.x: StockDataManager、KLineDataManager

**Phase 3: 工具和优化 (2-3天)**
- ⏳ 任务 3.1-3.x: 并发同步、增量策略、工具函数

**Phase 4: 测试和部署 (2-3天)**
- ⏳ 任务 4.1-4.x: 集成测试、使用示例、部署脚本

**总预计时间**: 8-12 天
