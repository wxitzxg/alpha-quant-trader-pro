# 配置需求分析

## 当前配置文件列表

### 1. `common/config.py` (主配置)
**类型**: Pydantic + YAML + 环境变量
**当前模块**:
- DatabaseConfig (数据库配置)
- DataSourceConfig (数据源配置)
- FeeConfig (手续费配置)
- LoggingConfig (日志配置)
- StockMarketConfig (股票市场配置)
- PortfolioConfig (投资组合配置)
- TechnicalAnalysisConfig (技术分析配置)

### 2. `api_server/config.py`
**类型**: Pydantic Settings + 环境变量
**配置字段**:
- **基础配置**
  - API_TITLE: "Alpha Quant Trader Pro API"
  - API_VERSION: "2.0.0"
  - API_DESCRIPTION: "量化交易系统开放API"

- **服务器配置**
  - HOST: "0.0.0.0"
  - PORT: 8000
  - DEBUG: bool (从环境变量读取)

- **数据库配置**
  - DATABASE_URL: str (从环境变量读取)

- **Redis配置**
  - REDIS_URL: Optional[str] (从环境变量读取)

- **认证配置**
  - API_KEY_SECRET: str (从环境变量读取)
  - API_KEY_HEADER: "X-API-Key"
  - API_SIGNATURE_HEADER: "X-API-Signature"
  - API_TIMESTAMP_HEADER: "X-Timestamp"

- **限流配置**
  - RATE_LIMIT_FREE: 60 (免费用户每分钟)
  - RATE_LIMIT_STANDARD: 600 (标准用户每分钟)
  - RATE_LIMIT_PREMIUM: 3600 (高级用户每分钟)

- **日志配置**
  - LOG_LEVEL: str (从环境变量读取)
  - LOG_FILE: "logs/api.log"

**环境变量文件**: `.env.api`

### 3. `backtest/config.py`
**类型**: Dataclass
**配置字段**:
- **基础配置**
  - initial_capital: 100000.0 (初始资金)
  - commission_rate: 0.00025 (手续费率)
  - slippage_rate: 0.001 (滑点率)
  - stamp_duty_rate: 0.001 (印花税率)

- **回测参数**
  - start_date: "2023-01-01"
  - end_date: "2024-12-31"
  - interval: "1d" (K线周期)

- **资金管理**
  - position_size: 0.1 (单笔交易仓位)
  - max_positions: 5 (最大持仓股票数)
  - use_dynamic_position: True (是否动态调整仓位)

- **风控参数**
  - stop_loss_pct: 0.08 (止损比例)
  - take_profit_pct: 0.20 (止盈比例)
  - enable_trailing_stop: False (启用移动止损)
  - enable_position_control: True (启用仓位控制)

### 4. `simulate_trading/config/simulate_trading.yaml`
**类型**: YAML
**配置内容**:
```yaml
trading:
  execution_interval: 300 (执行间隔秒)
  check_interval: 60 (健康检查间隔秒)
  market_close_time: "15:00"
  market_open_time: "09:30"

database:
  url: "${DATABASE_URL}" (环境变量)

logging:
  level: "INFO"
  file: "logs/simulate_trading.log"
```

### 5. `simulate_trading/config/strategies.yaml`
**类型**: YAML (策略配置)
**配置内容**:
```yaml
strategies:
  aggressive: (激进型策略)
    enabled: true
    initial_cash: 80000
    max_position: 0.9
    min_position: 0.5
    stop_loss: -0.08
    take_profit: 0.15
    ...

  moderate: (稳健型策略)
    enabled: true
    initial_cash: 60000
    max_position: 0.7
    ...

  conservative: (保守型策略)
    enabled: true
    initial_cash: 50000
    max_position: 0.5
    ...
```

## 统一配置字段汇总

### 应用通用配置 (AppConfig)
```python
app_name: str = "alpha-quant-trader-pro"
debug: bool = False
environment: str = "development"  # development, testing, production
timezone: str = "Asia/Shanghai"
```

