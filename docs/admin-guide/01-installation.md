# 🔧 Installation Guide

> Complete installation guide for production environments

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Installation Methods](#installation-methods)
4. [Manual Installation](#manual-installation)
5. [Docker Installation](#docker-installation)
6. [Post-Installation Verification](#post-installation-verification)
7. [Common Installation Issues](#common-installation-issues)

---

## 🖥️ System Requirements

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 4 GB | 8 GB | 16+ GB |
| **Storage** | 50 GB | 100 GB | 500+ GB SSD |
| **Network** | 10 Mbps | 50 Mbps | 100+ Mbps |

### Software Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS** | Ubuntu 20.04 | Ubuntu 22.04 | CentOS 8+ supported |
| **Python** | 3.8 | 3.10 | 3.11 also works |
| **PostgreSQL** | 12.x | 14.x | 15.x recommended |
| **Redis** | 6.0 | 7.0 | Optional but recommended |
| **Docker** | 20.10 | 24.0 | For container deployment |

### Supported Operating Systems

**Primary Support**:
- ✅ **Ubuntu 20.04 LTS** - Fully tested
- ✅ **Ubuntu 22.04 LTS** - Fully tested (Recommended)
- ✅ **CentOS 8** - Fully tested
- ✅ **Rocky Linux 8/9** - Fully tested

**Secondary Support**:
- ⚠️ **Debian 11** - Community tested
- ⚠️ **Fedora 36+** - Community tested
- ⚠️ **Amazon Linux 2** - Community tested

**Not Recommended for Production**:
- ❌ Windows (use WSL for development only)
- ❌ macOS (development only)
- ❌ Older OS versions (EOL)

---

## ✅ Pre-Installation Checklist

### System Preparation

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install required system packages
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql-14 \
    postgresql-contrib-14 \
    redis-server \
    nginx \
    git \
    build-essential \
    libpq-dev \
    libssl-dev \
    curl \
    wget \
    unzip

# 3. Check Python version
python3.10 --version
# Expected: Python 3.10.x

# 4. Check PostgreSQL version
psql --version
# Expected: psql (PostgreSQL) 14.x

# 5. Check available disk space
df -h /opt
# Ensure at least 50 GB free space

# 6. Check available memory
free -h
# Ensure at least 4 GB RAM available
```

### Network Configuration

```bash
# 1. Check network connectivity
ping -c 4 google.com

# 2. Check DNS resolution
nslookup github.com

# 3. Check firewall status
sudo ufw status
# If active, allow necessary ports:
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
```

### User and Permissions

```bash
# 1. Create dedicated system user
sudo useradd -r -m -s /bin/bash alphaquant

# 2. Add user to necessary groups
sudo usermod -aG sudo alphaquant  # Optional: for admin access

# 3. Set secure password
sudo passwd alphaquant

# 4. Verify user creation
id alphaquant
# Expected: uid=xxx(alphaquant) gid=xxx(alphaquant) groups=xxx(alphaquant)

# 5. Create installation directory
sudo mkdir -p /opt/alpha-quant
sudo chown alphaquant:alphaquant /opt/alpha-quant
```

---

## 📦 Installation Methods

### Method 1: Manual Installation (Recommended)

**Best for**: Full control, customization, production deployments

See [Manual Installation](#manual-installation) section below.

### Method 2: Docker Installation

**Best for**: Quick setup, containerized environments, development

See [Docker Installation](#docker-installation) section below.

### Method 3: Automated Script

**Best for**: Repeatable deployments, CI/CD pipelines

```bash
# Download installation script
curl -fsSL https://raw.githubusercontent.com/your-org/alpha-quant-trader-pro/main/scripts/install.sh -o install.sh

# Make executable
chmod +x install.sh

# Run installation
sudo ./install.sh --production

# Options:
# --production : Production installation
# --development : Development installation
# --help : Show help
```

---

## 🔨 Manual Installation

### Step 1: Clone Repository

```bash
# Switch to installation user
sudo su - alphaquant

# Navigate to installation directory
cd /opt/alpha-quant

# Clone repository
git clone https://github.com/your-org/alpha-quant-trader-pro.git .

# Checkout production branch
git checkout main  # or specific version tag

# Verify clone
ls -la
# Should see: api_server, backtest, common, config, data_sources, etc.
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation
which python
# Expected: /opt/alpha-quant/venv/bin/python

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn uvicorn[standard]

# Verify installation
python -c "import fastapi, sqlalchemy, pandas; print('✅ Dependencies installed successfully')"
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env.production

# Edit production environment
nano .env.production
```

**Required Environment Variables**:

```bash
# Database Configuration
DATABASE__URL=postgresql://alphaquant:your_secure_password@localhost:5432/stock_market

# Tushare Configuration
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_TIMEOUT=30
TUSHARE_RETRY_TIMES=3

# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=generate_using_python_secrets_module
ALLOWED_HOSTS=localhost,yourdomain.com

# Redis Configuration (optional)
REDIS__URL=redis://localhost:6379/0
REDIS_ENABLED=true

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
```

**Generate Secret Key**:

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Example output: a1b2c3d4e5f6... (copy this to SECRET_KEY)
```

### Step 4: Initialize Database

```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE stock_market
    WITH OWNER = alphaquant
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

CREATE USER alphaquant WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE stock_market TO alphaquant;
EOF

# Initialize database tables (auto-created on first startup)
source venv/bin/activate
# Tables are automatically created when API server starts
# Alternatively, run a quick test to verify database connection:
python -c "from common.database import DatabaseManager; from common.config import get_config; db = DatabaseManager(get_config().get_database_url()); db.create_all(); print('Database tables created successfully')"
```

### Step 5: Install and Configure Services

#### PostgreSQL Configuration

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

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'none'
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

#### Redis Configuration (Optional)

Edit `/etc/redis/redis.conf`:

```conf
# Bind to localhost only
bind 127.0.0.1

# Enable persistence
appendonly yes

# Set memory limit (adjust based on available RAM)
maxmemory 2gb
maxmemory-policy allkeys-lru

# Enable protected mode
protected-mode yes
```

Restart Redis:
```bash
sudo systemctl restart redis-server
```

### Step 6: Configure Systemd Service

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
Environment="DATABASE__URL=postgresql://alphaquant:your_password@localhost:5432/stock_market"
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

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

Create log directory:
```bash
sudo mkdir -p /var/log/alphaquant
sudo chown alphaquant:alphaquant /var/log/alphaquant
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alphaquant
sudo systemctl start alphaquant
sudo systemctl status alphaquant
```

### Step 7: Configure Nginx (Reverse Proxy)

Install Nginx:
```bash
sudo apt install nginx
```

Create `/etc/nginx/sites-available/alphaquant`:

```nginx
upstream alphaquant_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # SSL redirect (uncomment after SSL setup)
    # return 301 https://$server_name$request_uri;

    access_log /var/log/nginx/alphaquant_access.log;
    error_log /var/log/nginx/alphaquant_error.log;

    location / {
        proxy_pass http://alphaquant_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /opt/alpha-quant/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/alphaquant /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 🐳 Docker Installation

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in for group change to take effect
```

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/alpha-quant-trader-pro.git /opt/alpha-quant
cd /opt/alpha-quant
```

### Step 2: Create Environment File

```bash
cat > .env << EOF
# Database
POSTGRES_USER=alphaquant
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=stock_market
DB_HOST=db

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Tushare
TUSHARE_TOKEN=your_tushare_token_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
EOF
```

### Step 3: Create Docker Compose File

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
      - DATABASE__URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DB_HOST}:5432/${POSTGRES_DB}
      - TUSHARE_TOKEN=${TUSHARE_TOKEN}
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG=${DEBUG}
      - LOG_LEVEL=${LOG_LEVEL}
      - REDIS__URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - alphaquant-network
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  db:
    image: postgres:14-alpine
    container_name: alphaquant-db
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    networks:
      - alphaquant-network
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  redis:
    image: redis:7-alpine
    container_name: alphaquant-redis
    restart: always
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - alphaquant-network
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

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
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  alphaquant-network:
    driver: bridge
```

### Step 4: Create Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app_server {
        server app:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        location / {
            proxy_pass http://app_server;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Step 5: Start Services

```bash
# Build and start containers
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Database tables are auto-created on first API startup

# Test service
curl http://localhost:8000/health
```

---

## ✅ Post-Installation Verification

### 1. Service Status

```bash
# Check service status
sudo systemctl status alphaquant

# Check if service is listening on port 8000
sudo netstat -tlnp | grep 8000

# Expected output:
# tcp 0 0 0.0.0.0:8000  0.0.0.0:*  LISTEN  <pid>/gunicorn
```

### 2. Health Check

```bash
# Test API health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "2.0.0", "timestamp": "2026-03-18T..."}
```

### 3. Database Connection

```bash
# Test database connectivity
psql -U alphaquant -d stock_market -c "SELECT version();"

# Expected output:
# PostgreSQL 14.x on x86_64-pc-linux-gnu
```

### 4. Complete Verification Script

Create `verify_installation.sh`:

```bash
#!/bin/bash
# Installation verification script

echo "=== Alpha Quant Installation Verification ==="
echo

# Check Python
echo "Checking Python..."
python3.10 --version
if [ $? -eq 0 ]; then
    echo "✅ Python: OK"
else
    echo "❌ Python: FAILED"
    exit 1
fi
echo

# Check dependencies
echo "Checking Python dependencies..."
source venv/bin/activate
python -c "import fastapi, sqlalchemy, pandas" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dependencies: OK"
else
    echo "❌ Dependencies: FAILED"
    exit 1
fi
echo

# Check database
echo "Checking database connection..."
psql -U alphaquant -d stock_market -c "SELECT 1" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
    exit 1
fi
echo

# Check service
echo "Checking service status..."
sudo systemctl is-active alphaquant >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Service: OK"
else
    echo "❌ Service: FAILED"
    exit 1
fi
echo

# Check API
echo "Checking API endpoint..."
curl -sf http://localhost:8000/health >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ API: OK"
else
    echo "❌ API: FAILED"
    exit 1
fi
echo

echo "=== All Checks Passed! Installation Successful! ==="
```

Run verification:
```bash
chmod +x verify_installation.sh
./verify_installation.sh
```

---

## 🔍 Common Installation Issues

### Issue 1: Python Package Installation Fails

**Symptoms**: `pip install` fails with compilation errors

**Solution**:
```bash
# Install build dependencies
sudo apt install build-essential python3-dev libpq-dev

# Try installing again
pip install -r requirements.txt
```

### Issue 2: Database Connection Failed

**Symptoms**: `could not connect to server` error

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check if database exists
sudo -u postgres psql -l | grep stock_market

# Check pg_hba.conf configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure: host all all 127.0.0.1/32 md5
```

### Issue 3: Port Already in Use

**Symptoms**: `Address already in use` error

**Solution**:
```bash
# Check what's using the port
sudo lsof -i :8000

# Kill the process or change port in configuration
# Edit .env.production: API_PORT=8001
```

### Issue 4: Permission Denied

**Symptoms**: `Permission denied` errors

**Solution**:
```bash
# Check file ownership
ls -la /opt/alpha-quant

# Fix ownership
sudo chown -R alphaquant:alphaquant /opt/alpha-quant

# Check directory permissions
sudo chmod 755 /opt/alpha-quant
```

### Issue 5: Virtual Environment Activation Fails

**Symptoms**: `source: command not found` or activation doesn't work

**Solution**:
```bash
# Use full path
source /opt/alpha-quant/venv/bin/activate

# Or use bash explicitly
bash -c "source venv/bin/activate && python --version"
```

---

## 📚 Next Steps

- ⚙️ [Configuration Guide](./02-configuration.md) - Configure your installation
- 💾 [Database Setup](./04-database-setup.md) - Advanced database configuration
- 📡 [Data Source Setup](./05-data-source-setup.md) - Configure data sources
- 🔍 [Troubleshooting](./09-troubleshooting.md) - Common issues and solutions

---

**Next Chapter**: [Configuration Guide →](./02-configuration.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
