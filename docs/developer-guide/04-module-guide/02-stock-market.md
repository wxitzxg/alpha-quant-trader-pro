# 📈 Stock Market Module Guide

> Comprehensive guide for the Stock Market module

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [Usage Examples](#usage-examples)
5. [Data Synchronization](#data-synchronization)
6. [Best Practices](#best-practices)
7. [Testing](#testing)

---

## 🎯 Overview

The **Stock Market Module** manages stock and K-line data, providing a complete data layer for market information.

**Key Features:**
- **ORM Models**: SQLAlchemy models for Stock and KLine
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic implementation
- **Data Synchronization**: Automatic data sync from external sources
- **Batch Operations**: Efficient bulk data operations
- **Caching**: Performance optimization

---

## 🏛️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│        StockService /               │
│        KLineService                 │
│   (Business Logic Layer)            │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│   StockRepository /                 │
│   KLineRepository                   │
│   (Data Access Layer)               │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│          SQLAlchemy ORM             │
│        (Database Layer)             │
└─────────────────────────────────────┘
```

### Class Diagram

```
Base
    ├── Stock
    └── KLine

BaseRepository[T]
    ├── StockRepository
    └── KLineRepository

StockService
    ├── StockManager
    └── StockSyncService

KLineService
    ├── KLineManager
    └── KLineSyncService
```

---

## 🧩 Key Components

### 1. Models

#### Stock Model

```python
from sqlalchemy import Column, String, Integer, Float, Date
from common.database import Base

class Stock(Base):
    """Stock information model."""

    __tablename__ = 'stocks'

    symbol = Column(String(10), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    industry = Column(String(50), index=True)
    exchange = Column(String(10))
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    dividend_yield = Column(Float)
    listed_date = Column(Date)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    klines = relationship("KLine", back_populates="stock", cascade="all, delete-orphan")
```

#### KLine Model

```python
class KLine(Base):
    """K-line (OHLCV) data model."""

    __tablename__ = 'klines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), index=True)
    date = Column(Date, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer)
    amount = Column(Float)
    change_percent = Column(Float)

    # Compound index for efficient querying
    __table_args__ = (
        Index('ix_symbol_date', 'symbol', 'date', unique=True),
    )

    # Relationships
    stock = relationship("Stock", back_populates="klines")
```

### 2. Repositories

#### StockRepository

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from common.repositories import BaseRepository
from .models import Stock

class StockRepository(BaseRepository[Stock]):
    """Repository for Stock model."""

    def __init__(self, session: Session):
        super().__init__(Stock, session)

    def find_by_industry(self, industry: str) -> List[Stock]:
        """Find stocks by industry."""
        return self.session.query(Stock)\
            .filter(Stock.industry == industry)\
            .all()

    def find_by_exchange(self, exchange: str) -> List[Stock]:
        """Find stocks by exchange."""
        return self.session.query(Stock)\
            .filter(Stock.exchange == exchange)\
            .all()

    def bulk_upsert(self, stocks: List[Stock]) -> None:
        """Bulk upsert stocks."""
        for stock in stocks:
            self.session.merge(stock)
```

#### KLineRepository

```python
from datetime import date

class KLineRepository(BaseRepository[KLine]):
    """Repository for KLine model."""

    def __init__(self, session: Session):
        super().__init__(KLine, session)

    def get_by_symbol_and_date(self, symbol: str, date: date) -> Optional[KLine]:
        """Get K-line by symbol and date."""
        return self.session.query(KLine)\
            .filter_by(symbol=symbol, date=date)\
            .first()

    def get_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[KLine]:
        """Get K-lines in date range."""
        return self.session.query(KLine)\
            .filter(
                and_(
                    KLine.symbol == symbol,
                    KLine.date.between(start_date, end_date)
                )
            )\
            .order_by(KLine.date.desc())\
            .all()

    def bulk_insert(self, klines: List[KLine]) -> None:
        """Bulk insert K-lines."""
        self.session.bulk_save_objects(klines)
```

### 3. Services

#### StockService

```python
from typing import List
from datetime import datetime

from .repositories import StockRepository
from .models import Stock
from data_sources import DataSourceAggregator

class StockService:
    """Service for stock operations."""

    def __init__(self, repository: StockRepository, data_source: DataSourceAggregator):
        self.repository = repository
        self.data_source = data_source

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol."""
        return self.repository.get(symbol)

    def sync_all_stocks(self) -> int:
        """Sync all stocks from data source."""
        # Get from data source
        stock_list = self.data_source.get_stock_list()

        # Transform and save
        stocks = [
            Stock(
                symbol=item['symbol'],
                name=item['name'],
                industry=item['industry'],
                exchange=item['exchange'],
                market_cap=item.get('market_cap'),
                listed_date=datetime.strptime(item['listed_date'], '%Y%m%d').date()
            )
            for item in stock_list
        ]

        self.repository.bulk_upsert(stocks)
        self.repository.session.commit()

        return len(stocks)
```

---

## 💡 Usage Examples

### Basic CRUD Operations

```python
from sqlalchemy.orm import Session
from stock_market import StockService, StockRepository
from common.database import DatabaseManager

# Setup
db = DatabaseManager()
session = db.get_session()
repository = StockRepository(session)
service = StockService(repository)

# Create
stock = Stock(symbol="600519", name="贵州茅台", industry="白酒")
repository.create(stock)
session.commit()

# Read
stock = service.get_stock("600519")
print(f"{stock.name}: {stock.industry}")

# Update
stock.market_cap = 2000000000000
repository.save(stock)
session.commit()

# Delete
repository.delete(stock)
session.commit()

session.close()
```

### Query with Filters

```python
# Get stocks by industry
stocks = repository.find_by_industry("白酒")
print(f"Found {len(stocks)} 白酒 stocks")

# Get with pagination
stocks = session.query(Stock)\
    .filter(Stock.market_cap > 100000000000)\
    .order_by(Stock.market_cap.desc())\
    .offset(0)\
    .limit(20)\
    .all()

# Complex query
stocks = session.query(Stock)\
    .filter(
        and_(
            Stock.industry.in_(["白酒", "医药"]),
            Stock.pe_ratio < 50,
            Stock.dividend_yield > 1.0
        )
    )\
    .all()
```

### Batch Operations

```python
# Bulk insert
stocks = [
    Stock(symbol=f"STOCK{i:06d}", name=f"Stock {i}")
    for i in range(1000)
]

repository.bulk_upsert(stocks)
session.commit()
print("Inserted 1000 stocks")

# Bulk K-line insert
klines = [
    KLine(
        symbol="600519",
        date=date(2023, 1, i),
        open=100 + i,
        high=105 + i,
        low=95 + i,
        close=102 + i,
        volume=1000000
    )
    for i in range(1, 31)
]

kline_repository.bulk_insert(klines)
session.commit()
```

---

## 🔄 Data Synchronization

### Concurrent Sync

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

class ConcurrentStockSync:
    """Concurrently sync stocks using thread pool."""

    def __init__(self, service: StockService, max_workers: int = 10):
        self.service = service
        self.max_workers = max_workers

    def sync_stocks(self, symbols: List[str]) -> dict:
        """Sync multiple stocks concurrently."""
        results = {'success': 0, 'failed': 0, 'errors': []}

        def sync_single(symbol: str):
            try:
                self.service.sync_stock(symbol)
                return {'symbol': symbol, 'status': 'success'}
            except Exception as e:
                return {'symbol': symbol, 'status': 'failed', 'error': str(e)}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(sync_single, s) for s in symbols]

            for future in as_completed(futures):
                result = future.result()
                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(result)

        return results
```

### Incremental Sync

```python
from datetime import date, timedelta

class IncrementalKLineSync:
    """Incrementally sync K-line data."""

    def __init__(self, service: KLineService):
        self.service = service

    def sync_latest(self, symbol: str) -> int:
        """Sync latest K-line data."""
        # Get last synced date
        last_kline = self.service.get_latest_kline(symbol)
        if last_kline:
            start_date = last_kline.date + timedelta(days=1)
        else:
            start_date = date.today() - timedelta(days=365)

        # Sync from last date to today
        end_date = date.today()
        count = self.service.sync_klines(symbol, start_date, end_date)

        return count
```

---

## ✅ Best Practices

### 1. Use Transactions

```python
# ✅ DO: Use transactions for multiple operations
try:
    stock = Stock(symbol="600519", name="贵州茅台")
    repository.create(stock)

    kline = KLine(symbol="600519", date=date.today(), open=1800, ...)
    kline_repository.create(kline)

    session.commit()
except Exception as e:
    session.rollback()
    raise
```

### 2. Eager Loading

```python
# ✅ DO: Use eager loading to avoid N+1 queries
stocks = session.query(Stock)\
    .options(joinedload(Stock.klines))\
    .filter(Stock.industry == "白酒")\
    .all()

for stock in stocks:
    print(f"{stock.name}: {len(stock.klines)} klines")
```

### 3. Pagination

```python
# ✅ DO: Use pagination for large datasets
def get_stocks_paginated(page: int, page_size: int = 20):
    query = session.query(Stock)
    total = query.count()
    stocks = query.offset((page - 1) * page_size).limit(page_size).all()
    return stocks, total
```

---

## 🧪 Testing

```python
import pytest
from unittest.mock import Mock
from datetime import date

from stock_market.services import StockService
from stock_market.models import Stock

class TestStockService:
    """Test StockService."""

    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def mock_data_source(self):
        return Mock()

    @pytest.fixture
    def stock_service(self, mock_repository, mock_data_source):
        return StockService(mock_repository, mock_data_source)

    def test_get_stock_found(self, stock_service, mock_repository):
        expected = Stock(symbol="600519", name="贵州茅台")
        mock_repository.get.return_value = expected

        result = stock_service.get_stock("600519")

        assert result == expected
        mock_repository.get.assert_called_once_with("600519")

    def test_sync_all_stocks(self, stock_service, mock_data_source, mock_repository):
        mock_data_source.get_stock_list.return_value = [
            {'symbol': '600519', 'name': '贵州茅台', 'industry': '白酒', 'listed_date': '20010827'}
        ]

        count = stock_service.sync_all_stocks()

        assert count == 1
        mock_repository.bulk_upsert.assert_called_once()
```

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
