# 股票数据源聚合模块 (data_sources)

统一的数据访问层，聚合多个股票市场数据源，支持自动降级和优先级配置。

## 特性

- ✅ **统一接口** - 对上层业务提供一致的数据访问 API
- ✅ **自动降级** - 支持配置数据源优先级，失败时自动降级到备用源
- ✅ **可扩展** - 方便新增数据源适配器，无需修改核心逻辑
- ✅ **配置驱动** - JSON 配置文件定义数据源优先级和超时设置

## 支持的数据源

| 数据源 | 优势 | 状态 |
|--------|------|------|
| Tushare Pro | 数据规范、稳定、基本面数据强 | 待实现 |
| AKShare | 免费、覆盖广、特色数据丰富 | 待实现 |
| 新浪财经 | 实时性强、免费、速度快 | 待实现 |
| 东方财富 | 数据全面、复权数据好 | 待实现 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用示例

```python
from data_sources import QuoteAPI, KLineAPI, FundamentalsAPI

# 获取实时行情
quote = QuoteAPI.get_realtime("600519")
print(f"贵州茅台: {quote.price} 元")

# 批量获取实时行情
quotes = QuoteAPI.batch_get_realtime(["600519", "000001", "601318"])

# 获取历史K线
klines = KLineAPI.get(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 获取基本面数据
balance = FundamentalsAPI.get_balance_sheet("600519", year=2023, quarter=3)
indicators = FundamentalsAPI.get_indicators("600519", year=2023, quarter=3)
```

## 架构设计

```
┌─────────────────────────────────────────┐
│         数据源聚合模块 (data_sources)    │
│  ┌─────────────────────────────────┐  │
│  │   DataSourceAggregator (单例)   │  │
│  │  - 统一入口                      │  │
│  └────────────┬────────────────────┘  │
│               │                        │
│  ┌────────────▼────────────────────┐  │
│  │   FallbackExecutor              │  │
│  │  - 优先级执行 + 自动降级        │  │
│  └────────────┬────────────────────┘  │
│               │                        │
│  ┌────────────▼────────────────────┐  │
│  │   AdapterRegistry               │  │
│  │  - 自动发现适配器                │  │
│  └────────────┬────────────────────┘  │
│               │                        │
│  ┌────────────┴────────────────────┐  │
│  │  ┌──────────┬──────────┬───────┐ │
│  │  │ Tushare  │ AKShare  │ Sina  │ │
│  │  │ Adapter  │ Adapter  │ Adapter│ │
│  │  └──────────┴──────────┴───────┘ │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 核心组件

- **DataSourceAggregator** - 单例模式，提供统一的数据访问接口
- **FallbackExecutor** - 按优先级执行，失败自动降级 + 重试
- **AdapterRegistry** - 适配器自动发现和注册
- **DataSourceAdapter** - 抽象基类定义统一接口

## 配置文件

配置文件位置: `config/sources.json`

```json
{
  "version": "1.0",
  "sources": {
    "realtime": [
      {"name": "sina", "priority": 10, "enabled": true, "timeout": 3},
      {"name": "akshare", "priority": 20, "enabled": true, "timeout": 5},
      {"name": "tushare", "priority": 30, "enabled": true, "timeout": 5}
    ],
    "kline": [
      {"name": "tushare", "priority": 10, "enabled": true, "timeout": 10},
      {"name": "akshare", "priority": 20, "enabled": true, "timeout": 10},
      {"name": "sina", "priority": 30, "enabled": true, "timeout": 5}
    ],
    "fundamentals": [
      {"name": "tushare", "priority": 10, "enabled": true, "timeout": 15},
      {"name": "akshare", "priority": 20, "enabled": true, "timeout": 15}
    ]
  },
  "fallback": {
    "max_retries": 2,
    "retry_delay": 0.5,
    "log_failures": true
  }
}
```

## 测试

运行所有测试:

```bash
pytest tests/ -v
```

查看测试覆盖率:

```bash
pytest tests/ -v --cov=data_sources --cov-report=html
```

## 项目进度

### ✅ 已完成 (Chunk 1 & 2)

- [x] **Chunk 1: 基础设施**
  - [x] 数据模型 (models.py) - Pydantic 模型
  - [x] 异常定义 (exceptions.py)
  - [x] 抽象接口 (base.py) - DataSourceAdapter
  - [x] 单元测试 (17个测试全部通过)

- [x] **Chunk 2: 核心引擎**
  - [x] 适配器注册表 (registry.py) - 自动发现
  - [x] 降级执行器 (executor.py) - 自动重试 + 降级
  - [x] 数据源聚合器 (aggregator.py) - 单例 + 统一 API
  - [x] 配置文件 (config/sources.json)
  - [x] 单元测试

### 🚧 进行中/待实现 (Chunk 3 & 4)

- [ ] **Chunk 3: 数据源适配器**
  - [ ] Tushare 适配器
  - [ ] AKShare 适配器
  - [ ] 新浪财经适配器
  - [ ] 东方财富适配器

- [ ] **Chunk 4: 集成测试和文档**
  - [ ] 集成测试
  - [ ] 使用文档
  - [ ] 部署文档

## 开发计划

详见: `docs/superpowers/plans/2026-03-15-stock-data-source-implementation.md`

## 目录结构

```
data_sources/
├── __init__.py              # 模块入口
├── models.py                # Pydantic 数据模型
├── exceptions.py            # 自定义异常
├── base.py                  # 抽象适配器接口
├── registry.py              # 适配器注册表
├── executor.py              # 降级执行器
├── aggregator.py            # 数据源聚合器
└── adapters/                # 数据源适配器
    └── __init__.py

tests/
├── test_models.py           # 数据模型测试
├── test_exceptions.py       # 异常测试
├── test_base.py             # 抽象接口测试
├── test_registry.py         # 注册表测试
├── test_executor.py         # 执行器测试
└── test_aggregator.py       # 聚合器测试

config/
└── sources.json             # 配置文件
```

## 许可证

MIT License
