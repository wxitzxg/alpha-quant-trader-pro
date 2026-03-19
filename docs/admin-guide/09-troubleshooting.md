# 🔍 Troubleshooting Guide

> Common issues and solutions for Alpha Quant Trader Pro

## 📋 Table of Contents
1. [Database Issues](#database-issues)
2. [Application Issues](#application-issues)
3. [Data Source Issues](#data-source-issues)
4. [Performance Issues](#performance-issues)
5. [Deployment Issues](#deployment-issues)

## 💾 Database Issues

### Issue: Database Connection Failed

**Symptoms**: `OperationalError: could not connect to server`

**Solutions**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check if PostgreSQL is listening on correct port
sudo netstat -tlnp | grep 5432

# Verify database exists
sudo -u postgres psql -l | grep stock_market

# Check connection string in .env
echo $DATABASE_URL

# Test connection manually
psql -U alphaquant -d stock_market -c "SELECT 1;"
```

### Issue: Too Many Connections

**Symptoms**: `FATAL: sorry, too many clients already`

**Solutions**:
```bash
# Check current connections
psql -U alphaquant -d stock_market -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max_connections in postgresql.conf
echo "max_connections = 300" | sudo tee -a /etc/postgresql/14/main/postgresql.conf

# Restart PostgreSQL
sudo systemctl restart postgresql

# Optimize connection pool in application
# config/production.json:
{
  "database": {
    "pool_size": 30,
    "max_overflow": 60
  }
}
```

### Issue: Slow Queries

**Symptoms**: Queries taking > 1 second

**Solutions**:
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Find slow queries
SELECT query, total_time, calls
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Create missing indexes
CREATE INDEX CONCURRENTLY idx_klines_symbol_date ON klines(symbol, date);
```

## 🔌 Application Issues

### Issue: Service Won't Start

**Symptoms**: `Failed to start alphaquant.service`

**Solutions**:
```bash
# Check service logs
sudo journalctl -u alphaquant -n 50

# Check if port is in use
sudo lsof -i :8000

# Check environment variables
sudo systemctl show alphaquant | grep Environment

# Test manually
cd /opt/alpha-quant
source venv/bin/activate
python -m api_server.main

# Check for Python errors
python -c "from api_server.main import app; print('Import successful')"
```

### Issue: Import Errors

**Symptoms**: `ModuleNotFoundError: No module named '...'`

**Solutions**:
```bash
# Activate virtual environment
source /opt/alpha-quant/venv/bin/activate

# Check installed packages
pip list | grep fastapi

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue: Permission Denied

**Symptoms**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:
```bash
# Check file ownership
ls -la /opt/alpha-quant

# Fix ownership
sudo chown -R alphaquant:alphaquant /opt/alpha-quant

# Check directory permissions
sudo chmod 755 /opt/alpha-quant
sudo chmod 644 /opt/alpha-quant/*.py

# Check log directory
sudo mkdir -p /var/log/alphaquant
sudo chown alphaquant:alphaquant /var/log/alphaquant
```

## 📡 Data Source Issues

### Issue: Tushare API Error

**Symptoms**: `HTTP 403: Token authentication failed`

**Solutions**:
```bash
# Check token in environment
echo $TUSHARE_TOKEN

# Verify token at https://tushare.pro/
# Check if token has expired or been revoked

# Check API rate limits
# Free tier: 20 calls/minute, 500 calls/day
# Upgrade account if needed

# Add retry logic
from data_sources import StockAPI

api = StockAPI(max_retries=3, retry_delay=5)
try:
    stocks = api.get_list()
except Exception as e:
    print(f"API error: {e}")
```

### Issue: Data Sync Fails

**Symptoms**: `sync_stocks.py fails with timeout`

**Solutions**:
```bash
# Increase timeout
export TUSHARE_TIMEOUT=60

# Run sync manually to see errors
cd /opt/alpha-quant
source venv/bin/activate
python scripts/sync_stocks.py

# Check network connectivity
ping api.tushare.pro

# Use fallback data source
export DATA_SOURCE_FALLBACK=akshare
```

### Issue: Missing K-Line Data

**Symptoms**: Backtest fails due to missing data

**Solutions**:
```python
# Sync missing data manually
from stock_market.services import KLineService
from common.database import DatabaseManager

db = DatabaseManager(os.getenv('DATABASE_URL'))
kline_service = KLineService(db.get_session())

# Sync specific stock and date range
kline_service.sync_single_kline(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Check data completeness
count = kline_service.get_kline_count("600519", "1d")
print(f"Total K-lines: {count}")
```

## ⚡ Performance Issues

### Issue: High CPU Usage

**Symptoms**: CPU usage > 80% constantly

**Solutions**:
```bash
# Find CPU-intensive processes
top -o %CPU

# Check for long-running queries
psql -U alphaquant -d stock_market -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;"

# Optimize application
# - Use connection pooling
# - Implement caching
# - Optimize queries
# - Use async operations

# Scale horizontally
# - Add more application servers
# - Use load balancer
```

### Issue: High Memory Usage

**Symptoms**: Memory usage > 90%, OOM errors

**Solutions**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Optimize database
# Reduce shared_buffers if too high
# Increase work_mem for complex queries

# Optimize application
# - Use generators instead of lists
# - Close database sessions properly
# - Implement pagination for large queries
# - Use batch processing

# Add swap space (temporary solution)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Slow Response Times

**Symptoms**: API responses > 2 seconds

**Solutions**:
```python
# Enable performance monitoring
from fastapi import Request, Response
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(symbol, date):
    # Expensive operation
    return session.query(KLine).filter_by(symbol=symbol, date=date).first()

# Optimize database queries
# Use indexes
# Avoid N+1 queries
# Use eager loading
```

## 🚀 Deployment Issues

### Issue: Nginx 502 Bad Gateway

**Symptoms**: Nginx returns 502 error

**Solutions**:
```bash
# Check if application is running
sudo systemctl status alphaquant

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if application is listening
sudo netstat -tlnp | grep 8000

# Increase Nginx timeout
# /etc/nginx/sites-available/alphaquant:
location / {
    proxy_pass http://localhost:8000;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

# Restart services
sudo systemctl restart alphaquant
sudo systemctl restart nginx
```

### Issue: SSL Certificate Errors

**Symptoms**: `SSL_ERROR_BAD_CERT_DOMAIN` or expired certificate

**Solutions**:
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -noout -dates

# Force renewal
sudo certbot renew --force-renewal

# Auto-renewal is configured in /etc/cron.d/certbot
```

### Issue: Docker Container Won't Start

**Symptoms**: `docker-compose up` fails

**Solutions**:
```bash
# Check container logs
docker-compose logs app

# Check if ports are in use
sudo lsof -i :8000

# Rebuild images
docker-compose build --no-cache

# Remove and recreate containers
docker-compose down
docker-compose up -d

# Check disk space
docker system df

# Prune unused resources
docker system prune -a
```

## 📞 Getting Help

If issues persist:

1. **Check logs**:
   - Application: `/var/log/alphaquant/app.log`
   - Database: `/var/log/postgresql/postgresql-14-main.log`
   - Nginx: `/var/log/nginx/error.log`

2. **Gather diagnostics**:
   ```bash
   # System info
   uname -a
   python --version
   psql --version

   # Application status
   sudo systemctl status alphaquant
   sudo systemctl status postgresql

   # Network
   netstat -tlnp | grep -E '(8000|5432)'
   ```

3. **Contact support**:
   - Email: support@alphaquant.com
   - GitHub Issues: https://github.com/your-org/alpha-quant-trader-pro/issues
   - Discord: Join our community server

---

**Last Updated**: 2026-03-18
