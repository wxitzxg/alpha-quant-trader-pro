# ⚡ Performance Optimization

> Database and application performance tuning guide

## 📋 Table of Contents
1. [Database Optimization](#database-optimization)
2. [Application Optimization](#application-optimization)
3. [Caching Strategy](#caching-strategy)
4. [Load Testing](#load-testing)

## 💾 Database Optimization

### PostgreSQL Configuration

```conf
# Memory settings (adjust based on available RAM)
shared_buffers = 4GB              # 25% of RAM
work_mem = 16MB                   # Per operation
maintenance_work_mem = 1GB        # Maintenance operations
effective_cache_size = 12GB       # 75% of RAM

# Connection settings
max_connections = 200
superuser_reserved_connections = 3

# WAL settings
wal_level = replica
max_wal_size = 2GB
checkpoint_timeout = 30min
checkpoint_completion_target = 0.9

# Query planning
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Index Optimization

```sql
-- Analyze query patterns
SELECT schemaname, tablename, attname, null_frac, avg_width
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY null_frac DESC;

-- Create missing indexes
CREATE INDEX CONCURRENTLY idx_klines_symbol_date_desc ON klines(symbol, date DESC);
CREATE INDEX CONCURRENTLY idx_positions_user_symbol ON positions(user_id, symbol);

-- Remove unused indexes
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Query Optimization

```sql
-- Enable query logging for slow queries
log_min_duration_statement = 1000  # Log queries > 1s

-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM klines
WHERE symbol = '600519'
AND date >= '2023-01-01'
ORDER BY date DESC
LIMIT 100;

-- Optimize batch operations
-- BAD: Individual inserts
-- for record in records:
--     INSERT INTO klines VALUES (...)

-- GOOD: Batch insert
INSERT INTO klines (symbol, date, open, high, low, close, volume)
VALUES
    ('600519', '2023-01-01', 10.0, 11.0, 9.5, 10.5, 100000),
    ('600519', '2023-01-02', 10.5, 11.5, 10.0, 11.0, 120000),
    -- ...
ON CONFLICT (symbol, date) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    -- ...
```

## 🔌 Application Optimization

### Connection Pooling

```python
# SQLAlchemy connection pool configuration
engine = create_engine(
    DATABASE__URL,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)
```

### Async Operations

```python
# Use async for I/O operations
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    DATABASE__URL,
    pool_size=20,
    max_overflow=40
)

async def get_klines_async(symbol, date):
    async with async_engine.connect() as conn:
        result = await conn.execute(
            select(KLine).where(
                KLine.symbol == symbol,
                KLine.date >= date
            )
        )
        return result.fetchall()
```

### Batch Processing

```python
# Process data in batches
BATCH_SIZE = 1000

for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]
    session.bulk_insert_mappings(KLine, batch)
    session.commit()
```

## 🗂️ Caching Strategy

### Redis Configuration

```json
{
  "cache": {
    "enabled": true,
    "backend": "redis",
    "default_ttl": 3600,
    "namespace": "alphaquant",
    "key_prefix": "cache:",
    "compression": true
  }
}
```

### Cache Implementation

```python
from functools import wraps
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_parts = [func.__name__] + list(args) + [f"{k}={v}" for k, v in kwargs.items()]
            cache_key = f"cache:{':'.join(map(str, key_parts))}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=3600)
def get_stock_data(symbol, date):
    # Expensive database query
    return session.query(KLine).filter_by(symbol=symbol, date=date).first()
```

## 🧪 Load Testing

### Locust Load Test

```python
# locustfile.py
from locust import HttpUser, task, between

class AlphaQuantUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_stock_data(self):
        self.client.get("/api/stocks/600519/klines?interval=1d&limit=100")

    @task(3)
    def get_analysis(self):
        self.client.get("/api/analysis/600519?days=120")

    @task(2)
    def get_portfolio(self):
        self.client.get("/api/portfolio/positions", headers={"Authorization": "Bearer token"})
```

### Run Load Test
```bash
# Install locust
pip install locust

# Run test
locust -f locustfile.py --host=http://localhost:8000

# Web UI: http://localhost:8089
```

### Performance Benchmarks

**Target Metrics**:
- Response time: < 200ms (p95)
- Throughput: 1000+ requests/sec
- Error rate: < 0.1%
- Database connections: < 80% of pool size

**Monitoring During Test**:
```bash
# Monitor database
watch -n 1 "psql -U alphaquant -d stock_market -c \"SELECT count(*) FROM pg_stat_activity WHERE state = 'active';\""

# Monitor system resources
htop

# Monitor application logs
tail -f /var/log/alphaquant/app.log
```
