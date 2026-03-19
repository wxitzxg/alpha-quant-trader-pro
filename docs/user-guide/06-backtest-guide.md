# 📈 Backtest System Guide

> Complete guide to the backtesting system for strategy validation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Running a Basic Backtest](#running-a-basic-backtest)
4. [Understanding Results](#understanding-results)
5. [Performance Metrics](#performance-metrics)
6. [Strategy Testing](#strategy-testing)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

The backtesting system allows you to test trading strategies on historical data before using real money.

### Core Features

- ✅ **Historical Data Testing** - Test strategies on past market data
- ✅ **Performance Metrics** - Comprehensive performance analysis
- ✅ **Multiple Strategies** - Built-in VCP, Nine-Turn, Divergence
- ✅ **Custom Strategies** - Create and test your own strategies
- ✅ **Report Generation** - HTML and JSON reports
- ✅ **Parameter Optimization** - Find optimal strategy parameters

### System Architecture

```
┌─────────────────────────────────────────┐
│         BacktestEngine                   │
│  - High-level backtest interface         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Strategy Executor                │
│  - Strategy selection                    │
│  - Signal generation                     │
│  - Trade execution                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Performance Calculator           │
│  - Metrics calculation                   │
│  - Risk analysis                         │
│  - Statistics                            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Report Generator                 │
│  - HTML reports                          │
│  - JSON reports                          │
│  - Charts and visualizations             │
└─────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Initialize the Backtest Engine

```python
from common.database import DatabaseManager
from backtest import BacktestEngine

# Initialize database connection
db = DatabaseManager("postgresql://user:password@localhost:5432/stock_market")

# Create backtest engine
engine = BacktestEngine(db.get_session())

print("✅ Backtest engine initialized!")
```

---

## 🎯 Running a Basic Backtest

### Simple Backtest Example

```python
# Run backtest on a single stock
results = engine.run_backtest(
    symbol="600519",              # Stock code (贵州茅台)
    start_date="2023-01-01",      # Start date
    end_date="2023-12-31",        # End date
    initial_capital=100000,       # Starting capital (100,000 RMB)
    strategy="vcp",               # Strategy to test
    commission_rate=0.0003,       # Commission fee (0.03%)
    stamp_duty_rate=0.001         # Stamp duty (0.1%)
)

print("✅ Backtest completed!")
```

### Multiple Stocks Backtest

```python
# Test on multiple stocks
stock_symbols = ["600519", "600000", "000001", "601318"]

all_results = {}
for symbol in stock_symbols:
    print(f"Running backtest for {symbol}...")
    results = engine.run_backtest(
        symbol=symbol,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
        strategy="vcp"
    )
    all_results[symbol] = results
    print(f"  ✅ Completed: {results['total_return']:.2f}% return")

# Summary
print("\n=== BACKTEST SUMMARY ===")
for symbol, results in all_results.items():
    print(f"{symbol}: {results['total_return']:.2f}% return, {results['win_rate']:.1f}% win rate")
```

### Custom Strategy Backtest

```python
# Define custom strategy
def my_custom_strategy(kline_data, current_position):
    """
    Custom strategy: Buy when RSI < 30, Sell when RSI > 70
    """
    from technical_analysis.indicators import RSI

    rsi = RSI()
    rsi_values = rsi.calculate(kline_data['close'], period=14)

    if current_position == 0 and rsi_values[-1] < 30:
        return "buy"  # Buy signal
    elif current_position > 0 and rsi_values[-1] > 70:
        return "sell"  # Sell signal
    else:
        return "hold"  # No action

# Run backtest with custom strategy
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy=my_custom_strategy  # Pass function instead of string
)

print(f"Custom Strategy Results:")
print(f"  Total Return: {results['total_return']:.2f}%")
print(f"  Win Rate: {results['win_rate']:.2f}%")
```

---

## 📊 Understanding Results

### Basic Results

```python
results = engine.run_backtest(...)

print("=" * 60)
print("BACKTEST RESULTS")
print("=" * 60)

# Basic metrics
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Annual Return: {results['annual_return']:.2f}%")
print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Avg Win: {results['average_win']:.2f}%")
print(f"Avg Loss: {results['average_loss']:.2f}%")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print("=" * 60)
```

### Sample Results Output

```
============================================================
BACKTEST RESULTS
============================================================
Total Return: 67.45%
Annual Return: 67.45%
Total Trades: 28
Win Rate: 71.43%
Avg Win: 8.32%
Avg Loss: -3.15%
Profit Factor: 2.45
============================================================
```

---

## 📐 Performance Metrics

### Return Metrics

```python
# Total and annual returns
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Annual Return: {results['annual_return']:.2f}%")

# Monthly returns
if 'monthly_returns' in results:
    print("\nMonthly Returns:")
    for month, return_pct in results['monthly_returns'].items():
        print(f"  {month}: {return_pct:.2f}%")
```

### Risk Metrics

```python
# Risk analysis
print(f"\nRisk Metrics:")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Sortino Ratio: {results['sortino_ratio']:.2f}")
print(f"Volatility: {results['volatility']:.2f}%")
print(f"Calmar Ratio: {results['calmar_ratio']:.2f}")
```

### Trade Metrics

```python
# Trade statistics
print(f"\nTrade Statistics:")
print(f"Total Trades: {results['total_trades']}")
print(f"Wins: {results['winning_trades']}")
print(f"Losses: {results['losing_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Average Win: {results['average_win']:.2f}%")
print(f"Average Loss: {results['average_loss']:.2f}%")
print(f"Largest Win: {results['largest_win']:.2f}%")
print(f"Largest Loss: {results['largest_loss']:.2f}%")
```

### Risk-Adjusted Returns

```python
# Profit factor and expectancy
print(f"\nRisk-Adjusted Metrics:")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print(f"Expectancy: {results['expectancy']:.2f}%")
print(f"Risk-Reward Ratio: {results['risk_reward_ratio']:.2f}")
print(f"Recovery Factor: {results['recovery_factor']:.2f}")
```

---

## 🎯 Strategy Testing

### VCP (Volatility Contraction Pattern) Strategy

```python
# Test VCP strategy
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy="vcp"  # Built-in VCP strategy
)

print("VCP Strategy Results:")
print(f"  Total Return: {results['total_return']:.2f}%")
print(f"  Win Rate: {results['win_rate']:.2f}%")
print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")

# Get trade details
if 'trades' in results:
    print(f"\n  Total Trades: {len(results['trades'])}")
    winning_trades = [t for t in results['trades'] if t['pnl'] > 0]
    print(f"  Winning Trades: {len(winning_trades)}")
```

### Nine-Turn Sequence Strategy

```python
# Test Nine-Turn strategy
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy="nine_turn"  # Built-in Nine-Turn strategy
)

print("Nine-Turn Strategy Results:")
print(f"  Total Return: {results['total_return']:.2f}%")
print(f"  Win Rate: {results['win_rate']:.2f}%")
```

### Top Divergence Strategy

```python
# Test Divergence strategy
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy="divergence"  # Built-in Divergence strategy
)

