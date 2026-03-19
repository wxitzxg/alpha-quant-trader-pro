# 🚀 Production Deployment

> Complete guide for deploying Alpha Quant Trader Pro to production environment

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Requirements](#environment-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Data Source Configuration](#data-source-configuration)
7. [Service Deployment](#service-deployment)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Monitoring Setup](#monitoring-setup)

---

## ✅ Pre-Deployment Checklist

### System Requirements

**Hardware**:
- [ ] **CPU**: 4+ cores (recommended 8+)
- [ ] **RAM**: 8 GB minimum (recommended 16 GB)
- [ ] **Storage**: 100 GB SSD (recommended 500 GB)
- [ ] **Network**: 100 Mbps+ connection

**Software**:
- [ ] **OS**: Ubuntu 20.04+ or CentOS 8+
- [ ] **Python**: 3.10 or higher
- [ ] **PostgreSQL**: 14+ (recommended 15+)
- [ ] **Redis**: 6.0+ (optional, recommended for production)
- [ ] **Docker**: 20.10+ (if using container deployment)

### Dependencies

**System Packages**:
```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql-14 \
    postgresql-contrib-14 \
    redis-server \
    nginx \
    supervisor \
    git \
    build-essential \
    libpq-dev \
    libssl-dev
```

**Python Packages**:
- All dependencies listed in `requirements.txt`
- Additional production packages:
  - `gunicorn` - WSGI server
  - `uvicorn` - ASGI server (for FastAPI)
  - `psycopg2-binary` - PostgreSQL adapter
  - `redis` - Redis client

---

## 🌐 Environment Requirements

### Supported Operating Systems

| OS | Version | Status | Notes |
|----|---------|--------|-------|
| Ubuntu | 20.04+ | ✅ Recommended | Best support |
| Ubuntu | 22.04+ | ✅ Recommended | Latest LTS |
| CentOS | 8+ | ✅ Supported | Enterprise ready |
| Debian | 11+ | ✅ Supported | Stable |
| macOS | 12+ | ⚠️ Development only | Not for production |
| Windows | 10+ | ⚠️ Development only | Use WSL for production |

### Python Version Matrix

| Python | Status | Recommendation |
|--------|--------|----------------|
| 3.8 | ✅ Supported | Minimum version |
| 3.9 | ✅ Supported | Good choice |
| 3.10 | ✅ Recommended | Optimal |
| 3.11 | ✅ Supported | Latest stable |
| 3.12+ | ⚠️ Testing | May have compatibility issues |

### Database Requirements

**PostgreSQL**:
- **Minimum**: 12.x
- **Recommended**: 14.x or 15.x
- **Storage Engine**: Default (no special requirements)
- **Extensions**: `pg_trgm`, `uuid-ossp`

**Redis** (Optional but Recommended):
- **Minimum**: 6.0
- **Recommended**: 7.0+
- **Use Case**: Caching, session storage, task queues

---

## 📦 Installation Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/alpha-quant-trader-pro.git /opt/alpha-quant

# Navigate to project directory
cd /opt/alpha-quant

# Checkout production branch
git checkout main  # or specific release tag
```

### Step 2: Create System User

```bash
# Create dedicated system user
sudo useradd -r -m -s /bin/bash alphaquant

# Set ownership
sudo chown -R alphaquant:alphaquant /opt/alpha-quant

# Switch to user
sudo su - alphaquant
```

### Step 3: Set Up Python Environment

```bash
# Navigate to project
cd /opt/alpha-quant

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn uvicorn
```

### Step 4: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env.production

# Edit production environment file
nano .env.production
```

**Required Configuration**:
```bash
# Database
DATABASE_URL=postgresql://alphaquant:secure_password@localhost:5432/stock_market

# Tushare
TUSHARE_TOKEN=your_production_token_here

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_very_secure_random_string_here
```

**Generate Secure Secret Key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## ⚙️ Configuration

### Production Configuration File

Create `config/production.json`:

```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": false,
    "echo_pool": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,
    "timeout": 120,
    "keepalive": 5,
    "log_level": "info",
    "access_log": true
  },
  "data_sources": {
    "primary": "tushare",
    "fallback": ["akshare"],
    "cache_enabled": true,
    "cache_ttl": 3600
  },
  "security": {
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst": 10
    },
    "cors": {
      "enabled": true,
      "origins": ["https://yourdomain.com"],
      "credentials": true
    }
  }
}
```

### Environment Variables Priority

The system uses the following priority (highest to lowest):
1. **Environment Variables** (e.g., `DATABASE_URL`)
2. **Configuration File** (e.g., `config/production.json`)
3. **Default Values** (hardcoded defaults)

---

## 💾 Database Setup

### Step 1: Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql-14 postgresql-contrib-14

# CentOS/RHEL
sudo dnf install postgresql14-server postgresql14-contrib

# Initialize database (CentOS only)
sudo /usr/pgsql-14/bin/postgresql-14-setup initdb
```

### Step 2: Configure PostgreSQL

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Connection settings
listen_addresses = '*'
max_connections = 200

# Memory settings
shared_buffers = 4GB
work_mem = 16MB
maintenance_work_mem = 1GB

# WAL settings
wal_level = replica
max_wal_size = 2GB
min_wal_size = 1GB

# Query planning
random_page_cost = 1.1
effective_cache_size = 12GB

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'none'
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```conf
# IPv4 local connections
host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               md5

# IPv6 local connections
host    all             all             ::1/128                 md5
```

### Step 3: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database
CREATE DATABASE stock_market
    WITH OWNER = alphaquant
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create user
CREATE USER alphaquant WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE stock_market TO alphaquant;

-- Exit
\q
```

### Step 4: Run Database Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### Step 5: Configure Database Backup

Create `/etc/cron.d/alphaquant-db-backup`:

```bash
# Daily database backup at 2 AM
0 2 * * * postgres pg_dump -U alphaquant stock_market | gzip > /backup/stock_market_$(date +\%Y\%m\%d).sql.gz

# Keep only last 7 days of backups
0 3 * * * root find /backup -name "stock_market_*.sql.gz" -mtime +7 -delete
```

---

## 📡 Data Source Configuration

### Tushare Configuration

**Register and Get Token**:
1. Visit [Tushare Pro](https://tushare.pro/)
2. Register account
3. Upgrade to appropriate tier
4. Get API token

**Configure in `.env.production`**:
```bash
TUSHARE_TOKEN=your_production_token
TUSHARE_TIMEOUT=30
TUSHARE_RETRY_TIMES=3
TUSHARE_RETRY_DELAY=5
```

**Tushare Tier Recommendations**:

| Tier | Cost | API Calls/Minute | Suitable For |
|------|------|------------------|--------------|
| Free | ¥0 | 20 | Development only |
| Basic | ¥500/yr | 120 | Small production |
| Pro | ¥1500/yr | 240 | Medium production |
| VIP | ¥3000/yr | 480 | Large production |

### AKShare Configuration (Fallback)

```bash
# Enable AKShare as fallback
DATA_SOURCE_FALLBACK=akshare
AKSHARE_TIMEOUT=30
```

### Data Update Schedule

Create `/etc/cron.d/alphaquant-data-sync`:

```bash
# Sync stock list daily at 6 PM
0 18 * * * alphaquant cd /opt/alpha-quant && source venv/bin/activate && python scripts/sync_stocks.py

# Sync daily K-line data after market close (6 PM)
0 18 * * 1-5 alphaquant cd /opt/alpha-quant && source venv/bin/activate && python scripts/sync_klines.py --interval 1d

# Sync weekly K-line data on Friday after market close
0 19 * * 5 alphaquant cd /opt/alpha-quant && source venv/bin/activate && python scripts/sync_klines.py --interval 1w

# Sync monthly K-line data on last trading day of month
0 19 28-31 * * alphaquant cd /opt/alpha-quant && source venv/bin/activate && [ "$(date +\%d -d tomorrow)" = "01" ] && python scripts/sync_klines.py --interval 1M
```

---

## 🚀 Service Deployment

### Option 1: Using Gunicorn (Recommended)

Create `/etc/systemd/system/alphaquant.service`:

```ini
[Unit]
Description=Alpha Quant Trader Pro
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=alphaquant
Group=alphaquant
WorkingDirectory=/opt/alpha-quant
Environment="PATH=/opt/alpha-quant/venv/bin"
Environment="DATABASE_URL=postgresql://alphaquant:password@localhost:5432/stock_market"
Environment="ENVIRONMENT=production"

ExecStart=/opt/alpha-quant/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/alphaquant/access.log \
    --error-logfile /var/log/alphaquant/error.log \
    --log-level info \
    api_server.main:app

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Create Log Directory**:
```bash
sudo mkdir -p /var/log/alphaquant
sudo chown alphaquant:alphaquant /var/log/alphaquant
```

**Enable and Start Service**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable alphaquant

# Start service
sudo systemctl start alphaquant

# Check status
sudo systemctl status alphaquant

# View logs
sudo journalctl -u alphaquant -f
```

### Option 2: Using Docker

Create `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: alphaquant-app
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://alphaquant:${DB_PASSWORD}@db:5432/stock_market
      - TUSHARE_TOKEN=${TUSHARE_TOKEN}
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - alphaquant-network

  db:
    image: postgres:14-alpine
    container_name: alphaquant-db
    restart: always
    environment:
      - POSTGRES_USER=alphaquant
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=stock_market
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    networks:
      - alphaquant-network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: alphaquant-redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - alphaquant-network
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    container_name: alphaquant-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - alphaquant-network

volumes:
  postgres_data:
  redis_data:

networks:
  alphaquant-network:
    driver: bridge
```

**Deploy with Docker**:
```bash
# Create .env file for docker-compose
cat > .env << EOF
DB_PASSWORD=your_secure_password
TUSHARE_TOKEN=your_token_here
EOF

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

---

## ✅ Post-Deployment Verification

### 1. Service Health Check

```bash
# Check if service is running
sudo systemctl status alphaquant

# Check if port is listening
sudo netstat -tlnp | grep 8000

# Test API endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "2.0.0"}
```

### 2. Database Connection Test

```bash
# Test database connectivity
psql -U alphaquant -d stock_market -c "SELECT 1;"

# Expected output:
#  ?column?
# ----------
#         1
```

### 3. Data Source Test

```bash
# Activate virtual environment
source venv/bin/activate

# Test Tushare connection
python -c "
from data_sources import StockAPI
import os
os.environ['TUSHARE_TOKEN'] = 'your_token'
try:
    stocks = StockAPI.get_list()
    print(f'✅ Tushare connection successful. Found {len(stocks)} stocks.')
except Exception as e:
    print(f'❌ Tushare connection failed: {e}')
"
```

### 4. Complete Integration Test

Create `test_deployment.py`:

```python
#!/usr/bin/env python
"""Deployment verification script"""

import sys
from common.database import DatabaseManager
from stock_market.services import StockService
from technical_analysis.services import AnalysisService

def test_database():
    """Test database connection"""
    try:
        db = DatabaseManager("postgresql://alphaquant:password@localhost:5432/stock_market")
        with db.get_session() as session:
            session.execute("SELECT 1")
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

def test_stock_service():
    """Test stock service"""
    try:
        db = DatabaseManager("postgresql://alphaquant:password@localhost:5432/stock_market")
        stock_service = StockService(db.get_session())
        stocks = stock_service.get_active_stocks(limit=5)
        print(f"✅ Stock service: OK ({len(stocks)} stocks found)")
        return True
    except Exception as e:
        print(f"❌ Stock service: FAILED - {e}")
        return False

def test_analysis_service():
    """Test analysis service"""
    try:
        db = DatabaseManager("postgresql://alphaquant:password@localhost:5432/stock_market")
        analysis_service = AnalysisService(db.get_session())
        result = analysis_service.analyze_stock("600519", days=30)
        print(f"✅ Analysis service: OK (score: {result['total_score']}/100)")
        return True
    except Exception as e:
        print(f"❌ Analysis service: FAILED - {e}")
        return False

if __name__ == "__main__":
    print("Running deployment verification...\n")

    results = [
        test_database(),
        test_stock_service(),
        test_analysis_service()
    ]

    if all(results):
        print("\n🎉 All tests passed! Deployment successful!")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)
```

Run the test:
```bash
python test_deployment.py
```

---

## 📊 Monitoring Setup

### 1. Application Monitoring

**Install Prometheus and Grafana**:
```bash
# Add Prometheus repository
sudo apt install prometheus grafana

# Configure Prometheus to scrape application metrics
cat > /etc/prometheus/prometheus.yml << EOF
scrape_configs:
  - job_name: 'alphaquant'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
EOF

# Restart Prometheus
sudo systemctl restart prometheus
```

### 2. Log Aggregation

**Configure centralized logging**:
```bash
# Install rsyslog
sudo apt install rsyslog

# Configure log forwarding
cat > /etc/rsyslog.d/alphaquant.conf << EOF
module(load="imfile" mode="inotify")

input(
    type="imfile"
    File="/var/log/alphaquant/*.log"
    Tag="alphaquant"
    Severity="info"
    Facility="local7"
)

if $programname == 'alphaquant' then @logserver.example.com:514
& stop
EOF

sudo systemctl restart rsyslog
```

### 3. Health Check Script

Create `/usr/local/bin/alphaquant-health-check.sh`:

```bash
#!/bin/bash
# AlphaQuant health check script

HEALTH_URL="http://localhost:8000/health"
ALERT_EMAIL="admin@example.com"

# Check service
if curl -sf -m 5 "$HEALTH_URL" > /dev/null; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is down!" | mail -s "AlphaQuant Alert: Service Down" "$ALERT_EMAIL"
    exit 1
fi
```

Make it executable and schedule:
```bash
chmod +x /usr/local/bin/alphaquant-health-check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/alphaquant-health-check.sh") | crontab -
```

---

## 🔒 Security Considerations

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL (only from app server)
sudo ufw enable
```

### 2. SSL/TLS Configuration

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

### 3. Database Security

```bash
# Change default postgres password
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_secure_password';
\q

# Disable remote postgres access if not needed
# Edit pg_hba.conf and comment out non-local connections
```

---

## 📚 Next Steps

- 🔧 [Configuration Guide](./02-configuration.md) - Detailed configuration
- 💾 [Database Setup](./04-database-setup.md) - Advanced database configuration
- 📡 [Data Source Setup](./05-data-source-setup.md) - Data source management
- 🔍 [Troubleshooting](./09-troubleshooting.md) - Common issues

---

**Next Chapter**: [Configuration Guide →](./02-configuration.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
