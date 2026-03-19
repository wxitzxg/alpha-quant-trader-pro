# 💹 Trading System Guide

> Complete guide to the trading system features

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Account Management](#account-management)
3. [Position Management](#position-management)
4. [Transaction Management](#transaction-management)
5. [Order Execution](#order-execution)
6. [Fee Structure](#fee-structure)
7. [Risk Management](#risk-management)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

The trading system provides a comprehensive platform for managing stock investments:

### Core Features

- ✅ **Account Management** - Cash, assets, portfolio tracking
- ✅ **Position Management** - Buy, sell, track holdings
- ✅ **Transaction History** - Complete trade records
- ✅ **Real-time P&L** - Profit and loss tracking
- ✅ **Fee Calculation** - Automatic commission and tax calculation
- ✅ **Portfolio Analysis** - Asset allocation and performance metrics

### System Architecture

```
┌─────────────────────────────────────────┐
│         PortfolioCommands               │
│  - High-level trading interface          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  - PositionService                       │
│  - TransactionService                    │
│  - AccountService                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Repository Layer                 │
│  - PositionRepository                    │
│  - TransactionRepository                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Database (PostgreSQL)            │
│  - positions, transactions, accounts     │
└─────────────────────────────────────────┘
```

---

## 💰 Account Management

### Initializing Your Account

```python
from portfolio_manager import PortfolioCommands

# Create portfolio instance
portfolio = PortfolioCommands()

# Add initial capital
portfolio.add_cash(100000)  # Add 100,000 RMB

print("✅ Account initialized with 100,000 RMB")
```

### Adding/Withdrawing Cash

```python
# Add more cash
portfolio.add_cash(50000)
print("Added 50,000 RMB")

# Withdraw cash
portfolio.withdraw_cash(20000)
print("Withdrew 20,000 RMB")
```

### Viewing Account Summary

```python
# Get complete account summary
summary = portfolio.account_summary()

print("=" * 50)
print("ACCOUNT SUMMARY")
print("=" * 50)
print(f"Cash Balance: {summary.cash:,.2f} RMB")
print(f"Total Market Value: {summary.total_market_value:,.2f} RMB")
print(f"Total Assets: {summary.total_assets:,.2f} RMB")
print(f"Unrealized P&L: {summary.unrealized_pnl:,.2f} RMB")
print(f"Realized P&L: {summary.realized_pnl:,.2f} RMB")
print(f"Total P&L: {summary.total_pnl:,.2f} RMB")
print(f"Return Rate: {summary.return_rate:.2f}%")
print("=" * 50)
```

### Account Dashboard

```python
# Get comprehensive dashboard
dashboard = portfolio.get_dashboard()

# Cash & Assets
print(f"💰 Cash: {dashboard['cash']:,.2f} RMB")
print(f"📊 Market Value: {dashboard['market_value']:,.2f} RMB")
print(f"📈 Total Assets: {dashboard['total_assets']:,.2f} RMB")

# Performance
print(f"\n📈 Performance:")
print(f"  Realized P&L: {dashboard['realized_pnl']:,.2f} RMB")
print(f"  Unrealized P&L: {dashboard['unrealized_pnl']:,.2f} RMB")
print(f"  Total Return: {dashboard['return_rate']:.2f}%")

# Positions Overview
print(f"\n📊 Positions:")
for pos in dashboard['positions']:
    print(f"  {pos['stock_name']}: {pos['quantity']} shares")
    print(f"    Market Value: {pos['market_value']:,.2f} RMB")
    print(f"    P&L: {pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_pct']:.2f}%)")
```

---

## 📦 Position Management

### Opening a Position (Buy)

```python
# Buy shares
result = portfolio.buy(
    symbol="600000",
    quantity=100,
    price=10.00
)

print(f"✅ Bought {result.quantity} shares of {result.stock_name}")
print(f"   Price: {result.price:.2f} RMB")
print(f"   Total Cost: {result.total_cost:.2f} RMB")
print(f"   Commission: {result.commission_fee:.2f} RMB")
```

**Buy Order Details**:
- **Symbol**: Stock code (e.g., "600000")
- **Quantity**: Number of shares (must be positive integer)
- **Price**: Price per share (RMB)
- **Validation**: Checks available cash before execution

### Closing a Position (Sell)

```python
# Sell shares
result = portfolio.sell(
    symbol="600000",
    quantity=50,
    price=12.00
)

print(f"✅ Sold {result.quantity} shares of {result.stock_name}")
print(f"   Price: {result.price:.2f} RMB")
print(f"   Total Revenue: {result.total_revenue:.2f} RMB")
print(f"   Commission: {result.commission_fee:.2f} RMB")
print(f"   Stamp Duty: {result.stamp_duty:.2f} RMB")
print(f"   Realized P&L: {result.realized_pnl:.2f} RMB")
```

**Sell Order Details**:
- **Symbol**: Stock code
- **Quantity**: Number of shares (must not exceed position)
- **Price**: Price per share (RMB)
- **Validation**: Checks available shares before execution

### Viewing Positions

```python
# Get all positions
positions = portfolio.get_positions()

print("CURRENT POSITIONS:")
print("-" * 60)

for pos in positions:
    print(f"Stock: {pos.stock_name} ({pos.symbol})")
    print(f"Shares: {pos.quantity:,}")
    print(f"Avg Cost: {pos.average_cost:.2f} RMB")
    print(f"Current Price: {pos.current_price:.2f} RMB")
    print(f"Market Value: {pos.market_value:,.2f} RMB")
    print(f"Unrealized P&L: {pos.unrealized_pnl:,.2f} RMB")
    print(f"Unrealized P&L %: {pos.unrealized_pnl_pct:.2f}%")
    print("-" * 60)
```

### Getting a Specific Position

```python
# Get position for a specific stock
position = portfolio.get_position("600000")

if position:
    print(f"Holding {position.quantity} shares of {position.stock_name}")
    print(f"Average Cost: {position.average_cost:.2f} RMB")
    print(f"Current Value: {position.market_value:,.2f} RMB")
else:
    print("No position found for this stock")
```

### Closing a Position Completely

```python
# Get current position size
position = portfolio.get_position("600000")

if position:
    # Sell all shares
    portfolio.sell(
        symbol="600000",
        quantity=position.quantity,
        price=12.50
    )
    print(f"✅ Closed entire position of {position.stock_name}")
```

---

## 📝 Transaction Management

### Viewing Transaction History

```python
# Get all transactions
transactions = portfolio.get_transaction_history()

print("TRANSACTION HISTORY:")
print("-" * 80)

for txn in transactions:
    print(f"Date: {txn.timestamp}")
    print(f"Type: {txn.transaction_type}")
    print(f"Stock: {txn.stock_name} ({txn.symbol})")
    print(f"Quantity: {txn.quantity:,}")
    print(f"Price: {txn.price:.2f} RMB")
    print(f"Amount: {txn.amount:,.2f} RMB")

    if txn.commission_fee:
        print(f"Commission: {txn.commission_fee:.2f} RMB")

    if txn.stamp_duty:
        print(f"Stamp Duty: {txn.stamp_duty:.2f} RMB")

    if txn.realized_pnl is not None:
        print(f"Realized P&L: {txn.realized_pnl:,.2f} RMB")

    print("-" * 80)
```

### Filtering Transactions

```python
# Filter by stock
transactions = portfolio.get_transaction_history(symbol="600000")
print(f"Found {len(transactions)} transactions for 600000")

# Filter by type
buy_transactions = [t for t in portfolio.get_transaction_history()
                    if t.transaction_type == "buy"]
print(f"Found {len(buy_transactions)} buy transactions")

sell_transactions = [t for t in portfolio.get_transaction_history()
                     if t.transaction_type == "sell"]
print(f"Found {len(sell_transactions)} sell transactions")
```

### Transaction Details

Each transaction record includes:
- **timestamp**: Execution time
- **transaction_type**: "buy" or "sell"
- **symbol**: Stock code
- **stock_name**: Stock name
- **quantity**: Number of shares
- **price**: Execution price per share
- **amount**: Total amount (quantity × price)
- **commission_fee**: Broker commission
- **stamp_duty**: Stamp duty (sell only)
- **realized_pnl**: Profit/loss (sell only)
- **position_after**: Position size after transaction

---

## 🎯 Order Execution

### Order Flow

```python
# 1. Check available cash
summary = portfolio.account_summary()
print(f"Available cash: {summary.cash:,.2f} RMB")

# 2. Execute buy order
buy_result = portfolio.buy(
    symbol="600000",
    quantity=100,
    price=10.00
)

# 3. Verify position opened
position = portfolio.get_position("600000")
print(f"Position opened: {position.quantity} shares")

# 4. Wait for price movement (or simulate)
portfolio.update_current_price("600000", 12.00)

# 5. Execute sell order
sell_result = portfolio.sell(
    symbol="600000",
    quantity=50,
    price=12.00
)

# 6. Verify position reduced
position = portfolio.get_position("600000")
print(f"Position remaining: {position.quantity} shares")
```

### Order Validation

The system automatically validates orders:

**Buy Order Validation**:
- ✅ Sufficient cash available
- ✅ Valid stock symbol
- ✅ Positive quantity
- ✅ Valid price

**Sell Order Validation**:
- ✅ Sufficient shares available
- ✅ Valid stock symbol
- ✅ Positive quantity
- ✅ Valid price

### Error Handling

```python
try:
    # Attempt to buy more than available cash
    portfolio.buy(symbol="600000", quantity=10000, price=100.00)
except Exception as e:
    print(f"Order failed: {e}")
    # Check available cash
    summary = portfolio.account_summary()
    print(f"Available cash: {summary.cash:,.2f} RMB")
```

---

## 💸 Fee Structure

### Commission Fees

**Broker Commission**: 0.03% of transaction amount

```python
# Example: Buy 100 shares at 10.00 RMB
quantity = 100
price = 10.00
amount = quantity * price  # 1,000 RMB

commission = amount * 0.0003  # 0.30 RMB
print(f"Commission: {commission:.2f} RMB")
```

### Stamp Duty

**Stamp Duty**: 0.1% of transaction amount (sell orders only)

```python
# Example: Sell 100 shares at 12.00 RMB
quantity = 100
price = 12.00
amount = quantity * price  # 1,200 RMB

stamp_duty = amount * 0.001  # 1.20 RMB
print(f"Stamp Duty: {stamp_duty:.2f} RMB")
```

### Complete Fee Example

```python
# Buy order
buy_result = portfolio.buy(symbol="600000", quantity=100, price=10.00)
print(f"Buy - Commission: {buy_result.commission_fee:.2f} RMB")

# Sell order
sell_result = portfolio.sell(symbol="600000", quantity=100, price=12.00)
print(f"Sell - Commission: {sell_result.commission_fee:.2f} RMB")
print(f"Sell - Stamp Duty: {sell_result.stamp_duty:.2f} RMB")

# Total fees
total_fees = buy_result.commission_fee + sell_result.commission_fee + sell_result.stamp_duty
print(f"Total Fees: {total_fees:.2f} RMB")
```

### Fee Impact on Returns

```python
# Buy 100 shares at 10.00, sell at 12.00
buy_amount = 100 * 10.00  # 1,000 RMB
sell_amount = 100 * 12.00  # 1,200 RMB

buy_commission = buy_amount * 0.0003  # 0.30 RMB
sell_commission = sell_amount * 0.0003  # 0.36 RMB
stamp_duty = sell_amount * 0.001  # 1.20 RMB

total_fees = buy_commission + sell_commission + stamp_duty  # 1.86 RMB
gross_profit = sell_amount - buy_amount  # 200 RMB
net_profit = gross_profit - total_fees  # 198.14 RMB

print(f"Gross Profit: {gross_profit:.2f} RMB")
print(f"Total Fees: {total_fees:.2f} RMB")
print(f"Net Profit: {net_profit:.2f} RMB")
print(f"Fee Impact: {total_fees/gross_profit*100:.2f}%")
```

---

## ⚠️ Risk Management

### Position Sizing

**Recommended**: Never risk more than 2% of total capital per trade

```python
# Calculate position size (2% risk rule)
total_capital = 100000
max_risk_per_trade = total_capital * 0.02  # 2,000 RMB

# If you set stop-loss at 10% below entry
entry_price = 10.00
stop_loss_price = entry_price * 0.90  # 9.00 RMB
risk_per_share = entry_price - stop_loss_price  # 1.00 RMB

# Maximum shares you can buy
max_shares = max_risk_per_trade / risk_per_share  # 2,000 shares
print(f"Maximum position size: {max_shares} shares")
```

### Stop-Loss Strategy

```python
# Monitor positions and execute stop-loss
positions = portfolio.get_positions()

for pos in positions:
    current_price = pos.current_price
    stop_loss_price = pos.average_cost * 0.90  # 10% stop-loss

    if current_price <= stop_loss_price:
        print(f"⚠️ Stop-loss triggered for {pos.stock_name}")
        print(f"   Current: {current_price:.2f}, Stop: {stop_loss_price:.2f}")

        # Execute sell order
        portfolio.sell(
            symbol=pos.symbol,
            quantity=pos.quantity,
            price=current_price
        )
        print(f"   ✅ Position closed")
```

### Diversification

**Recommended**: Hold 5-15 different stocks

```python
# Check portfolio concentration
positions = portfolio.get_positions()
total_value = sum(p.market_value for p in positions)

print("Portfolio Concentration:")
for pos in positions:
    concentration = pos.market_value / total_value * 100
    print(f"  {pos.stock_name}: {concentration:.1f}%")

    if concentration > 20:
        print(f"    ⚠️ Warning: Over 20% concentration")

# Check number of positions
if len(positions) < 5:
    print(f"⚠️ Warning: Under-diversified ({len(positions)} positions)")
elif len(positions) > 15:
    print(f"⚠️ Warning: Over-diversified ({len(positions)} positions)")
```

---

## 💡 Best Practices

### 1. Start Small

```python
# Begin with small positions
portfolio.buy(symbol="600000", quantity=100, price=10.00)  # 1,000 RMB
# Gradually increase as you gain experience
```

### 2. Keep a Trading Journal

```python
# Record your trades and reasoning
trade_journal = {
    "date": "2026-03-18",
    "symbol": "600000",
    "action": "buy",
    "quantity": 100,
    "price": 10.00,
    "reason": "Breakout above resistance",
    "target_price": 12.00,
    "stop_loss": 9.00,
    "outcome": "pending"
}

print(f"Trade recorded: {trade_journal['symbol']} {trade_journal['action']}")
```

### 3. Use Technical Analysis

Always analyze before trading:
- Read: [Technical Analysis Guide](./05-analysis-guide.md)
- Use the five-dimensional scoring system
- Wait for high-confidence signals (score > 80)

### 4. Backtest Before Real Trading

```python
# Test your strategy first
from backtest import BacktestEngine

engine = BacktestEngine(db.get_session())
results = engine.run_backtest(
    symbol="600000",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="vcp"
)

if results['win_rate'] > 60 and results['sharpe_ratio'] > 1.0:
    print("✅ Strategy passed backtest, consider live trading")
else:
    print("⚠️ Strategy failed backtest, refine before trading")
```

### 5. Review Regularly

```python
# Weekly review
summary = portfolio.account_summary()
print(f"Weekly Performance:")
print(f"  Total Return: {summary.return_rate:.2f}%")
print(f"  Win Rate: {calculate_win_rate()}%")
print(f"  Best Trade: {get_best_trade()}")
print(f"  Worst Trade: {get_worst_trade()}")

# Monthly review
positions = portfolio.get_positions()
for pos in positions:
    if pos.unrealized_pnl_pct < -10:
        print(f"⚠️ Review needed: {pos.stock_name} down {pos.unrealized_pnl_pct:.1f}%")
```

---

## 📊 Common Trading Patterns

### Pattern 1: Pyramid Buying

```python
# Buy initial position
portfolio.buy(symbol="600000", quantity=100, price=10.00)

# Add to position as price rises
portfolio.buy(symbol="600000", quantity=50, price=11.00)
portfolio.buy(symbol="600000", quantity=50, price=12.00)

# Average cost will be weighted average
position = portfolio.get_position("600000")
print(f"Average Cost: {position.average_cost:.2f} RMB")
```

### Pattern 2: Scaling Out

```python
# Sell portions as price rises
portfolio.sell(symbol="600000", quantity=50, price=12.00)
portfolio.sell(symbol="600000", quantity=50, price=13.00)
portfolio.sell(symbol="600000", quantity=50, price=14.00)

# Lock in profits gradually
```

### Pattern 3: Dollar-Cost Averaging

```python
# Invest fixed amount regularly
monthly_investment = 10000

# Buy at different prices
prices = [10.00, 9.50, 10.50, 9.80]
for price in prices:
    quantity = monthly_investment / price
    portfolio.buy(symbol="600000", quantity=int(quantity), price=price)

# Average cost smoothed out
```

---

## 🆘 Troubleshooting

### Issue: Position Not Updating

**Cause**: Current price not updated

**Solution**:
```python
# Update current price
portfolio.update_current_price("600000", 12.50)

# Or sync from data source
from stock_market.services import KLineService
kline_service = KLineService(db.get_session())
latest = kline_service.get_latest_kline("600000", "1d")
portfolio.update_current_price("600000", latest.close)
```

### Issue: Transaction History Missing

**Cause**: Transactions not committed to database

**Solution**:
```python
# Ensure database session is committed
db.get_session().commit()

# Refresh transaction history
transactions = portfolio.get_transaction_history()
```

### Issue: P&L Calculation Wrong

**Cause**: Price data inconsistency

**Solution**:
```python
# Re-calculate all positions
portfolio.recalculate_all_positions()

# Verify P&L
summary = portfolio.account_summary()
print(f"Verified P&L: {summary.total_pnl:.2f} RMB")
```

---

## 📚 Next Steps

- 📗 [Technical Analysis Guide](./05-analysis-guide.md) - Analysis tools
- 📙 [Backtest System Guide](./06-backtest-guide.md) - Strategy testing
- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Trading strategies
- 📖 [Portfolio Management Guide](./07-portfolio-management.md) - Advanced management

---

**Next Chapter**: [Technical Analysis Guide →](./05-analysis-guide.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
