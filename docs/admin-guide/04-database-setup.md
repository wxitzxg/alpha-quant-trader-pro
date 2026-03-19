# 💾 Database Setup

> PostgreSQL database configuration and optimization guide

## 📋 Table of Contents
1. [PostgreSQL Installation](#postgresql-installation)
2. [Database Configuration](#database-configuration)
3. [Performance Optimization](#performance-optimization)
4. [Backup and Recovery](#backup-and-recovery)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)

## 📦 PostgreSQL Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql-14 postgresql-contrib-14

sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### CentOS/RHEL
```bash
sudo dnf install postgresql14-server postgresql14-contrib

sudo /usr/pgsql-14/bin/postgresql-14-setup initdb
sudo systemctl start postgresql-14
sudo systemctl enable postgresql-14
```

## ⚙️ Database Configuration

Edit `/etc/postgresql/14/main/postgresql.conf`:
```conf
listen_addresses = '*'
max_connections = 200
shared_buffers = 4GB
work_mem = 16MB
maintenance_work_mem = 1GB
wal_level = replica
max_wal_size = 2GB
checkpoint_timeout = 30min
effective_cache_size = 12GB
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
```

## ⚡ Performance Optimization

### Index Strategy
```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_klines_symbol_date ON klines(symbol, date);
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);

-- Composite indexes for multi-column queries
CREATE INDEX idx_klines_symbol_interval_date ON klines(symbol, interval, date DESC);
```

### Connection Pooling
Configure SQLAlchemy connection pool:
```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": true
  }
}
```

## 💾 Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/stock_market_$DATE.sql.gz"

pg_dump -U alphaquant stock_market | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "stock_market_*.sql.gz" -mtime +7 -delete
```

### Restore Procedure
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE stock_market;"
psql -U postgres -c "CREATE DATABASE stock_market OWNER alphaquant;"

# Restore from backup
gunzip -c /backup/stock_market_20260318_120000.sql.gz | psql -U alphaquant stock_market
```

## 🔍 Monitoring and Maintenance

### Daily Maintenance Tasks
```bash
# Analyze database
psql -U alphaquant -d stock_market -c "ANALYZE;"

# Vacuum database
psql -U alphaquant -d stock_market -c "VACUUM ANALYZE;"

# Check for bloat
psql -U alphaquant -d stock_market -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"
```

### Monitoring Queries
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Long-running queries
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;

-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```
