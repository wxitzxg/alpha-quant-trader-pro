# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alpha Quant Trader Pro is a quantitative trading platform built with Python/FastAPI. It provides stock market data management, portfolio tracking, backtesting, and simulated trading capabilities for A-share markets.

## Common Commands

### Environment Setup
```bash
# Copy environment file
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/common/test_database.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run Docker-based integration tests
python tests/run_tests.py
```

### Start API Server
```bash
# Development mode
python -m uvicorn api_server.main:app --reload --host 0.0.0.0 --port 8000

# Or directly
python -m api_server.main

# Docker Compose (includes PostgreSQL + Redis)
docker-compose up -d
```

### Code Quality
```bash
# Type checking
python -m mypy .

# Linting
python -m ruff check .
```

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `api_server/` | FastAPI REST API endpoints, middleware, exception handlers |
| `common/` | Shared utilities: database (SQLAlchemy), config (YAML+env), repositories, DI container |
| `stock_market/` | Stock data models, sync services, K-line repositories |
| `portfolio_manager/` | Position/transaction tracking, account management |
| `technical_analysis/` | Technical indicators (RSI, MACD, KDJ, Bollinger, etc.) |
| `backtest/` | Backtesting engine with strategy framework |
| `simulate_trading/` | Paper trading with strategy execution |
| `data_sources/` | Multi-source data adapters (Sina, Akshare, Tushare) with priority-based fallback |

### Key Patterns

**Configuration**: Unified YAML + environment variable config in `common/config.py`. Priority: runtime params > env vars > .env > YAML > defaults. Environment variables use `__` delimiter for nested config (e.g., `DATABASE__URL`).

```python
from common.config import get_config
config = get_config()
db_url = config.database.url
```

**Database**: All models inherit from `common.database.Base`. Tables are auto-created at startup via `Base.metadata.create_all()` in `api_server/main.py`. **Models must be imported before `create_all()` is called.**

**Repository Pattern**: Database access via repositories in `{module}/repositories/`. Base class at `common/repositories/base.py`.

**Service Layer**: Business logic in `{module}/services/` or `{module}_service.py`.

**Dependency Injection**: Container-based DI via `common/di_container.py` using `dependency-injector` library.

**Error Handling**: Custom exceptions in `common/exceptions.py`. API error responses use dict format (not Pydantic model) to avoid datetime serialization issues.

## Module Details

### data_sources/
Multi-source data fetching with priority-based fallback:
- Adapters for Sina (realtime), Akshare, Tushare
- `aggregator.py` orchestrates fallback logic
- Configured via `config/data_sources.yaml` with priority values

### stock_market/
- `models.py`: Stock, KLine, SyncRecord
- `sync/`: Background sync managers for stock list, K-line data
- `managers/`: High-level business operations

### portfolio_manager/
- `database.py`: Position, Transaction, CashBalance models
- `commands/`: CLI-style command handlers

### simulate_trading/
- `models/`: StrategyAccount, StrategyTrade, DailyReport
- Paper trading simulation with configurable strategies

## Configuration Files

All YAML files in `config/` are automatically loaded and merged:
- `database.yaml` - PostgreSQL connection settings
- `data_sources.yaml` - Data source priorities and timeouts
- `stock_market.yaml` - Sync settings, trading hours
- `backtest.yaml` - Backtest parameters
- `simulation.yaml` - Paper trading configuration

Sensitive values (database URL, API keys) should use environment variables:
```bash
DATABASE__URL=postgresql://user:pass@host:port/db
API_SERVER__API_KEY_SECRET=your-secret-key
```

## Database Models Location

| Module | File | Models |
|--------|------|--------|
| `stock_market/` | `models.py` | Stock, KLine, SyncRecord |
| `portfolio_manager/` | `database.py` | Position, Transaction, CashBalance |
| `simulate_trading/` | `models/` | StrategyAccount, StrategyTrade, DailyReport |

All use `from common.database import Base`.

## File Naming Conventions

- Models: `{module}/models.py` or `{module}/models/__init__.py`
- Repositories: `{module}/repositories/__init__.py`
- Services: `{module}/services/__init__.py` or `{module}_service.py`
- Tests: `tests/{module}/test_{name}.py`

## Testing Structure

```
tests/
├── conftest.py              # Shared fixtures
├── common/                  # Common module tests
├── stock_market/            # Stock market tests
├── portfolio_manager/       # Portfolio tests
├── api_server/              # API integration tests
└── run_tests.py             # Docker-based test runner
```

Tests use pytest with in-memory SQLite for unit tests. Integration tests use Docker Compose with PostgreSQL.
