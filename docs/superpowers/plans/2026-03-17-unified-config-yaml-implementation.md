# 统一配置系统 (YAML) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有的 JSON 配置系统迁移到基于 YAML 的全局统一配置系统，支持环境分离和环境变量优先级。

**Architecture:** 使用 Pydantic + PyYAML 构建类型安全的配置管理系统，通过单文件设计集中管理所有模块配置，支持环境变量覆盖和启动时加载。

**Tech Stack:** Pydantic 2.0+, PyYAML 6.0+, pydantic-settings

---

## Chunk 1: 依赖和配置文件

### Task 1: 更新依赖

**Files:**
- Modify: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/requirements.txt`

- [ ] **Step 1: 添加 YAML 依赖**

```bash
# 在 requirements.txt 中添加以下行
```

在 `requirements.txt` 中，在 `pydantic>=2.0.0` 之后添加：

```txt
pyyaml>=6.0                  # YAML解析
pydantic-settings>=2.0.0     # Pydantic设置管理
```

- [ ] **Step 2: 提交依赖更新**

```bash
git add requirements.txt
git commit -m "chore: add pyyaml and pydantic-settings dependencies"
```

---

### Task 2: 创建默认配置文件

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/config/config.yaml`

- [ ] **Step 1: 创建配置文件**

```bash
mkdir -p config
```

- [ ] **Step 2: 写入配置内容**

```yaml
# ==================== 应用配置 ====================
app:
  name: "alpha-quant-trader-pro"
  debug: false
  environment: "development"
  timezone: "Asia/Shanghai"

# ==================== 数据库配置 ====================
database:
  url: "postgresql://postgres:postgres@localhost:5432/stock_market"
  pool_size: 10
  max_overflow: 20
  pool_pre_ping: true
  pool_recycle: 3600
  connect_timeout: 30

# ==================== 数据源配置 ====================
data_sources:
  timeout: 10
  max_retries: 3
  retry_delay: 0.5
  log_failures: true
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
      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 10
      - name: "sina"
        priority: 30
        enabled: true
        timeout: 5
    fundamentals:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 15
      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 15

# ==================== 手续费配置 ====================
fee:
  stamp_duty: 0.001
  exchange_fee: 0.00002
  broker_commission: 0.0003
  min_commission: 5.0

# ==================== 日志配置 ====================
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: ""
  max_file_size: 100
  backup_count: 5

# ==================== 股票市场配置 ====================
stock_market:
  sync:
    incremental: true
    concurrency: 5
    batch_size: 100
    interval: 60
  data_retention:
    kline_days: 365
    fundamentals_days: 1825
  trading_hours:
    morning_open: "09:30"
    morning_close: "11:30"
    afternoon_open: "13:00"
    afternoon_close: "15:00"

# ==================== 投资组合配置 ====================
portfolio:
  trading:
    default_amount: 10000
    min_amount: 1000
    max_position_ratio: 0.3
  risk:
    max_loss_ratio: 0.05
    max_drawdown_ratio: 0.15
  account:
    initial_capital: 1000000
    available_ratio: 0.9

# ==================== 技术分析配置 ====================
technical_analysis:
  calculation:
    concurrency: 4
    cache_ttl: 3600
  indicators:
    ma:
      periods: [5, 10, 20, 60]
    rsi:
      period: 14
    kdj:
      fast_k: 9
      slow_k: 3
      slow_d: 3
    bollinger:
      period: 20
      std_dev: 2.0
    vcp:
      consolidation_periods: 5
      breakout_threshold: 0.05
    td_sequential:
      setup_period: 9
      countdown_period: 13
```

- [ ] **Step 3: 提交配置文件**

```bash
git add config/config.yaml
git commit -m "feat: add default YAML configuration file"
```

---

### Task 3: 创建环境配置文件

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/config/config.production.yaml`
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/config/config.testing.yaml`

- [ ] **Step 1: 创建生产环境配置**