print("Divergence Strategy Results:")
print(f"  Total Return: {results['total_return']:.2f}%")
print(f"  Win Rate: {results['win_rate']:.2f}%")
```

### Compare Multiple Strategies

```python
strategies = ["vcp", "nine_turn", "divergence"]
results_dict = {}

for strategy in strategies:
    print(f"Testing {strategy}...")
    results = engine.run_backtest(
        symbol="600519",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
        strategy=strategy
    )
    results_dict[strategy] = results
    print(f"  ✅ {strategy}: {results['total_return']:.2f}% return")

# Comparison table
print("\n=== STRATEGY COMPARISON ===")
print(f"{'Strategy':<15} {'Return':<10} {'Win Rate':<10} {'Max DD':<10}")
print("-" * 45)
for strategy, results in results_dict.items():
    print(f"{strategy:<15} {results['total_return']:>7.2f}%  {results['win_rate']:>8.1f}%  {results['max_drawdown']:>7.2f}%")
```

---

## ⚙️ Advanced Features

### Parameter Optimization

```python
# Optimize strategy parameters
from backtest import ParameterOptimizer

optimizer = ParameterOptimizer(engine)

# Define parameter ranges
param_ranges = {
    'rsi_period': range(10, 20, 2),  # Test RSI periods 10, 12, 14, 16, 18
    'rsi_oversold': range(25, 35, 5),  # Test oversold levels 25, 30
    'rsi_overbought': range(70, 80, 5)  # Test overbought levels 70, 75
}

# Run optimization
best_params, best_results = optimizer.optimize(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy=my_custom_strategy,
    param_ranges=param_ranges
)

print("Optimization Results:")
print(f"Best Parameters: {best_params}")
print(f"Best Return: {best_results['total_return']:.2f}%")
print(f"Best Win Rate: {best_results['win_rate']:.2f}%")
```

### Walk-Forward Analysis

```python
# Test strategy robustness with walk-forward analysis
from backtest import WalkForwardAnalyzer

wfa = WalkForwardAnalyzer(engine)

results = wfa.analyze(
    symbol="600519",
    start_date="2022-01-01",
    end_date="2023-12-31",
    training_period=252,  # 1 year training
    testing_period=63,    # 3 months testing
    strategy="vcp"
)

print("Walk-Forward Analysis Results:")
print(f"Average Return: {results['avg_return']:.2f}%")
print(f"Std Dev: {results['std_dev']:.2f}%")
print(f"Consistency: {results['consistency']:.2f}%")
```

### Monte Carlo Simulation

```python
# Test strategy with Monte Carlo simulation
from backtest import MonteCarloSimulator

simulator = MonteCarloSimulator(engine)

results = simulator.simulate(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="vcp",
    iterations=1000  # Run 1000 simulations
)

