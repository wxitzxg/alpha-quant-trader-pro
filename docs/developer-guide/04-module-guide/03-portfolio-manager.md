# 💼 Portfolio Manager Module Guide

> Guide for the Portfolio Manager module

## Overview

Manages user positions, transactions, and account information.

## Key Components

- **Position**: User's stock holdings
- **Transaction**: Trade records
- **Account**: User account and balance
- **PortfolioCommands**: High-level trading operations

## Usage Examples

```python
from portfolio_manager import PortfolioCommands

commands = PortfolioCommands(user_id=123)

# Buy stock
position = commands.buy(symbol="600519", quantity=100, price=1800)
print(f"Position value: {position.market_value}")

# Sell stock
commands.sell(symbol="600519", quantity=50, price=1850)

# Get portfolio summary
summary = commands.get_portfolio_summary()
print(f"Total value: {summary['total_value']}")
```

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
