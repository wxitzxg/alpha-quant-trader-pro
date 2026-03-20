# 股票数据源聚合模块 (data_sources)

统一的数据访问层，聚合多个股票市场数据源，支持自动降级和优先级配置。

## 特性

- ✅ **统一接口** - 对上层业务提供一致的数据访问 API
- ✅ **自动降级** - 支持配置数据源优先级，失败时自动降级到备用源
- ✅ **可扩展** - 方便新增数据源适配器，无需修改核心逻辑
- ✅ **配置驱动** - YAML 配置文件定义数据源优先级和超时设置
- ✅ **环境隔离** - 通过 .env 文件管理环境变量（Token、API Key等）

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
quote = QuoteAPI.get("600519")
print(f"贵州茅台: {quote.price} 元")

# 批量获取实时行情
quotes = QuoteAPI.batch_get(["600519", "000001", "601318"])

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

配置文件位置: `config/data_sources.yaml`

```yaml
data_sources:
  timeout: 10
  max_retries: 3
  retry_delay: 0.5
  log_failures: true

  # 数据源特定配置（Token、API Key等敏感信息从环境变量读取）
  source_config:
    tushare:
      token: "${TUSHARE_TOKEN}"
    investoday:
      api_key: "${INVESTODAY_API_KEY}"
    akshare: {}

  # 数据源列表
  sources:
    realtime:
      - name: "sina"
        priority: 10
        enabled: true
        timeout: 3
      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 5
      - name: "tushare"
        priority: 30
        enabled: true
        timeout: 5

    kline:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 10

    fundamentals:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 15
      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 15
```

**环境变量文件**: `.env` (不提交到 Git)

```bash
# Tushare Token
TUSHARE_TOKEN=your_tushare_token_here

# Investoday API Key
INVESTODAY_API_KEY=your_investoday_api_key_here

# 环境切换
APP_ENV=development  # production, test
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

### ✅ 已完成

- [x] **基础设施**
  - [x] 数据模型 (models.py) - Pydantic 模型
  - [x] 异常定义 (exceptions.py)
  - [x] 抽象接口 (base.py) - DataSourceAdapter
  - [x] 单元测试

- [x] **核心引擎**
  - [x] 适配器注册表 (registry.py) - 自动发现
  - [x] 降级执行器 (executor.py) - 自动重试 + 降级
  - [x] 数据源聚合器 (aggregator.py) - 线程安全单例 + 统一 API
  - [x] 配置系统 - 统一 YAML 配置 + 环境变量
  - [x] 单元测试

- [x] **数据源适配器**
  - [x] Tushare 适配器 (完整版)
  - [x] AKShare 适配器 (完整版)
  - [x] 新浪财经适配器 (完整版)
  - [x] Investoday 适配器 (完整版)

### 🎯 配置系统特点

- **统一 YAML 配置**: 所有模块配置集中管理
- **环境变量支持**: 敏感信息通过 .env 文件管理
- **配置一致性**: 方法名与配置键完全一致（无映射表）
- **构造函数参数化**: 所有适配器支持 priority/timeout 参数
- **模块化配置**: 每个模块独立 YAML 配置文件

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
├── config.yaml                # 主配置文件
├── config.development.yaml    # 开发环境配置
├── config.production.yaml     # 生产环境配置
└── data_sources.yaml          # 数据源模块配置

.env.example                     # 环境变量示例（提交到 Git）
.env                             # 环境变量文件（不提交到 Git）
```

## 许可证

MIT License
