# 🔌 Data Sources Module Guide

> Comprehensive guide for the Data Sources module

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [Usage Examples](#usage-examples)
5. [Adding New Data Sources](#adding-new-data-sources)
6. [Best Practices](#best-practices)
7. [Testing](#testing)

---

## 🎯 Overview

The **Data Sources Module** provides a unified interface for accessing financial market data from multiple external sources.

**Key Features:**
- **Adapter Pattern**: Abstract interface for different data sources
- **Aggregation**: Automatic failover and load balancing
- **Caching**: Built-in caching for performance
- **Rate Limiting**: Respect API rate limits
- **Error Handling**: Robust error handling and retry logic

**Supported Data Sources:**
- **Tushare Pro** - Primary source (Chinese stock market)
- **AKShare** - Fallback source
- **Sina Finance** - Fallback source

---

## 🏛️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────┐
│         DataSourceAggregator            │
│  (Coordinates multiple data sources)    │
└─────────────────────────────────────────┘
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Tushare  │  │  AKShare │  │   Sina   │
│ Adapter  │  │  Adapter │  │  Adapter │
└──────────┘  └──────────┘  └──────────┘
    ↓               ↓               ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Tushare  │  │  AKShare │  │ Sina API │
│   API    │  │   API    │  │          │
└──────────┘  └──────────┘  └──────────┘
```

### Class Hierarchy

```
DataSourceAdapter (Abstract Base Class)
    ├── TushareAdapter
    ├── AKShareAdapter
    └── SinaFinanceAdapter

DataSourceAggregator
    └── DataSourceManager
```

---

## 🧩 Key Components

### 1. DataSourceAdapter (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters."""

    @abstractmethod
    def get_stock_list(self) -> List[dict]:
        """Get list of all available stocks."""
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """Get detailed information for a specific stock."""
        pass

    @abstractmethod
    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 120
    ) -> List[dict]:
        """Get K-line (OHLCV) data for a stock."""
        pass

    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Optional[dict]:
        """Get real-time quote for a stock."""
        pass

    @abstractmethod
    def get_market_overview(self) -> dict:
        """Get overall market statistics."""
        pass
```

### 2. DataSourceAggregator

```python
from typing import List, Optional
from datetime import date

class DataSourceAggregator:
    """Aggregates multiple data sources with failover support."""

    def __init__(self, config: dict):
        """
        Initialize aggregator with configuration.

        Args:
            config: Configuration dict with data source settings
        """
        self.primary_source = self._create_adapter(config['primary'])
        self.fallback_sources = [
            self._create_adapter(src) for src in config['fallback']
        ]
        self.cache_enabled = config.get('cache_enabled', False)
        self.cache_ttl = config.get('cache_ttl', 3600)

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 120
    ) -> List[dict]:
        """
        Get K-line data with automatic failover.

        Tries primary source first, then fallbacks in order.
        """
        sources = [self.primary_source] + self.fallback_sources

        for source in sources:
            try:
                return source.get_kline(symbol, interval, start_date, end_date, limit)
            except Exception as e:
                logger.warning(f"{source.__class__.__name__} failed: {e}")
                continue

        raise DataUnavailableError(f"All data sources failed for {symbol}")

    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """Get stock info with failover."""
        # Similar pattern to get_kline
        pass
```

### 3. TushareAdapter (Example Implementation)

```python
import tushare as ts
from datetime import date
from typing import List, Optional

class TushareAdapter(DataSourceAdapter):
    """Adapter for Tushare Pro API."""

    def __init__(self, token: str):
        """Initialize with Tushare token."""
        self.token = token
        ts.set_token(token)
        self.pro = ts.pro_api()

    def get_stock_list(self) -> List[dict]:
        """Get list of all stocks from Tushare."""
        try:
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Tushare get_stock_list failed: {e}")
            raise

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 120
    ) -> List[dict]:
        """Get K-line data from Tushare."""
        try:
            # Convert symbol format (600519 -> 600519.SH)
            ts_code = self._format_symbol(symbol)

            # Prepare parameters
            params = {
                'ts_code': ts_code,
                'start_date': start_date.strftime('%Y%m%d') if start_date else None,
                'end_date': end_date.strftime('%Y%m%d') if end_date else None,
                'limit': limit
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            # Fetch data
            df = self.pro.daily(**params)

            # Convert to list of dicts
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Tushare get_kline failed for {symbol}: {e}")
            raise

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for Tushare API."""
        if symbol.startswith('6'):
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"{symbol}.SZ"
        else:
            raise ValueError(f"Unknown exchange for symbol: {symbol}")
```

---

## 💡 Usage Examples

### Basic Usage

```python
from data_sources import DataSourceAggregator

# Initialize aggregator
config = {
    'primary': 'tushare',
    'fallback': ['akshare', 'sina'],
    'cache_enabled': True,
    'cache_ttl': 3600
}

aggregator = DataSourceAggregator(config)

# Get K-line data
klines = aggregator.get_kline(
    symbol="600519",
    interval="1d",
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

for kline in klines[:5]:
    print(f"{kline['trade_date']}: {kline['close']}")
```

### With Error Handling

```python
from data_sources import DataSourceAggregator, DataUnavailableError

aggregator = DataSourceAggregator(config)

try:
    klines = aggregator.get_kline("600519", interval="1d")
    print(f"Retrieved {len(klines)} K-lines")
except DataUnavailableError as e:
    logger.error(f"Failed to get data: {e}")
    # Fallback to cached data or default values
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### Batch Data Fetching

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_stock_data(symbol):
    """Fetch data for a single stock."""
    try:
        return aggregator.get_kline(symbol, interval="1d", limit=120)
    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")
        return None

# Fetch data for multiple stocks in parallel
symbols = ["600519", "000001", "601318", "600036"]

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_stock_data, s): s for s in symbols}

    for future in as_completed(futures):
        symbol = futures[future]
        try:
            data = future.result()
            if data:
                print(f"{symbol}: {len(data)} K-lines")
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
```

---

## ➕ Adding New Data Sources

### Step 1: Create Adapter Class

```python
from data_sources.base import DataSourceAdapter

class MyDataSourceAdapter(DataSourceAdapter):
    """Adapter for MyDataSource API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = MyDataSourceClient(api_key)

    def get_stock_list(self) -> List[dict]:
        response = self.client.get_stocks()
        return self._transform_stocks(response)

    def get_kline(self, symbol: str, **kwargs) -> List[dict]:
        response = self.client.get_klines(symbol, **kwargs)
        return self._transform_klines(response)

    def _transform_klines(self, data) -> List[dict]:
        """Transform API response to standard format."""
        return [
            {
                'symbol': item['code'],
                'date': item['date'],
                'open': item['open'],
                'high': item['high'],
                'low': item['low'],
                'close': item['close'],
                'volume': item['volume']
            }
            for item in data
        ]
```

### Step 2: Register Adapter

```python
# data_sources/factory.py

_ADAPTER_REGISTRY = {
    'tushare': TushareAdapter,
    'akshare': AKShareAdapter,
    'sina': SinaFinanceAdapter,
    'mydatasource': MyDataSourceAdapter  # Add new adapter
}

def create_adapter(source_type: str, **kwargs) -> DataSourceAdapter:
    """Factory function to create adapter instances."""
    adapter_class = _ADAPTER_REGISTRY.get(source_type)
    if not adapter_class:
        raise ValueError(f"Unknown data source: {source_type}")
    return adapter_class(**kwargs)
```

### Step 3: Update Configuration

```json
{
  "data_sources": {
    "primary": "mydatasource",
    "fallback": ["tushare", "akshare"],
    "mydatasource": {
      "api_key": "your_api_key_here"
    }
  }
}
```

---

## ✅ Best Practices

### 1. Error Handling

```python
# ✅ DO: Catch specific exceptions
try:
    data = adapter.get_kline(symbol)
except (ConnectionError, TimeoutError) as e:
    logger.warning(f"Network error: {e}")
    # Retry or use fallback
except APIError as e:
    logger.error(f"API error: {e}")
    # Handle API-specific errors
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 2. Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_second: float):
    """Decorator to limit API calls."""
    min_interval = 1.0 / calls_per_second
    last_call = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator

class RateLimitedAdapter(TushareAdapter):
    @rate_limit(calls_per_second=0.5)  # Max 1 call every 2 seconds
    def get_kline(self, symbol, **kwargs):
        return super().get_kline(symbol, **kwargs)
```

### 3. Caching

```python
from functools import lru_cache
import redis

class CachedAdapter(TushareAdapter):
    def __init__(self, token: str, cache_ttl: int = 3600):
        super().__init__(token)
        self.cache = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = cache_ttl

    def get_kline(self, symbol: str, **kwargs) -> List[dict]:
        # Create cache key
        key = f"kline:{symbol}:{kwargs.get('interval', '1d')}"

        # Try cache first
        cached = self.cache.get(key)
        if cached:
            return json.loads(cached)

        # Fetch from API
        data = super().get_kline(symbol, **kwargs)

        # Cache the result
        self.cache.setex(key, self.cache_ttl, json.dumps(data))

        return data
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from data_sources.adapters import TushareAdapter

class TestTushareAdapter:
    """Test TushareAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mock token."""
        return TushareAdapter(token="test_token")

    @patch('tushare.pro_api')
    def test_get_kline_success(self, mock_pro_api, adapter):
        """Test successful K-line retrieval."""
        # Arrange
        mock_df = Mock()
        mock_df.to_dict.return_value = [
            {'trade_date': '20230101', 'close': 100.0}
        ]
        mock_pro_api.return_value.daily.return_value = mock_df

        # Act
        result = adapter.get_kline("600519")

        # Assert
        assert len(result) == 1
        assert result[0]['close'] == 100.0

    @patch('tushare.pro_api')
    def test_get_kline_api_error(self, mock_pro_api, adapter):
        """Test API error handling."""
        # Arrange
        mock_pro_api.return_value.daily.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(Exception):
            adapter.get_kline("600519")
```

### Integration Tests

```python
import pytest
from data_sources import DataSourceAggregator

class TestDataAggregatorIntegration:
    """Integration tests for DataSourceAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator for testing."""
        config = {
            'primary': 'tushare',
            'fallback': ['akshare'],
            'tushare': {'token': 'test_token'}
        }
        return DataSourceAggregator(config)

    def test_aggregator_failover(self, aggregator):
        """Test automatic failover to fallback source."""
        # This test requires actual API access
        # Use pytest.mark.integration decorator
        result = aggregator.get_kline("600519", limit=5)
        assert len(result) > 0
```

---

## 📚 Additional Resources

- 🔧 [Development Setup](../05-development-setup.md)
- 📏 [Coding Standards](../06-coding-standards.md)
- 🧪 [Testing Guide](../07-testing.md)
- 🏗️ [Architecture](../01-architecture.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