```yaml
# config/config.production.yaml
app:
  name: "alpha-quant-trader-pro"
  debug: false
  environment: "production"
  timezone: "Asia/Shanghai"

database:
  url: "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  pool_size: 20
  max_overflow: 40
  pool_pre_ping: true
  pool_recycle: 1800
  connect_timeout: 30

data_sources:
  timeout: 15
  max_retries: 5
  retry_delay: 1.0
  log_failures: true
  sources:
    realtime:
      - name: "sina"
        priority: 10
        enabled: true
        timeout: 5
      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 10
    kline:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 15
    fundamentals:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 20

fee:
  stamp_duty: 0.001
  exchange_fee: 0.00002
  broker_commission: 0.0003
  min_commission: 5.0

logging:
  level: "WARNING"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/app.log"
  max_file_size: 100
  backup_count: 10

stock_market:
  sync:
    incremental: true
    concurrency: 10
    batch_size: 200
    interval: 300
  data_retention:
    kline_days: 730
    fundamentals_days: 1825
  trading_hours:
    morning_open: "09:30"
    morning_close: "11:30"
    afternoon_open: "13:00"
    afternoon_close: "15:00"

portfolio:
  trading:
    default_amount: 50000
    min_amount: 5000
    max_position_ratio: 0.2
  risk:
    max_loss_ratio: 0.03
    max_drawdown_ratio: 0.1
  account:
    initial_capital: 10000000
    available_ratio: 0.85

technical_analysis:
  calculation:
    concurrency: 8
    cache_ttl: 7200
  indicators:
    ma:
      periods: [5, 10, 20, 60]
    rsi:
      period: 14
    kdj:
      fast_k: 9
      slow_k: 3
      slow_d: 3
    bollinger:
      period: 20
      std_dev: 2.0
    vcp:
      consolidation_periods: 5
      breakout_threshold: 0.05
    td_sequential:
      setup_period: 9
      countdown_period: 13
```

- [ ] **Step 2: 创建测试环境配置**

```yaml
# config/config.testing.yaml
app:
  name: "alpha-quant-trader-pro-test"
  debug: true
  environment: "testing"
  timezone: "Asia/Shanghai"

database:
  url: "postgresql://test:test@localhost:5432/stock_market_test"
  pool_size: 5
  max_overflow: 10
  pool_pre_ping: true
  pool_recycle: 3600
  connect_timeout: 30

data_sources:
  timeout: 5
  max_retries: 2
  retry_delay: 0.1
  log_failures: true
  sources:
    realtime:
      - name: "sina"
        priority: 10
        enabled: true
        timeout: 2
    kline:
      - name: "akshare"
        priority: 10
        enabled: true
        timeout: 5

fee:
  stamp_duty: 0.001
  exchange_fee: 0.00002
  broker_commission: 0.0003
  min_commission: 5.0

logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: ""
  max_file_size: 50
  backup_count: 3

stock_market:
  sync:
    incremental: false
    concurrency: 2
    batch_size: 50
    interval: 10
  data_retention:
    kline_days: 30
    fundamentals_days: 90
  trading_hours:
    morning_open: "09:30"
    morning_close: "11:30"
    afternoon_open: "13:00"
    afternoon_close: "15:00"

portfolio:
  trading:
    default_amount: 1000
    min_amount: 100
    max_position_ratio: 0.5
  risk:
    max_loss_ratio: 0.1
    max_drawdown_ratio: 0.2
  account:
    initial_capital: 10000
    available_ratio: 1.0

technical_analysis:
  calculation:
    concurrency: 2
    cache_ttl: 600
  indicators:
    ma:
      periods: [5, 10]
    rsi:
      period: 14
    kdj:
      fast_k: 9
      slow_k: 3
      slow_d: 3
    bollinger:
      period: 20
      std_dev: 2.0
```

- [ ] **Step 3: 更新 .gitignore**

在 `config/.gitignore` 中添加：

```gitignore
# Local overrides
config.local.yaml

# Sensitive config files
*.local.yaml
*.secret.yaml
```

- [ ] **Step 4: 提交环境配置**

```bash
git add config/config.production.yaml config/config.testing.yaml config/.gitignore
git commit -m "feat: add production and testing environment configs"
```

---

### Task 4: 创建配置示例文件

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/config/config.example.yaml`

- [ ] **Step 1: 创建完整示例配置**

（内容与设计文档中的完整示例一致，包含所有注释）

- [ ] **Step 2: 提交示例配置**

```bash
git add config/config.example.yaml
git commit -m "docs: add comprehensive config example with comments"
```

---

## Chunk 2: 配置系统核心代码

### Task 5: 实现配置系统

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/common/config.py`

- [ ] **Step 1: 编写配置类代码**

