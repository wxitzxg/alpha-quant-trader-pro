# 📡 Data Source Setup

> Configure Tushare, AKShare, and other data sources

## 📋 Table of Contents
1. [Tushare Configuration](#tushare-configuration)
2. [AKShare Configuration](#akshare-configuration)
3. [Multi-Source Setup](#multi-source-setup)
4. [Data Synchronization](#data-synchronization)

## 📊 Tushare Configuration

### Register and Get Token
1. Visit https://tushare.pro/
2. Register account
3. Get API token

### Configure in Environment
```bash
TUSHARE_TOKEN=your_token_here
TUSHARE_TIMEOUT=30
TUSHARE_RETRY_TIMES=3
TUSHARE_RETRY_DELAY=5
```

### Tier Comparison
| Tier | Price | Calls/Min | Daily Limit |
|------|-------|-----------|-------------|
| Free | ¥0 | 20 | 500 |
| Basic | ¥500/yr | 120 | 5,000 |
| Pro | ¥1500/yr | 240 | 10,000 |
| VIP | ¥3000/yr | 480 | 20,000 |

## 📈 AKShare Configuration

### Installation
```bash
pip install akshare
```

### Enable as Fallback
```bash
DATA_SOURCE_FALLBACK=akshare
AKSHARE_TIMEOUT=30
```

## 🔀 Multi-Source Setup

### Primary and Fallback
```json
{
  "data_sources": {
    "primary": "tushare",
    "fallback": ["akshare"],
    "auto_failover": true,
    "retry_on_failure": true
  }
}
```

### Data Source Priority
1. Tushare (primary)
2. AKShare (fallback)
3. Sina Finance (fallback)

## 🔄 Data Synchronization

### Cron Jobs
```bash
# Daily stock list sync at 6 PM
0 18 * * * alphaquant cd /opt/alpha-quant && source venv/bin/activate && python scripts/sync_stocks.py

# Daily K-line sync after market close
0 18 * * 1-5 alphaquant python scripts/sync_klines.py --interval 1d

# Weekly K-line sync on Friday
0 19 * * 5 alphaquant python scripts/sync_klines.py --interval 1w

# Monthly K-line sync on month end
0 19 28-31 * * alphaquant [ "$(date +\%d -d tomorrow)" = "01" ] && python scripts/sync_klines.py --interval 1M
```

### Sync Script Example
```python
#!/usr/bin/env python
from stock_market.services import StockService, KLineService
from common.database import DatabaseManager

db = DatabaseManager(os.getenv('DATABASE__URL'))
stock_service = StockService(db.get_session())

# Sync all stocks
stock_service.sync_all_stocks()

# Sync K-lines for active stocks
active_stocks = stock_service.get_active_stocks()
for stock in active_stocks[:100]:  # Limit to 100 stocks per run
    kline_service = KLineService(db.get_session())
    kline_service.sync_single_kline(stock.symbol, "1d")
```
