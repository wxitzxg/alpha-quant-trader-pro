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

## Sync Position (Recommended)

```python
from portfolio_manager import PortfolioCommands

commands = PortfolioCommands()

# 同步持仓（存在则覆盖，不存在则新增）
position = commands.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0
)
print(f"Position value: {position.market_value}")

# 可选：手动指定现价
position = commands.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0,
    current_price=1650.0
)
```

## Legacy Methods (Deprecated)

```python
# ⚠️ 已废弃，建议使用 sync_position()
position = commands.add_position("600519", quantity=100, cost_price=1600.0)  # Deprecated
position = commands.update_position("600519", quantity=150, cost_price=1550.0)  # Deprecated
```

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
