# 🐛 Debugging Guide

> Debugging techniques and troubleshooting for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Debugging Tools](#debugging-tools)
2. [Logging Best Practices](#logging-best-practices)
3. [Common Debugging Scenarios](#common-debugging-scenarios)
4. [Performance Debugging](#performance-debugging)
5. [Database Debugging](#database-debugging)
6. [API Debugging](#api-debugging)
7. [Testing Debugging](#testing-debugging)
8. [Production Debugging](#production-debugging)

---

## 🛠️ Debugging Tools

### Built-in Python Debugger (pdb)

**Basic Usage:**
```python
import pdb

def complex_function(data):
    # Set breakpoint
    pdb.set_trace()
    result = process_data(data)
    return result
```

**Python 3.7+ (breakpoint):**
```python
def complex_function(data):
    # Cleaner breakpoint syntax
    breakpoint()
    result = process_data(data)
    return result
```

**pdb Commands:**
```python
# Common commands
n  # Next line
s  # Step into function
c  # Continue execution
r  # Return from current function
l  # List source code
p variable  # Print variable
pp variable  # Pretty print variable
q  # Quit debugger
```

### IDE Debuggers

**VSCode Debugging:**

1. **Create `.vscode/launch.json`:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: API Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api_server.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

2. **Set breakpoints:**
   - Click left gutter next to line numbers
   - Or use `# breakpoint` comment

3. **Start debugging:**
   - Press F5 or click "Run and Debug"
   - Use debug toolbar (Continue, Step Over, Step Into, etc.)

**PyCharm Debugging:**

1. **Set breakpoints:**
   - Click left gutter or press Ctrl+F8 (Cmd+F8 on macOS)

2. **Start debugging:**
   - Right-click file → Debug 'filename'
   - Or click Debug icon (green bug)

3. **Debug toolbar:**
   - Step Over (F8)
   - Step Into (F7)
   - Step Out (Shift+F8)
   - Resume Program (F9)
   - Evaluate Expression (Alt+F8)

### IPython Debugger (ipdb)

**Enhanced pdb with IPython features:**
```bash
pip install ipdb
```

```python
import ipdb

def complex_function(data):
    ipdb.set_trace()  # Better tab completion and syntax highlighting
    result = process_data(data)
    return result
```

### Remote Debugger (debugpy)

**For remote/container debugging:**
```bash
pip install debugpy
```

```python
# In your code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # Pause until debugger attaches

def my_function():
    breakpoint()  # Now VSCode can attach
    pass
```

**VSCode configuration for remote debugging:**
```json
{
  "name": "Python: Remote Attach",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ]
}
```

---

## 📝 Logging Best Practices

### Logging Configuration

**Basic Configuration:**
```python
import logging

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

**Production Configuration:**
```python
# common/logging_config.py

import logging
import logging.handlers
import sys
from pathlib import Path

def setup_logging(log_level="INFO", log_file="logs/app.log"):
    """Configure logging for the application."""

    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
```

### Logging Levels

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    # DEBUG: Detailed information for debugging
    logger.debug("Debug message with data: %s", data)

    # INFO: General information about application flow
    logger.info("Processing stock: %s", symbol)

    # WARNING: Unexpected events that are not errors
    logger.warning("Rate limit approaching: %d requests", count)

    # ERROR: Errors that occur during execution
    try:
        result = risky_operation()
    except Exception as e:
        logger.error("Operation failed: %s", str(e), exc_info=True)

    # CRITICAL: Critical errors that may cause system failure
    logger.critical("Database connection lost!")
```

### Structured Logging

**Using JSON format:**
```python
import json
import logging

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)

# Usage
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Log with extra context
logger.info("User login", extra={
    "user_id": user_id,
    "ip_address": ip_address,
    "user_agent": user_agent
})
```

### Contextual Logging

**Using contextvars for request context:**
```python
import contextvars
import logging
from uuid import uuid4

# Create context variable for request ID
request_id_ctx = contextvars.ContextVar("request_id", default=None)

class RequestContextFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

# Configure logger
handler = logging.StreamHandler()
handler.addFilter(RequestContextFilter())
formatter = logging.Formatter(
    '%(asctime)s - %(request_id)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Usage in request handler
async def handle_request(request):
    # Set request ID at start of request
    request_id = str(uuid4())
    request_id_ctx.set(request_id)

    logger.info("Processing request")
    # ... process request
    logger.info("Request completed")
```

---

## 🐛 Common Debugging Scenarios

### 1. Database Connection Issues

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Debugging Steps:**
```python
import logging
import traceback

logger = logging.getLogger(__name__)

def test_database_connection():
    """Debug database connection issues."""
    try:
        from common.database import DatabaseManager

        logger.info("Testing database connection...")

        # Try to create engine
        db = DatabaseManager()

        # Test connection
        with db.session_scope() as session:
            result = session.execute("SELECT 1")
            logger.info(f"Database connection successful: {result.scalar()}")

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(traceback.format_exc())

        # Check connection string
        import os
        db_url = os.getenv("DATABASE_URL")
        logger.error(f"DATABASE_URL: {db_url}")

        # Test PostgreSQL directly
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            logger.info("psycopg2 connection successful")
            conn.close()
        except Exception as e2:
            logger.error(f"psycopg2 connection failed: {e2}")
```

**Common Fixes:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -c "\l"

# Check connection string format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:port/database

# Test connection manually
psql -U alphaquant -d stock_market -h localhost
```

### 2. API Request Failures

**Symptoms:**
```
ConnectionError: Failed to establish connection
HTTPError: 401 Unauthorized
```

**Debugging Steps:**
```python
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

def debug_api_request(url, headers=None, params=None):
    """Debug API request issues."""

    # Enable HTTP request logging
    import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

    try:
        logger.info(f"Making request to: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Params: {params}")

        response = requests.get(url, headers=headers, params=params, timeout=30)

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.info(f"Response content: {response.text[:500]}")  # First 500 chars

        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        logger.error(traceback.format_exc())
        raise
```

**Common Fixes:**
```python
# Add retry logic
def create_session_with_retry():
    """Create requests session with retry logic."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Use session
session = create_session_with_retry()
response = session.get(url, headers=headers, timeout=30)
```

### 3. Data Processing Errors

**Symptoms:**
```
KeyError: 'close_price'
ValueError: could not convert string to float
```

**Debugging Steps:**
```python
import logging
import traceback

logger = logging.getLogger(__name__)

def debug_data_processing(data):
    """Debug data processing issues."""

    logger.debug(f"Input data type: {type(data)}")
    logger.debug(f"Input data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")

    # Log first few items
    if isinstance(data, list) and len(data) > 0:
        logger.debug(f"First item: {data[0]}")
        logger.debug(f"First item type: {type(data[0])}")

        if isinstance(data[0], dict):
            logger.debug(f"First item keys: {data[0].keys()}")

    try:
        # Process data
        result = process_data(data)
        logger.info(f"Processing successful, result: {result}")
        return result

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        logger.error(f"Data sample: {data[:3] if isinstance(data, list) else data}")
        logger.error(traceback.format_exc())
        raise
```

---

## ⚡ Performance Debugging

### Profiling with cProfile

**Basic Profiling:**
```bash
# Profile script execution
python -m cProfile -s cumulative my_script.py

# Profile and save to file
python -m cProfile -o profile.stats my_script.py

# View profile results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

**Programmatic Profiling:**
```python
import cProfile
import pstats
import io
from pstats import SortKey

def profile_function(func, *args, **kwargs):
    """Profile a function and print results."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats(SortKey.CUMULATIVE)
    ps.print_stats(20)  # Print top 20 functions

    print(s.getvalue())
    return result

# Usage
profile_function(calculate_indicators, klines)
```

### Line Profiler

**Install:**
```bash
pip install line_profiler
```

**Usage:**
```python
@profile  # Add this decorator
def calculate_indicators(klines):
    total = 0
    for kline in klines:  # This line will be profiled
        total += kline.close
    return total / len(klines)

# Run with: kernprof -l -v script.py
```

### Memory Profiler

**Install:**
```bash
pip install memory_profiler
```

**Usage:**
```python
from memory_profiler import profile

@profile
def load_large_dataset():
    data = []
    for i in range(1000000):
        data.append(i)
    return data

# Run with: python -m memory_profiler script.py
```

### Time Measurement

**Simple timing:**
```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name):
    """Context manager for timing code blocks."""
    start = time.time()
    yield
    end = time.time()
    print(f"{name}: {end - start:.4f} seconds")

# Usage
with timer("Processing klines"):
    result = calculate_indicators(klines)
```

**Multiple measurements:**
```python
import timeit

# Time a function
execution_time = timeit.timeit(
    lambda: calculate_indicators(klines),
    number=100
)
print(f"Average execution time: {execution_time / 100:.4f}s")
```

---

## 💾 Database Debugging

### SQLAlchemy Query Logging

**Enable query logging:**
```python
from sqlalchemy import create_engine

# Enable echo for development
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries
    echo_pool=True  # Log connection pool events
)

# Or use logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```

**Log specific queries:**
```python
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log SQL statements before execution."""
    logger.debug(f"SQL: {statement}")
    logger.debug(f"Parameters: {parameters}")
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time."""
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    logger.debug(f"Query took {total_time:.4f}s")
```

### Query Optimization

**Identify slow queries:**
```python
from sqlalchemy import text

def analyze_query(session, query):
    """Analyze query performance."""

    # Get raw SQL
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

    # Explain query
    result = session.execute(text(f"EXPLAIN ANALYZE {sql}"))

    for row in result:
        print(row[0])

# Usage
query = session.query(Stock).filter(Stock.industry == "白酒")
analyze_query(session, query)
```

**Fix N+1 queries:**
```python
# ❌ BAD: N+1 queries
def get_stocks_with_indicators_bad():
    stocks = session.query(Stock).all()
    for stock in stocks:
        print(stock.indicators)  # Separate query for each stock

# ✅ GOOD: Eager loading
from sqlalchemy.orm import joinedload

def get_stocks_with_indicators_good():
    stocks = session.query(Stock)\
        .options(joinedload(Stock.indicators))\
        .all()
    for stock in stocks:
        print(stock.indicators)  # No additional queries
```

---

## 🔌 API Debugging

### FastAPI Debugging

**Middleware for request logging:**
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

class DebugMiddleware(BaseHTTPMiddleware):
    """Middleware to log request/response details."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.debug(f"Request: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")

        # Get request body
        body = await request.body()
        logger.debug(f"Body: {body.decode()[:500]}")  # First 500 chars

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response time: {duration:.4f}s")

        return response

# Add to app
app.add_middleware(DebugMiddleware)
```

**Exception handlers:**
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

app = FastAPI()

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    """Debug exception handler with detailed logging."""

    logger.error(f"Exception occurred: {exc}")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc().split("\n")
        }
    )
```

---

## 🧪 Testing Debugging

### Debugging Failing Tests

**Run with verbose output:**
```bash
# Show print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v -l

# Drop to pdb on failure
pytest tests/ -v --pdb

# Drop to pdb on first failure, exit
pytest tests/ -v --pdb --exitfirst

# Continue until all failures, then enter pdb
pytest tests/ -v --pdb --maxfail=1
```

**Debug specific test:**
```bash
# Run single test with breakpoints
pytest tests/test_stock_service.py::TestStockService::test_get_stock -v --pdb

# Use VSCode debugger
# Set breakpoint in test, then run with "Python: pytest" configuration
```

**Inspect fixtures:**
```python
def test_with_fixture(my_fixture):
    """Test with fixture inspection."""
    import pdb; pdb.set_trace()  # Inspect fixture value
    assert my_fixture is not None
```

---

## 🚀 Production Debugging

### Safe Debugging in Production

**Never use in production:**
```python
# ❌ DON'T: Debug endpoints in production
@app.get("/debug/memory")
async def debug_memory():
    import gc
    return {"objects": len(gc.get_objects())}
```

**Use feature flags:**
```python
import os

DEBUG_ENABLED = os.getenv("DEBUG_ENABLED", "false").lower() == "true"

if DEBUG_ENABLED:
    @app.get("/debug/memory")
    async def debug_memory():
        import gc
        return {"objects": len(gc.get_objects())}
```

### Monitoring and Alerts

**Health check endpoint:**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    checks = {
        "database": False,
        "cache": False,
        "version": "2.0.0"
    }

    try:
        # Check database
        with db.session_scope() as session:
            session.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    try:
        # Check Redis
        if redis_client:
            redis_client.ping()
            checks["cache"] = True
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")

    # Determine overall status
    status = "healthy" if all(checks.values()) else "unhealthy"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📚 Summary

### Debugging Checklist

When debugging an issue:

1. **Reproduce the issue** - Can you consistently reproduce it?
2. **Check logs** - What do the logs say?
3. **Isolate the problem** - Is it database, API, or logic?
4. **Use debugger** - Set breakpoints and step through code
5. **Check inputs** - Are the inputs what you expect?
6. **Check outputs** - Are the outputs correct?
7. **Test assumptions** - Are your assumptions valid?
8. **Fix and verify** - Does the fix work? Any side effects?

### Essential Tools

- **pdb/ipdb** - Interactive debugging
- **VSCode/PyCharm** - IDE debugging
- **Logging** - Structured, contextual logging
- **Profiling** - cProfile, line_profiler, memory_profiler
- **SQLAlchemy logging** - Query debugging
- **Postman/curl** - API testing

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
