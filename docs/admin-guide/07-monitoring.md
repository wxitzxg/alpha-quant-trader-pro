# 🔍 Monitoring and Logging

> Application monitoring, logging, and alerting setup

## 📋 Table of Contents
1. [Application Monitoring](#application-monitoring)
2. [Log Management](#log-management)
3. [Alerting Setup](#alerting-setup)
4. [Performance Metrics](#performance-metrics)

## 📊 Application Monitoring

### Health Check Endpoint
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "timestamp": "2026-03-18T12:00:00Z"
}
```

### Prometheus Metrics
```python
# Add to api_server/main.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_DURATION.time():
        response = await call_next(request)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Grafana Dashboard
Create dashboard with panels:
- Request rate
- Response time
- Error rate
- Database connections
- Cache hit ratio
- System resources (CPU, memory, disk)

## 📝 Log Management

### Log Configuration
```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "handlers": ["file", "console", "syslog"],
    "file_path": "/var/log/alphaquant/app.log",
    "max_size": 10485760,
    "backup_count": 5,
    "syslog_address": "/dev/log",
    "logstash_enabled": false,
    "logstash_host": "localhost",
    "logstash_port": 5000
  }
}
```

### Log Rotation
```bash
# /etc/logrotate.d/alphaquant
/var/log/alphaquant/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 alphaquant alphaquant
    sharedscripts
    postrotate
        systemctl reload alphaquant > /dev/null 2>&1 || true
    endscript
}
```

## 🔔 Alerting Setup

### Alert Rules (Prometheus)
```yaml
groups:
  - name: alphaquant_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate > 10% for 2 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time > 2s"

      - alert: DatabaseDown
        expr: database_connected == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "Database connection lost"
```

### Email Alerts
```python
# Health check with email alert
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'alphaquant@example.com'
    msg['To'] = 'admin@example.com'

    smtp = smtplib.SMTP('smtp.example.com')
    smtp.send_message(msg)
    smtp.quit()
```

## 📈 Performance Metrics

### Key Metrics to Monitor

**Application Metrics**:
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active connections

**Database Metrics**:
- Connection pool usage
- Query execution time
- Cache hit ratio
- Lock contention

**System Metrics**:
- CPU usage (%)
- Memory usage (%)
- Disk I/O (IOPS)
- Network bandwidth

### Monitoring Script
```bash
#!/bin/bash
# System monitoring script

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')

# Memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f"), $3/$2 * 100.0}')

# Disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}')

# Database connections
DB_CONNECTIONS=$(psql -U alphaquant -d stock_market -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)

# Log to file
echo "$(date): CPU=${CPU_USAGE}%, MEM=${MEMORY_USAGE}%, DISK=${DISK_USAGE}, DB_CONN=${DB_CONNECTIONS}" >> /var/log/alphaquant/monitoring.log
```
