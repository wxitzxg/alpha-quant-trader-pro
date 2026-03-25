# 👨‍💻 Developer Guide

> Development and contribution guide for developers

---

## 📚 Table of Contents

### Architecture & Design
1. [System Architecture](./01-architecture.md) - Complete architecture overview
2. [Project Structure](./02-project-structure.md) - Code organization
3. [API Reference](./03-api-reference.md) - API documentation

### Module Development
4. [Module Guides](./04-module-guide/)
   - [Data Sources Module](./04-module-guide/01-data-sources.md)
   - [Stock Market Module](./04-module-guide/02-stock-market.md)
   - [Portfolio Manager Module](./04-module-guide/03-portfolio-manager.md)
   - [Technical Analysis Module](./04-module-guide/04-technical-analysis.md)
   - [Backtest Module](./04-module-guide/05-backtest.md)

### Development Setup
5. [Development Environment](./05-development-setup.md) - Setup guide
6. [Coding Standards](./06-coding-standards.md) - Code style guide
7. [Testing Guide](./07-testing.md) - Testing practices
8. [Contribution Guide](./08-contribution.md) - How to contribute
9. [Debugging Guide](./09-debugging.md) - Debugging techniques

---

## 🚀 Getting Started for Developers

**Quick start for new contributors**:
1. → [System Architecture](./01-architecture.md) - Understand the system
2. → [Development Environment](./05-development-setup.md) - Set up your environment
3. → [Project Structure](./02-project-structure.md) - Navigate the codebase
4. → [Contribution Guide](./08-contribution.md) - Learn how to contribute

---

## 🎯 Choose by Your Task

- **Understand the system**: [System Architecture](./01-architecture.md)
- **Start development**: [Development Environment](./05-development-setup.md)
- **Work on a module**: [Module Guides](./04-module-guide/)
- **Write tests**: [Testing Guide](./07-testing.md)
- **Contribute code**: [Contribution Guide](./08-contribution.md)
- **Debug issues**: [Debugging Guide](./09-debugging.md)

---

## 🏗️ System Architecture Highlights

### Layered Architecture
```
┌─────────────────────────────────────────┐
│         Application Layer                │
│  - Commands (PortfolioCommands)          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  - StockService, KLineService            │
│  - PositionService, TransactionService   │
│  - AccountService, AnalysisService       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Repository Layer                 │
│  - StockRepository, KLineRepository      │
│  - PositionRepository, TransactionRepo   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Data Source Layer                │
│  - DatabaseManager (PostgreSQL)          │
│  - DataSourceAggregator (API)            │
└─────────────────────────────────────────┘
```

### Core Modules

#### 1. Data Sources Module (`data_sources/`)
- Unified data access layer
- Multiple data source support (Tushare, AKShare, Sina Finance)
- Adapter pattern for easy extension

#### 2. Stock Market Module (`stock_market/`)
- Stock information management
- KLine data management
- Incremental sync strategy
- Concurrent sync support

#### 3. Portfolio Manager Module (`portfolio_manager/`)
- Position management
- Transaction management
- Account management
- Fee calculation

#### 4. Technical Analysis Module (`technical_analysis/`)
- Five-dimensional resonance scoring
- Three strategies (VCP, Nine-Turn, Divergence)
- Complete technical indicators
- Analysis engine

#### 5. Backtest Module (`backtest/`)
- Historical data backtesting
- Performance metrics calculation
- Report generation
- Trade analysis

---

## 🛠️ Development Tools

### Required
- Python 3.8+
- PostgreSQL 12+
- pip or poetry

### Recommended
- IDE: VS Code, PyCharm
- Linter: flake8, pylint
- Formatter: black, isort
- Testing: pytest, pytest-cov
- Type Checking: mypy

---

## 📦 Module Structure Pattern

Each module follows this pattern:
```
module_name/
├── __init__.py
├── repositories/           # Repository layer
│   ├── __init__.py
│   └── *.py
├── services/               # Service layer
│   ├── __init__.py
│   └── *.py
├── models.py              # Data models
├── exceptions.py          # Module-specific exceptions
└── utils/                 # Utility functions
```

---

## 🧪 Testing Standards

### Test Coverage
- **Target**: 80%+ code coverage
- **Unit Tests**: Individual functions and classes
- **Integration Tests**: Module interactions
- **E2E Tests**: Critical user flows

### Test File Naming
- Unit tests: `test_<module>.py`
- Integration tests: `test_integration.py`
- E2E tests: `test_e2e.py`

---

## 🔧 Development Workflow

### 1. Setup
```bash
# Clone repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start API server (tables auto-created on startup)
python -m api_server.main
```

### 2. Development
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=module_name

# Format code
black .
isort .

# Lint code
flake8 .
```

### 3. Contribution
1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Run all tests locally
5. Create a pull request
6. Address review feedback

---

## 📊 Code Quality Metrics

### File Size
- **Target**: 200-400 lines per file
- **Maximum**: 800 lines
- **Action**: Split files exceeding limit

### Function Size
- **Target**: < 50 lines per function
- **Maximum**: 100 lines
- **Action**: Extract helper functions

### Nesting Depth
- **Maximum**: 4 levels
- **Action**: Refactor deeply nested code

### Complexity
- **Cyclomatic Complexity**: < 10 per function
- **Maintainability Index**: > 75

---

## 🎓 Learning Resources

### System Documentation
- 📐 [Design Documents](../project-docs/design-archive/) - Original design specs
- 🏗️ [Architecture Guide](./01-architecture.md) - Detailed architecture

### External Resources
- SQLAlchemy Documentation
- FastAPI Documentation
- Python Best Practices

---

## 🤝 Community & Support

### How to Get Help
1. Check the [FAQ](../user-guide/09-faq.md)
2. Read the relevant module guide
3. Check existing issues
4. Ask in the community chat
5. Create a GitHub issue

### Contribution Types
- **Bug Fixes**: Fix existing issues
- **Features**: Add new functionality
- **Documentation**: Improve docs
- **Testing**: Add tests
- **Performance**: Optimize code

---

**Next Chapter**: [System Architecture →](./01-architecture.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
**Audience**: Developers, Contributors, Code Reviewers
