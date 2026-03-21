# 股票市场模块配置指南

## 概述

股票市场模块的所有配置现在统一从 `common/config.py` 获取，使用嵌套的 Pydantic 模型提供类型安全和验证。

## 配置结构

```
Config
└── stock_market: StockMarketConfig
    ├── sync: SyncConfig
    │   ├── incremental: bool
    │   ├── concurrency: int
    │   ├── kline_workers: int
    │   ├── retry_times: int
    │   └── retry_delay: float
    ├── data_retention: DataRetentionConfig
    │   ├── kline_days: int
    │   └── fundamentals_days: int
    └── trading_hours: TradingHoursConfig
        ├── morning_open: str
        ├── morning_close: str
        ├── afternoon_open: str
        └── afternoon_close: str
```

## 配置文件

### 主配置文件

`config/stock_market.yaml` - 实际使用的配置文件

### 示例配置文件

`config/stock_market.example.yaml` - 完整的配置示例和说明

## 配置字段说明

### 同步配置 (sync)

| 字段 | 类型 | 默认值 | 范围 | 说明 |
|-----|------|--------|------|------|
| incremental | bool | true | - | 是否启用增量同步 |
| concurrency | int | 10 | 1-100 | 最大并发数 |
| kline_workers | int | 5 | 1-20 | K线工作线程数 |
| retry_times | int | 3 | 0-10 | 重试次数 |
| retry_delay | float | 1.0 | 0.0-60.0 | 重试延迟（秒） |

### 数据保留配置 (data_retention)

| 字段 | 类型 | 默认值 | 范围 | 说明 |
|-----|------|--------|------|------|
| kline_days | int | 365 | 1-3650 | K线数据保留天数 |
| fundamentals_days | int | 730 | 1-3650 | 基本面数据保留天数 |

### 交易时间配置 (trading_hours)

| 字段 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| morning_open | str | "09:30" | 上午开盘时间 (HH:MM) |
| morning_close | str | "11:30" | 上午收盘时间 (HH:MM) |
| afternoon_open | str | "13:00" | 下午开盘时间 (HH:MM) |
| afternoon_close | str | "15:00" | 下午收盘时间 (HH:MM) |

## 使用配置

### 在代码中访问配置

```python
from common.config import get_config

# 获取完整配置
config = get_config()

# 访问股票市场配置
stock_market_config = config.stock_market

# 访问同步配置
sync_config = config.stock_market.sync
print(sync_config.concurrency)  # 输出: 10

# 访问交易时间
trading_hours = config.stock_market.trading_hours
print(trading_hours.morning_open)  # 输出: "09:30"
```

### 使用 stock_market 配置模块

```python
from stock_market.config import (
    get_stock_market_config,
    get_sync_config,
    get_trading_hours,
    get_data_retention_config
)

# 获取配置
sync_config = get_sync_config()
trading_hours = get_trading_hours()
```

## 配置优先级

配置遵循以下优先级（从高到低）:

1. 运行时参数
2. 环境变量
3. YAML 配置文件
4. 模型默认值

### 环境变量覆盖

环境变量格式: `SECTION__SUBSECTION__FIELD`

示例:

```bash
# 覆盖并发数
export STOCK_MARKET__SYNC__CONCURRENCY=20

# 覆盖 K线工作线程数
export STOCK_MARKET__SYNC__KLINE_WORKERS=15

# 重启应用后生效
```

## 验证规则

### SyncConfig 验证

- `concurrency` ≥ 1 且 ≤ 100
- `kline_workers` ≥ 1 且 ≤ 20
- `retry_times` ≥ 0 且 ≤ 10
- `retry_delay` ≥ 0.0 且 ≤ 60.0

### DataRetentionConfig 验证

- `kline_days` ≥ 1 且 ≤ 3650
- `fundamentals_days` ≥ 1 且 ≤ 3650

### TradingHoursConfig 验证

- 时间格式必须为 `HH:MM` (24小时制)
- 例如: `09:30`, `15:00`
- 小时范围: 00-23
- 分钟范围: 00-59

## 迁移指南

### 从旧版本迁移

1. 备份现有配置
2. 更新 `config/stock_market.yaml`
3. 无需修改代码 - 自动兼容

### 已删除的功能

- ❌ `stock_market/migrations/` - 不再使用 Alembic 迁移
- ❌ `stock_market/config/database.json` - 本地 JSON 配置已废弃
- ❌ `stock_market/config/load_config()` - 旧配置加载函数已删除

## 常见问题

### Q: 如何修改并发数?

A: 编辑 `config/stock_market.yaml`:

```yaml
stock_market:
  sync:
    concurrency: 20  # 修改此值
```

或者使用环境变量:

```bash
export STOCK_MARKET__SYNC__CONCURRENCY=20
```

### Q: 配置修改后需要重启吗?

A: 是的，配置在应用启动时加载，修改后需要重启生效。

### Q: 如何验证配置是否正确?

A: 运行配置测试:

```bash
python -m pytest tests/stock_market/test_config_module.py -v
```

### Q: 如何测试环境变量覆盖?

A: 

```bash
export STOCK_MARKET__SYNC__CONCURRENCY=50
python -c "from common.config import get_config; print(get_config().stock_market.sync.concurrency)"
# 输出: 50
```

## 参考

- [通用配置文档](./02-configuration.md)
- [配置模型源码](../../common/config.py)
- [配置示例文件](../../config/stock_market.example.yaml)
- [测试总结](../../tests/stock_market/TEST_SUMMARY.md)