```python
"""
统一的 YAML 配置管理系统

配置优先级：运行时参数 > 环境变量 > YAML配置 > 默认值
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

logger = logging.getLogger(__name__)


# ========== 嵌套配置模型 ==========

class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/stock_market",
        description="数据库连接URL"
    )
    pool_size: int = Field(default=10, ge=1, description="连接池大小")
    max_overflow: int = Field(default=20, ge=0, description="最大溢出连接数")
    pool_pre_ping: bool = Field(default=True, description="连接预检")
    pool_recycle: int = Field(default=3600, ge=0, description="连接回收时间（秒）")
    connect_timeout: int = Field(default=30, ge=1, description="连接超时时间（秒）")


class DataSourceConfig(BaseModel):
    """数据源配置"""
    timeout: int = Field(default=10, ge=1, description="默认请求超时（秒）")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_delay: float = Field(default=0.5, ge=0, description="重试延迟（秒）")
    log_failures: bool = Field(default=True, description="是否记录失败日志")
    sources: Dict[str, Any] = Field(default_factory=dict, description="数据源列表")


class FeeConfig(BaseModel):
    """手续费配置"""
    stamp_duty: float = Field(default=0.001, ge=0, le=1, description="印花税")
    exchange_fee: float = Field(default=0.00002, ge=0, le=1, description="交易所费用")
    broker_commission: float = Field(default=0.0003, ge=0, le=1, description="券商佣金")
    min_commission: float = Field(default=5.0, ge=0, description="最低佣金（元）")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    file_path: str = Field(default="", description="日志文件路径（可选）")
    max_file_size: int = Field(default=100, ge=1, description="日志文件大小限制（MB）")
    backup_count: int = Field(default=5, ge=0, description="保留的旧日志文件数量")


class StockMarketConfig(BaseModel):
    """股票市场配置"""
    sync: Dict[str, Any] = Field(default_factory=dict, description="数据同步配置")
    data_retention: Dict[str, Any] = Field(default_factory=dict, description="数据保留策略")
    trading_hours: Dict[str, str] = Field(default_factory=dict, description="市场交易时间")


class PortfolioConfig(BaseModel):
    """投资组合配置"""
    trading: Dict[str, Any] = Field(default_factory=dict, description="交易配置")
    risk: Dict[str, Any] = Field(default_factory=dict, description="风险控制")
    account: Dict[str, Any] = Field(default_factory=dict, description="账户配置")


class TechnicalAnalysisConfig(BaseModel):
    """技术分析配置"""
    calculation: Dict[str, Any] = Field(default_factory=dict, description="计算配置")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="指标参数")


# ========== 主配置类 ==========

class Config(BaseSettings):
    """
    统一配置类

    配置优先级：运行时参数 > 环境变量 > YAML配置 > 默认值
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__"
    )

    # ========== 应用配置 ==========
    app_name: str = Field(default="alpha-quant-trader-pro", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    timezone: str = Field(default="Asia/Shanghai", description="时区设置")

    # ========== 模块配置 ==========
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig, description="数据源配置")
    fee: FeeConfig = Field(default_factory=FeeConfig, description="手续费配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")
    stock_market: StockMarketConfig = Field(default_factory=StockMarketConfig, description="股票市场配置")
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig, description="投资组合配置")
    technical_analysis: TechnicalAnalysisConfig = Field(default_factory=TechnicalAnalysisConfig, description="技术分析配置")

    # 内部使用
    _config_file: Optional[str] = None

    def __init__(self, config_file: Optional[str] = None, **kwargs):
        """
        初始化配置

        Args:
            config_file: 配置文件路径
            **kwargs: 其他配置参数（运行时参数，优先级最高）
        """
        # 确定配置文件路径
        if config_file:
            self._config_file = config_file
        else:
            env = os.getenv("APP_ENV", "development")
            if env == "development":
                self._config_file = "config/config.yaml"
            else:
                self._config_file = f"config/config.{env}.yaml"

        # 加载YAML配置
        yaml_config = self._load_yaml_config()

        # 合并配置：YAML配置 + 运行时参数
        merged_config = {**yaml_config, **kwargs}

        # 调用父类初始化
        super().__init__(**merged_config)

        logger.info(f"Configuration loaded from {self._config_file}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")

    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        if not self._config_file:
            return {}

        config_path = Path(self._config_file)

        if not config_path.exists():
            logger.warning(f"Config file not found: {self._config_file}")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config file {self._config_file}: {e}")
            raise

    def save_to_file(self, config_file: str):
        """
        保存配置到YAML文件

        Args:
            config_file: 配置文件路径
        """
        config_path = Path(config_file)
        config_dir = config_path.parent

        config_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self.model_dump()
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            logger.info(f"Saved config to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
            raise

    def get_database_url(self) -> str:
        """获取数据库连接字符串"""
        return self.database.url

    def get_fee_config(self) -> FeeConfig:
        """获取手续费配置"""
        return self.fee


# ========== 配置管理器（单例模式） ==========

class ConfigManager:
    """配置管理器"""

    _instance: Optional["ConfigManager"] = None
    _config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = Config()

    def get(self) -> Config:
        """获取配置对象"""
        return self._config

    def reload(self):
        """重新加载配置"""
        self._config = Config()
        logger.info("Configuration reloaded")


# ========== 全局配置 ==========

config_manager = ConfigManager()

# 便捷函数
get_config = config_manager.get
reload_config = config_manager.reload
save_config = config_manager.save
```

