# 🔌 API Reference

> Complete API documentation for Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Error Responses](#error-responses)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Stock Endpoints](#stock-endpoints)
   - [K-Line Endpoints](#k-line-endpoints)
   - [Portfolio Endpoints](#portfolio-endpoints)
   - [Analysis Endpoints](#analysis-endpoints)
   - [Backtest Endpoints](#backtest-endpoints)
   - [Account Endpoints](#account-endpoints)
6. [WebSocket Endpoints](#websocket-endpoints)
7. [API Examples](#api-examples)

---

## 🔐 Authentication

### Token Authentication

All API requests require authentication using JWT tokens.

**Get Access Token:**

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Use Token in Requests:**
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Token Refresh

```bash
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>

Response:
{
  "access_token": "new_access_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🌐 Base URL

```
Development: http://localhost:8000
Production: https://api.alphaquant.com
```

All endpoints are prefixed with `/api/v1/`.

---

## ❌ Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "value"
    }
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Example Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for 2 fields",
    "details": {
      "symbol": "Symbol must be 6 characters",
      "quantity": "Quantity must be positive"
    }
  }
}
```

---

## ⏱️ Rate Limiting

### Rate Limits

- **Default**: 60 requests per minute per IP
- **Authenticated**: 120 requests per minute per user
- **Premium**: 600 requests per minute per user

### Rate Limit Headers

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 119
X-RateLimit-Reset: 1677649455
Retry-After: 60
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 120,
      "remaining": 0,
      "reset": 1677649455
    }
  }
}
```

---

## 🔗 Endpoints

### Stock Endpoints

#### Get All Stocks

```bash
GET /api/v1/stocks
Authorization: Bearer <token>

Query Parameters:
- page: integer (default: 1)
- page_size: integer (default: 20, max: 100)
- industry: string (optional)
- exchange: string (optional)

Response (200 OK):
{
  "data": [
    {
      "symbol": "600519",
      "name": "贵州茅台",
      "industry": "白酒",
      "exchange": "SH",
      "market_cap": 2000000000000,
      "current_price": 1800.50,
      "change_percent": 1.25,
      "listed_date": "2001-08-27"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 4500,
    "total_pages": 225
  }
}
```

#### Get Stock by Symbol

```bash
GET /api/v1/stocks/{symbol}
Authorization: Bearer <token>

Response (200 OK):
{
  "symbol": "600519",
  "name": "贵州茅台",
  "industry": "白酒",
  "exchange": "SH",
  "market_cap": 2000000000000,
  "current_price": 1800.50,
  "change_percent": 1.25,
  "pe_ratio": 35.2,
  "pb_ratio": 8.5,
  "dividend_yield": 1.2,
  "listed_date": "2001-08-27",
  "updated_at": "2023-03-18T10:30:00Z"
}

Response (404 NOT FOUND):
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Stock not found: INVALID"
  }
}
```

#### Sync Stock Data

```bash
POST /api/v1/stocks/{symbol}/sync
Authorization: Bearer <token>

Response (200 OK):
{
  "message": "Stock synced successfully",
  "symbol": "600519",
  "synced_at": "2023-03-18T10:30:00Z"
}
```

---

### K-Line Endpoints

#### Get K-Line Data

```bash
GET /api/v1/klines/{symbol}
Authorization: Bearer <token>

Query Parameters:
- interval: string (default: "1d", options: 1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)
- start_date: string (format: YYYY-MM-DD, optional)
- end_date: string (format: YYYY-MM-DD, optional)
- limit: integer (default: 120, max: 1000)

Response (200 OK):
{
  "symbol": "600519",
  "interval": "1d",
  "data": [
    {
      "date": "2023-03-18",
      "open": 1795.00,
      "high": 1815.50,
      "low": 1790.00,
      "close": 1805.25,
      "volume": 3500000,
      "amount": 6300000000,
      "change_percent": 0.56
    },
    {
      "date": "2023-03-17",
      "open": 1785.00,
      "high": 1800.00,
      "low": 1780.50,
      "close": 1795.00,
      "volume": 3200000,
      "amount": 5700000000,
      "change_percent": 0.53
    }
  ],
  "count": 120
}
```

#### Bulk Sync K-Line Data

```bash
POST /api/v1/klines/sync
Authorization: Bearer <token>

Request Body:
{
  "symbols": ["600519", "000001"],
  "interval": "1d",
  "start_date": "2023-01-01",
  "end_date": "2023-03-18"
}

Response (202 Accepted):
{
  "task_id": "task_12345",
  "message": "Sync task started",
  "status": "processing",
  "estimated_time": 300
}
```

---

### Portfolio Endpoints

#### Get Positions

```bash
GET /api/v1/portfolio/positions
Authorization: Bearer <token>

Query Parameters:
- page: integer (default: 1)
- page_size: integer (default: 20)

Response (200 OK):
{
  "data": [
    {
      "symbol": "600519",
      "quantity": 100,
      "avg_cost": 1750.00,
      "current_price": 1805.25,
      "market_value": 180525.00,
      "profit_loss": 5525.00,
      "profit_loss_percent": 3.16,
      "created_at": "2023-01-15T09:30:00Z",
      "updated_at": "2023-03-18T10:30:00Z"
    }
  ],
  "summary": {
    "total_positions": 5,
    "total_market_value": 500000.00,
    "total_profit_loss": 25000.00,
    "total_profit_loss_percent": 5.0
  }
}
```

#### Create Position

```bash
POST /api/v1/portfolio/positions
Authorization: Bearer <token>

Request Body:
{
  "symbol": "600519",
  "quantity": 100,
  "price": 1800.00,
  "transaction_type": "buy"
}

Response (201 Created):
{
  "symbol": "600519",
  "quantity": 100,
  "avg_cost": 1800.00,
  "current_price": 1805.25,
  "market_value": 180525.00,
  "profit_loss": 525.00,
  "created_at": "2023-03-18T10:30:00Z"
}

Response (400 BAD REQUEST):
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Insufficient balance",
    "details": {
      "required": 180000,
      "available": 100000
    }
  }
}
```

#### Close Position

```bash
DELETE /api/v1/portfolio/positions/{symbol}
Authorization: Bearer <token>

Query Parameters:
- quantity: integer (optional, default: all)

Response (200 OK):
{
  "message": "Position closed successfully",
  "symbol": "600519",
  "quantity_closed": 100,
  "profit_loss": 5525.00,
  "closed_at": "2023-03-18T10:30:00Z"
}
```

#### Get Transactions

```bash
GET /api/v1/portfolio/transactions
Authorization: Bearer <token>

Query Parameters:
- symbol: string (optional)
- transaction_type: string (optional, buy/sell)
- start_date: string (optional)
- end_date: string (optional)
- page: integer (default: 1)
- page_size: integer (default: 20)

Response (200 OK):
{
  "data": [
    {
      "id": "txn_12345",
      "symbol": "600519",
      "quantity": 100,
      "price": 1800.00,
      "amount": 180000.00,
      "transaction_type": "buy",
      "status": "completed",
      "created_at": "2023-03-18T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### Analysis Endpoints

#### Get Stock Analysis

```bash
GET /api/v1/analysis/{symbol}
Authorization: Bearer <token>

Query Parameters:
- days: integer (default: 120, max: 365)

Response (200 OK):
{
  "symbol": "600519",
  "name": "贵州茅台",
  "analysis_date": "2023-03-18",
  "overall_score": 85.5,
  "dimensions": {
    "trend": {
      "score": 90,
      "rating": "strong_upward",
      "indicators": {
        "ma20": "above",
        "ma60": "above",
        "ma120": "above"
      }
    },
    "pattern": {
      "score": 85,
      "rating": "bullish",
      "patterns": ["golden_cross", "cup_handle"]
    },
    "position": {
      "score": 80,
      "rating": "good",
      "support_levels": [1750, 1700],
      "resistance_levels": [1850, 1900]
    },
    "momentum": {
      "score": 88,
      "rating": "strong",
      "indicators": {
        "rsi": 65,
        "macd": "positive",
        "volume_ratio": 1.2
      }
    },
    "trigger": {
      "score": 84,
      "rating": "ready",
      "signals": ["breakout", "volume_spike"]
    }
  },
  "recommendation": {
    "action": "buy",
    "confidence": "high",
    "target_price": 1900,
    "stop_loss": 1750
  },
  "indicators": {
    "moving_averages": {
      "ma5": 1802.50,
      "ma10": 1795.30,
      "ma20": 1785.60,
      "ma60": 1760.20,
      "ma120": 1740.80
    },
    "oscillators": {
      "rsi": 65.3,
      "kdj": {
        "k": 75.2,
        "d": 68.5,
        "j": 88.6
      },
      "macd": {
        "diff": 15.2,
        "dea": 10.5,
        "macd": 4.7
      }
    },
    "volatility": {
      "bollinger_bands": {
        "upper": 1850.50,
        "middle": 1800.25,
        "lower": 1750.00
      },
      "atr": 35.5
    }
  }
}
```

#### Get Multiple Stocks Analysis

```bash
POST /api/v1/analysis/batch
Authorization: Bearer <token>

Request Body:
{
  "symbols": ["600519", "000001", "601318"],
  "days": 120
}

Response (200 OK):
{
  "results": [
    {
      "symbol": "600519",
      "overall_score": 85.5,
      "recommendation": "buy"
    },
    {
      "symbol": "000001",
      "overall_score": 72.3,
      "recommendation": "hold"
    }
  ]
}
```

#### Get Strategy Signals

```bash
GET /api/v1/analysis/strategies/{strategy_name}/signals
Authorization: Bearer <token>

Path Parameters:
- strategy_name: vcp, nine_turn, divergence

Query Parameters:
- date: string (optional, format: YYYY-MM-DD)

Response (200 OK):
{
  "strategy": "vcp",
  "date": "2023-03-18",
  "signals": [
    {
      "symbol": "600519",
      "name": "贵州茅台",
      "signal_type": "buy",
      "strength": "strong",
      "price": 1805.25,
      "pattern_details": {
        "vcp_stage": 2,
        "consolidation_days": 15,
        "volume_dry_up": true
      }
    }
  ]
}
```

---

### Backtest Endpoints

#### Run Backtest

```bash
POST /api/v1/backtest/run
Authorization: Bearer <token>

Request Body:
{
  "strategy": "vcp",
  "symbols": ["600519", "000001"],
  "start_date": "2022-01-01",
  "end_date": "2023-01-01",
  "initial_capital": 100000,
  "parameters": {
    "risk_per_trade": 0.02,
    "max_positions": 5,
    "commission_rate": 0.0003
  }
}

Response (202 Accepted):
{
  "task_id": "backtest_12345",
  "status": "processing",
  "estimated_time": 60
}
```

#### Get Backtest Results

```bash
GET /api/v1/backtest/results/{task_id}
Authorization: Bearer <token>

Response (200 OK):
{
  "task_id": "backtest_12345",
  "status": "completed",
  "strategy": "vcp",
  "period": {
    "start": "2022-01-01",
    "end": "2023-01-01"
  },
  "performance": {
    "total_return": 35.2,
    "annual_return": 35.2,
    "max_drawdown": -12.5,
    "sharpe_ratio": 1.8,
    "win_rate": 68.5,
    "profit_factor": 2.3,
    "total_trades": 45,
    "winning_trades": 31,
    "losing_trades": 14
  },
  "trades": [
    {
      "symbol": "600519",
      "entry_date": "2022-03-15",
      "entry_price": 1750.00,
      "exit_date": "2022-05-20",
      "exit_price": 1920.00,
      "quantity": 50,
      "profit_loss": 8500.00,
      "profit_loss_percent": 9.71
    }
  ],
  "equity_curve": [
    {"date": "2022-01-01", "value": 100000},
    {"date": "2022-01-02", "value": 100150}
  ]
}
```

#### Optimize Parameters

```bash
POST /api/v1/backtest/optimize
Authorization: Bearer <token>

Request Body:
{
  "strategy": "vcp",
  "symbols": ["600519"],
  "start_date": "2022-01-01",
  "end_date": "2023-01-01",
  "parameter_ranges": {
    "risk_per_trade": [0.01, 0.05],
    "max_positions": [3, 10]
  },
  "optimization_metric": "sharpe_ratio"
}

Response (202 Accepted):
{
  "task_id": "optimize_12345",
  "status": "processing"
}
```

---

### Account Endpoints

#### Get Account Info

```bash
GET /api/v1/account
Authorization: Bearer <token>

Response (200 OK):
{
  "user_id": "user_12345",
  "username": "trader1",
  "email": "trader1@example.com",
  "account_type": "premium",
  "balance": 100000.00,
  "equity": 125000.00,
  "margin": 25000.00,
  "risk_level": "moderate",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-03-18T10:30:00Z"
}
```

#### Update Account Settings

```bash
PUT /api/v1/account/settings
Authorization: Bearer <token>

Request Body:
{
  "risk_level": "conservative",
  "notification_preferences": {
    "email": true,
    "sms": false,
    "push": true
  },
  "auto_sync": true
}

Response (200 OK):
{
  "message": "Settings updated successfully"
}
```

---

## 🔌 WebSocket Endpoints

### Real-time Price Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.alphaquant.com/ws/prices');

// Subscribe to symbols
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['600519', '000001']
  }));
};

// Receive price updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
  // {
  //   "symbol": "600519",
  //   "price": 1805.25,
  //   "change": 5.25,
  //   "change_percent": 0.29,
  //   "volume": 150000,
  //   "timestamp": "2023-03-18T10:30:00Z"
  // }
};

