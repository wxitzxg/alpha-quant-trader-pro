# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alpha Quant Trader Pro is a quantitative trading platform built with Python/FastAPI. It provides stock market data management, portfolio tracking, backtesting, and simulated trading capabilities.

## Common Commands

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
```

### Code Quality
```bash
# Type checking
python -m mypy .

# Linting (if configured)
python -m ruff check .
```

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `api_server/` | FastAPI REST API endpoints, schemas, services |
| `common/` | Shared utilities: database (SQLAlchemy), config (YAML+env), repositories |
| `stock_market/` | Stock data models, sync services, repositories |
| `portfolio_manager/` | Position/transaction tracking, account management |
| `technical_analysis/` | Technical indicators (RSI, MACD, KDJ, etc.) |
| `backtest/` | Backtesting engine with strategy framework |
| `simulate_trading/` | Paper trading with strategy execution |
| `data_sources/` | Multi-source data adapters (Sina, Akshare, Tushare) |

### Key Patterns

**Database**: All models inherit from `common.database.Base`. Tables are auto-created at startup via `Base.metadata.create_all()` in `api_server/main.py`. Models must be imported before `create_all()` is called.

**Config**: Unified YAML + environment variable config via `common/config.py`. Priority: runtime params > env vars > .env > YAML > defaults. Access via `from common.config import get_config; config = get_config()`.

**Repository Pattern**: Database access via repositories in `{module}/repositories/`. Base class at `common/repositories/base.py`.

**Service Layer**: Business logic in `{module}/services/` or `{module}_service.py`.

**Error Handling**: Custom exceptions in `common/exceptions.py`. API error responses use a simple dict helper (not Pydantic model) to avoid datetime serialization issues with JSONResponse.

## File Naming Conventions

- Models: `{module}/models.py` or `{module}/models/__init__.py`
- Repositories: `{module}/repositories/__init__.py`
- Services: `{module}/services/__init__.py` or `{module}_service.py`
- Tests: `tests/{module}/test_{name}.py`

## Database Models Location

- `stock_market/models.py` - Stock, KLine, SyncRecord
- `portfolio_manager/database.py` - Position, Transaction, CashBalance
- `simulate_trading/models/` - StrategyAccount, StrategyTrade, DailyReport

All use `from common.database import Base`.