- [ ] **Step 2: 提交配置系统代码**

```bash
git add common/config.py
git commit -m "feat: implement YAML-based config system with Pydantic"
```

---

## Chunk 3: 测试

### Task 6: 编写单元测试

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/tests/test_config.py`

- [ ] **Step 1: 编写测试代码**

```python
"""
配置系统单元测试
"""

import pytest
import tempfile
from pathlib import Path
from common.config import Config, get_config, reload_config


class TestConfigLoading:
    """测试配置加载"""

    def test_load_default_config(self):
        """测试加载默认配置"""
        config = Config()
        assert config.app_name == "alpha-quant-trader-pro"
        assert config.environment == "development"
        assert config.debug is False

    def test_load_custom_config_file(self):
        """测试加载自定义配置文件"""
        yaml_content = """
app_name: "test-app"
debug: true
database:
  url: "postgresql://test:test@localhost/test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name

        try:
            config = Config(config_file=temp_file)
            assert config.app_name == "test-app"
            assert config.debug is True
            assert "test" in config.database.url
        finally:
            Path(temp_file).unlink()

    def test_environment_variable_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE__URL", "postgresql://env:env@localhost/env")

        config = Config()
        assert config.debug is True
        assert "env" in config.database.url

    def test_runtime_parameter_override(self):
        """测试运行时参数覆盖"""
        config = Config(debug=True, app_name="runtime-app")
        assert config.debug is True
        assert config.app_name == "runtime-app"


class TestConfigValidation:
    """测试配置验证"""

    def test_invalid_pool_size(self):
        """测试无效的连接池大小"""
        with pytest.raises(ValueError):
            Config(database__pool_size=0)

    def test_invalid_fee_rate(self):
        """测试无效的费率"""
        with pytest.raises(ValueError):
            Config(fee__stamp_duty=1.5)  # 超过1.0


class TestConfigSave:
    """测试配置保存"""

    def test_save_to_file(self):
        """测试保存配置到文件"""
        config = Config(app_name="save-test")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            config.save_to_file(temp_file)

            assert Path(temp_file).exists()

            with open(temp_file, 'r', encoding='utf-8') as f:
                import yaml
                saved_config = yaml.safe_load(f)
                assert saved_config['app_name'] == "save-test"
        finally:
            Path(temp_file).unlink()


class TestConfigManager:
    """测试配置管理器"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        from common.config import config_manager

        manager1 = config_manager
        manager2 = config_manager

        assert manager1 is manager2
        assert manager1.get() is manager2.get()

    def test_reload(self, monkeypatch):
        """测试重新加载"""
        monkeypatch.setenv("DEBUG", "true")
        reload_config()
        config = get_config()
        assert config.debug is True

        monkeypatch.delenv("DEBUG")
        reload_config()
        config = get_config()
        assert config.debug is False
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/test_config.py -v
```

预期输出：
```
test_config.py::TestConfigLoading::test_load_default_config PASSED
test_config.py::TestConfigLoading::test_load_custom_config_file PASSED
test_config.py::TestConfigLoading::test_environment_variable_override PASSED
test_config.py::TestConfigLoading::test_runtime_parameter_override PASSED
test_config.py::TestConfigValidation::test_invalid_pool_size PASSED
test_config.py::TestConfigValidation::test_invalid_fee_rate PASSED
test_config.py::TestConfigSave::test_save_to_file PASSED
test_config.py::TestConfigManager::test_singleton_pattern PASSED
test_config.py::TestConfigManager::test_reload PASSED
```

- [ ] **Step 3: 提交测试代码**

```bash
git add tests/test_config.py
git commit -m "test: add comprehensive config system unit tests"
```

---

### Task 7: 运行完整测试套件

- [ ] **Step 1: 运行所有测试**

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 2: 检查测试覆盖率**

```bash
pytest tests/ -v --cov=common.config --cov-report=term-missing
```

预期覆盖率：>= 80%

- [ ] **Step 3: 修复任何失败的测试**

如果现有测试失败，修复它们或更新测试以适应新的配置系统。

---

## Chunk 4: 示例和文档

### Task 8: 更新配置示例

**Files:**
- Modify: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/examples/config_example.py`

