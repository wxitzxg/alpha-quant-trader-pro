# 📖 Portfolio Management Guide

> Advanced portfolio management and risk control techniques

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Portfolio Dashboard](#portfolio-dashboard)
3. [同步持仓](#同步持仓)
4. [Position Analysis](#position-analysis)
5. [Asset Allocation](#asset-allocation)
6. [Risk Management](#risk-management)
7. [Performance Tracking](#performance-tracking)
8. [Portfolio Optimization](#portfolio-optimization)
9. [Best Practices](#best-practices)

---

## 🎯 Overview

Effective portfolio management is crucial for long-term trading success. This guide covers advanced techniques for managing your portfolio.

### Core Concepts

- ✅ **Diversification** - Spread risk across multiple stocks
- ✅ **Position Sizing** - Determine optimal position sizes
- ✅ **Risk Control** - Manage and limit potential losses
- ✅ **Performance Analysis** - Track and improve performance
- ✅ **Rebalancing** - Maintain target allocations

---

## 📊 Portfolio Dashboard

### Getting Complete Portfolio Overview

```python
from portfolio_manager import PortfolioCommands

portfolio = PortfolioCommands()

# Get comprehensive dashboard
dashboard = portfolio.get_dashboard()

print("=" * 60)
print("PORTFOLIO DASHBOARD")
print("=" * 60)

# Cash and Assets
print(f"\n💰 CASH & ASSETS")
print(f"Cash Balance: {dashboard['cash']:,.2f} RMB")
print(f"Total Market Value: {dashboard['market_value']:,.2f} RMB")
print(f"Total Assets: {dashboard['total_assets']:,.2f} RMB")

# Performance
print(f"\n📈 PERFORMANCE")
print(f"Realized P&L: {dashboard['realized_pnl']:,.2f} RMB")
print(f"Unrealized P&L: {dashboard['unrealized_pnl']:,.2f} RMB")
print(f"Total P&L: {dashboard['total_pnl']:,.2f} RMB")
print(f"Return Rate: {dashboard['return_rate']:.2f}%")

# Positions Summary
print(f"\n📊 POSITIONS SUMMARY")
print(f"Total Positions: {dashboard['position_count']}")
print(f"Winning Positions: {dashboard['winning_positions']}")
print(f"Losing Positions: {dashboard['losing_positions']}")
print(f"Avg Position Size: {dashboard['avg_position_size']:,.2f} RMB")

# Detailed Positions
print(f"\n📦 DETAILED POSITIONS")
for pos in dashboard['positions']:
    print(f"\n{pos['stock_name']} ({pos['symbol']})")
    print(f"  Shares: {pos['quantity']:,}")
    print(f"  Avg Cost: {pos['average_cost']:.2f} RMB")
    print(f"  Current Price: {pos['current_price']:.2f} RMB")
    print(f"  Market Value: {pos['market_value']:,.2f} RMB")
    print(f"  Unrealized P&L: {pos['unrealized_pnl']:,.2f} RMB ({pos['unrealized_pnl_pct']:.2f}%)")
```

---

## 🔄 同步持仓

### 智能同步

```python
# 自动判断：存在则覆盖，不存在则新增
portfolio.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0
)

# 可选：手动指定现价
portfolio.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0,
    current_price=1650.0
)
```

**特点**:
- ✅ 无需判断持仓是否存在
- ✅ 现价未提供时自动查询
- ✅ 自动计算市值、盈亏等指标

### 迁移指南

**旧代码**:
```python
portfolio.add_position("600519", 100, 1600)
portfolio.update_position("600519", quantity=150)
```

**新代码**:
```python
portfolio.sync_position("600519", 100, 1600)
portfolio.sync_position("600519", 150, 1550)
```

---

## 📈 Position Analysis

### Position Concentration

```python
# Check portfolio concentration
positions = portfolio.get_positions()
total_value = sum(p.market_value for p in positions)

print("Position Concentration:")
print("-" * 50)

for pos in positions:
    concentration = pos.market_value / total_value * 100
    print(f"{pos.stock_name}: {concentration:.1f}%")

    # Warn if over-concentrated
    if concentration > 20:
        print(f"  ⚠️ WARNING: Over 20% concentration")

# Overall concentration metrics
top_3_concentration = sum(sorted([p.market_value / total_value * 100
                                  for p in positions], reverse=True)[:3])
print(f"\nTop 3 Positions: {top_3_concentration:.1f}% of portfolio")
```

### Position Performance

```python
# Analyze position performance
print("\nPosition Performance:")
print("-" * 60)

for pos in positions:
    print(f"{pos.stock_name} ({pos.symbol}):")
    print(f"  Entry: {pos.average_cost:.2f} RMB")
    print(f"  Current: {pos.current_price:.2f} RMB")
    print(f"  P&L: {pos.unrealized_pnl:,.2f} RMB ({pos.unrealized_pnl_pct:.2f}%)")

    # Performance categories
    if pos.unrealized_pnl_pct > 20:
        print(f"  Status: 🚀 Strong Winner")
    elif pos.unrealized_pnl_pct > 10:
        print(f"  Status: 💹 Winner")
    elif pos.unrealized_pnl_pct > -5:
        print(f"  Status: ➖ Breakeven")
    elif pos.unrealized_pnl_pct > -15:
        print(f"  Status: ⚠️ Moderate Loss")
    else:
        print(f"  Status: 🚨 Large Loss")
    print()
```

### Holding Period Analysis

```python
# Check holding periods
from datetime import datetime

print("Holding Period Analysis:")
print("-" * 50)

for pos in positions:
    # Get first buy date for this position
    first_buy = portfolio.get_first_transaction(
        symbol=pos.symbol,
        transaction_type="buy"
    )

    if first_buy:
        holding_days = (datetime.now() - first_buy.timestamp).days
        print(f"{pos.stock_name}: {holding_days} days")

        # Long-term vs short-term
        if holding_days > 365:
            print(f"  Category: 📅 Long-term (> 1 year)")
        elif holding_days > 90:
            print(f"  Category: 📆 Medium-term (3-12 months)")
        else:
            print(f"  Category: 📅 Short-term (< 3 months)")
```

---

## 💰 Asset Allocation

### Current Allocation

```python
# Get current asset allocation
allocation = portfolio.get_asset_allocation()

print("Current Asset Allocation:")
print("-" * 40)

for asset_class, percentage in allocation.items():
    print(f"{asset_class}: {percentage:.1f}%")

# By industry
industry_allocation = portfolio.get_industry_allocation()
print("\nIndustry Allocation:")
for industry, percentage in industry_allocation.items():
    print(f"{industry}: {percentage:.1f}%")

# By market cap
market_cap_allocation = portfolio.get_market_cap_allocation()
print("\nMarket Cap Allocation:")
for size, percentage in market_cap_allocation.items():
    print(f"{size}: {percentage:.1f}%")
```

### Target Allocation

```python
# Define target allocation
target_allocation = {
    "Financial": 25.0,
    "Technology": 20.0,
    "Consumer": 20.0,
    "Healthcare": 15.0,
    "Energy": 10.0,
    "Other": 10.0
}

# Compare with current
current_allocation = portfolio.get_industry_allocation()

print("Allocation Comparison:")
print(f"{'Industry':<15} {'Target':<10} {'Current':<10} {'Difference':<10}")
print("-" * 45)

for industry, target_pct in target_allocation.items():
    current_pct = current_allocation.get(industry, 0.0)
    diff = current_pct - target_pct

    indicator = "→" if abs(diff) < 1 else ("↑" if diff > 0 else "↓")
    print(f"{industry:<15} {target_pct:>6.1f}%   {current_pct:>6.1f}%   {indicator:>3} {diff:+.1f}%")
```

### Rebalancing Recommendations

```python
# Get rebalancing suggestions
rebalance_suggestions = portfolio.get_rebalance_suggestions(target_allocation)

print("\nRebalancing Suggestions:")
print("-" * 60)

for suggestion in rebalance_suggestions:
    action = "BUY" if suggestion['action'] == 'buy' else "SELL"
    amount = suggestion['amount']

    print(f"{action} {suggestion['industry']}: {amount:,.0f} RMB")
    print(f"  Reason: {suggestion['reason']}")
    print()

# Total rebalancing amount
total_buy = sum(s['amount'] for s in rebalance_suggestions if s['action'] == 'buy')
total_sell = sum(s['amount'] for s in rebalance_suggestions if s['action'] == 'sell')
print(f"Total Buy Amount: {total_buy:,.0f} RMB")
print(f"Total Sell Amount: {total_sell:,.0f} RMB")
```

---

## ⚠️ Risk Management

### Position Sizing

```python
# Calculate optimal position size (2% risk rule)
def calculate_position_size(entry_price, stop_loss_price, total_capital, risk_pct=0.02):
    """
    Calculate position size based on risk percentage

    Args:
        entry_price: Entry price per share
        stop_loss_price: Stop-loss price per share
        total_capital: Total portfolio capital
        risk_pct: Maximum risk percentage (default 2%)

    Returns:
        Maximum number of shares to buy
    """
    risk_per_share = entry_price - stop_loss_price
    max_risk_amount = total_capital * risk_pct
    max_shares = max_risk_amount / risk_per_share

    return int(max_shares)

# Example usage
total_capital = 100000
entry_price = 10.00
stop_loss_price = 9.00

position_size = calculate_position_size(
    entry_price=entry_price,
    stop_loss_price=stop_loss_price,
    total_capital=total_capital,
    risk_pct=0.02  # 2% risk
)

print(f"Maximum Position Size: {position_size} shares")
print(f"Position Value: {position_size * entry_price:,.0f} RMB")
print(f"Risk Amount: {position_size * (entry_price - stop_loss_price):,.0f} RMB")
```

### Portfolio Risk Metrics

```python
# Calculate portfolio-level risk metrics
risk_metrics = portfolio.get_risk_metrics()

print("Portfolio Risk Metrics:")
print("-" * 40)

print(f"Total Portfolio Value: {risk_metrics['total_value']:,.2f} RMB")
print(f"Portfolio Volatility: {risk_metrics['volatility']:.2f}%")
print(f"Value at Risk (95%): {risk_metrics['var_95']:,.2f} RMB")
print(f"Expected Shortfall: {risk_metrics['expected_shortfall']:,.2f} RMB")

# Risk concentration
print(f"\nRisk Concentration:")
print(f"  Top Position Risk: {risk_metrics['top_position_risk']:.1f}%")
print(f"  Top 3 Positions Risk: {risk_metrics['top_3_risk']:.1f}%")
print(f"  Herfindahl Index: {risk_metrics['herfindahl_index']:.3f}")

if risk_metrics['herfindahl_index'] > 0.2:
    print("  ⚠️ WARNING: High concentration risk")
```

### Stop-Loss Management

```python
# Monitor and manage stop-losses
positions = portfolio.get_positions()

print("Stop-Loss Monitoring:")
print("-" * 60)

for pos in positions:
    # Calculate stop-loss price (10% below entry)
    stop_loss_price = pos.average_cost * 0.90

    print(f"{pos.stock_name} ({pos.symbol}):")
    print(f"  Entry Price: {pos.average_cost:.2f} RMB")
    print(f"  Stop-Loss: {stop_loss_price:.2f} RMB")
    print(f"  Current Price: {pos.current_price:.2f} RMB")

    # Check if stop-loss triggered
    if pos.current_price <= stop_loss_price:
        print(f"  ⚠️ STOP-LOSS TRIGGERED!")
        print(f"  Action: Sell {pos.quantity} shares")

        # Execute stop-loss
        portfolio.sell(
            symbol=pos.symbol,
            quantity=pos.quantity,
            price=pos.current_price
        )
        print(f"  ✅ Position closed")
    else:
        distance_to_sl = (pos.current_price - stop_loss_price) / pos.current_price * 100
        print(f"  Distance to SL: {distance_to_sl:.1f}%")
    print()
```

---

## 📊 Performance Tracking

### Performance Over Time

```python
# Get historical performance
performance_history = portfolio.get_performance_history(months=12)

print("12-Month Performance:")
print("-" * 40)

for month, data in performance_history.items():
    print(f"{month}: {data['return']:.2f}%")
    print(f"  Starting Value: {data['starting_value']:,.0f} RMB")
    print(f"  Ending Value: {data['ending_value']:,.0f} RMB")
    print(f"  Net Contribution: {data['net_contribution']:,.0f} RMB")
    print()

# Calculate annual metrics
annual_return = portfolio.calculate_annual_return()
sharpe_ratio = portfolio.calculate_sharpe_ratio()
max_drawdown = portfolio.calculate_max_drawdown()

print("Annual Performance Metrics:")
print(f"  Annual Return: {annual_return:.2f}%")
print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"  Max Drawdown: {max_drawdown:.2f}%")
```

### Benchmark Comparison

```python
# Compare with benchmark (e.g., CSI 300)
benchmark_returns = portfolio.get_benchmark_returns(
    benchmark="000300",  # CSI 300 index
    months=12
)

portfolio_returns = portfolio.get_portfolio_returns(months=12)

print("Benchmark Comparison (Last 12 Months):")
print("-" * 50)

print(f"{'Month':<10} {'Portfolio':<15} {'Benchmark':<15} {'Alpha':<10}")
print("-" * 50)

for month in sorted(portfolio_returns.keys()):
    port_return = portfolio_returns[month]
    bench_return = benchmark_returns.get(month, 0)
    alpha = port_return - bench_return

    alpha_indicator = "✅" if alpha > 0 else "❌"
    print(f"{month:<10} {port_return:>8.2f}%     {bench_return:>8.2f}%     {alpha_indicator} {alpha:>6.2f}%")

# Summary
total_alpha = sum(portfolio_returns.values()) - sum(benchmark_returns.values())
print("-" * 50)
print(f"Total Alpha: {total_alpha:.2f}%")
```

---

## ⚙️ Portfolio Optimization

### Mean-Variance Optimization

```python
from portfolio_manager import PortfolioOptimizer

optimizer = PortfolioOptimizer(portfolio)

# Get optimization suggestions
optimization_result = optimizer.optimize(
    method="mean_variance",  # or "risk_parity", "sharpe_max"
    risk_aversion=1.0,       # 0.5-2.0 (lower = more aggressive)
    max_positions=10         # Maximum number of positions
)

print("Optimization Results:")
print("-" * 40)

print(f"Expected Return: {optimization_result['expected_return']:.2f}%")
print(f"Expected Volatility: {optimization_result['expected_volatility']:.2f}%")
print(f"Sharpe Ratio: {optimization_result['sharpe_ratio']:.2f}")

print("\nRecommended Allocation:")
for stock, weight in optimization_result['allocation'].items():
    print(f"  {stock}: {weight:.1f}%")
```

### Risk Parity Optimization

```python
# Alternative: Risk parity optimization
risk_parity_result = optimizer.optimize(
    method="risk_parity",
    max_positions=15
)

print("Risk Parity Allocation:")
for stock, weight in risk_parity_result['allocation'].items():
    print(f"  {stock}: {weight:.1f}%")

print(f"\nPortfolio Risk: {risk_parity_result['portfolio_risk']:.2f}%")
```

---

## 💡 Best Practices

### 1. Diversification Guidelines

**Recommended Diversification**:
- ✅ **Number of Positions**: 5-15 stocks
- ✅ **Single Position Max**: 20% of portfolio
- ✅ **Top 3 Positions**: < 50% of portfolio
- ✅ **Industry Concentration**: < 30% per industry
- ✅ **Market Cap Diversification**: Mix large, mid, small caps

### 2. Position Sizing Rules

**Risk Management**:
- ✅ **Per Trade Risk**: Never risk more than 2% of total capital
- ✅ **Position Size**: Calculate based on stop-loss distance
- ✅ **Correlation**: Reduce size for highly correlated positions
- ✅ **Volatility**: Smaller positions for high-volatility stocks

### 3. Regular Review Schedule

**Review Frequency**:
- 📅 **Daily**: Monitor stop-losses and major positions
- 📅 **Weekly**: Review performance and adjust positions
- 📅 **Monthly**: Rebalance portfolio, review strategy
- 📅 **Quarterly**: Comprehensive review and optimization
- 📅 **Annually**: Major rebalancing and strategy update

### 4. Rebalancing Triggers

**When to Rebalance**:
- 🔔 Position exceeds target by > 5%
- 🔔 Portfolio drift > 10% from target allocation
- 🔔 Major market moves (> 10% up or down)
- 🔔 Change in investment horizon or risk tolerance
- 🔔 Tax-loss harvesting opportunities

### 5. Performance Tracking

**Key Metrics to Track**:
- 📊 **Return Metrics**: Total return, annual return, monthly returns
- 📊 **Risk Metrics**: Sharpe ratio, max drawdown, volatility
- 📊 **Trade Metrics**: Win rate, profit factor, expectancy
- 📊 **Benchmark**: Alpha vs. CSI 300 or other benchmark

---

## 📚 Next Steps

- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Trading strategies
- 💹 [Trading System Guide](./04-trading-guide.md) - Trading execution
- 📈 [Backtest System Guide](./06-backtest-guide.md) - Strategy testing
- 📊 [Technical Analysis Guide](./05-analysis-guide.md) - Analysis tools

---

**Next Chapter**: [Three Strategies Guide →](./08-strategy-guide.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
