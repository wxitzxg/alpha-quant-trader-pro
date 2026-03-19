# 🎯 Your First Trade

> Complete beginner tutorial for executing your first trade

---

## 📋 Table of Contents

1. [Before You Start](#before-you-start)
2. [Understanding Trading Concepts](#understanding-trading-concepts)
3. [Step-by-Step First Trade](#step-by-step-first-trade)
4. [Viewing Your Results](#viewing-your-results)
5. [Practice Exercises](#practice-exercises)
6. [Next Steps](#next-steps)

---

## ⚠️ Before You Start

### Important Notes for Beginners

**This is a simulated trading tutorial**. If you're using real money:
- ⚠️ **Start with small amounts** (recommend 1,000-10,000 RMB)
- ⚠️ **Never risk more than 2%** of your total capital per trade
- ⚠️ **Paper trade first** - practice with the backtest system
- ⚠️ **Set stop-loss orders** to limit potential losses
- ⚠️ **Keep a trading journal** to track your decisions

### Prerequisites

- ✅ Alpha Quant Trader Pro installed (see [Installation Guide](./02-installation.md))
- ✅ Database initialized and running
- ✅ Tushare token configured in `.env`
- ✅ Basic understanding of stock trading concepts

---

## 📖 Understanding Trading Concepts

### Key Terms

| Term | Definition | Example |
|------|------------|---------|
| **Symbol** | Stock code | 600000 (浦发银行) |
| **Quantity** | Number of shares | 100 shares |
| **Price** | Price per share | 10.00 RMB |
| **Position** | Your holdings | 100 shares of 600000 |
| **Cost** | Total amount paid | 1,000 RMB |
| **Market Value** | Current value | 1,200 RMB |
| **P&L** | Profit and Loss | +200 RMB |

### Trade Types

#### 1. Buy Order (Opening a Position)
- **Purpose**: Acquire shares of a stock
- **Effect**: Increases your position, decreases cash
- **Fee**: Typically 0.03% commission

#### 2. Sell Order (Closing a Position)
- **Purpose**: Sell shares you own
- **Effect**: Decreases your position, increases cash
- **Fee**: Typically 0.03% commission + 0.1% stamp duty

### Position Management

**Long Position**: You own shares (bought and holding)
- Profit when price goes up
- Loss when price goes down

**No Position**: You own zero shares
- No exposure to price movements

**Short Position**: Not supported in this system (requires margin account)

---

## 🚀 Step-by-Step First Trade

### Step 1: Initialize Your Portfolio

```python
from portfolio_manager import PortfolioCommands

# Create portfolio manager instance
portfolio = PortfolioCommands()

# Add initial capital (100,000 RMB)
portfolio.add_cash(100000)

print("✅ Portfolio initialized with 100,000 RMB capital!")
```

**What This Does**:
- Creates a new portfolio account
- Adds 100,000 RMB as starting capital
- Initializes all tracking systems

---

### Step 2: Research a Stock

Let's research 浦发银行 (600000):

```python
from common.database import DatabaseManager
from stock_market.services import StockService, KLineService

# Initialize database and services
db = DatabaseManager("postgresql://stock_user:your_password@localhost:5432/stock_market")
stock_service = StockService(db.get_session())

# Get stock information
stock_info = stock_service.get_stock("600000")
print(f"Stock Name: {stock_info.name}")
print(f"Industry: {stock_info.industry}")
print(f"List Date: {stock_info.list_date}")
print(f"Current Status: {stock_info.status}")

# Get recent K-line data
kline_service = KLineService(db.get_session())
recent_klines = kline_service.query_klines(
    symbol="600000",
    interval="1d",
    limit=5
)

print("\nRecent Price Data:")
for kline in recent_klines:
    print(f"Date: {kline.date}, Close: {kline.close}, Volume: {kline.volume}")
```

---

### Step 3: Execute Your First Buy Order

```python
# Buy 100 shares of 浦发银行 (600000) at 10.00 RMB per share
result = portfolio.buy(
    symbol="600000",
    quantity=100,
    price=10.00
)

print("✅ Buy order executed!")
print(f"Stock: {result.stock_name}")
print(f"Quantity: {result.quantity} shares")
print(f"Price: {result.price:.2f} RMB per share")
print(f"Total Cost: {result.total_cost:.2f} RMB")
print(f"Commission Fee: {result.commission_fee:.2f} RMB")
```

**What Happens**:
1. System checks you have enough cash
2. Executes the buy order
3. Adds 100 shares to your position
4. Deducts 1,000 RMB + fees from your cash
5. Records the transaction

---

### Step 4: View Your Position

```python
# Get all your current positions
positions = portfolio.get_positions()

print("\nYour Current Positions:")
print("-" * 50)

for pos in positions:
    print(f"Stock: {pos.stock_name} ({pos.symbol})")
    print(f"Shares Held: {pos.quantity}")
    print(f"Average Cost: {pos.average_cost:.2f} RMB")
    print(f"Current Price: {pos.current_price:.2f} RMB")
    print(f"Market Value: {pos.market_value:.2f} RMB")
    print(f"Unrealized P&L: {pos.unrealized_pnl:.2f} RMB")
    print(f"Unrealized P&L %: {pos.unrealized_pnl_pct:.2f}%")
    print("-" * 50)

# Get account summary
summary = portfolio.account_summary()
print("\nAccount Summary:")
print(f"Total Cash: {summary.cash:.2f} RMB")
print(f"Total Market Value: {summary.total_market_value:.2f} RMB")
print(f"Total Assets: {summary.total_assets:.2f} RMB")
print(f"Unrealized P&L: {summary.unrealized_pnl:.2f} RMB")
```

---

### Step 5: Wait for Price Movement

In real trading, you'd wait for the stock price to move. For this tutorial, let's simulate a price increase to 12.00 RMB:

```python
# Update the current price (simulated)
portfolio.update_current_price("600000", 12.00)

print("✅ Simulated price update to 12.00 RMB")
```

---

### Step 6: Execute Your First Sell Order

```python
# Sell 50 shares at 12.00 RMB per share
result = portfolio.sell(
    symbol="600000",
    quantity=50,
    price=12.00
)

print("✅ Sell order executed!")
print(f"Stock: {result.stock_name}")
print(f"Quantity Sold: {result.quantity} shares")
print(f"Sale Price: {result.price:.2f} RMB per share")
print(f"Total Revenue: {result.total_revenue:.2f} RMB")
print(f"Commission Fee: {result.commission_fee:.2f} RMB")
print(f"Realized P&L: {result.realized_pnl:.2f} RMB")
```

**What Happens**:
1. System checks you have enough shares
2. Executes the sell order
3. Removes 50 shares from your position
4. Adds (50 × 12.00) - fees to your cash
5. Records realized profit/loss
6. Updates remaining position

---

### Step 7: Review Your Trade

```python
# Get transaction history
transactions = portfolio.get_transaction_history()

print("\nYour Transaction History:")
print("-" * 60)

for txn in transactions:
    print(f"Date: {txn.timestamp}")
    print(f"Type: {txn.transaction_type}")
    print(f"Stock: {txn.stock_name} ({txn.symbol})")
    print(f"Quantity: {txn.quantity}")
    print(f"Price: {txn.price:.2f} RMB")
    print(f"Amount: {txn.amount:.2f} RMB")
    if txn.realized_pnl is not None:
        print(f"P&L: {txn.realized_pnl:.2f} RMB")
    print("-" * 60)

# Get final account status
summary = portfolio.account_summary()
print("\nFinal Account Status:")
print(f"Remaining Cash: {summary.cash:.2f} RMB")
print(f"Remaining Shares: {positions[0].quantity if positions else 0}")
print(f"Total Assets: {summary.total_assets:.2f} RMB")
print(f"Realized P&L: {summary.realized_pnl:.2f} RMB")
print(f"Unrealized P&L: {summary.unrealized_pnl:.2f} RMB")
```

---

## 📊 Viewing Your Results

### Account Dashboard

```python
# Comprehensive account view
dashboard = portfolio.get_dashboard()

print("=" * 60)
print("ACCOUNT DASHBOARD")
print("=" * 60)

print(f"\n💰 CASH & ASSETS")
print(f"Cash Balance: {dashboard['cash']:.2f} RMB")
print(f"Total Market Value: {dashboard['market_value']:.2f} RMB")
print(f"Total Assets: {dashboard['total_assets']:.2f} RMB")

print(f"\n📈 PERFORMANCE")
print(f"Realized P&L: {dashboard['realized_pnl']:.2f} RMB")
print(f"Unrealized P&L: {dashboard['unrealized_pnl']:.2f} RMB")
print(f"Total P&L: {dashboard['total_pnl']:.2f} RMB")
print(f"Return Rate: {dashboard['return_rate']:.2f}%")

print(f"\n📊 POSITIONS")
for pos in dashboard['positions']:
    print(f"\n  {pos['stock_name']} ({pos['symbol']})")
    print(f"    Shares: {pos['quantity']}")
    print(f"    Avg Cost: {pos['average_cost']:.2f}")
    print(f"    Current: {pos['current_price']:.2f}")
    print(f"    Market Value: {pos['market_value']:.2f}")
    print(f"    P&L: {pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_pct']:.2f}%)")

print("=" * 60)
```

---

## 🎓 Practice Exercises

### Exercise 1: Complete a Round-Trip Trade

**Goal**: Buy and sell the same stock completely

```python
portfolio = PortfolioCommands()
portfolio.add_cash(50000)

# Buy 200 shares
portfolio.buy(symbol="600001", quantity=200, price=8.50)

# Check position
positions = portfolio.get_positions()
print(f"Position after buy: {positions[0].quantity} shares")

# Sell all shares
portfolio.sell(symbol="600001", quantity=200, price=9.20)

# Check final status
summary = portfolio.account_summary()
print(f"Final cash: {summary.cash:.2f}")
print(f"Realized P&L: {summary.realized_pnl:.2f}")
```

**Expected Result**: Realized P&L should be approximately 1,400 RMB (before fees)

---

### Exercise 2: Multiple Positions

**Goal**: Manage multiple stocks simultaneously

```python
portfolio = PortfolioCommands()
portfolio.add_cash(100000)

# Buy three different stocks
portfolio.buy(symbol="600000", quantity=100, price=10.00)  # 浦发银行
portfolio.buy(symbol="600519", quantity=50, price=150.00)   # 贵州茅台
portfolio.buy(symbol="000001", quantity=200, price=12.00)   # 平安银行

# View all positions
positions = portfolio.get_positions()
for pos in positions:
    print(f"{pos.stock_name}: {pos.quantity} shares, P&L: {pos.unrealized_pnl:.2f}")

# Sell one position
portfolio.sell(symbol="600000", quantity=50, price=11.00)

# View updated positions
print("\nAfter selling 50 shares of 浦发银行:")
positions = portfolio.get_positions()
for pos in positions:
    print(f"{pos.stock_name}: {pos.quantity} shares")
```

---

### Exercise 3: Price Movement Simulation

**Goal**: Track P&L as prices change

```python
portfolio = PortfolioCommands()
portfolio.add_cash(50000)
portfolio.buy(symbol="600000", quantity=100, price=10.00)

# Initial status
summary = portfolio.account_summary()
print(f"Initial: {summary.unrealized_pnl:.2f} RMB")

# Simulate price increase to 11.00
portfolio.update_current_price("600000", 11.00)
summary = portfolio.account_summary()
print(f"After +10%: {summary.unrealized_pnl:.2f} RMB")

# Simulate price decrease to 9.50
portfolio.update_current_price("600000", 9.50)
summary = portfolio.account_summary()
print(f"After -5%: {summary.unrealized_pnl:.2f} RMB")
```

---

## 📚 Next Steps

### Recommended Learning Path

1. **Master Position Management**
   - Read: [Portfolio Management Guide](./07-portfolio-management.md)
   - Practice: Manage 5+ different positions

2. **Learn Technical Analysis**
   - Read: [Technical Analysis Guide](./05-analysis-guide.md)
   - Practice: Analyze 10+ stocks using the five-dimensional system

3. **Understand Trading Strategies**
   - Read: [Three Strategies Guide](./08-strategy-guide.md)
   - Practice: Backtest each strategy on historical data

4. **Use the Backtest System**
   - Read: [Backtest System Guide](./06-backtest-guide.md)
   - Practice: Test your strategies before real trading

---

## 💡 Tips for Your First Real Trades

### Before Trading
- ✅ Paper trade for at least 1 month
- ✅ Understand the stock's fundamentals
- ✅ Set clear entry and exit criteria
- ✅ Determine your position size (max 2% risk)

### During Trading
- ✅ Stick to your plan
- ✅ Don't chase momentum
- ✅ Use stop-loss orders
- ✅ Keep emotions out of trading

### After Trading
- ✅ Review every trade
- ✅ Track what worked and what didn't
- ✅ Adjust your strategy based on results
- ✅ Keep a trading journal

---

## 🆘 Common Issues

### Issue: "Insufficient Cash" Error

**Cause**: Not enough cash for the buy order

**Solution**:
```python
# Check your cash first
summary = portfolio.account_summary()
print(f"Available cash: {summary.cash}")

# Either add more cash
portfolio.add_cash(10000)

# Or reduce your order size
portfolio.buy(symbol="600000", quantity=50, price=10.00)  # Smaller order
```

---

### Issue: "Insufficient Shares" Error

**Cause**: Trying to sell more shares than you own

**Solution**:
```python
# Check your position first
positions = portfolio.get_positions()
for pos in positions:
    if pos.symbol == "600000":
        print(f"Available shares: {pos.quantity}")
        break

# Sell only what you have
portfolio.sell(symbol="600000", quantity=50, price=12.00)
```

---

### Issue: "Stock Not Found" Error

**Cause**: Invalid stock symbol or stock not in database

**Solution**:
```python
# Sync stock data first
from stock_market.services import StockService
stock_service = StockService(db.get_session())
stock_service.sync_all_stocks()

# Verify the stock exists
stock = stock_service.get_stock("600000")
if stock:
    print(f"Stock found: {stock.name}")
else:
    print("Stock not found in database")
```

---

## 📖 Additional Resources

- 📘 [Trading System Guide](./04-trading-guide.md) - Complete trading features
- 📗 [Technical Analysis Guide](./05-analysis-guide.md) - Analysis tools
- 📙 [Backtest System Guide](./06-backtest-guide.md) - Strategy testing
- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Trading strategies

---

**Next Chapter**: [Trading System Guide →](./04-trading-guide.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