- [ ] **Step 1: 更新示例代码**

```python
"""
统一配置系统使用示例
"""

from common.config import get_config, Config, save_config


def example_load_config():
    """示例：加载配置"""
    print("=" * 60)
    print("加载配置示例")
    print("=" * 60)

    # 方式 1：获取当前配置
    config = get_config()
    print(f"✓ 应用名称: {config.app_name}")
    print(f"✓ 环境: {config.environment}")
    print(f"✓ 调试模式: {config.debug}")

    # 方式 2：获取数据库配置
    db_url = config.get_database_url()
    print(f"✓ 数据库 URL: {db_url}")

    # 方式 3：获取手续费配置
    fee_config = config.get_fee_config()
    print(f"✓ 印花税: {fee_config.stamp_duty}")
    print(f"✓ 交易所费用: {fee_config.exchange_fee}")
    print(f"✓ 券商佣金: {fee_config.broker_commission}")
    print(f"✓ 最低佣金: {fee_config.min_commission}")


def example_override_with_env():
    """示例：环境变量覆盖"""
    print("\n" + "=" * 60)
    print("环境变量覆盖示例")
    print("=" * 60)

    import os
    os.environ["DEBUG"] = "true"

    from common.config import reload_config
    reload_config()

    config = get_config()
    print(f"✓ Debug 模式: {config.debug}")

    del os.environ["DEBUG"]
    reload_config()


def example_override_with_runtime():
    """示例：运行时参数覆盖"""
    print("\n" + "=" * 60)
    print("运行时参数覆盖示例")
    print("=" * 60)

    custom_config = Config(
        app_name="my-custom-app",
        debug=True
    )
    print(f"✓ 应用名称: {custom_config.app_name}")
    print(f"✓ Debug 模式: {custom_config.debug}")


def example_save_config():
    """示例：保存配置"""
    print("\n" + "=" * 60)
    print("保存配置示例")
    print("=" * 60)

    config = get_config()
    config.debug = True

    save_config("config/local.yaml")
    print("✓ 配置已保存到 config/local.yaml")


def example_fee_calculator_with_config():
    """示例：手续费计算器使用统一配置"""
    print("\n" + "=" * 60)
    print("手续费计算器 - 使用统一配置")
    print("=" * 60)

    from portfolio_manager.fee_calculator import FeeCalculator

    calculator = FeeCalculator()

    amount = 10000.0
    buy_fee = calculator.calculate_buy_fee(amount)
    sell_fee = calculator.calculate_sell_fee(amount)

    print(f"✓ 交易金额: {amount:.2f}")
    print(f"✓ 买入手续费: {buy_fee:.2f}")
    print(f"✓ 卖出手续费: {sell_fee:.2f}")


def example_configure_logging():
    """示例：配置日志"""
    print("\n" + "=" * 60)
    print("日志配置示例")
    print("=" * 60)

    import logging
    from common.config import get_config

    config = get_config()

    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format
    )

    logger = logging.getLogger(__name__)
    logger.info("✓ 日志配置完成")


if __name__ == "__main__":
    example_load_config()
    example_override_with_env()
    example_override_with_runtime()
    example_fee_calculator_with_config()
    example_configure_logging()
    example_save_config()

    print("\n" + "=" * 60)
    print("✓ 所有配置示例执行完成")
    print("=" * 60)
```

- [ ] **Step 2: 提交示例更新**

```bash
git add examples/config_example.py
git commit -m "docs: update config example with YAML system usage"
```

---

