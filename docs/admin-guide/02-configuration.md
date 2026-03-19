# ⚙️ Configuration Guide

> Complete configuration guide for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [Database Configuration](#database-configuration)
5. [Application Configuration](#application-configuration)
6. [Security Configuration](#security-configuration)
7. [Performance Configuration](#performance-configuration)
8. [Advanced Configuration](#advanced-configuration)

---

## 📝 Configuration Overview

### Configuration Sources

The system uses multiple configuration sources with the following priority (highest to lowest):

1. **Environment Variables** - Runtime configuration
2. **Configuration Files** - `config/*.json`
3. **Default Values** - Hardcoded defaults

### Configuration File Structure

```
config/
├── default.json          # Default configuration
├── development.json      # Development overrides
├── production.json       # Production overrides
├── staging.json          # Staging overrides
└── local.json            # Local machine overrides (not in git)
```

### Loading Order

```python
# Configuration loading priority:
# 1. default.json
# 2. {environment}.json (development/production/staging)
# 3. local.json (if exists)
# 4. Environment variables (override all)

from common.config import ConfigManager

config = ConfigManager()
print(config.get('database.url'))
```

---

## 🔧 Environment Variables

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/stock_market` |
| `TUSHARE_TOKEN` | Tushare API token | `your_token_here` |
| `ENVIRONMENT` | Environment name | `production` |
| `SECRET_KEY` | Application secret key | `generated_secure_key` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `REDIS_URL` | `None` | Redis connection string |
| `REDIS_ENABLED` | `false` | Enable Redis caching |
| `DATA_SOURCE` | `tushare` | Primary data source |
| `DATA_SOURCE_FALLBACK` | `akshare` | Fallback data source |

### Setting Environment Variables

**Method 1: .env File** (Recommended for development)
```bash
# .env.production
DATABASE_URL=postgresql://alphaquant:password@localhost:5432/stock_market
TUSHARE_TOKEN=your_token_here
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Method 2: System Environment** (Recommended for production)
```bash
# Add to /etc/environment or systemd service file
export DATABASE_URL="postgresql://alphaquant:password@localhost:5432/stock_market"
export TUSHARE_TOKEN="your_token_here"
```

**Method 3: Docker Environment**
```yaml
# docker-compose.yml
environment:
  - DATABASE_URL=postgresql://alphaquant:password@db:5432/stock_market
  - TUSHARE_TOKEN=${TUSHARE_TOKEN}
  - ENVIRONMENT=production
```

---

## 📄 Configuration Files

### default.json

```json
{
  "database": {
    "url": "",
    "pool_size": 10,
    "max_overflow": 20,
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
    "cache_enabled": false,
    "cache_ttl": 3600
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "handlers": ["file", "console"],
    "file_path": "logs/app.log",
    "max_size": 10485760,
    "backup_count": 5
  },
  "security": {
    "secret_key": "",
    "algorithm": "HS256",
    "token_expire_minutes": 30,
    "cors_enabled": true,
    "cors_origins": ["*"],
    "rate_limit": {
      "enabled": false,
      "requests_per_minute": 60,
      "burst": 10
    }
  }
}
```

### production.json

```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 60,
    "echo": false
  },
  "server": {
    "workers": 8,
    "timeout": 120,
    "log_level": "warning"
  },
  "data_sources": {
    "cache_enabled": true,
    "cache_ttl": 7200
  },
  "logging": {
    "level": "WARNING",
    "format": "json",
    "handlers": ["file"]
  },
  "security": {
    "cors_enabled": true,
    "cors_origins": ["https://yourdomain.com"],
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 120
    }
  }
}
```

---

## 💾 Database Configuration

### Connection String Format

```bash
# Standard format
postgresql://username:password@host:port/database

# With SSL
postgresql://username:password@host:port/database?sslmode=require

# With connection pool parameters
postgresql://username:password@host:port/database?pool_size=20&max_overflow=40
```

### Pool Configuration

```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": true,
    "echo": false,
    "echo_pool": false
  }
}
```

**Parameter Explanation**:
- `pool_size`: Number of connections to keep open (default: 10)
- `max_overflow`: Max additional connections beyond pool_size (default: 20)
- `pool_timeout`: Seconds to wait for connection (default: 30)
- `pool_recycle`: Seconds before recycling connections (default: 3600)
- `pool_pre_ping`: Test connections before use (recommended: true)
- `echo`: Log SQL statements (development only)

### SSL Configuration

```json
{
  "database": {
    "ssl_mode": "require",
    "ssl_cert": "/path/to/client-cert.pem",
    "ssl_key": "/path/to/client-key.pem",
    "ssl_ca": "/path/to/ca-cert.pem",
    "ssl_verify": true
  }
}
```

---

## 🔌 Application Configuration

### Server Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,
    "worker_class": "uvicorn.workers.UvicornWorker",
    "timeout": 120,
    "graceful_timeout": 30,
    "keepalive": 5,
    "log_level": "info",
    "access_log": true,
    "reload": false,
    "reload_dirs": ["api_server", "common"],
    "backlog": 2048,
    "limit_concurrency": 100,
    "timeout_keep_alive": 5
  }
}
```

### CORS Configuration

```json
{
  "security": {
    "cors_enabled": true,
    "cors_origins": [
      "https://yourdomain.com",
      "https://api.yourdomain.com"
    ],
    "cors_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "cors_headers": ["Content-Type", "Authorization"],
    "cors_credentials": true,
    "cors_max_age": 86400
  }
}
```

### Rate Limiting

```json
{
  "security": {
    "rate_limit": {
      "enabled": true,
      "backend": "redis",  // or "memory"
      "requests_per_minute": 60,
      "burst": 10,
      "exempt_ips": ["127.0.0.1", "10.0.0.0/8"],
      "exempt_paths": ["/health", "/metrics"]
    }
  }
}
```

---

## 🔒 Security Configuration

### Secret Key

**Generate Secure Key**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Example: a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890
```

**Configuration**:
```json
{
  "security": {
    "secret_key": "your_generated_key_here",
    "algorithm": "HS256",
    "token_expire_minutes": 30,
    "refresh_token_expire_days": 7
  }
}
```

### Password Policy

```json
{
  "security": {
    "password": {
      "min_length": 8,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_digit": true,
      "require_special": true,
      "max_age_days": 90,
      "history_count": 5
    }
  }
}
```

### Session Configuration

```json
{
  "security": {
    "session": {
      "lifetime_minutes": 60,
      "idle_timeout_minutes": 30,
      "renewal_threshold_minutes": 10,
      "secure": true,
      "httponly": true,
      "samesite": "strict"
    }
  }
}
```

---

## ⚡ Performance Configuration

### Caching Configuration

```json
{
  "cache": {
    "enabled": true,
    "backend": "redis",
    "default_ttl": 3600,
    "namespace": "alphaquant",
    "key_prefix": "cache:",
    "compression": true,
    "compression_level": 6
  }
}
```

### Worker Configuration

```json
{
  "server": {
    "workers": 8,
    "worker_connections": 1000,
    "max_requests": 1000,
    "max_requests_jitter": 50,
    "threads": 2,
    "async_workers": 4
  }
}
```

### Database Optimization

```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_pre_ping": true,
    "pool_recycle": 3600,
    "statement_cache_size": 100,
    "query_cache_size": 500
  }
}
```

---

## 🚀 Advanced Configuration

### Custom Configuration Loader

```python
from common.config import ConfigManager

class CustomConfigManager(ConfigManager):
    def load_custom_config(self):
        """Load custom configuration from database or external source"""
        # Example: Load from database
        db_config = self.load_from_database()
        self.merge_config(db_config)
        return self.config

# Usage
config = CustomConfigManager()
config.load_custom_config()
```

### Dynamic Configuration Updates

```python
from common.config import ConfigManager

config = ConfigManager()

# Update configuration at runtime
config.set('database.pool_size', 30)
config.set('server.workers', 10)

# Reload configuration from files
config.reload()

# Get current configuration
current_config = config.get_all()
```

### Configuration Validation

```python
from common.config import ConfigValidator

validator = ConfigValidator()

# Validate configuration
errors = validator.validate(config.get_all())

if errors:
    for error in errors:
        print(f"Configuration error: {error}")
    exit(1)
```

---

## 📚 Next Steps

- 🚀 [Deployment Guide](./03-deployment.md) - Deploy to production
- 💾 [Database Setup](./04-database-setup.md) - Database configuration
- 📡 [Data Source Setup](./05-data-source-setup.md) - Configure data sources
- 🔍 [Troubleshooting](./09-troubleshooting.md) - Common issues

---

**Next Chapter**: [Deployment Guide →](./03-deployment.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