print("Monte Carlo Simulation Results:")
print(f"Mean Return: {results['mean_return']:.2f}%")
print(f"Median Return: {results['median_return']:.2f}%")
print(f"5th Percentile: {results['percentile_5']:.2f}%")
print(f"95th Percentile: {results['percentile_95']:.2f}%")
print(f"Probability of Profit: {results['prob_profit']:.2f}%")
```

---

## 📄 Report Generation

### HTML Report

```python
from backtest import ReportGenerator

report_gen = ReportGenerator()

# Generate HTML report
html_report = report_gen.generate_report(results)

# Save to file
with open("backtest_report.html", "w", encoding="utf-8") as f:
    f.write(html_report)

print("✅ HTML report saved to backtest_report.html")
```

### JSON Report

```python
import json

# Generate JSON report
json_report = report_gen.generate_json_report(results)

# Save to file
with open("backtest_report.json", "w", encoding="utf-8") as f:
    json.dump(json_report, f, indent=2, ensure_ascii=False)

print("✅ JSON report saved to backtest_report.json")
```

### Excel Report

```python
# Generate Excel report
report_gen.generate_excel_report(
    results=results,
    filename="backtest_report.xlsx",
    include_trades=True  # Include individual trade details
)

print("✅ Excel report saved to backtest_report.xlsx")
```

---

## 💡 Best Practices

### 1. Test Multiple Time Periods

```python
# Test across different market conditions
time_periods = [
    ("2021-01-01", "2021-12-31"),  # Bull market
    ("2022-01-01", "2022-12-31"),  # Bear market
    ("2023-01-01", "2023-12-31"),  # Sideways market
]

for start, end in time_periods:
    results = engine.run_backtest(
        symbol="600519",
        start_date=start,
        end_date=end,
        strategy="vcp"
    )
    print(f"{start} to {end}: {results['total_return']:.2f}% return")
```

### 2. Use Realistic Assumptions

```python
# Include realistic trading costs
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy="vcp",
    commission_rate=0.0003,        # Realistic commission
    stamp_duty_rate=0.001,         # Stamp duty
    slippage_rate=0.001,           # 0.1% slippage
    position_size=0.1              # 10% of capital per trade
)
```

### 3. Validate with Out-of-Sample Data

```python
# In-sample training
train_results = engine.run_backtest(
    symbol="600519",
    start_date="2022-01-01",
    end_date="2022-12-31",
    strategy="vcp"
)

# Out-of-sample testing
test_results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="vcp"
)

print(f"In-sample: {train_results['total_return']:.2f}%")
print(f"Out-of-sample: {test_results['total_return']:.2f}%")

# Strategy is robust if performance is similar
if abs(train_results['total_return'] - test_results['total_return']) < 10:
    print("✅ Strategy is robust")
else:
    print("⚠️ Strategy may be overfit")
```

### 4. Monitor Key Metrics

**Good Strategy Indicators**:
- Win Rate > 60%
- Sharpe Ratio > 1.0
- Max Drawdown < 20%
- Profit Factor > 1.5

**Warning Signs**:
- Win Rate < 50%
- Sharpe Ratio < 0.5
- Max Drawdown > 30%
- Profit Factor < 1.0

---

## 🆘 Troubleshooting

### Issue: Backtest Takes Too Long

**Solution**: Reduce data range or optimize strategy

```python
# Use shorter period for testing
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-06-01",  # 6 months instead of 12
    end_date="2023-12-31",
    strategy="vcp"
)

# Or optimize strategy code
def optimized_strategy(kline_data, position):
    # Simplified logic
    pass
```

### Issue: No Trades Generated

**Cause**: Strategy too conservative or wrong parameters

**Solution**:
```python
# Check strategy signals
from backtest import StrategyTester

tester = StrategyTester()
signals = tester.test_signals(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="vcp"
)

print(f"Buy signals: {signals['buy_count']}")
print(f"Sell signals: {signals['sell_count']}")

if signals['buy_count'] == 0:
    print("⚠️ No buy signals - strategy may be too conservative")
    # Try adjusting parameters
```

### Issue: Negative Returns

**Analysis**:
```python
# Analyze losing trades
losing_trades = [t for t in results['trades'] if t['pnl'] < 0]

print(f"Losing Trades: {len(losing_trades)}")
print(f"Avg Loss: {sum(t['pnl'] for t in losing_trades) / len(losing_trades):.2f}%")

# Check market conditions
from technical_analysis.indicators import MarketTrend
trend = MarketTrend().analyze_broad_market(
    start_date="2023-01-01",
    end_date="2023-12-31"
)
print(f"Market Condition: {trend}")
```

---

## 📚 Next Steps

- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Strategy details
- 💹 [Trading System Guide](./04-trading-guide.md) - Execute trades
- 📊 [Technical Analysis Guide](./05-analysis-guide.md) - Analysis tools
- 📖 [Portfolio Management Guide](./07-portfolio-management.md) - Portfolio analysis

---

**Next Chapter**: [Portfolio Management Guide →](./07-portfolio-management.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
