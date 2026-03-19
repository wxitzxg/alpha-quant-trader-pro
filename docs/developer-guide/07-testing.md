# 🧪 Testing Guide

> Comprehensive testing practices and guidelines for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Test Structure](#test-structure)
4. [Unit Testing](#unit-testing)
5. [Integration Testing](#integration-testing)
6. [Test Fixtures](#test-fixtures)
7. [Mocking Strategies](#mocking-strategies)
8. [Test Coverage](#test-coverage)
9. [Running Tests](#running-tests)
10. [Common Testing Patterns](#common-testing-patterns)
11. [Testing Best Practices](#testing-best-practices)

---

## 🎯 Testing Philosophy

### Test-Driven Development (TDD)

We follow the **Red-Green-Refactor** cycle:

1. **Red**: Write a failing test first
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Improve code while keeping tests passing

**Benefits:**
- ✅ Better code design (testable code)
- ✅ Immediate feedback on changes
- ✅ Living documentation
- ✅ Confidence to refactor

### Testing Pyramid

```
         E2E Tests (5%)
              ↓
   Integration Tests (15%)
              ↓
      Unit Tests (80%)
```

**Distribution:**
- **80% Unit Tests** - Fast, isolated, test individual functions/classes
- **15% Integration Tests** - Test interactions between components
- **5% E2E Tests** - Test complete user flows

---

## 🧪 Test Types

### 1. Unit Tests

**Purpose**: Test individual units of code in isolation

**Characteristics:**
- Fast (milliseconds)
- Isolated (no external dependencies)
- Deterministic (same input = same output)
- Repeatable (no side effects)

**Examples:**
```python
# Test a service method
def test_calculate_score():
    klines = [mock_kline_1, mock_kline_2]
    score = calculate_score(klines)
    assert 0 <= score <= 100

# Test a utility function
def test_validate_symbol():
    assert validate_symbol("600519") == True
    assert validate_symbol("123") == False
```

### 2. Integration Tests

**Purpose**: Test interactions between components

**Characteristics:**
- Slower (seconds)
- Test database integration
- Test API endpoints
- Test service-repository interactions

**Examples:**
```python
# Test database operations
def test_stock_repository_save(session):
    repository = StockRepository(session)
    stock = Stock(symbol="600519", name="贵州茅台")
    repository.save(stock)
    session.commit()

    saved = repository.get("600519")
    assert saved.symbol == "600519"
    assert saved.name == "贵州茅台"

# Test API endpoint
def test_get_stock_endpoint(client):
    response = client.get("/api/v1/stocks/600519")
    assert response.status_code == 200
    assert response.json()["symbol"] == "600519"
```

### 3. E2E Tests

**Purpose**: Test complete user flows

**Characteristics:**
- Slowest (minutes)
- Test from UI to database
- Test complete workflows
- Use real browser (Playwright/Selenium)

**Example:**
```python
# Test complete trading flow
def test_complete_trading_flow(page):
    # Login
    page.goto("/login")
    page.fill("#username", "testuser")
    page.fill("#password", "password")
    page.click("#login-button")

    # Search stock
    page.fill("#search", "600519")
    page.click("#search-button")

    # Buy stock
    page.click("#buy-button")
    page.fill("#quantity", "100")
    page.click("#confirm-button")

    # Verify position created
    assert page.text_content("#positions") == "1 position"
```

---

## 📁 Test Structure

### Directory Organization

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── test_common/                   # Common module tests
│   ├── test_database.py
│   ├── test_config.py
│   └── test_exceptions.py
├── test_data_sources/             # Data sources tests
│   ├── test_aggregator.py
│   └── test_adapters/
│       ├── test_tushare_adapter.py
│       └── test_akshare_adapter.py
├── test_stock_market/             # Stock market tests
│   ├── test_models.py
│   ├── test_repositories/
│   │   ├── test_stock_repository.py
│   │   └── test_kline_repository.py
│   ├── test_services/
│   │   ├── test_stock_service.py
│   │   └── test_kline_service.py
│   └── test_managers/
│       ├── test_stock_manager.py
│       └── test_kline_manager.py
├── test_portfolio_manager/        # Portfolio manager tests
│   ├── test_models.py
│   ├── test_repositories/
│   ├── test_services/
│   └── test_commands.py
├── test_technical_analysis/       # Technical analysis tests
│   ├── test_services/
│   ├── test_engines/
│   └── test_indicators/
├── test_backtest/                 # Backtest tests
│   └── test_engine.py
└── integration/                   # Integration tests
    ├── test_trading_flow.py
    ├── test_analysis_flow.py
    └── test_api_endpoints.py
```

### Test File Template

```python
# tests/test_stock_market/test_services/test_stock_service.py

"""
Test module for StockService class.

Tests cover:
- CRUD operations
- Business logic
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from stock_market.services import StockService
from stock_market.repositories import StockRepository
from stock_market.models import Stock
from common.exceptions import DataNotFoundError


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

    # Test methods follow below...
```

---

## 🔴 Unit Testing

### Testing Services

```python
import pytest
from unittest.mock import Mock

from stock_market.services import StockService
from stock_market.models import Stock


class TestStockService:
    """Test StockService unit tests."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return Mock()

    @pytest.fixture
    def stock_service(self, mock_repository):
        """Create StockService with mock repository."""
        return StockService(mock_repository)

    def test_get_stock_success(self, stock_service, mock_repository):
        """Test getting a stock successfully."""
        # Arrange
        expected_stock = Stock(symbol="600519", name="贵州茅台")
        mock_repository.get.return_value = expected_stock

        # Act
        result = stock_service.get_stock("600519")

        # Assert
        assert result == expected_stock
        mock_repository.get.assert_called_once_with("600519")

    def test_get_stock_not_found(self, stock_service, mock_repository):
        """Test getting a stock that doesn't exist."""
        # Arrange
        mock_repository.get.return_value = None

        # Act & Assert
        with pytest.raises(DataNotFoundError):
            stock_service.get_stock("INVALID")

    def test_create_stock_success(self, stock_service, mock_repository):
        """Test creating a stock successfully."""
        # Arrange
        stock_data = {
            "symbol": "600519",
            "name": "贵州茅台",
            "industry": "白酒"
        }
        expected_stock = Stock(**stock_data)
        mock_repository.create.return_value = expected_stock

        # Act
        result = stock_service.create_stock(stock_data)

        # Assert
        assert result.symbol == "600519"
        assert result.name == "贵州茅台"
        mock_repository.create.assert_called_once()

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
```

### Testing Repositories

```python
import pytest
from unittest.mock import Mock

from stock_market.repositories import StockRepository
from stock_market.models import Stock


class TestStockRepository:
    """Test StockRepository unit tests."""

    @pytest.fixture
    def mock_session(self):
        """Create mock SQLAlchemy session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create StockRepository with mock session."""
        return StockRepository(mock_session)

    def test_get_success(self, repository, mock_session):
        """Test getting a stock by symbol."""
        # Arrange
        expected_stock = Stock(symbol="600519", name="贵州茅台")
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = expected_stock
        mock_session.query.return_value = mock_query

        # Act
        result = repository.get("600519")

        # Assert
        assert result == expected_stock
        mock_session.query.assert_called_once()
        mock_query.filter_by.assert_called_once_with(symbol="600519")

    def test_get_not_found(self, repository, mock_session):
        """Test getting a stock that doesn't exist."""
        # Arrange
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        # Act
        result = repository.get("INVALID")

        # Assert
        assert result is None
```

---

## 🔗 Integration Testing

### Database Integration Tests

```python
import pytest
from sqlalchemy.orm import Session

from stock_market.models import Stock
from stock_market.repositories import StockRepository


class TestStockRepositoryIntegration:
    """Integration tests for StockRepository with real database."""

    def test_save_and_get(self, session: Session):
        """Test saving and retrieving a stock."""
        # Arrange
        repository = StockRepository(session)
        stock = Stock(symbol="600519", name="贵州茅台", industry="白酒")

        # Act
        repository.save(stock)
        session.commit()

        retrieved = repository.get("600519")

        # Assert
        assert retrieved is not None
        assert retrieved.symbol == "600519"
        assert retrieved.name == "贵州茅台"
        assert retrieved.industry == "白酒"

    def test_find_all(self, session: Session):
        """Test retrieving all stocks."""
        # Arrange
        repository = StockRepository(session)
        stocks = [
            Stock(symbol="600519", name="贵州茅台"),
            Stock(symbol="000001", name="平安银行"),
        ]

        for stock in stocks:
            repository.save(stock)
        session.commit()

        # Act
        result = repository.find_all()

        # Assert
        assert len(result) >= 2
        symbols = {s.symbol for s in result}
        assert "600519" in symbols
        assert "000001" in symbols

    def test_update(self, session: Session):
        """Test updating a stock."""
        # Arrange
        repository = StockRepository(session)
        stock = Stock(symbol="600519", name="贵州茅台")
        repository.save(stock)
        session.commit()

        # Act
        stock.name = "贵州茅台酒"
        repository.save(stock)
        session.commit()

        # Assert
        updated = repository.get("600519")
        assert updated.name == "贵州茅台酒"
```

### API Integration Tests

```python
import pytest
from fastapi.testclient import TestClient

from api_server.main import app


class TestStockAPI:
    """Integration tests for stock API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers."""
        # In real implementation, get actual token
        return {"Authorization": "Bearer test_token"}

    def test_get_stock(self, client, auth_headers):
        """Test GET /stocks/{symbol} endpoint."""
        # Act
        response = client.get(
            "/api/v1/stocks/600519",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "600519"
        assert "name" in data
        assert "industry" in data

    def test_create_stock(self, client, auth_headers):
        """Test POST /stocks endpoint."""
        # Arrange
        stock_data = {
            "symbol": "600519",
            "name": "贵州茅台",
            "industry": "白酒"
        }

        # Act
        response = client.post(
            "/api/v1/stocks",
            json=stock_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "600519"
        assert data["name"] == "贵州茅台"

    def test_get_stock_not_found(self, client, auth_headers):
        """Test GET endpoint with non-existent stock."""
        # Act
        response = client.get(
            "/api/v1/stocks/INVALID",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
```

---

## 🔧 Test Fixtures

### conftest.py

```python
# tests/conftest.py

"""
Pytest configuration and shared fixtures.

Fixtures defined here are available to all test files.
"""

import pytest
from typing import Generator
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from common.database import Base


# Database fixtures
@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite database engine for testing."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(engine, tables) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Mock fixtures
@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_tushare_adapter():
    """Create a mock Tushare adapter."""
    adapter = Mock()
    adapter.get_stock = Mock()
    adapter.get_kline = Mock()
    return adapter


# Test data fixtures
@pytest.fixture
def sample_stock():
    """Create a sample stock for testing."""
    from stock_market.models import Stock
    return Stock(
        symbol="600519",
        name="贵州茅台",
        industry="白酒",
        market_cap=2000000000000
    )


@pytest.fixture
def sample_klines():
    """Create sample K-line data for testing."""
    from stock_market.models import KLine
    return [
        KLine(
            symbol="600519",
            date="2023-01-01",
            open=1800,
            high=1850,
            low=1790,
            close=1830,
            volume=1000000
        ),
        KLine(
            symbol="600519",
            date="2023-01-02",
            open=1830,
            high=1880,
            low=1820,
            close=1860,
            volume=1200000
        ),
    ]
```

### Factory Fixtures

```python
# tests/factories.py

"""
Test data factories using factory_boy.

Creates realistic test data with minimal setup.
"""

import factory
from datetime import datetime, timedelta

from stock_market.models import Stock, KLine
from portfolio_manager.models import Position, Transaction


class StockFactory(factory.Factory):
    """Factory for creating Stock instances."""

    class Meta:
        model = Stock

    symbol = factory.Sequence(lambda n: f"STOCK{n:06d}")
    name = factory.Faker("company")
    industry = factory.Faker("word")
    market_cap = factory.Faker("random_int", min=1000000000, max=1000000000000)
    listed_date = factory.Faker("date_between", start_date="-10y", end_date="today")


class KLineFactory(factory.Factory):
    """Factory for creating KLine instances."""

    class Meta:
        model = KLine

    symbol = factory.Sequence(lambda n: f"STOCK{n:06d}")
    date = factory.Faker("date_between", start_date="-1y", end_date="today")
    open = factory.Faker("pyfloat", min_value=10, max_value=10000, right_digits=2)
    high = factory.LazyAttribute(lambda obj: obj.open * factory.Faker("pyfloat", min_value=1.0, max_value=1.1).evaluate(None, None, {}))
    low = factory.LazyAttribute(lambda obj: obj.open * factory.Faker("pyfloat", min_value=0.9, max_value=1.0).evaluate(None, None, {}))
    close = factory.LazyAttribute(lambda obj: (obj.high + obj.low) / 2)
    volume = factory.Faker("random_int", min=100000, max=10000000)


class PositionFactory(factory.Factory):
    """Factory for creating Position instances."""

    class Meta:
        model = Position

    symbol = factory.Sequence(lambda n: f"STOCK{n:06d}")
    quantity = factory.Faker("random_int", min=100, max=10000)
    avg_cost = factory.Faker("pyfloat", min_value=10, max_value=1000, right_digits=2)
    market_value = factory.LazyAttribute(lambda obj: obj.quantity * obj.avg_cost * 1.1)


class TransactionFactory(factory.Factory):
    """Factory for creating Transaction instances."""

    class Meta:
        model = Transaction

    symbol = factory.Sequence(lambda n: f"STOCK{n:06d}")
    quantity = factory.Faker("random_int", min=100, max=10000)
    price = factory.Faker("pyfloat", min_value=10, max_value=1000, right_digits=2)
    transaction_type = factory.Iterator(["buy", "sell"])
    amount = factory.LazyAttribute(lambda obj: obj.quantity * obj.price)
    transaction_date = factory.Faker("date_time_between", start_date="-1y", end_date="now")


# Usage in tests
def test_with_factories():
    """Test using factories."""
    # Create a single stock
    stock = StockFactory(symbol="600519", name="贵州茅台")

    # Create multiple K-lines
    klines = KLineFactory.create_batch(10, symbol="600519")

    # Create a position with related transaction
    position = PositionFactory(symbol="600519", quantity=1000)
    transaction = TransactionFactory(symbol="600519", quantity=1000, transaction_type="buy")
```

---

## 🎭 Mocking Strategies

### When to Mock

**Mock external dependencies:**
- Database connections (use in-memory SQLite for integration tests)
- External APIs (Tushare, AKShare)
- File I/O
- Network calls
- Time/date functions

**Don't mock:**
- Your own code (test actual implementation)
- Simple data classes
- Pure functions (deterministic, no side effects)

### Mocking Examples

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# Mock external API
@patch('stock_market.services.TushareAdapter')
def test_sync_stock_with_mock(mock_adapter, stock_service):
    """Test syncing stock with mocked Tushare API."""
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


# Mock datetime for time-dependent tests
@patch('stock_market.services.datetime')
def test_time_dependent_logic(mock_datetime, stock_service):
    """Test logic that depends on current time."""
    # Arrange
    mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 0)

    # Act
    result = stock_service.is_market_open()

    # Assert
    assert result == True


# Mock with side effects for error testing
def test_handle_api_error(stock_service):
    """Test error handling when API fails."""
    # Arrange
    mock_adapter = Mock()
    mock_adapter.get_stock.side_effect = ConnectionError("API unavailable")
    stock_service.data_source = mock_adapter

    # Act & Assert
    with pytest.raises(DataUnavailableError):
        stock_service.sync_stock("600519")


# Mock context managers
def test_file_operation_with_mock():
    """Test file operations with mocked open."""
    with patch('builtins.open', mock_open(read_data='test data')) as mock_file:
        # Act
        with open('test.txt', 'r') as f:
            content = f.read()

        # Assert
        assert content == 'test data'
        mock_file.assert_called_once_with('test.txt', 'r')
```

---

## 📊 Test Coverage

### Configuration

**pyproject.toml or pytest.ini:**
```toml
[tool.pytest.ini_options]
min_coverage = 80
addopts = [
    "-v",
    "--strict-markers",
    "--cov=.",
    "--cov-report=term",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",
    "--cov-branch",
]

[tool.coverage.run]
source = ["."]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Running Coverage

```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=term

# Generate HTML report
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Generate XML report (for CI)
pytest tests/ --cov=. --cov-report=xml

# Fail if coverage < 80%
pytest tests/ --cov=. --cov-fail-under=80

# Coverage by file
pytest tests/ --cov=. --cov-report=term-missing
```

### Coverage Report Example

```
----------- coverage: platform linux, python 3.10.12 -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
api_server/main.py                  120      5    96%
api_server/routers/portfolio.py     200     10    95%
common/database.py                  150      8    95%
common/exceptions.py                 50      0   100%
stock_market/models.py              100      5    95%
stock_market/repositories/          300     20    93%
stock_market/services/              400     30    93%
---------------------------------------------------------------
TOTAL                              1320     78    94%

Required test coverage of 80% reached. Total coverage: 94.1%
```

---

## 🏃 Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_stock_market/test_services/test_stock_service.py

# Run specific test class
pytest tests/test_stock_market/test_services/test_stock_service.py::TestStockService

# Run specific test method
pytest tests/test_stock_market/test_services/test_stock_service.py::TestStockService::test_get_stock_success

# Run with verbose output
pytest tests/ -v

# Run with output capture disabled (see print statements)
pytest tests/ -v -s

# Run failed tests only
pytest --lf

# Run last failed tests first, then all others
pytest --ff

# Run tests matching pattern
pytest tests/ -k "test_get_stock"

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

### Test Markers

```python
import pytest


# Mark slow tests
@pytest.mark.slow
def test_slow_integration():
    """This test takes a long time."""
    pass


# Mark integration tests
@pytest.mark.integration
def test_database_integration():
    """This is an integration test."""
    pass


# Mark API tests
@pytest.mark.api
def test_api_endpoint():
    """This tests an API endpoint."""
    pass


# Run specific markers
pytest tests/ -m "not slow"  # Run all except slow tests
pytest tests/ -m "integration"  # Run only integration tests
pytest tests/ -m "api or integration"  # Run API or integration tests
```

### CI/CD Integration

**GitHub Actions Example (.github/workflows/test.yml):**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=. --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
```

---

## 🎨 Common Testing Patterns

### Arrange-Act-Assert Pattern

```python
def test_calculate_score():
    """Test score calculation."""
    # Arrange
    klines = [
        KLine(symbol="600519", date="2023-01-01", open=100, high=110, low=95, close=105),
        KLine(symbol="600519", date="2023-01-02", open=105, high=115, low=100, close=110),
    ]

    # Act
    score = calculate_score(klines)

    # Assert
    assert isinstance(score, float)
    assert 0 <= score <= 100
```

### Given-When-Then Pattern

```python
def test_buy_stock_success():
    """Test buying stock successfully."""
    # Given: User has sufficient balance and stock is available
    account = Account(balance=100000)
    stock = Stock(symbol="600519", current_price=1000)

    # When: User buys 10 shares
    result = buy_stock(account, stock, quantity=10)

    # Then: Position is created and balance is updated
    assert result.position.quantity == 10
    assert account.balance == 90000
```

### Test Table Pattern (Parametrize)

```python
@pytest.mark.parametrize("symbol,quantity,price,expected_success", [
    ("600519", 100, 1000, True),      # Valid purchase
    ("600519", 0, 1000, False),       # Zero quantity
    ("600519", -10, 1000, False),     # Negative quantity
    ("INVALID", 100, 1000, False),    # Invalid symbol
])
def test_buy_stock_validation(symbol, quantity, price, expected_success):
    """Test buy stock with various inputs."""
    if expected_success:
        result = buy_stock(symbol, quantity, price)
        assert result is not None
    else:
        with pytest.raises(ValidationError):
            buy_stock(symbol, quantity, price)
```

---

## ✅ Testing Best Practices

### DO

✅ **Write tests first (TDD)**
```python
# 1. Write failing test
def test_calculate_roi():
    assert calculate_roi(1000, 1100) == 10.0

# 2. Implement minimal code to pass
def calculate_roi(cost, revenue):
    return (revenue - cost) / cost * 100

# 3. Refactor and improve
```

✅ **Test one thing per test**
```python
# Good: One assertion per test (or related assertions)
def test_stock_creation():
    stock = Stock(symbol="600519", name="贵州茅台")
    assert stock.symbol == "600519"
    assert stock.name == "贵州茅台"
```

✅ **Use descriptive test names**
```python
# Good
def test_calculate_score_returns_float_between_0_and_100():
    pass

# Avoid
def test_calc():
    pass
```

✅ **Test edge cases**
```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_empty_list():
    assert calculate_average([]) == 0
```

✅ **Clean up after tests**
```python
@pytest.fixture
def temporary_file():
    """Create temporary file for testing."""
    filepath = "/tmp/test_file.txt"
    with open(filepath, 'w') as f:
        f.write("test data")
    yield filepath
    # Cleanup
    os.remove(filepath)
```

### DON'T

❌ **Don't test implementation details**
```python
# Bad: Testing private methods
def test__calculate_internal_score():
    pass

# Good: Test public interface
def test_calculate_score():
    pass
```

❌ **Don't write slow unit tests**
```python
# Bad: Unit test making network calls
def test_get_stock():
    stock = get_stock_from_api("600519")  # Slow API call
    assert stock is not None

# Good: Mock external dependencies
@patch('stock_service.api_client')
def test_get_stock(mock_client):
    mock_client.get.return_value = {"symbol": "600519"}
    stock = get_stock("600519")
    assert stock.symbol == "600519"
```

❌ **Don't duplicate production code in tests**
```python
# Bad: Copy-paste logic from production
def test_calculate():
    # Duplicated calculation logic
    result = price * quantity * (1 + tax_rate)
    assert calculate(price, quantity, tax_rate) == result

# Good: Use known inputs and expected outputs
def test_calculate():
    assert calculate(100, 2, 0.1) == 220
```

❌ **Don't leave commented-out tests**
```python
# Bad
# def test_old_feature():
#     pass  # This test was failing, will fix later

# Good: Mark as skip with reason
@pytest.mark.skip(reason="Feature deprecated in v2.0")
def test_old_feature():
    pass
```

---

## 📚 Next Steps

- 🐛 [Debugging Guide](./09-debugging.md) - Debugging techniques and tools
- 🔌 [API Reference](./03-api-reference.md) - Complete API documentation
- 📖 [Module Guides](./04-module-guide/) - Module-specific guides
- 🏗️ [Architecture](./01-architecture.md) - System architecture overview

---

**Next Chapter**: [Debugging Guide →](./09-debugging.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
