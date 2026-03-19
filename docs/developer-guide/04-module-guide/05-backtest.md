# 🧪 Backtest Module Guide

> Guide for the Backtest module

## Overview

Backtests trading strategies and analyzes performance.

## Key Components

- **BacktestEngine**: Main backtest orchestrator
- **StrategyExecutor**: Execute strategy signals
- **PerformanceCalculator**: Calculate metrics (Sharpe, drawdown, win rate)
- **ReportGenerator**: Generate backtest reports
- **Optimizers**: Parameter optimization tools

## Usage Examples

```python
from backtest import BacktestEngine

engine = BacktestEngine()

# Run backtest
results = engine.run_backtest(
    strategy="vcp",
    symbols=["600519", "000001"],
    start_date="2022-01-01",
    end_date="2023-01-01",
    initial_capital=100000
)

# View results
print(f"Total return: {results['total_return']}%")
print(f"Sharpe ratio: {results['sharpe_ratio']}")
print(f"Max drawdown: {results['max_drawdown']}%")
```

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
