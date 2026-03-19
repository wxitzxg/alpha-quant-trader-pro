# 🏗️ System Architecture

> Complete architecture overview of Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layered Architecture](#layered-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)

---

## 🏛️ Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  - Web UI, Mobile App, API Clients                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  API Gateway Layer                       │
│  - Authentication, Rate Limiting, Request Routing       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│  - Commands (PortfolioCommands, AnalysisCommands)       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│  - StockService, KLineService, AnalysisService          │
│  - PositionService, TransactionService, AccountService  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Repository Layer                        │
│  - StockRepository, KLineRepository                     │
│  - PositionRepository, TransactionRepository            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Data Source Layer                       │
│  - DatabaseManager (PostgreSQL)                         │
│  - DataSourceAggregator (Tushare, AKShare, Sina)        │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Layered Architecture

### 1. Application Layer

**Purpose**: High-level business operations and user interactions

**Components**:
- `PortfolioCommands` - Trading operations
- `AnalysisCommands` - Technical analysis operations
- `BacktestCommands` - Backtesting operations

**Responsibilities**:
- Coordinate multiple services
- Handle complex business workflows
- Manage transactions
- Validate high-level business rules

**Example**:
```python
class PortfolioCommands:
    def __init__(self):
        self.position_service = PositionService(...)
        self.transaction_service = TransactionService(...)
        self.account_service = AccountService(...)

    def buy(self, symbol, quantity, price):
        # Coordinate multiple services
        position = self.position_service.get_or_create(symbol)
        transaction = self.transaction_service.create_buy(...)
        self.account_service.update_cash(...)
        return position
```

---

### 2. Service Layer

**Purpose**: Business logic and domain operations

**Core Services**:
- `StockService` - Stock data operations
- `KLineService` - K-line data operations
- `AnalysisService` - Technical analysis
- `PositionService` - Position management
- `TransactionService` - Transaction management
- `AccountService` - Account management

**Responsibilities**:
- Implement business rules
- Coordinate repository operations
- Handle domain-specific logic
- Ensure data consistency

**Example**:
```python
class AnalysisService:
    def __init__(self, repository):
        self.repository = repository

    def analyze_stock(self, symbol, days=120):
        # Business logic
        klines = self.repository.get_klines(symbol, days)
        score = self._calculate_five_dimension_score(klines)
        signals = self._generate_trading_signals(klines)
        return {
            'symbol': symbol,
            'score': score,
            'signals': signals
        }
```

---

### 3. Repository Layer

**Purpose**: Data access abstraction

**Core Repositories**:
- `StockRepository` - Stock data access
- `KLineRepository` - K-line data access
- `PositionRepository` - Position data access
- `TransactionRepository` - Transaction data access

**Responsibilities**:
- Abstract database operations
- Provide clean query interface
- Handle data mapping
- Manage caching (optional)

**Example**:
```python
class KLineRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(KLine, session)

    def get_by_symbol_and_date(self, symbol, date):
        return self.session.query(KLine).filter_by(
            symbol=symbol,
            date=date
        ).first()

    def get_range(self, symbol, start_date, end_date):
        return self.session.query(KLine).filter(
            KLine.symbol == symbol,
            KLine.date.between(start_date, end_date)
        ).order_by(KLine.date.desc()).all()
```

---

### 4. Data Source Layer

**Purpose**: External data access

**Components**:
- `DatabaseManager` - PostgreSQL connection management
- `DataSourceAggregator` - Multiple data source aggregation
- `TushareAdapter` - Tushare data source
- `AKShareAdapter` - AKShare data source
- `SinaFinanceAdapter` - Sina Finance data source

**Responsibilities**:
- Manage database connections
- Handle external API calls
- Implement adapter patterns
- Manage data source failover

**Example**:
```python
class DataSourceAggregator:
    def __init__(self):
        self.primary = TushareAdapter()
        self.fallbacks = [AKShareAdapter(), SinaFinanceAdapter()]

    def get_kline(self, symbol, interval, start_date, end_date):
        try:
            return self.primary.get_kline(...)
        except Exception:
            for fallback in self.fallbacks:
                try:
                    return fallback.get_kline(...)
                except Exception:
                    continue
            raise DataUnavailableError()
```

---

## 🧩 Core Components

### 1. Data Sources Module (`data_sources/`)

**Purpose**: Unified data access layer

**Structure**:
```
data_sources/
├── __init__.py
├── base.py                    # DataSourceAdapter base class
├── aggregator.py              # DataSourceAggregator
├── exceptions.py              # Data source exceptions
└── adapters/
    ├── __init__.py
    ├── tushare_adapter.py     # Tushare adapter
    ├── akshare_adapter.py     # AKShare adapter
    └── sina_adapter.py        # Sina Finance adapter
```

**Key Classes**:
```python
class DataSourceAdapter(ABC):
    @abstractmethod
    def get_kline(self, symbol, interval, start_date, end_date):
        pass

    @abstractmethod
    def get_stock_list(self):
        pass

class DataSourceAggregator:
    def __init__(self, config):
        self.adapters = self._load_adapters(config)

    def get_data(self, source_type, **kwargs):
        # Try primary, then fallbacks
        pass
```

---

### 2. Stock Market Module (`stock_market/`)

**Purpose**: Stock and K-line data management

**Structure**:
```
stock_market/
├── __init__.py
├── models.py                  # SQLAlchemy models
├── repositories/
│   ├── __init__.py
│   ├── stock_repository.py
│   └── kline_repository.py
├── services/
│   ├── __init__.py
│   ├── stock_service.py
│   └── kline_service.py
├── managers/
│   ├── __init__.py
│   ├── stock_manager.py
│   └── kline_manager.py
└── sync/
    ├── __init__.py
    ├── concurrent_sync.py
    └── incremental_sync.py
```

---

### 3. Portfolio Manager Module (`portfolio_manager/`)

**Purpose**: User position and transaction management

**Structure**:
```
portfolio_manager/
├── __init__.py
├── commands.py                # PortfolioCommands
├── models.py
├── repositories/
│   ├── position_repository.py
│   └── transaction_repository.py
├── services/
│   ├── position_service.py
│   ├── transaction_service.py
│   └── account_service.py
└── exceptions.py
```

---

### 4. Technical Analysis Module (`technical_analysis/`)

**Purpose**: Technical indicators and strategy engine

**Structure**:
```
technical_analysis/
├── __init__.py
├── models.py
├── services/
│   └── analysis_service.py
├── engines/
│   ├── scoring_engine.py
│   ├── strategy_engine.py
│   └── indicator_engine.py
├── indicators/
│   ├── moving_average.py
│   ├── macd.py
│   ├── rsi.py
│   ├── bollinger_bands.py
│   └── stochastic.py
└── strategies/
    ├── vcp_strategy.py
    ├── nine_turn_strategy.py
    └── divergence_strategy.py
```

---

### 5. Backtest Module (`backtest/`)

**Purpose**: Strategy backtesting and performance analysis

**Structure**:
```
backtest/
├── __init__.py
├── engine.py                  # BacktestEngine
├── executor.py                # StrategyExecutor
├── calculator.py              # PerformanceCalculator
├── report_generator.py        # ReportGenerator
└── optimizers/
    ├── parameter_optimizer.py
    ├── walk_forward_analyzer.py
    └── monte_carlo_simulator.py
```

---

## 🔄 Data Flow

### Example: Buy Stock Flow

```
1. User Request
   ↓
2. API Gateway (Auth, Rate Limit)
   ↓
3. PortfolioCommands.buy(symbol, quantity, price)
   ↓
4. PositionService.get_or_create(symbol)
   → PositionRepository.get(symbol)
   → Database query
   ← Position entity
   ↓
5. TransactionService.create_buy(...)
   → TransactionRepository.create(...)
   → Database insert
   ← Transaction entity
   ↓
6. AccountService.update_cash(...)
   → AccountRepository.update(...)
   → Database update
   ↓
7. Database Transaction Commit
   ↓
8. Return Position to User
```

### Example: Technical Analysis Flow

```
1. User Request Analysis
   ↓
2. AnalysisService.analyze_stock(symbol, days=120)
   ↓
3. KLineRepository.get_range(symbol, days)
   → Database query
   ← K-line data
   ↓
4. IndicatorEngine.calculate_all_indicators(klines)
   → MovingAverage.calculate(...)
   → MACD.calculate(...)
   → RSI.calculate(...)
   ← Indicator values
   ↓
5. ScoringEngine.calculate_five_dimension_score(...)
   → Trend analysis
   → Pattern recognition
   → Position evaluation
   → Momentum calculation
   → Trigger detection
   ← Total score (0-100)
   ↓
6. StrategyEngine.generate_signals(...)
   → VCP strategy check
   → Nine-turn sequence check
   → Divergence detection
   ← Trading signals
   ↓
7. Return Analysis Results
```

---

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.8+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7.0+
- **Task Queue**: Celery (optional)

### Data Sources
- **Primary**: Tushare Pro
- **Fallback 1**: AKShare
- **Fallback 2**: Sina Finance

### DevOps
- **Container**: Docker, Docker Compose
- **Deployment**: Gunicorn, Systemd
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack (optional)

### Testing
- **Unit Test**: pytest
- **Coverage**: pytest-cov
- **Mock**: unittest.mock
- **Integration**: pytest-asyncio

---

## 🎨 Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access

```python
class BaseRepository:
    def __init__(self, model, session):
        self.model = model
        self.session = session

    def get(self, id):
        return self.session.query(self.model).get(id)

    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.session.add(obj)
        return obj
```

---

### 2. Adapter Pattern

**Purpose**: Unified interface for different data sources

```python
class DataSourceAdapter(ABC):
    @abstractmethod
    def get_kline(self, symbol, interval, start_date, end_date):
        pass

class TushareAdapter(DataSourceAdapter):
    def get_kline(self, symbol, interval, start_date, end_date):
        # Tushare-specific implementation
        pass
```

---

### 3. Strategy Pattern

**Purpose**: Flexible algorithm selection

```python
class TradingStrategy(ABC):
    @abstractmethod
    def analyze(self, klines):
        pass

class VCPStrategy(TradingStrategy):
    def analyze(self, klines):
        # VCP pattern detection
        pass

class NineTurnStrategy(TradingStrategy):
    def analyze(self, klines):
        # Nine-turn sequence detection
        pass
```

---

### 4. Dependency Injection

**Purpose**: Loose coupling and testability

```python
class AnalysisService:
    def __init__(self, repository: KLineRepository):
        self.repository = repository  # Injected dependency

    def analyze(self, symbol):
        klines = self.repository.get_klines(symbol)
        # ...
```

---

### 5. Factory Pattern

**Purpose**: Object creation abstraction

```python
class DataSourceFactory:
    @staticmethod
    def create_source(source_type: str) -> DataSourceAdapter:
        if source_type == "tushare":
            return TushareAdapter()
        elif source_type == "akshare":
            return AKShareAdapter()
        raise ValueError(f"Unknown source: {source_type}")
```

---

## 🔗 Key Design Decisions

### 1. Repository Pattern
**Why**: Separation of concerns, easier testing, database agnostic

### 2. Layered Architecture
**Why**: Clear separation of responsibilities, maintainability

### 3. Adapter Pattern for Data Sources
**Why**: Easy to add new data sources, failover support

### 4. SQLAlchemy ORM
**Why**: Pythonic, powerful query API, good PostgreSQL support

### 5. FastAPI Framework
**Why**: Automatic OpenAPI docs, async support, performance

---

## 📚 Next Steps

- 📦 [Project Structure](./02-project-structure.md) - Detailed project organization
- 🔌 [API Reference](./03-api-reference.md) - API documentation
- 📖 [Module Guides](./04-module-guide/) - Module-specific guides
- 🛠️ [Development Setup](./05-development-setup.md) - Development environment

---

**Next Chapter**: [Project Structure →](./02-project-structure.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
