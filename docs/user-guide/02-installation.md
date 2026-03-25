# 🔧 Installation Guide

> Complete installation guide for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Quick Installation](#quick-installation)
4. [Docker Installation](#docker-installation)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows (WSL recommended)
- **Python**: 3.8 or higher
- **Database**: PostgreSQL 12 or higher
- **Memory**: 4 GB RAM
- **Storage**: 10 GB available disk space
- **Network**: Internet connection (for data sources)

### Recommended Requirements
- **Operating System**: Ubuntu 20.04+ or macOS 12+
- **Python**: 3.10 or higher
- **Database**: PostgreSQL 14+ with 8 GB RAM
- **Memory**: 8 GB RAM or more
- **Storage**: 50 GB SSD
- **CPU**: 4 cores or more

---

## 📦 Installation Methods

### Method 1: Quick Installation (Recommended for Beginners)

**Best for**: Local development, learning, testing

See [Quick Installation](#quick-installation) section below.

### Method 2: Docker Installation

**Best for**: Production deployment, isolated environments

See [Docker Installation](#docker-installation) section below.

### Method 3: Manual Installation

**Best for**: Custom configurations, advanced users

Follow the Quick Installation steps and customize as needed.

---

## 🚀 Quick Installation

### Step 1: Install Prerequisites

#### On Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Git
sudo apt install git
```

#### On macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Install PostgreSQL
brew install postgresql@14

# Install Git
brew install git
```

#### On Windows (WSL)
```bash
# Use Ubuntu WSL and follow Ubuntu instructions above
```

---

### Step 2: Install PostgreSQL

#### Start PostgreSQL Service
```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql@14
```

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE stock_market;

# Create user
CREATE USER stock_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE stock_market TO stock_user;

# Exit
\q
```

---

### Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/alpha-quant-trader-pro.git
cd alpha-quant-trader-pro

# Checkout the latest release
git checkout v2.0.0
```

---

### Step 4: Set Up Python Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

---

### Step 5: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

**Required Packages**:
- fastapi - Web framework
- sqlalchemy - ORM
- psycopg2-binary - PostgreSQL driver
- pandas - Data analysis
- numpy - Numerical computing
- tushare - Chinese stock data
- akshare - Alternative data source

---

### Step 6: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Required Configuration in `.env`**:
```bash
# Database Configuration
DATABASE__URL=postgresql://stock_user:your_secure_password@localhost:5432/stock_market

# Tushare Configuration (Get token from https://tushare.pro/)
TUSHARE_TOKEN=your_tushare_token_here

# Application Configuration
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO

# Optional: Redis Configuration (for caching)
REDIS__URL=redis://localhost:6379/0
```

**Getting Tushare Token**:
1. Visit [Tushare Pro](https://tushare.pro/)
2. Register and login
3. Go to "我的账户" → "接口TOKEN"
4. Copy your token and paste in `.env`

---

### Step 7: Initialize Database

```bash
# Start the API server - tables are auto-created on startup
python -m api_server.main
# You should see: "数据库表同步完成"
```

This will:
- Create all necessary tables
- Initialize system data

---

### Step 8: Verify Installation

```bash
# Run quick test
python -c "from portfolio_manager import PortfolioCommands; print('✅ Installation successful!')"

# Test database connection
python -c "from common.database import DatabaseManager; db = DatabaseManager('postgresql://stock_user:your_secure_password@localhost:5432/stock_market'); print('✅ Database connected!')"
```

---

## 🐳 Docker Installation

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/alpha-quant-trader-pro.git
cd alpha-quant-trader-pro
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env as described in Quick Installation
```

### Step 3: Start Services

```bash
# Start all services (database, application, redis)
docker-compose up -d
```

This will:
- Start PostgreSQL container
- Start Redis container (optional)
- Initialize the database
- Run migrations automatically

### Step 4: Verify Docker Installation

```bash
# Check running containers
docker-compose ps

# Expected output:
# alpha-quant-trader-pro-db-1      ...  Up
# alpha-quant-trader-pro-redis-1   ...  Up (optional)
```

### Step 5: Access the System

The application will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE__URL` | ✅ Yes | - | PostgreSQL connection string |
| `TUSHARE_TOKEN` | ✅ Yes | - | Tushare API token |
| `ENVIRONMENT` | No | development | Environment (development/production) |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `REDIS__URL` | No | - | Redis connection (optional) |
| `DATA_SOURCE` | No | tushare | Primary data source (tushare/akshare/sina) |

### Configuration Files

The system also supports JSON configuration files:

```bash
config/
├── default.json      # Default configuration
├── development.json  # Development overrides
└── production.json   # Production overrides
```

---

## ✅ Verification

### 1. Check Installation

```bash
# Check Python version
python --version  # Should be 3.8+

# Check installed packages
pip list | grep -E "fastapi|sqlalchemy|pandas"
```

### 2. Test Database

```bash
# Connect to database
psql -U stock_user -d stock_market

# Check tables
\dt
# Should see tables like: stocks, klines, positions, transactions

# Exit
\q
```

### 3. Run Test Script

Create `test_installation.py`:
```python
from portfolio_manager import PortfolioCommands
from common.database import DatabaseManager

print("Testing installation...")

# Test 1: Database connection
print("1. Testing database connection...")
db = DatabaseManager("postgresql://stock_user:your_password@localhost:5432/stock_market")
print("   ✅ Database connected!")

# Test 2: Portfolio manager
print("2. Testing portfolio manager...")
portfolio = PortfolioCommands()
portfolio.add_cash(10000)
print("   ✅ Portfolio initialized!")

# Test 3: Technical analysis
print("3. Testing technical analysis...")
from technical_analysis.services import AnalysisService
analysis = AnalysisService(db.get_session())
print("   ✅ Analysis service ready!")

print("\n✅✅✅ All tests passed! Installation successful!")
```

Run it:
```bash
python test_installation.py
```

---

## 🔍 Troubleshooting

### Issue: Database Connection Failed

**Symptoms**: `OperationalError: could not connect to server`

**Solutions**:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify connection string in `.env`
3. Check database exists: `psql -U postgres -l`
4. Verify user has access: `psql -U stock_user -d stock_market`

---

### Issue: Tushare API Error

**Symptoms**: `Token authentication failed` or `HTTP 403`

**Solutions**:
1. Verify token is correct in `.env`
2. Check token has not expired
3. Register at [Tushare Pro](https://tushare.pro/) if you don't have a token
4. Upgrade account if hitting rate limits

---

### Issue: Python Package Installation Failed

**Symptoms**: `ERROR: Failed building wheel` or dependency conflicts

**Solutions**:
1. Upgrade pip: `pip install --upgrade pip`
2. Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev build-essential

   # macOS
   xcode-select --install
   ```
3. Try installing problematic packages individually
4. Use a clean virtual environment

---

### Issue: Database Initialization Failed

**Symptoms**: Tables not created on startup

**Solutions**:
1. Drop and recreate database:
   ```bash
   psql -U postgres
   DROP DATABASE stock_market;
   CREATE DATABASE stock_market;
   GRANT ALL PRIVILEGES ON DATABASE stock_market TO stock_user;
   \q
   # Restart API server to recreate tables
   python -m api_server.main
   ```
2. Check database user has correct permissions
3. Review error logs for specific issues

---

### Issue: Port Already in Use

**Symptoms**: `Address already in use` when starting services

**Solutions**:
1. Check what's using the port: `lsof -i :5432` (or `netstat -tuln | grep 5432`)
2. Stop conflicting service or change port in configuration
3. For Docker: `docker-compose down` before `docker-compose up`

---

## 📚 Next Steps

After successful installation:

1. 📘 [Your First Trade](./03-first-trade.md) - Execute your first trade
2. 📗 [Trading System Guide](./04-trading-guide.md) - Learn trading features
3. 📙 [Technical Analysis Guide](./05-analysis-guide.md) - Understand analysis tools

---

## 🆘 Getting Help

- 📖 [FAQ](./09-faq.md) - Common questions
- 🔧 [Troubleshooting Guide](../admin-guide/09-troubleshooting.md) - Detailed troubleshooting
- 📧 Email: support@alphaquant.com
- 💬 Community: Join our Discord/Telegram group

---

**Next Chapter**: [Your First Trade →](./03-first-trade.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
