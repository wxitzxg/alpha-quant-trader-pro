# 股票市场管理模块 - 快速参考

## 一键初始化

```python
from stock_market.database import DatabaseManager
from stock_market.managers.stock_manager import StockDataManager
from stock_market.managers.kline_manager import KLineDataManager

db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
stocks = StockDataManager(db)
klines = KLineDataManager(db)
```

## 核心功能速查

### 股票管理
```python
# 同步股票列表
stocks.sync_all_stocks()

# 获取股票列表
all_stocks = stocks.get_active_stocks()

# 按行业查询
bank_stocks = stocks.get_stocks_by_industry("银行")

# 按概念查询
wine_stocks = stocks.get_stocks_by_concept("白酒")

# 获取单只股票
stock = stocks.get_stock("600000")
```

### K线管理
```python
# 同步单只股票K线
klines.sync_single_kline(
    symbol="600000",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 查询K线
data = klines.query_klines(
    symbol="600000",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-01-31"
)

# 获取最新K线
latest = klines.get_latest_kline("600000", "1d")
```

### 并发同步
```python
from stock_market.sync.concurrent_sync import ConcurrentSyncManager

concurrent = ConcurrentSyncManager(db, max_workers=5)
results = concurrent.sync_klines_concurrently(
    symbols=["600000", "600001", "600002"],
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### 增量同步
```python
from stock_market.sync.incremental_sync import IncrementalSyncStrategy

strategy = IncrementalSyncStrategy(db)

# 增量同步（自动检测时间范围）
klines.sync_single_kline(symbol="600000", interval="1d")

# 检查缺失日期
missing = strategy.get_missing_dates(
    symbol="600000",
    interval="1d",
    start_date=date(2023, 1, 1),
    end_date=date(2023, 1, 31)
)

# 获取同步缺口
gaps = strategy.get_sync_gaps("600000", "1d")
```

### 日期工具
```python
from stock_market.utils.date_utils import *

# 交易日列表
days = get_trade_days(date(2023, 1, 1), date(2023, 1, 31))

# 格式化
date_str = format_date(date(2023, 1, 1))  # "2023-01-01"

# 解析
date_obj = parse_date("2023-01-01")

# 月份范围
start, end = get_month_range(2023, 1)
```

## 周期参数

| 参数 | 说明 |
|------|------|
| `1d` | 日线 |
| `5d` | 5日线 |
| `10d` | 10日线 |
| `1M` | 月线 |

## 数据模型字段

### Stock 股票
- `symbol`: 股票代码
- `name`: 股票名称
- `exchange`: 交易所
- `list_date`: 上市日期
- `industry`: 行业
- `concept`: 概念
- `shares`: 总股本

### KLine K线
- `symbol`: 股票代码
- `date`: 日期
- `interval`: 周期
- `open/high/low/close`: OHLC
- `volume`: 成交量
- `amount`: 成交额
- `ma5/ma10/ma20/ma30/ma60`: 移动平均线

## 运行测试

```bash
# 单元测试
pytest tests/ -v

# 特定测试
pytest tests/test_integration.py -v

# 覆盖率
pytest tests/ -v --cov=stock_market
```

## 常用命令

```bash
# 运行示例
python examples/usage.py

# 数据库迁移
cd stock_market/migrations && alembic upgrade head

# 创建数据库
createdb stock_market

# 查看文档
cat docs/STOCK_MARKET_MODULE.md
```