// Unsubscribe
ws.send(JSON.stringify({
  action: 'unsubscribe',
  symbols: ['600519']
}));
```

### Trading Signals

```javascript
const ws = new WebSocket('wss://api.alphaquant.com/ws/signals');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    strategies: ['vcp', 'nine_turn']
  }));
};

ws.onmessage = (event) => {
  const signal = JSON.parse(event.data);
  console.log('New signal:', signal);
  // {
  //   "strategy": "vcp",
  //   "symbol": "600519",
  //   "signal_type": "buy",
  //   "strength": "strong",
  //   "price": 1805.25,
  //   "timestamp": "2023-03-18T10:30:00Z"
  // }
};
```

---

## 💡 API Examples

### Python Example

```python
import requests

class AlphaQuantClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        """Login and get access token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def _headers(self):
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_stock(self, symbol):
        """Get stock information."""
        response = requests.get(
            f"{self.base_url}/api/v1/stocks/{symbol}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_analysis(self, symbol, days=120):
        """Get technical analysis."""
        response = requests.get(
            f"{self.base_url}/api/v1/analysis/{symbol}",
            headers=self._headers(),
            params={"days": days}
        )
        response.raise_for_status()
        return response.json()

    def buy_stock(self, symbol, quantity, price):
        """Buy stock."""
        response = requests.post(
            f"{self.base_url}/api/v1/portfolio/positions",
            headers=self._headers(),
            json={
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "transaction_type": "buy"
            }
        )
        response.raise_for_status()
        return response.json()

    def get_positions(self):
        """Get all positions."""
        response = requests.get(
            f"{self.base_url}/api/v1/portfolio/positions",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AlphaQuantClient()
client.login("username", "password")

# Get stock info
stock = client.get_stock("600519")
print(f"{stock['name']}: {stock['current_price']}")

# Get analysis
analysis = client.get_analysis("600519")
print(f"Score: {analysis['overall_score']}")
print(f"Recommendation: {analysis['recommendation']['action']}")

# Buy stock
position = client.buy_stock("600519", quantity=100, price=1800)
print(f"Position created: {position['market_value']}")
```

### cURL Examples

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Get stock (with token)
curl -X GET http://localhost:8000/api/v1/stocks/600519 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analysis
curl -X GET "http://localhost:8000/api/v1/analysis/600519?days=120" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Buy stock
curl -X POST http://localhost:8000/api/v1/portfolio/positions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "quantity": 100,
    "price": 1800,
    "transaction_type": "buy"
  }'

# Run backtest
curl -X POST http://localhost:8000/api/v1/backtest/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "vcp",
    "symbols": ["600519"],
    "start_date": "2022-01-01",
    "end_date": "2023-01-01",
    "initial_capital": 100000
  }'
```

---

## 📚 Next Steps

- 📖 [Module Guides](./04-module-guide/) - Module-specific documentation
- 🧪 [Testing Guide](./07-testing.md) - Testing best practices
- 🐛 [Debugging Guide](./09-debugging.md) - Debugging techniques
- 🏗️ [Architecture](./01-architecture.md) - System architecture

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
