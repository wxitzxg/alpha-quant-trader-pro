# 📁 Project Structure

> Detailed project organization and file structure

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Module Organization](#module-organization)
4. [File Naming Conventions](#file-naming-conventions)
5. [Import Structure](#import-structure)
6. [Configuration Files](#configuration-files)

---

## 🎯 Project Overview

Alpha Quant Trader Pro is organized as a **monorepo** with clearly separated modules. Each module follows the same internal structure for consistency.

### Core Principles

- **Separation of Concerns**: Each module has a single responsibility
- **Consistent Structure**: All modules follow the same pattern
- **Clear Boundaries**: Well-defined interfaces between modules
- **Testability**: Easy to test individual components

---

## 📂 Directory Structure

```
alpha-quant-trader-pro/
│
├── README.md                          # Project overview
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── .env.example                       # Environment template
├── alembic/                           # Database migrations
│
├── api_server/                        # API Server Module
│   ├── __init__.py
│   ├── main.py                        # FastAPI app entry point
│   ├── routers/                       # API route handlers
│   │   ├── __init__.py
│   │   ├── portfolio.py
│   │   ├── analysis.py
│   │   ├── backtest.py
│   │   └── ...
│   ├── middleware/                    # Custom middleware
│   ├── dependencies.py                # Dependency injection
│   └── schemas/                       # Pydantic schemas
│
├── common/                            # Shared Infrastructure
│   ├── __init__.py
│   ├── database.py                    # DatabaseManager
│   ├── exceptions.py                  # Custom exceptions
│   ├── config.py                      # ConfigManager
│   ├── di_container.py                # Dependency injection container
│   └── repositories/                  # Base repository classes
│       ├── __init__.py
│       └── base_repository.py
│
├── data_sources/                      # Data Source Module
│   ├── __init__.py
│   ├── base.py                        # DataSourceAdapter abstract base
│   ├── aggregator.py                  # DataSourceAggregator
│   ├── exceptions.py                  # Data source exceptions
│   └── adapters/                      # Data source adapters
│       ├── __init__.py
│       ├── tushare_adapter.py
│       ├── akshare_adapter.py
│       └── sina_adapter.py
│
├── stock_market/                      # Stock Market Module
│   ├── __init__.py
│   ├── models.py                      # SQLAlchemy models
│   ├── repositories/                  # Data access layer
│   │   ├── __init__.py
│   │   ├── stock_repository.py
│   │   └── kline_repository.py
│   ├── services/                      # Business logic
│   │   ├── __init__.py
│   │   ├── stock_service.py
│   │   └── kline_service.py
│   ├── managers/                      # High-level managers
│   │   ├── __init__.py
│   │   ├── stock_manager.py
│   │   └── kline_manager.py
│   ├── sync/                          # Data synchronization
│   │   ├── __init__.py
│   │   ├── concurrent_sync.py
│   │   └── incremental_sync.py
│   └── utils/                         # Utility functions
│       ├── __init__.py
│       └── date_utils.py
│
├── portfolio_manager/                 # Portfolio Manager Module
│   ├── __init__.py
│   ├── models.py
│   ├── commands.py                    # PortfolioCommands
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── position_repository.py
│   │   └── transaction_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── position_service.py
│   │   ├── transaction_service.py
│   │   └── account_service.py
│   └── exceptions.py
│
├── technical_analysis/                # Technical Analysis Module
│   ├── __init__.py
│   ├── models.py
│   ├── services/
│   │   └── analysis_service.py
│   ├── engines/                       # Analysis engines
│   │   ├── __init__.py
│   │   ├── scoring_engine.py
│   │   ├── strategy_engine.py
│   │   └── indicator_engine.py
│   ├── indicators/                    # Technical indicators
│   │   ├── __init__.py
│   │   ├── moving_average.py
│   │   ├── macd.py
│   │   ├── rsi.py
│   │   ├── bollinger_bands.py
│   │   └── stochastic.py
│   └── strategies/                    # Trading strategies
│       ├── __init__.py
│       ├── vcp_strategy.py
│       ├── nine_turn_strategy.py
│       └── divergence_strategy.py
│
├── backtest/                          # Backtest Module
│   ├── __init__.py
│   ├── engine.py                      # BacktestEngine
│   ├── executor.py                    # StrategyExecutor
│   ├── calculator.py                  # PerformanceCalculator
│   ├── report_generator.py            # ReportGenerator
│   └── optimizers/                    # Optimization tools
│       ├── __init__.py
│       ├── parameter_optimizer.py
│       ├── walk_forward_analyzer.py
│       └── monte_carlo_simulator.py
│
├── config/                            # Configuration Files
│   ├── default.json                   # Default configuration
│   ├── development.json               # Development overrides
│   ├── production.json                # Production overrides
│   └── sources.json                   # Data source configuration
│
├── scripts/                           # Utility Scripts
│   ├── __init__.py
│   ├── sync_stocks.py                 # Stock data sync script
│   ├── sync_klines.py                 # K-line data sync script
│   └── backup_database.py             # Database backup script
│
├── tests/                             # Test Suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration
│   ├── test_common/                   # Common module tests
│   ├── test_data_sources/             # Data sources tests
│   ├── test_stock_market/             # Stock market tests
│   ├── test_portfolio_manager/        # Portfolio manager tests
│   ├── test_technical_analysis/       # Technical analysis tests
│   ├── test_backtest/                 # Backtest tests
│   └── integration/                   # Integration tests
│
├── docs/                              # Documentation
│   ├── README.md                      # Documentation index
│   ├── user-guide/                    # User documentation
│   ├── admin-guide/                   # Admin documentation
│   ├── developer-guide/               # Developer documentation
│   └── project-docs/                  # Project documentation
│
└── examples/                          # Example Code
    ├── __init__.py
    ├── usage.py                       # Complete usage example
    ├── trading_example.py             # Trading example
    └── analysis_example.py            # Analysis example
```

---

## 📦 Module Organization

### Common Module (`common/`)

**Purpose**: Shared infrastructure used by all modules

**Key Components**:
```python
common/
├── database.py           # DatabaseManager - Connection management
├── exceptions.py         # Custom exception hierarchy
├── config.py            # ConfigManager - Configuration loading
├── di_container.py      # Dependency injection container
└── repositories/
    └── base_repository.py  # BaseRepository - Abstract base class
```

**Usage**:
```python
from common.database import DatabaseManager
from common.exceptions import DataNotFoundError
from common.config import ConfigManager

db = DatabaseManager("postgresql://...")
config = ConfigManager()
```

---

### Data Sources Module (`data_sources/`)

**Purpose**: Unified data access layer

**Structure**:
```python
data_sources/
├── base.py              # DataSourceAdapter (abstract base)
├── aggregator.py        # DataSourceAggregator
└── adapters/           # Concrete adapter implementations
    ├── tushare_adapter.py
    ├── akshare_adapter.py
    └── sina_adapter.py
```

**Usage**:
```python
from data_sources import DataSourceAggregator

aggregator = DataSourceAggregator()
klines = aggregator.get_kline("600519", "1d", "2023-01-01", "2023-12-31")
```

---

### Stock Market Module (`stock_market/`)

**Purpose**: Stock and K-line data management

**Layered Structure**:
```python
stock_market/
├── models.py           # SQLAlchemy ORM models
├── repositories/       # Data access layer
│   ├── stock_repository.py
│   └── kline_repository.py
├── services/          # Business logic layer
│   ├── stock_service.py
│   └── kline_service.py
├── managers/          # High-level operations
│   ├── stock_manager.py
│   └── kline_manager.py
└── sync/              # Data synchronization
    ├── concurrent_sync.py
    └── incremental_sync.py
```

**Layer Responsibilities**:

| Layer | Responsibility | Example Classes |
|-------|---------------|-----------------|
| **Repository** | Data access abstraction | StockRepository, KLineRepository |
| **Service** | Business logic | StockService, KLineService |
| **Manager** | High-level operations | StockDataManager, KLineDataManager |

---

### Portfolio Manager Module (`portfolio_manager/`)

**Purpose**: User position and transaction management

**Structure**:
```python
portfolio_manager/
├── commands.py          # PortfolioCommands (application layer)
├── models.py           # Position, Transaction, Account models
├── repositories/       # Data access
│   ├── position_repository.py
│   └── transaction_repository.py
├── services/          # Business logic
│   ├── position_service.py
│   ├── transaction_service.py
│   └── account_service.py
└── exceptions.py      # Portfolio-specific exceptions
```

---

### Technical Analysis Module (`technical_analysis/`)

**Purpose**: Technical indicators and strategy engine

**Structure**:
```python
technical_analysis/
├── services/
│   └── analysis_service.py       # High-level analysis interface
├── engines/                      # Analysis engines
│   ├── scoring_engine.py         # Five-dimension scoring
│   ├── strategy_engine.py        # Strategy execution
│   └── indicator_engine.py       # Indicator calculation
├── indicators/                   # Technical indicators
│   ├── moving_average.py
│   ├── macd.py
│   ├── rsi.py
│   ├── bollinger_bands.py
│   └── stochastic.py
└── strategies/                   # Trading strategies
    ├── vcp_strategy.py
    ├── nine_turn_strategy.py
    └── divergence_strategy.py
```

---

### Backtest Module (`backtest/`)

**Purpose**: Strategy backtesting and performance analysis

**Structure**:
```python
backtest/
├── engine.py                    # BacktestEngine - Main orchestrator
├── executor.py                  # StrategyExecutor - Signal execution
├── calculator.py                # PerformanceCalculator - Metrics
├── report_generator.py          # ReportGenerator - Report creation
└── optimizers/                  # Optimization tools
    ├── parameter_optimizer.py
    ├── walk_forward_analyzer.py
    └── monte_carlo_simulator.py
```

---

## 📝 File Naming Conventions

### Python Files

| Type | Pattern | Example |
|------|---------|---------|
| **Module** | `snake_case` | `stock_service.py` |
| **Class** | `PascalCase` in `snake_case.py` | `class StockService` |
| **Function** | `snake_case` | `get_stock_data()` |
| **Constant** | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS = 100` |
| **Private** | `_snake_case` | `_internal_helper()` |

### Test Files

| Type | Pattern | Example |
|------|---------|---------|
| **Unit Test** | `test_<module>.py` | `test_stock_service.py` |
| **Integration Test** | `test_integration.py` | `test_integration.py` |
| **E2E Test** | `test_e2e.py` | `test_e2e_trading.py` |

### Configuration Files

| Type | Pattern | Example |
|------|---------|---------|
| **JSON Config** | `<name>.json` | `production.json` |
| **Environment** | `.env*` | `.env.production` |
| **YAML Config** | `<name>.yaml` | `docker-compose.yml` |

---

## 🔗 Import Structure

### Import Order (PEP 8)

```python
# 1. Standard library imports
import os
import sys
from datetime import datetime

# 2. Third-party imports
from fastapi import FastAPI
from sqlalchemy import create_engine
import pandas as pd

# 3. Local application imports
from common.database import DatabaseManager
from stock_market.services import StockService
from .models import KLine
```

### Absolute vs Relative Imports

**Use Absolute Imports** (Recommended):
```python
from stock_market.services import StockService
from common.database import DatabaseManager
```

**Use Relative Imports** (Within same module):
```python
from .models import KLine
from ..repositories import KLineRepository
```

---

## ⚙️ Configuration Files

### Project Configuration (`pyproject.toml`)

```toml
[tool.poetry]
name = "alpha-quant-trader-pro"
version = "2.0.0"
description = "Quantitative Trading System"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.104.0"
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.0"
pandas = "^2.0.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=."
```

### Environment Configuration (`.env.example`)

```bash
# Database
DATABASE__URL=postgresql://user:password@localhost:5432/stock_market

# Tushare
TUSHARE_TOKEN=your_token_here

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Redis (optional)
REDIS__URL=redis://localhost:6379/0
```

### JSON Configuration (`config/production.json`)

```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 8
  },
  "logging": {
    "level": "WARNING",
    "format": "json"
  }
}
```

---

## 📊 Module Dependencies

```
┌─────────────────────────────────────────┐
│         Application Layer                │
│  api_server, portfolio_manager.commands │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│            Service Layer                 │
│  stock_market.services,                  │
│  portfolio_manager.services,             │
│  technical_analysis.services,            │
│  backtest                                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Repository Layer                │
│  stock_market.repositories,              │
│  portfolio_manager.repositories          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Data Source Layer               │
│  common.database (PostgreSQL),           │
│  data_sources (API Aggregator)           │
└─────────────────────────────────────────┘
```

**Dependency Rules**:
- ✅ Higher layers can depend on lower layers
- ❌ Lower layers CANNOT depend on higher layers
- ✅ Modules at same layer can depend on `common/`
- ❌ Cross-module dependencies should go through `common/` or interfaces

---

## 🧪 Test Structure

### Test Organization

```
tests/
├── conftest.py                    # Pytest fixtures
├── test_common/
│   ├── test_database.py
│   ├── test_config.py
│   └── test_exceptions.py
├── test_data_sources/
│   ├── test_aggregator.py
│   └── test_adapters/
│       ├── test_tushare_adapter.py
│       └── test_akshare_adapter.py
├── test_stock_market/
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
└── integration/
    ├── test_trading_flow.py
    └── test_analysis_flow.py
```

### Test File Template

```python
# tests/test_stock_market/test_services/test_stock_service.py

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from stock_market.services import StockService
from stock_market.repositories import StockRepository
from stock_market.models import Stock


class TestStockService:
    """Test StockService class"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def stock_service(self, mock_session):
        """Create StockService instance"""
        repository = StockRepository(mock_session)
        return StockService(repository)

    def test_get_stock(self, stock_service):
        """Test getting a stock by symbol"""
        # Test implementation
        pass

    def test_sync_all_stocks(self, stock_service):
        """Test syncing all stocks"""
        # Test implementation
        pass
```

---

## 📚 Next Steps

- 🛠️ [Development Setup](./05-development-setup.md) - Set up development environment
- 📏 [Coding Standards](./06-coding-standards.md) - Code style guidelines
- 🤝 [Contribution Guide](./08-contribution.md) - How to contribute
- 📦 [Module Guides](./04-module-guide/) - Module-specific guides

---

**Next Chapter**: [Development Setup →](./05-development-setup.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
