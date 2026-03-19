# ❓ FAQ (Frequently Asked Questions)

> Common questions and answers about Alpha Quant Trader Pro

---

## 📋 Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Trading System](#trading-system)
3. [Technical Analysis](#technical-analysis)
4. [Backtesting](#backtesting)
5. [Data & Performance](#data--performance)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation & Setup

### Q1: What are the system requirements?

**Minimum**:
- Python 3.8+
- PostgreSQL 12+
- 4 GB RAM
- 10 GB disk space

**Recommended**:
- Python 3.10+
- PostgreSQL 14+
- 8 GB RAM
- SSD storage

---

### Q2: I'm getting "Database connection failed" error

**Solutions**:

1. **Check PostgreSQL is running**:
   ```bash
   sudo systemctl status postgresql
   # Or on macOS:
   brew services list | grep postgresql
   ```

2. **Verify connection string** in `.env`:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/stock_market
   ```

3. **Test database connection**:
   ```bash
   psql -U stock_user -d stock_market
   ```

4. **Check database exists**:
   ```bash
   psql -U postgres -l | grep stock_market
   ```

---

### Q3: How do I get a Tushare token?

1. Visit [Tushare Pro](https://tushare.pro/)
2. Register and login
3. Go to "我的账户" → "接口TOKEN"
4. Copy your token
5. Add to `.env`:
   ```bash
   TUSHARE_TOKEN=your_token_here
   ```

**Note**: Free tier has API rate limits. Upgrade for higher limits.

---

### Q4: Can I use this on Windows?

**Yes**, but with WSL (Windows Subsystem for Linux) recommended:

```bash
# Install Ubuntu WSL
wsl --install -d Ubuntu

# Then follow Ubuntu installation instructions
```

Native Windows support is limited due to PostgreSQL and other dependencies.

---

## 💹 Trading System

### Q5: How do I add more cash to my account?

```python
from portfolio_manager import PortfolioCommands

portfolio = PortfolioCommands()
portfolio.add_cash(50000)  # Add 50,000 RMB
```

---

### Q6: What's the difference between realized and unrealized P&L?

**Realized P&L**: Profit/loss from completed trades (you've sold)
**Unrealized P&L**: Profit/loss from current positions (still holding)

```python
summary = portfolio.account_summary()
print(f"Realized P&L: {summary.realized_pnl:.2f}")  # From closed trades
print(f"Unrealized P&L: {summary.unrealized_pnl:.2f}")  # From open positions
```

---

### Q7: How are fees calculated?

**Buy Orders**:
- Commission: 0.03% of transaction amount

**Sell Orders**:
- Commission: 0.03% of transaction amount
- Stamp Duty: 0.1% of transaction amount

```python
# Example: Buy 100 shares at 10.00
buy_amount = 100 * 10.00  # 1,000 RMB
buy_commission = buy_amount * 0.0003  # 0.30 RMB

# Example: Sell 100 shares at 12.00
sell_amount = 100 * 12.00  # 1,200 RMB
sell_commission = sell_amount * 0.0003  # 0.36 RMB
stamp_duty = sell_amount * 0.001  # 1.20 RMB
```

---

### Q8: Can I short sell stocks?

**No**, short selling is not supported in the current version. The system only supports **long positions** (buying and holding).

Short selling requires:
- Margin account
- Additional regulatory compliance
- Different risk management

---

### Q9: How do I close a position completely?

```python
# Get current position
position = portfolio.get_position("600000")

if position:
    # Sell all shares
    portfolio.sell(
        symbol="600000",
        quantity=position.quantity,
        price=current_price
    )
    print("✅ Position closed completely")
```

---

## 📊 Technical Analysis

### Q10: What does the five-dimensional score mean?

Each dimension is scored 0-20 points:

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | ⭐⭐⭐⭐⭐ | Strong Buy - Very high confidence |
| 80-89 | ⭐⭐⭐⭐ | Buy - High confidence |
| 70-79 | ⭐⭐⭐ | Hold/Consider - Medium confidence |
| 60-69 | ⭐⭐ | Watch - Low confidence |
| 0-59 | ⭐ | Avoid/Sell - Very low confidence |

---

### Q11: How do I interpret RSI values?

**RSI (Relative Strength Index)** ranges from 0-100:

- **< 30**: Oversold (potential buy)
- **30-50**: Bearish momentum
- **50-70**: Bullish momentum
- **> 70**: Overbought (potential sell)

---

### Q12: What is a Golden Cross?

**Golden Cross**: When short-term MA crosses above long-term MA (bullish signal)

```python
# Example: 5-day MA crosses above 20-day MA
if sma_5[-1] > sma_20[-1] and sma_5[-2] <= sma_20[-2]:
    print("✅ Golden Cross - Bullish signal")
```

**Death Cross**: When short-term MA crosses below long-term MA (bearish signal)

---

### Q13: How accurate is the analysis system?

The five-dimensional scoring system has been backtested with:

- **Win Rate**: 65-75% on high-scoring stocks (>80 points)
- **Accuracy**: Varies by market conditions
- **Best Performance**: Trending markets
- **Limitations**: Choppy/sideways markets

**Always**:
- Backtest before real trading
- Use stop-loss orders
- Diversify your portfolio
- Never risk more than 2% per trade

---

## 📈 Backtesting

### Q14: What's a good backtest result?

**Excellent**:
- Win Rate: > 65%
- Sharpe Ratio: > 1.5
- Max Drawdown: < 15%
- Annual Return: > 20%

**Good**:
- Win Rate: > 60%
- Sharpe Ratio: > 1.0
- Max Drawdown: < 20%
- Annual Return: > 15%

**Acceptable**:
- Win Rate: > 55%
- Sharpe Ratio: > 0.8
- Max Drawdown: < 25%
- Annual Return: > 10%

---

### Q15: Why is my backtest different from live trading?

**Common reasons**:

1. **Slippage**: Backtest uses exact prices, live trading has price impact
2. **Liquidity**: Backtest assumes unlimited liquidity
3. **Market Impact**: Large orders move the market
4. **Timing**: Backtest uses historical data, live trading has delays
5. **Emotions**: Live trading has psychological factors

**Solution**: Use conservative estimates and paper trade first.

---

### Q16: How far back should I backtest?

**Minimum**: 1 year (to cover different market conditions)

**Recommended**:
- **Trend Strategies**: 3-5 years
- **Mean Reversion**: 2-3 years
- **Volatility Strategies**: 5+ years

**Include**:
- Bull markets
- Bear markets
- Sideways markets

---

## 💾 Data & Performance

### Q17: How often is stock data updated?

**Daily K-line**: Updated after market close (around 17:00-18:00 CST)

**Real-time**: Not supported in current version. Uses end-of-day data.

**Manual Update**:
```python
from stock_market.services import KLineService

kline_service = KLineService(db.get_session())
kline_service.sync_single_kline("600519", "1d")  # Sync specific stock
```

---

### Q18: Can I use my own data source?

**Yes**! The system supports custom data sources:

1. Create adapter class:
   ```python
   from data_sources.base import DataSourceAdapter

   class MyDataSourceAdapter(DataSourceAdapter):
       def get_kline(self, symbol, interval, start_date, end_date):
           # Your implementation
           pass
   ```

2. Register in configuration:
   ```json
   {
     "data_sources": {
       "my_source": {
         "adapter": "path.to.MyDataSourceAdapter",
         "priority": 1
       }
     }
   }
   ```

---

### Q19: How much disk space does the database need?

**Estimates**:

- **100 stocks × 1 year**: ~50 MB
- **100 stocks × 5 years**: ~250 MB
- **3000 stocks × 1 year**: ~1.5 GB
- **3000 stocks × 5 years**: ~7.5 GB

**Growth Rate**: ~300 MB per year for full A-share market.

---

### Q20: Is there a performance benchmark?

**System Performance**:

| Operation | Time | Notes |
|-----------|------|-------|
| Database query (single stock) | < 50ms | With index |
| Technical analysis (120 days) | 100-200ms | All indicators |
| Backtest (1 year) | 2-5 seconds | Single stock |
| Full market sync (3000 stocks) | 30-60 minutes | With throttling |

**Hardware Impact**:
- SSD: 2-3x faster than HDD
- More RAM: Better cache performance
- Multiple cores: Parallel processing

---

## 🔍 Troubleshooting

### Q21: "Insufficient cash" error

**Cause**: Not enough cash for buy order

**Solution**:
```python
# Check available cash
summary = portfolio.account_summary()
print(f"Available cash: {summary.cash:.2f}")

# Either add more cash
portfolio.add_cash(10000)

# Or reduce order size
portfolio.buy(symbol="600000", quantity=50, price=10.00)
```

---

### Q22: "Insufficient shares" error

**Cause**: Trying to sell more than you own

**Solution**:
```python
# Check position first
position = portfolio.get_position("600000")
if position:
    print(f"Available shares: {position.quantity}")

    # Sell only what you have
    portfolio.sell(symbol="600000", quantity=position.quantity, price=12.00)
```

---

### Q23: "Stock not found" error

**Cause**: Stock not in database

**Solution**:
```python
# Sync stock data
from stock_market.services import StockService

stock_service = StockService(db.get_session())
stock_service.sync_all_stocks()  # Sync all stocks

# Or sync specific stock
stock_service.sync_stock("600000")
```

---

### Q24: Analysis returns low scores for all stocks

**Possible causes**:

1. **Bear market**: All stocks trending down
2. **Data issue**: Check if K-line data is up to date
3. **Parameters**: Adjust scoring thresholds

**Solution**:
```python
# Check market condition
from technical_analysis.indicators import MarketTrend

trend = MarketTrend()
market_status = trend.analyze_broad_market(days=60)

print(f"Market Status: {market_status}")

if market_status == "bear":
    print("⚠️ Bear market detected - consider reducing position size")
```

---

### Q25: Backtest is slow

**Optimizations**:

1. **Reduce date range**:
   ```python
   # Instead of 5 years, try 1 year first
   results = engine.run_backtest(..., start_date="2023-01-01", ...)
   ```

2. **Use fewer indicators**:
   ```python
   # Disable unnecessary indicators in configuration
   ```

3. **Upgrade hardware**:
   - Use SSD
   - Increase RAM
   - Use faster CPU

4. **Batch processing**:
   ```python
   # Test multiple stocks in parallel
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=4) as executor:
       results = executor.map(run_backtest_for_stock, stock_list)
   ```

---

## 📞 Getting Help

### Still have questions?

1. **Check the documentation**:
   - [Quick Start](./01-quick-start.md)
   - [User Guide](./README.md)
   - [Trading Guide](./04-trading-guide.md)

2. **Review examples**:
   ```bash
   ls examples/
   python examples/usage.py
   ```

3. **Search issues**:
   - GitHub Issues
   - Community forums

4. **Contact support**:
   - Email: support@alphaquant.com
   - Discord: [Join our server](https://discord.gg/alphaquant)

---

## 🆕 Frequently Updated

This FAQ is regularly updated with common questions from users. If you have a question that's not answered here, please:

1. **Submit an issue** on GitHub
2. **Contact support** via email
3. **Ask in the community** Discord/Telegram

Your feedback helps improve this documentation!

---

**Next**: [Glossary →](./10-glossary.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
