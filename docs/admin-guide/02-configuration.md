# ⚙️ 配置指南

> 统一配置系统完整指南 - Unified Configuration System Guide

---

## 📋 目录

1. [配置概述](#配置概述)
2. [配置优先级](#配置优先级)
3. [环境变量](#环境变量)
4. [配置文件](#配置文件)
5. [模块配置说明](#模块配置说明)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)

---

## 📝 配置概述

### 配置架构

系统使用 **统一配置管理系统**，基于 Pydantic 提供类型安全的配置管理。

**核心特性**:
- ✅ 配置集中管理
- ✅ 类型安全验证
- ✅ 多环境支持 (development/testing/production)
- ✅ 环境变量覆盖
- ✅ YAML 配置文件
- ✅ 运行时热重载

### 配置文件结构

```
project-root/
├── config/
│   ├── config.yaml              # 开发环境配置 (默认)
│   ├── config.testing.yaml      # 测试环境配置
│   ├── config.production.yaml   # 生产环境配置
│   └── strategies.yaml          # 策略配置 (保持独立)
├── .env.example                 # 环境变量示例
├── .env                         # 本地环境变量 (不在版本控制)
└── common/config.py             # 配置核心实现
```

---

## ⚡ 配置优先级

配置按照以下优先级加载 (从高到低):

```
1. 运行时参数 (Runtime parameters)
   ↓
2. 环境变量 (Environment variables)
   ↓
3. YAML 配置文件 (YAML config files)
   ↓
4. 默认值 (Default values in Pydantic models)
```

### 优先级示例

```bash
# config.yaml
database:
  url: "postgresql://localhost/dev_db"

# .env
DATABASE_URL="postgresql://localhost/prod_db"

# 代码中
from common.config import get_config
config = get_config()

# 实际使用的值
print(config.database.url)  # "postgresql://localhost/prod_db" (环境变量优先)
```

---

## 🔧 环境变量

### 环境变量命名规则

使用双下划线 `__` 分隔嵌套配置:

```bash
# 格式: {SECTION}__{FIELD}
# 示例:
DATABASE__URL="postgresql://..."
API_SERVER__PORT=8000
BACKTEST__INITIAL_CAPITAL=100000
```

### 必需环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `APP_ENV` | 运行环境 | `development` / `testing` / `production` |
| `DATABASE_URL` | 数据库连接字符串 | `postgresql://user:pass@localhost:5432/stock_market` |

### 可选环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `false` | 调试模式 |
| `REDIS_URL` | `null` | Redis 连接字符串 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `TZ` | `Asia/Shanghai` | 时区设置 |
| `API_SERVER__API_KEY_SECRET` | - | API 密钥密钥 |

### 环境变量文件

**复制示例文件**:
```bash
cp .env.example .env
```

**编辑 `.env` 文件**:
```bash
# .env
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_market
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
```

---

## 📄 配置文件

### config.yaml (开发环境)

完整配置示例见: [`config/config.yaml`](../../config/config.yaml)

### 多环境配置

系统根据 `APP_ENV` 环境变量自动选择配置文件:

```bash
# 开发环境 (默认)
APP_ENV=development  # 加载 config/config.yaml

# 测试环境
APP_ENV=testing      # 加载 config/config.testing.yaml

# 生产环境
APP_ENV=production   # 加载 config/config.production.yaml
```

### 创建新环境配置

```bash
# 复制开发配置
cp config/config.yaml config/config.production.yaml

# 编辑生产配置
nano config/config.production.yaml

# 设置生产环境变量
echo "APP_ENV=production" > .env
```

---

## 📦 模块配置说明

### 1. 应用通用配置 (AppConfig)

```yaml
app_name: "alpha-quant-trader-pro"
debug: false
environment: "development"
timezone: "Asia/Shanghai"
```

**字段说明**:
- `app_name`: 应用名称
- `debug`: 调试模式 (开发环境设为 true)
- `environment`: 运行环境
- `timezone`: 时区设置

---

### 2. 数据库配置 (DatabaseConfig)

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/stock_market"
  pool_size: 10
  max_overflow: 20
  pool_pre_ping: true
  pool_recycle: 3600
  connect_timeout: 30
```

**字段说明**:
- `url`: PostgreSQL 连接字符串
- `pool_size`: 连接池大小
- `max_overflow`: 最大溢出连接数
- `pool_pre_ping`: 连接预检 (防止失效连接)
- `pool_recycle`: 连接回收时间 (秒)
- `connect_timeout`: 连接超时时间 (秒)

---

### 3. 数据源配置 (DataSourceConfig)

```yaml
data_sources:
  timeout: 10
  max_retries: 3
  retry_delay: 0.5
  log_failures: true
  sources:
    akshare:
      enabled: true
      base_url: "https://api.akshare.com"
    sina:
      enabled: true
    investoday:
      enabled: true
```

**字段说明**:
- `timeout`: 请求超时 (秒)
- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟 (秒)
- `sources`: 数据源列表

---

### 4. 手续费配置 (FeeConfig)

```yaml
fee:
  stamp_duty: 0.001           # 印花税 (千分之1)
  exchange_fee: 0.00002       # 交易所费用 (万分之0.2)
  broker_commission: 0.0003   # 券商佣金 (万分之3)
  min_commission: 5.0         # 最低佣金 (5元)
```

---

### 5. API 服务器配置 (ApiServerConfig)

```yaml
api_server:
  api_title: "Alpha Quant Trader Pro API"
  api_version: "2.0.0"
  api_description: "量化交易系统开放API"
  host: "0.0.0.0"
  port: 8000
  redis_url: null
  api_key_secret: "your-secret-key-change-in-production"
  rate_limit_free: 60
  rate_limit_standard: 600
  rate_limit_premium: 3600
```

**字段说明**:
- `api_title`: API 标题
- `api_version`: API 版本
- `host/port`: 服务器监听地址和端口
- `redis_url`: Redis 连接 (用于限流)
- `rate_limit_*`: 不同用户等级的限流配置

---

### 6. 回测配置 (BacktestConfig)

```yaml
backtest:
  initial_capital: 100000.0
  commission_rate: 0.00025
  slippage_rate: 0.001
  stamp_duty_rate: 0.001
  start_date: "2023-01-01"
  end_date: "2024-12-31"
  interval: "1d"
  position_size: 0.1
  max_positions: 5
  stop_loss_pct: 0.08
  take_profit_pct: 0.20
```

**字段说明**:
- `initial_capital`: 初始资金
- `commission_rate`: 手续费率
- `slippage_rate`: 滑点率
- `start_date/end_date`: 回测时间范围
- `position_size`: 单笔交易仓位
- `stop_loss_pct`: 止损比例

---

### 7. 模拟交易配置 (SimulationConfig)

```yaml
simulation:
  execution_interval: 300       # 执行间隔 (5分钟)
  check_interval: 60            # 健康检查间隔 (1分钟)
  market_open_time: "09:30"
  market_close_time: "15:00"
  log_file: "logs/simulate_trading.log"
```

---

### 8. 策略配置 (Strategies)

策略配置保持独立文件: [`simulate_trading/config/strategies.yaml`](../../simulate_trading/config/strategies.yaml)

包含三种策略:
- `aggressive`: 激进型 (高仓位、高风险)
- `moderate`: 稳健型 (中等仓位、平衡风险)
- `conservative`: 保守型 (低仓位、低风险)

---

## 💻 使用示例

### 1. 基本使用

```python
from common.config import get_config

# 获取全局配置
config = get_config()

# 访问配置
print(f"应用名称: {config.app_name}")
print(f"环境: {config.environment}")
print(f"数据库: {config.database.url}")
print(f"API端口: {config.api_server.port}")
```

### 2. 获取特定模块配置

```python
from common.config import get_config

config = get_config()

# 数据库配置
db_config = config.database
print(f"数据库连接池: {db_config.pool_size}")

# 回测配置
bt_config = config.backtest
print(f"回测初始资金: {bt_config.initial_capital}")

# API配置
api_config = config.api_server
print(f"API限流: {api_config.rate_limit_free}/分钟")
```

### 3. 运行时覆盖配置

```python
from common.config import Config

# 创建自定义配置
custom_config = Config(
    debug=True,
    environment="testing",
    api_server__port=9000  # 使用嵌套参数
)

print(f"调试模式: {custom_config.debug}")
print(f"API端口: {custom_config.api_server.port}")
```

### 4. 保存配置到文件

```python
from common.config import save_config

# 保存当前配置
save_config("config/local.yaml")

# 从文件加载配置
from common.config import Config
config = Config(config_file="config/local.yaml")
```

### 5. 热重载配置

```python
from common.config import reload_config

# 重新加载配置 (例如配置文件更新后)
reload_config()
```

### 6. 兼容旧代码

**api_server/config.py** (自动从统一配置读取):
```python
from api_server.config import settings

# 旧代码无需修改
print(settings.HOST)
print(settings.PORT)
print(settings.DATABASE_URL)
```

**backtest/config.py** (自动从统一配置读取):
```python
from backtest.config import BacktestConfig

# 默认使用统一配置
config = BacktestConfig()

# 也可以覆盖特定字段
config = BacktestConfig(initial_capital=200000)
```

---

## ❓ 常见问题

### Q1: 如何添加新的配置字段?

**步骤 1**: 在 `common/config.py` 中添加 Pydantic 模型字段

```python
class MyModuleConfig(BaseModel):
    new_field: str = Field(default="default_value", description="新字段说明")
```

**步骤 2**: 在主 `Config` 类中添加配置字段

```python
class Config(BaseSettings):
    my_module: MyModuleConfig = Field(default_factory=MyModuleConfig)
```

**步骤 3**: 在 `config/config.yaml` 中添加默认值

```yaml
my_module:
  new_field: "default_value"
```

### Q2: 如何在生产环境使用不同的配置?

```bash
# 方法1: 使用环境变量文件
cp config/config.yaml config/config.production.yaml
# 编辑生产配置...
echo "APP_ENV=production" > .env

# 方法2: 使用环境变量覆盖
export APP_ENV=production
export DATABASE__URL="postgresql://prod_user:prod_pass@prod_host:5432/prod_db"
```

### Q3: 配置修改后如何生效?

**开发环境**: 重启应用或调用 `reload_config()`

```python
from common.config import reload_config
reload_config()
```

**生产环境**: 重启服务

```bash
# Docker
docker-compose restart api-server

# Systemd
sudo systemctl restart alpha-quant-trader
```

### Q4: 如何查看当前生效的配置?

```python
from common.config import get_config
import json

config = get_config()
print(json.dumps(config.model_dump(), indent=2, ensure_ascii=False))
```

### Q5: 环境变量和 YAML 配置冲突怎么办?

环境变量优先级高于 YAML 配置。如需强制使用 YAML 配置，删除对应的环境变量。

---

## 📚 相关文档

- [快速开始](./01-quick-start.md)
- [部署指南](./03-deployment.md)
- [数据源配置](./05-data-source-setup.md)
- [性能调优](./08-performance-tuning.md)
- [故障排查](./09-troubleshooting.md)

---

**版本**: v2.0.0
**最后更新**: 2026-03-19