### 数据库配置 (DatabaseConfig) - 已存在
```python
url: str
pool_size: int = 10
max_overflow: int = 20
pool_pre_ping: bool = True
pool_recycle: int = 3600
connect_timeout: int = 30
```

### API服务器配置 (ApiServerConfig) - **需要新增**
```python
# 基础配置
api_title: str = "Alpha Quant Trader Pro API"
api_version: str = "2.0.0"
api_description: str = "量化交易系统开放API"

# 服务器配置
host: str = "0.0.0.0"
port: int = 8000

# Redis配置
redis_url: Optional[str] = None

# 认证配置
api_key_secret: str
api_key_header: str = "X-API-Key"
api_signature_header: str = "X-API-Signature"
api_timestamp_header: str = "X-Timestamp"

# 限流配置
rate_limit_free: int = 60
rate_limit_standard: int = 600
rate_limit_premium: int = 3600
```

### 回测配置 (BacktestConfig) - **需要新增**
```python
# 基础配置
initial_capital: float = 100000.0
commission_rate: float = 0.00025
slippage_rate: float = 0.001
stamp_duty_rate: float = 0.001

# 回测参数
start_date: str = "2023-01-01"
end_date: str = "2024-12-31"
interval: str = "1d"

# 资金管理
position_size: float = 0.1
max_positions: int = 5
use_dynamic_position: bool = True

# 风控参数
stop_loss_pct: float = 0.08
take_profit_pct: float = 0.20
enable_trailing_stop: bool = False
enable_position_control: bool = True
```

### 模拟交易配置 (SimulationConfig) - **需要新增**
```python
# 执行配置
execution_interval: int = 300  # 秒
check_interval: int = 60  # 秒
market_open_time: str = "09:30"
market_close_time: str = "15:00"

# 日志配置 (可复用 LoggingConfig)
```

### 策略配置 (StrategiesConfig) - **需要新增**
```python
strategies: Dict[str, StrategyConfig]  # 从 strategies.yaml 读取
```

### 数据源配置 (DataSourceConfig) - 已存在
```python
timeout: int = 10
max_retries: int = 3
retry_delay: float = 0.5
log_failures: bool = True
sources: Dict[str, Any] = {}
```

### 手续费配置 (FeeConfig) - 已存在
```python
stamp_duty: float = 0.001
exchange_fee: float = 0.00002
broker_commission: float = 0.0003
min_commission: float = 5.0
```

### 日志配置 (LoggingConfig) - 已存在
```python
level: str = "INFO"
format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
file_path: str = ""
max_file_size: int = 100  # MB
backup_count: int = 5
```

### 股票市场配置 (StockMarketConfig) - 已存在
```python
sync: Dict[str, Any] = {}
data_retention: Dict[str, Any] = {}
trading_hours: Dict[str, str] = {}
```

### 投资组合配置 (PortfolioConfig) - 已存在
```python
trading: Dict[str, Any] = {}
risk: Dict[str, Any] = {}
account: Dict[str, Any] = {}
```

### 技术分析配置 (TechnicalAnalysisConfig) - 已存在
```python
calculation: Dict[str, Any] = {}
indicators: Dict[str, Any] = {}
```

## 环境变量清单

### 必需环境变量
- `APP_ENV`: 运行环境 (development/testing/production)
- `DATABASE_URL`: 数据库连接字符串
- `API_KEY_SECRET`: API密钥密钥

### 可选环境变量
- `DEBUG`: 调试模式 (true/false)
- `REDIS_URL`: Redis连接字符串
- `LOG_LEVEL`: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- `TZ`: 时区设置

## 优先级规则

1. **运行时参数** (函数调用时传入) - 最高优先级
2. **环境变量** (`.env` 或系统环境变量)
3. **YAML配置文件** (`config/config.yaml` 或 `config/config.{env}.yaml`)
4. **默认值** (Pydantic模型中的默认值) - 最低优先级

## 配置文件结构建议

```
config/
├── config.yaml              # 开发环境配置
├── config.testing.yaml      # 测试环境配置
├── config.production.yaml   # 生产环境配置
├── strategies.yaml          # 策略配置（保持独立）
└── README.md                # 配置说明文档

.env.example                 # 环境变量示例
```