### Task 9: 创建配置指南文档

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/docs/CONFIG_GUIDE.md`

- [ ] **Step 1: 编写配置指南**

（内容包括：快速开始、配置文件结构说明、环境变量使用、常见问题等）

- [ ] **Step 2: 提交文档**

```bash
git add docs/CONFIG_GUIDE.md
git commit -m "docs: add comprehensive configuration guide"
```

---

## Chunk 5: 配置转换工具

### Task 10: 创建JSON转YAML工具

**Files:**
- Create: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/scripts/convert_config.py`

- [ ] **Step 1: 编写转换脚本**

```python
#!/usr/bin/env python3
"""
将JSON配置文件转换为YAML格式

使用方法:
    python scripts/convert_config.py config/default.json config/config.yaml
"""

import json
import yaml
from pathlib import Path
import sys


def convert_json_to_yaml(json_file: str, yaml_file: str):
    """
    转换JSON配置到YAML

    Args:
        json_file: JSON配置文件路径
        yaml_file: YAML配置文件路径
    """
    json_path = Path(json_file)
    yaml_path = Path(yaml_file)

    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_file}")
        return False

    try:
        # 读取JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 创建输出目录
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入YAML
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"✓ 转换完成: {json_file} → {yaml_file}")
        return True

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法: python scripts/convert_config.py <input.json> <output.yaml>")
        print("\n示例:")
        print("  python scripts/convert_config.py config/default.json config/config.yaml")
        sys.exit(1)

    json_file = sys.argv[1]
    yaml_file = sys.argv[2]

    success = convert_json_to_yaml(json_file, yaml_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 添加执行权限**

```bash
chmod +x scripts/convert_config.py
```

- [ ] **Step 3: 测试转换工具**

```bash
python scripts/convert_config.py config/sources.json config/sources_converted.yaml
```

- [ ] **Step 4: 提交转换工具**

```bash
git add scripts/convert_config.py
git commit -m "feat: add JSON to YAML config conversion tool"
```

---

## Chunk 6: 向后兼容性（可选）

### Task 11: 保留旧配置系统

**Files:**
- Rename: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/common/config.py` → `common/config_legacy.py`

- [ ] **Step 1: 重命名旧配置文件**

```bash
cp common/config.py common/config_legacy.py
```

- [ ] **Step 2: 更新旧配置文件的导入**

在 `common/config_legacy.py` 中，更新所有内部导入。

- [ ] **Step 3: 提交旧配置系统**

```bash
git add common/config_legacy.py
git commit -m "chore: preserve legacy JSON config system for backward compatibility"
```

---

## Chunk 7: 清理和最终验证

### Task 12: 最终验证

- [ ] **Step 1: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 2: 运行所有测试**

```bash
pytest tests/ -v --cov=common.config --cov-report=html
```

- [ ] **Step 3: 运行示例**

```bash
python examples/config_example.py
```

- [ ] **Step 4: 验证配置加载**

```bash
python -c "from common.config import get_config; c = get_config(); print(f'App: {c.app_name}, Env: {c.environment}')"
```

- [ ] **Step 5: 检查代码质量**

```bash
python -m py_compile common/config.py
python -m py_compile tests/test_config.py
```

---

### Task 13: 更新项目文档

**Files:**
- Modify: `/home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/dataformat/README.md`

- [ ] **Step 1: 添加配置系统说明**

在 README 中添加 "配置系统" 章节，说明如何使用新的 YAML 配置系统。

- [ ] **Step 2: 提交文档更新**

```bash
git add README.md
git commit -m "docs: update README with YAML config system documentation"
```

---

### Task 14: 最终提交

- [ ] **Step 1: 查看所有更改**

```bash
git status
git diff --stat
```

- [ ] **Step 2: 创建最终提交**

```bash
git add -A
git commit -m "feat: complete YAML-based unified config system

- Implement Config class with Pydantic validation
- Add environment-specific config files (dev/prod/test)
- Create comprehensive config.example.yaml with comments
- Add unit tests with 80%+ coverage
- Provide JSON to YAML conversion tool
- Update examples and documentation
- Support environment variable overrides

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 验收标准

- [ ] 所有单元测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] 示例代码运行成功
- [ ] 配置文件可以正常加载
- [ ] 环境变量覆盖功能正常
- [ ] 配置保存功能正常
- [ ] 文档完整且准确

---

**Plan complete and saved to `docs/superpowers/plans/2026-03-17-unified-config-yaml-implementation.md`. Ready to execute?**
