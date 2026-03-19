# 📏 Coding Standards

> Comprehensive coding standards and style guide for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Code Style](#code-style)
2. [Naming Conventions](#naming-conventions)
3. [File Organization](#file-organization)
4. [Documentation](#documentation)
5. [Error Handling](#error-handling)
6. [Type Hints](#type-hints)
7. [Testing Standards](#testing-standards)
8. [Security Guidelines](#security-guidelines)
9. [Performance Guidelines](#performance-guidelines)
10. [Code Review Checklist](#code-review-checklist)

---

## 🎨 Code Style

### Black Code Formatter

All Python code MUST be formatted using [Black](https://black.readthedocs.io/) with default settings.

**Configuration (.black):**
```toml
[tool.black]
line-length = 120
target-version = ['py38', 'py39', 'py310']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | \.eggs
  | \.nox
  | \.tox
  | \.mypy_cache
  | build
  | dist
)/
'''
```

**Running Black:**
```bash
# Format all files
black .

# Format specific file
black api_server/main.py

# Check without formatting
black --check .

# Integrate with pre-commit
pre-commit run black --all-files
```

### Line Length

- **Maximum line length**: 120 characters
- **Docstring line length**: 80 characters (for readability)

### Imports

**Order and Grouping:**
```python
# 1. Standard library imports
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable

# 2. Third-party imports
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session, declarative_base
import pandas as pd
import numpy as np

# 3. Local application imports
from common.database import DatabaseManager
from common.exceptions import DataNotFoundError
from stock_market.models import Stock, KLine
from stock_market.repositories import StockRepository
from .base import BaseRepository
```

**Import Rules:**
```python
# ✅ DO: Import specific classes/functions
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# ✅ DO: Use absolute imports for cross-module references
from stock_market.services import StockService
from portfolio_manager.models import Position

# ✅ DO: Use relative imports within same module
from .models import KLine
from ..repositories import KLineRepository

# ❌ DON'T: Import * (wildcard imports)
from sqlalchemy import *

# ❌ DON'T: Use unnecessary aliases
import pandas as pd  # OK for common abbreviations
import numpy as np  # OK for common abbreviations
import fastapi as fp  # Avoid - not standard

# ❌ DON'T: Mix absolute and relative imports unnecessarily
from stock_market import models  # Absolute
from .. import models  # Relative - inconsistent
```

### isort Configuration

**.isort.cfg:**
```ini
[settings]
profile = black
line_length = 120
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
sections = FUTURE,STDLIB,THIRDPARTY,FIRSTPARTY,LOCALFOLDER
```

---

## 🔠 Naming Conventions

### General Rules

| Type | Convention | Example |
|------|-----------|---------|
| **Classes** | `PascalCase` | `StockService`, `DataNotFoundError` |
| **Functions** | `snake_case` | `get_stock_data()`, `calculate_score()` |
| **Variables** | `snake_case` | `stock_symbol`, `max_price` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS = 100` |
| **Private** | `_snake_case` | `_internal_helper()` |
| **Modules** | `snake_case.py` | `stock_service.py`, `kline_repository.py` |
| **Packages** | `snake_case/` | `stock_market/`, `data_sources/` |

### Class Naming

```python
# ✅ Service classes
class StockService:
    pass

class AnalysisService:
    pass

# ✅ Repository classes
class StockRepository:
    pass

class KLineRepository:
    pass

# ✅ Manager classes
class StockManager:
    pass

class PortfolioManager:
    pass

# ✅ Exception classes
class DataNotFoundError(Exception):
    pass

class ValidationError(Exception):
    pass

# ✅ Model classes (SQLAlchemy)
class Stock(Base):
    pass

class Position(Base):
    pass

# ✅ Strategy classes
class VCPStrategy:
    pass

class NineTurnStrategy:
    pass
```

### Function Naming

```python
# ✅ CRUD operations
def create_stock(data):
    pass

def get_stock(symbol):
    pass

def update_stock(symbol, data):
    pass

def delete_stock(symbol):
    pass

# ✅ Query operations
def get_all_stocks():
    pass

def get_stocks_by_industry(industry):
    pass

def count_stocks():
    pass

# ✅ Calculation operations
def calculate_score(klines):
    pass

def calculate_indicators(data):
    pass

def compute_performance(trades):
    pass

# ✅ Boolean operations (use is/has/can)
def is_valid_symbol(symbol):
    pass

def has_sufficient_balance(account, amount):
    pass

def can_execute_trade(position):
    pass

# ❌ DON'T: Use vague names
def process(data):  # What does it process?
    pass

def handle(stuff):  # What does it handle?
    pass

def do_work():  # What work?
    pass
```

### Variable Naming

```python
# ✅ Use descriptive names
stock_symbol = "600519"
max_price = 2000
transaction_count = 10

# ✅ Use type hints for clarity
stocks: List[Stock] = []
prices: Dict[str, float] = {}
score: Optional[float] = None

# ✅ Use plural for collections
stocks = [stock1, stock2, stock3]
positions = portfolio.positions
klines = get_klines(symbol)

# ❌ DON'T: Use single-letter names (except in loops)
i = 0  # OK in loops
for s in stocks:  # Avoid
    pass

# ❌ DON'T: Use abbreviations without context
stk = get_stock(symbol)  # Avoid
acc = get_account(user)  # Avoid
```

---

## 📁 File Organization

### File Size Limits

- **Maximum file size**: 800 lines
- **Target file size**: 200-400 lines
- **Large files**: Split into smaller, focused files

### Module Structure

```python
# ✅ Good structure - focused and maintainable
stock_market/
├── __init__.py
├── models.py              # ~200 lines
├── repositories/
│   ├── __init__.py
│   ├── stock_repository.py    # ~300 lines
│   └── kline_repository.py    # ~300 lines
├── services/
│   ├── __init__.py
│   ├── stock_service.py       # ~400 lines
│   └── kline_service.py       # ~400 lines
└── managers/
    ├── __init__.py
    ├── stock_manager.py       # ~300 lines
    └── kline_manager.py       # ~300 lines
```

### Code Structure Within Files

```python
"""
Module docstring - Describe the module's purpose, usage, and key classes/functions
"""

# 1. Imports (standard, third-party, local)
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

# 2. Constants
MAX_RETRY_COUNT = 3
DEFAULT_PAGE_SIZE = 20

# 3. Type aliases
StockList = List[Stock]
PriceDict = Dict[str, float]

# 4. Helper functions (private)
def _validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format."""
    return bool(symbol and len(symbol) == 6)

# 5. Classes (public)
class StockService:
    """Main service class for stock operations."""

    def __init__(self, repository: StockRepository):
        self.repository = repository

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol."""
        if not _validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        return self.repository.get(symbol)

# 6. Module-level functions (if any)
def get_all_stocks() -> StockList:
    """Get all stocks from database."""
    pass
```

---

## 📝 Documentation

### Docstrings (Google Style)

```python
class StockService:
    """Service class for stock-related operations.

    Provides methods for retrieving, creating, updating, and deleting stocks.
    Uses repository pattern for data access abstraction.

    Attributes:
        repository: StockRepository instance for data access
    """

    def __init__(self, repository: StockRepository):
        """Initialize StockService with repository.

        Args:
            repository: Repository for stock data access
        """
        self.repository = repository

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """Retrieve a stock by symbol.

        Args:
            symbol: Stock symbol (e.g., "600519")

        Returns:
            Stock object if found, None otherwise

        Raises:
            ValueError: If symbol is invalid
            DatabaseError: If database query fails

        Examples:
            >>> service = StockService(repository)
            >>> stock = service.get_stock("600519")
            >>> print(stock.name)
            贵州茅台
        """
        pass

    def create_stock(self, data: Dict[str, Any]) -> Stock:
        """Create a new stock record.

        Args:
            data: Dictionary containing stock data
                - symbol: Stock symbol (required)
                - name: Stock name (required)
                - industry: Industry classification (optional)

        Returns:
            Created Stock object

        Raises:
            ValidationError: If data is invalid
            DuplicateError: If stock already exists

        Examples:
            >>> data = {
            ...     "symbol": "600519",
            ...     "name": "贵州茅台",
            ...     "industry": "白酒"
            ... }
            >>> stock = service.create_stock(data)
        """
        pass


def calculate_score(klines: List[KLine]) -> float:
    """Calculate technical analysis score for a stock.

    Computes five-dimension score based on:
    - Trend analysis
    - Pattern recognition
    - Position evaluation
    - Momentum calculation
    - Trigger detection

    Args:
        klines: List of K-line data points

    Returns:
        Score between 0 and 100, where higher is better

    Examples:
        >>> klines = repository.get_klines("600519", days=120)
        >>> score = calculate_score(klines)
        >>> print(f"Score: {score:.2f}")
        Score: 85.50
    """
    pass
```

### Comments

```python
# ✅ Good comments - explain WHY, not WHAT
# Retry up to 3 times because Tushare API can be unstable
for attempt in range(MAX_RETRY_COUNT):
    try:
        return tushare_api.get_data(symbol)
    except ConnectionError:
        if attempt == MAX_RETRY_COUNT - 1:
            raise
        time.sleep(2 ** attempt)  # Exponential backoff

# ✅ Complex algorithm explanation
# The five-dimension scoring uses weighted averages:
# - Trend: 30% weight
# - Pattern: 25% weight
# - Position: 20% weight
# - Momentum: 15% weight
# - Trigger: 10% weight
score = (trend_score * 0.3 + pattern_score * 0.25 +
         position_score * 0.2 + momentum_score * 0.15 +
         trigger_score * 0.1)

# ❌ DON'T: Redundant comments
x = x + 1  # Increment x by 1

# ❌ DON'T: Outdated comments
# TODO: Remove this after migration
# (Code was already migrated but comment remains)
```

---

## ⚠️ Error Handling

### Custom Exceptions

```python
# common/exceptions.py

class AlphaQuantError(Exception):
    """Base exception for all Alpha Quant errors."""
    pass


class DataError(AlphaQuantError):
    """Base exception for data-related errors."""
    pass


class DataNotFoundError(DataError):
    """Raised when requested data is not found."""

    def __init__(self, entity_type: str, identifier: str):
        message = f"{entity_type} not found: {identifier}"
        super().__init__(message)
        self.entity_type = entity_type
        self.identifier = identifier


class DataUnavailableError(DataError):
    """Raised when data source is unavailable."""

    def __init__(self, source: str, message: str):
        super().__init__(f"{source} unavailable: {message}")
        self.source = source


class ValidationError(AlphaQuantError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        super().__init__(f"Validation failed for {field}: {message}")
        self.field = field
        self.message = message


class DatabaseError(AlphaQuantError):
    """Raised when database operations fail."""
    pass
```

### Error Handling Patterns

```python
# ✅ DO: Handle errors explicitly
def get_stock(symbol: str) -> Stock:
    """Get stock with explicit error handling."""
    try:
        stock = repository.get(symbol)
        if stock is None:
            raise DataNotFoundError("Stock", symbol)
        return stock
    except SQLAlchemyError as e:
        logger.error(f"Database error getting stock {symbol}: {e}")
        raise DatabaseError(f"Failed to get stock: {e}") from e


# ✅ DO: Validate inputs early
def create_position(symbol: str, quantity: int, price: float) -> Position:
    """Create position with validation."""
    if not symbol or len(symbol) != 6:
        raise ValidationError("symbol", "Symbol must be 6 characters")

    if quantity <= 0:
        raise ValidationError("quantity", "Quantity must be positive")

    if price <= 0:
        raise ValidationError("price", "Price must be positive")

    # Proceed with creation
    return repository.create(...)


# ✅ DO: Use context managers for resources
def process_file(filepath: str) -> None:
    """Process file with proper cleanup."""
    try:
        with open(filepath, 'r') as f:
            data = f.read()
            # Process data
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except IOError as e:
        logger.error(f"IO error processing {filepath}: {e}")
        raise


# ❌ DON'T: Bare except clauses
try:
    result = risky_operation()
except:  # Catches everything including KeyboardInterrupt
    pass


# ❌ DON'T: Silent failures
try:
    send_notification(user)
except Exception:
    pass  # Error silently ignored
```

### Logging Errors

```python
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def log_operation(operation_name: str):
    """Context manager for logging operations."""
    logger.info(f"Starting {operation_name}")
    try:
        yield
        logger.info(f"Completed {operation_name}")
    except Exception as e:
        logger.error(f"Failed {operation_name}: {e}", exc_info=True)
        raise


def sync_stock_data(symbol: str) -> None:
    """Sync stock data with proper logging."""
    with log_operation(f"sync_stock_{symbol}"):
        logger.debug(f"Fetching data for {symbol}")
        data = data_source.get_stock(symbol)
        logger.debug(f"Saving {len(data)} records")
        repository.save(data)
        logger.info(f"Successfully synced {symbol}")
```

---

## 🏷️ Type Hints

### Basic Type Hints

```python
from typing import List, Dict, Optional, Tuple, Set, Callable, Any


# ✅ Function parameters and return types
def get_stock(symbol: str) -> Optional[Stock]:
    pass


# ✅ Complex types
def get_stocks_by_industry(industry: str) -> List[Stock]:
    pass


def get_price_history(symbol: str) -> Dict[str, float]:
    pass


def calculate_metrics(data: List[float]) -> Tuple[float, float, float]:
    """Return (mean, median, std_dev)."""
    pass


# ✅ Optional parameters
def search_stocks(
    keyword: str,
    limit: int = 20,
    offset: int = 0
) -> List[Stock]:
    pass


# ✅ Callable types
def process_data(
    data: List[float],
    transform: Callable[[float], float]
) -> List[float]:
    return [transform(x) for x in data]


# ✅ Any type (use sparingly)
def parse_config(config: Dict[str, Any]) -> None:
    pass
```

### Class Type Hints

```python
from typing import TypeVar, Generic

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Generic base repository."""

    def __init__(self, model: type[T], session: Session):
        self.model = model
        self.session = session

    def get(self, id: int) -> Optional[T]:
        return self.session.query(self.model).get(id)

    def find_all(self) -> List[T]:
        return self.session.query(self.model).all()


class StockRepository(BaseRepository[Stock]):
    """Repository for Stock model."""

    def __init__(self, session: Session):
        super().__init__(Stock, session)
```

### Type Aliases

```python
from typing import NewType, Union

# ✅ Type aliases for clarity
StockSymbol = NewType('StockSymbol', str)
Price = NewType('Price', float)
Quantity = NewType('Quantity', int)

def buy_stock(
    symbol: StockSymbol,
    quantity: Quantity,
    price: Price
) -> Position:
    pass


# ✅ Union types
from typing import Union

Number = Union[int, float]

def calculate_average(values: List[Number]) -> float:
    pass
```

---

## 🧪 Testing Standards

### Test Structure

```python
# tests/test_stock_market/test_services/test_stock_service.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from stock_market.services import StockService
from stock_market.repositories import StockRepository
from stock_market.models import Stock


class TestStockService:
    """Test StockService class."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def stock_repository(self, mock_session) -> StockRepository:
        """Create StockRepository instance."""
        return StockRepository(mock_session)

    @pytest.fixture
    def stock_service(self, stock_repository) -> StockService:
        """Create StockService instance."""
        return StockService(stock_repository)

    def test_get_stock_success(self, stock_service, stock_repository):
        """Test getting a stock successfully."""
        # Arrange
        expected_stock = Stock(symbol="600519", name="贵州茅台")
        stock_repository.get = Mock(return_value=expected_stock)

        # Act
        result = stock_service.get_stock("600519")

        # Assert
        assert result == expected_stock
        stock_repository.get.assert_called_once_with("600519")

    def test_get_stock_not_found(self, stock_service, stock_repository):
        """Test getting a stock that doesn't exist."""
        # Arrange
        stock_repository.get = Mock(return_value=None)

        # Act & Assert
        with pytest.raises(DataNotFoundError):
            stock_service.get_stock("INVALID")

    @pytest.mark.parametrize("symbol,expected", [
        ("600519", True),
        ("000001", True),
        ("123", False),  # Too short
        ("", False),  # Empty
        (None, False),  # None
    ])
    def test_validate_symbol(self, stock_service, symbol, expected):
        """Test symbol validation with multiple cases."""
        result = stock_service._validate_symbol(symbol)
        assert result == expected

    @patch('stock_market.services.TushareAdapter')
    def test_sync_stock(self, mock_adapter, stock_service):
        """Test syncing stock data from external source."""
        # Arrange
        mock_instance = MagicMock()
        mock_adapter.return_value = mock_instance
        mock_instance.get_stock.return_value = {
            'symbol': '600519',
            'name': '贵州茅台',
            'industry': '白酒'
        }

        # Act
        result = stock_service.sync_stock("600519")

        # Assert
        assert result.symbol == "600519"
        assert result.name == "贵州茅台"
        mock_instance.get_stock.assert_called_once_with("600519")
```

### Test Naming Conventions

```python
# ✅ Good test names
def test_get_stock_success():
    pass

def test_get_stock_not_found():
    pass

def test_create_stock_with_valid_data():
    pass

def test_create_stock_with_invalid_symbol():
    pass

def test_calculate_score_returns_float():
    pass

def test_calculate_score_within_range():
    pass


# ❌ DON'T: Vague test names
def test_get():
    pass

def test_stock():
    pass

def test_1():
    pass
```

### Test Coverage

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
min_coverage = 80
addopts = [
    "-v",
    "--cov=.",
    "--cov-report=html",
    "--cov-report=term",
    "--cov-fail-under=80",
    "--strict-markers",
]

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## 🔒 Security Guidelines

### Never Hardcode Secrets

```python
# ❌ DON'T: Hardcode secrets
DATABASE_URL = "postgresql://user:password@localhost/db"
API_KEY = "sk-1234567890abcdef"
SECRET_KEY = "hardcoded_secret"


# ✅ DO: Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("TUSHARE_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")


# ✅ DO: Validate required secrets at startup
def validate_config():
    """Validate all required environment variables are set."""
    required_vars = ["DATABASE_URL", "TUSHARE_TOKEN", "SECRET_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


# ✅ DO: Use pydantic settings for validation
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    tushare_token: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### SQL Injection Prevention

```python
# ✅ DO: Use parameterized queries
def get_stock(symbol: str) -> Optional[Stock]:
    return session.query(Stock).filter(Stock.symbol == symbol).first()


# ✅ DO: Use SQLAlchemy ORM (automatically parameterized)
def get_stocks_by_industry(industry: str) -> List[Stock]:
    return session.query(Stock).filter(Stock.industry == industry).all()


# ❌ DON'T: String formatting in queries
def get_stock_bad(symbol: str) -> Optional[Stock]:
    # SQL injection vulnerability!
    query = f"SELECT * FROM stocks WHERE symbol = '{symbol}'"
    return session.execute(query).fetchone()
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from datetime import datetime


class CreatePositionRequest(BaseModel):
    """Request model for creating a position."""

    symbol: str = Field(..., min_length=6, max_length=6)
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    trade_date: datetime = Field(default_factory=datetime.now)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format."""
        if not v.isdigit():
            raise ValueError('Symbol must be numeric')
        return v

    @validator('price')
    def validate_price(cls, v):
        """Validate price is reasonable."""
        if v > 100000:  # Arbitrary high limit
            raise ValueError('Price seems unreasonably high')
        return v


# Usage in FastAPI
from fastapi import APIRouter

router = APIRouter()

@router.post("/positions")
async def create_position(request: CreatePositionRequest):
    """Create position with automatic validation."""
    # request is already validated by Pydantic
    position = Position(**request.dict())
    repository.save(position)
    return position
```

---

## ⚡ Performance Guidelines

### Database Optimization

```python
# ✅ DO: Use eager loading for related objects
def get_stock_with_indicators(symbol: str) -> Stock:
    return session.query(Stock)\
        .filter(Stock.symbol == symbol)\
        .options(joinedload(Stock.indicators))\
        .first()


# ✅ DO: Use batch operations
def bulk_insert_stocks(stocks: List[Stock]) -> None:
    session.bulk_save_objects(stocks)
    session.commit()


# ✅ DO: Use indexes for frequently queried fields
class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(6), unique=True, index=True)  # Indexed
    name = Column(String(100))
    industry = Column(String(50), index=True)  # Indexed


# ❌ DON'T: N+1 queries
def get_stocks_bad() -> List[Stock]:
    stocks = session.query(Stock).all()
    for stock in stocks:
        print(stock.indicators)  # Separate query for each stock


# ✅ DO: Use pagination for large datasets
def get_stocks_paginated(page: int, page_size: int) -> Tuple[List[Stock], int]:
    query = session.query(Stock)
    total = query.count()
    stocks = query.offset((page - 1) * page_size).limit(page_size).all()
    return stocks, total
```

### Caching

```python
from functools import lru_cache
import redis


# ✅ DO: Use LRU cache for pure functions
@lru_cache(maxsize=1000)
def calculate_indicator(klines: tuple) -> float:
    """Calculate indicator from immutable klines tuple."""
    # Pure function - same input always gives same output
    pass


# ✅ DO: Use Redis for shared cache
class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis.setex(key, ttl, json.dumps(value))


# ✅ DO: Cache expensive operations
def get_stock_data(symbol: str) -> dict:
    cache_key = f"stock:{symbol}"
    cached = cache_manager.get(cache_key)

    if cached:
        return cached

    # Fetch from database or API
    data = expensive_operation(symbol)
    cache_manager.set(cache_key, data, ttl=3600)
    return data
```

---

## ✅ Code Review Checklist

Use this checklist during code reviews:

### Code Quality
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation (immutable patterns used)

### Testing
- [ ] All new code has tests
- [ ] Test coverage is 80%+
- [ ] Tests are meaningful (not just code coverage)
- [ ] Edge cases are tested
- [ ] Test names are descriptive

### Documentation
- [ ] Public functions have docstrings
- [ ] Complex logic is explained
- [ ] Examples are provided where helpful
- [ ] Type hints are complete

### Security
- [ ] No hardcoded secrets
- [ ] All user inputs are validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] No XSS vulnerabilities
- [ ] Proper authentication/authorization

### Performance
- [ ] Database queries are optimized
- [ ] No N+1 queries
- [ ] Appropriate caching used
- [ ] Pagination for large datasets
- [ ] No unnecessary computations

### Style
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] No linting errors (flake8)
- [ ] Type hints are used
- [ ] Follows naming conventions

---

## 📚 Next Steps

- 🧪 [Testing Guide](./07-testing.md) - Comprehensive testing practices
- 🤝 [Contribution Guide](./08-contribution.md) - How to contribute to the project
- 🐛 [Debugging Guide](./09-debugging.md) - Debugging techniques and tools
- 🔗 [API Reference](./03-api-reference.md) - Complete API documentation

---

**Next Chapter**: [Testing Guide →](./07-testing.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
