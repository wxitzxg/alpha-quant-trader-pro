# 🔧 Development Setup

> Complete guide for setting up your development environment for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Project Setup](#project-setup)
4. [Development Tools](#development-tools)
5. [Running the Application](#running-the-application)
6. [Development Workflow](#development-workflow)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Required Software

| Software | Version | Description |
|----------|---------|-------------|
| **Python** | 3.8+ | Programming language runtime |
| **Git** | 2.30+ | Version control system |
| **PostgreSQL** | 14+ | Primary database |
| **Redis** | 7.0+ | Cache (optional) |
| **Docker** | 20.10+ | Containerization (optional) |
| **Docker Compose** | 2.0+ | Container orchestration (optional) |

### Recommended Software

| Software | Description |
|----------|-------------|
| **PyCharm / VSCode** | Python IDE |
| **pgAdmin** | PostgreSQL admin tool |
| **RedisInsight** | Redis admin tool |
| **Postman** | API testing tool |
| **Docker Desktop** | Docker UI |

---

## 🌍 Environment Setup

### 1. Python Installation

**Ubuntu/Debian:**
```bash
# Install Python 3.8+
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Verify installation
python3.10 --version
# Python 3.10.12
```

**macOS:**
```bash
# Install via Homebrew
brew install python@3.10

# Verify installation
python3.10 --version
```

**Windows:**
1. Download Python 3.10+ from https://www.python.org/downloads/
2. Run installer (check "Add Python to PATH")
3. Verify: `python --version`

### 2. PostgreSQL Installation

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres psql
CREATE USER alphaquant WITH PASSWORD 'alphaquant';
CREATE DATABASE stock_market OWNER alphaquant;
GRANT ALL PRIVILEGES ON DATABASE stock_market TO alphaquant;
\q

# Test connection
psql -U alphaquant -d stock_market -h localhost
```

**macOS:**
```bash
# Install via Homebrew
brew install postgresql@14

# Start service
brew services start postgresql@14

# Create user and database
createuser -P alphaquant
createdb -O alphaquant stock_market
```

**Windows:**
1. Download PostgreSQL 14+ from https://www.postgresql.org/download/windows/
2. Run installer
3. During installation:
   - Set password: `alphaquant`
   - Create database: `stock_market`
   - Create user: `alphaquant`

### 3. Redis Installation (Optional)

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping
# PONG
```

**macOS:**
```bash
brew install redis
brew services start redis
```

---

## 📦 Project Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/alpha-quant-trader-pro.git
cd alpha-quant-trader-pro

# Create development branch
git checkout -b feature/your-feature-name
```

### 2. Create Python Virtual Environment

**Using venv (Recommended):**
```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation
which python  # Should show venv/bin/python
```

**Using conda:**
```bash
# Create conda environment
conda create -n alphaquant python=3.10
conda activate alphaquant
```

**Using poetry:**
```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
poetry shell
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Verify installation
python -c "import fastapi; import sqlalchemy; print('Dependencies installed successfully')"
```

### 4. Configure Environment Variables

**Create `.env` file:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Minimal required configuration:**
```bash
# Database
DATABASE__URL=postgresql://alphaquant:alphaquant@localhost:5432/stock_market

# Tushare
TUSHARE_TOKEN=your_token_here

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your_generated_secret_key_here

# Redis (optional)
REDIS__URL=redis://localhost:6379/0
REDIS_ENABLED=false
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Example output: a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890
```

### 5. Database Migration

```bash
# Initialize database (if first time)
alembic upgrade head

# Or create tables directly
python -c "from common.database import DatabaseManager; db = DatabaseManager(); db.create_all()"

# Verify database tables
psql -U alphaquant -d stock_market -c "\dt"
```

### 6. Load Initial Data (Optional)

```bash
# Sync stock list
python scripts/sync_stocks.py

# Sync historical K-line data (small subset for testing)
python scripts/sync_klines.py --start_date 2023-01-01 --end_date 2023-12-31 --limit 10
```

---

## 🛠️ Development Tools

### IDE Setup

#### VSCode Configuration

**Install Extensions:**
```bash
# Python extension
code --install-extension ms-python.python

# Pylance (type checking)
code --install-extension ms-python.vscode-pylance

# Black (code formatter)
code --install-extension ms-python.black-formatter

# isort (import sorting)
code --install-extension ms-python.isort

# pytest (testing)
code --install-extension ms-python.vscode-pytest
```

**Create `.vscode/settings.json`:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true
  }
}
```

#### PyCharm Configuration

1. **Open Project:**
   - File → Open → Select project directory
   - Choose "This Window"

2. **Configure Python Interpreter:**
   - File → Settings → Project → Python Interpreter
   - Click gear icon → Add
   - Select "Existing environment"
   - Browse to `venv/bin/python`

3. **Configure Code Style:**
   - File → Settings → Editor → Code Style → Python
   - Set scheme to "Black"
   - Import sorting: use `isort`

4. **Configure Run/Debug:**
   - Run → Edit Configurations
   - Click "+" → Python
   - Name: "API Server"
   - Script path: `api_server/main.py`
   - Working directory: Project root

### Pre-commit Hooks

**Install pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

**Create `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=120"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ["--no-strict-optional", "--ignore-missing-imports"]
        additional_dependencies:
          - sqlalchemy-stubs
          - types-requests
```

**Run pre-commit manually:**
```bash
pre-commit run --all-files
```

---

## ▶️ Running the Application

### Development Mode

**Using uvicorn directly:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Run with auto-reload
uvicorn api_server.main:app --reload --host 0.0.0.0 --port 8000

# With custom settings
uvicorn api_server.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --reload-dir api_server \
  --reload-dir common \
  --log-level debug
```

**Using gunicorn (production-like):**
```bash
gunicorn api_server.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**Using poetry:**
```bash
poetry run uvicorn api_server.main:app --reload
```

### Docker Development

**Create `docker-compose.dev.yml`:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    container_name: alphaquant-db
    environment:
      POSTGRES_USER: alphaquant
      POSTGRES_PASSWORD: alphaquant
      POSTGRES_DB: stock_market
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alphaquant"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: alphaquant-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: alphaquant-app
    environment:
      DATABASE__URL: postgresql://alphaquant:alphaquant@db:5432/stock_market
      TUSHARE_TOKEN: ${TUSHARE_TOKEN}
      ENVIRONMENT: development
      DEBUG: "true"
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./venv:/app/venv
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn api_server.main:app --reload --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
```

**Run with Docker:**
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Clean up
docker-compose -f docker-compose.dev.yml down -v
```

### Hot Reload Configuration

**For faster development:**
```bash
# Only reload specific directories
uvicorn api_server.main:app \
  --reload \
  --reload-dir api_server \
  --reload-dir common \
  --reload-dir stock_market \
  --reload-dir portfolio_manager \
  --reload-dir technical_analysis
```

---

## 🔁 Development Workflow

### 1. Feature Development

**Typical workflow:**
```bash
# 1. Create feature branch
git checkout -b feature/user-profile-api

# 2. Implement feature (TDD approach)
# - Write tests first
# - Implement code
# - Run tests
# - Refactor

# 3. Run linters and formatters
black .
isort .
flake8 .
mypy .

# 4. Run tests
pytest tests/ -v --cov=.

# 5. Commit changes
git add .
git commit -m "feat: add user profile API endpoint"

# 6. Push to remote
git push origin feature/user-profile-api
```

### 2. Testing Workflow

**Run specific tests:**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_stock_market/test_services/test_stock_service.py -v

# Run specific test class
pytest tests/test_stock_market/test_services/test_stock_service.py::TestStockService -v

# Run specific test method
pytest tests/test_stock_market/test_services/test_stock_service.py::TestStockService::test_get_stock -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run with verbose output
pytest tests/ -v -s

# Run failed tests only
pytest --lf
```

### 3. Debugging

**Using pdb:**
```python
# In your code
import pdb; pdb.set_trace()

# Or using breakpoint() (Python 3.7+)
breakpoint()
```

**Using VSCode debugger:**
1. Set breakpoints in code
2. Run → Start Debugging (F5)
3. Use debug console to inspect variables

**Logging for debugging:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
```

### 4. API Testing

**Using curl:**
```bash
# Health check
curl http://localhost:8000/health

# Get stocks
curl http://localhost:8000/api/v1/stocks

# Analyze stock
curl http://localhost:8000/api/v1/analysis/600519 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Using httpie:**
```bash
# Install httpie
pip install httpie

# Health check
http GET http://localhost:8000/health

# Get stocks
http GET http://localhost:8000/api/v1/stocks

# Create position
http POST http://localhost:8000/api/v1/portfolio/positions \
  symbol="600519" \
  quantity=100 \
  price=1800 \
  Authorization:"Bearer YOUR_TOKEN"
```

**Using Postman:**
1. Import OpenAPI schema: `http://localhost:8000/docs`
2. Create collection from schema
3. Test endpoints interactively

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Database Connection Error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check database exists
psql -U postgres -c "\l"

# Check connection string in .env
grep DATABASE__URL .env

# Test connection manually
psql -U alphaquant -d stock_market -h localhost
```

#### Issue 2: Module Import Error

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
```bash
# Check virtual environment is activated
which python

# If not activated, activate it
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check installed packages
pip list | grep fastapi
```

#### Issue 3: Port Already in Use

**Symptoms:**
```
OSError: [Errno 98] Address already in use
```

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn api_server.main:app --reload --port 8001
```

#### Issue 4: Alembic Migration Error

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxx'
```

**Solutions:**
```bash
# Check current revision
alembic current

# Upgrade to latest
alembic upgrade head

# Downgrade and upgrade again
alembic downgrade -1
alembic upgrade head

# Reset database (WARNING: deletes all data)
dropdb stock_market
createdb -O alphaquant stock_market
alembic upgrade head
```

#### Issue 5: Tushare API Error

**Symptoms:**
```
DataUnavailableError: Tushare API request failed
```

**Solutions:**
```bash
# Check Tushare token is set
grep TUSHARE_TOKEN .env

# Verify token is valid
python -c "import tushare as ts; ts.set_token('YOUR_TOKEN'); print(ts.get_token())"

# Check Tushare account status
# Visit: https://tushare.pro/user/token
```

### Debug Checklist

When encountering issues:

```bash
# 1. Check environment variables
cat .env | grep -E "(DATABASE|TUSHARE|REDIS)"

# 2. Check Python version
python --version

# 3. Check virtual environment
which python
pip list | head -20

# 4. Check database connection
psql -U alphaquant -d stock_market -c "SELECT 1;"

# 5. Check Redis connection
redis-cli ping

# 6. Check application logs
tail -f logs/app.log

# 7. Run health check
curl http://localhost:8000/health
```

---

## 📚 Next Steps

- 📏 [Coding Standards](./06-coding-standards.md) - Code style guidelines
- 🧪 [Testing Guide](./07-testing.md) - Testing best practices
- 🤝 [Contribution Guide](./08-contribution.md) - How to contribute
- 🐛 [Debugging Guide](./09-debugging.md) - Debugging techniques

---

**Next Chapter**: [Coding Standards →](./06-coding-standards.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
