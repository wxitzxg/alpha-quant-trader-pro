# 💾 Backup and Restore

> Complete backup and disaster recovery guide

## 📋 Table of Contents
1. [Backup Strategy](#backup-strategy)
2. [Database Backup](#database-backup)
3. [Application Backup](#application-backup)
4. [Restore Procedures](#restore-procedures)
5. [Disaster Recovery](#disaster-recovery)

## 🎯 Backup Strategy

### Backup Types
- **Full Backup**: Complete database dump (daily)
- **Incremental Backup**: Changes since last backup (hourly)
- **Point-in-Time Recovery**: WAL archiving (continuous)

### Retention Policy
- Daily backups: Keep 7 days
- Weekly backups: Keep 4 weeks
- Monthly backups: Keep 12 months

## 💾 Database Backup

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/stock_market_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
pg_dump -U alphaquant stock_market | gzip > $BACKUP_FILE

# Set permissions
chmod 600 $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "stock_market_*.sql.gz" -mtime +7 -delete

# Weekly full backup
if [ $(date +%u) -eq 7 ]; then
    cp $BACKUP_FILE ${BACKUP_FILE/.sql.gz/_weekly.sql.gz}
fi
```

### Schedule with Cron
```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-database.sh

# Hourly incremental backup
0 * * * * /usr/local/bin/backup-incremental.sh
```

## 📦 Application Backup

### Backup Application Files
```bash
#!/bin/bash
BACKUP_DIR="/backup/application"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup application code
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    /opt/alpha-quant \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv'

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /opt/alpha-quant/config \
    /opt/alpha-quant/.env.production
```

## 🔙 Restore Procedures

### Database Restore
```bash
# Step 1: Stop application
sudo systemctl stop alphaquant

# Step 2: Drop and recreate database
psql -U postgres -c "DROP DATABASE stock_market;"
psql -U postgres -c "CREATE DATABASE stock_market OWNER alphaquant;"

# Step 3: Restore from backup
gunzip -c /backup/postgresql/stock_market_20260318_020000.sql.gz | psql -U alphaquant stock_market

# Step 4: Run migrations
cd /opt/alpha-quant
source venv/bin/activate
alembic upgrade head

# Step 5: Start application
sudo systemctl start alphaquant
```

### Point-in-Time Recovery
```bash
# Restore to specific point in time
pg_restore -U alphaquant -d stock_market \
    --recovery-target-time="2026-03-18 14:30:00" \
    /backup/postgresql/stock_market_20260318_020000.sql
```

## 🚨 Disaster Recovery

### Recovery Plan
1. **Assessment**: Determine extent of data loss
2. **Isolation**: Isolate affected systems
3. **Restoration**: Restore from latest backup
4. **Validation**: Verify data integrity
5. **Recovery**: Resume operations

### Emergency Contacts
- Database Administrator: dba@example.com
- System Administrator: sysadmin@example.com
- Support Hotline: +86-XXX-XXXX-XXXX
