# stock_market 模块配置统一化规格文档

**文档日期**: 2026-03-20
**版本**: 1.0
**项目**: Alpha Quant Trader Pro
**作者**: AI Assistant

---

## 目录

1. [概述](#概述)
2. [当前问题](#当前问题)
3. [设计目标](#设计目标)
4. [配置依赖分析](#配置依赖分析)
5. [修改范围](#修改范围)
6. [实施步骤](#实施步骤)
7. [迁移策略](#迁移策略)
8. [测试计划](#测试计划)
9. [验收标准](#验收标准)
10. [回滚方案](#回滚方案)

---

## 概述

本规格文档描述了如何将 `stock_market` 模块中的所有配置信息统一从 `common/config.py` 模块获取，移除本地硬编码配置文件，确保整个项目使用统一的配置管理系统。

### 背景

当前项目已经实现了统一的 YAML 配置管理系统（`common/config.py`），支持多层配置优先级：
- 运行时参数 > 环境变量 > YAML 配置 > 默认值

但 `stock_market` 模块仍存在本地配置文件和硬编码的配置项，导致配置管理分散，不便于维护和统一管理。

---

## 当前问题

### 1. 本地 JSON 配置文件

**文件**: `stock_market/config/database.json`

```json
{
  "database": {
    "url": "postgresql://stock_user:stock_pass@localhost:5432/stock_db",
    "pool_size": 10,
    "max_overflow": 20,
    "echo": false
  },
  "sync": {
    "kline": {
      "max_workers": 5,
      "batch_size": 1000,
      "retry_times": 3,
      "retry_delay": 1
    },
    "stock": {
      "batch_size": 500
    }
  }
}
```

**问题**:
- ❌ 硬编码数据库连接信息（包含密码）
- ❌ 与 `common/config.py` 中的 `DatabaseConfig` 重复
- ❌ 同步配置（`max_workers`, `batch_size` 等）与 `stock_market.yaml` 重复
- ❌ 配置文件格式不统一（JSON vs YAML）

### 2. 本地配置加载模块

**文件**: `stock_market/config/__init__.py`

```python
def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(__file__).parent / "database.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

**问题**:
- ❌ 独立的配置加载逻辑，与项目统一配置系统脱节
- ❌ 不支持配置优先级（运行时参数、环境变量）
- ❌ 无配置验证（无 Pydantic 模型校验）

### 3. 迁移环境使用旧配置

**文件**: `stock_market/migrations/env.py`

```python
from stock_market.config import load_config

# 使用本地配置加载
db_config = load_config()
```

**问题**:
- ❌ 迁移工具使用独立的配置加载方式
- ❌ 与运行时配置可能不一致

### 4. 硬编码配置参数

在多个文件中存在硬编码的配置值：

```python
# stock_market/sync/concurrent_sync.py
def __init__(self, db_manager: DatabaseManager, max_workers: int = 5):
    self.max_workers = max_workers  # ❌ 应该从配置获取
```

---

## 设计目标

### 主要目标

1. ✅ **移除本地配置文件**: 删除 `stock_market/config/database.json`
2. ✅ **统一配置来源**: 所有配置从 `common/config.py` 的 `ConfigManager` 获取
3. ✅ **配置复用**: 复用已有的 `Config` 模型定义（`DatabaseConfig`, `DataSourceConfig` 等）
4. ✅ **增强配置模型**: 为 `stock_market` 模块特定配置添加新的 Pydantic 模型
5. ✅ **向后兼容**: 平滑迁移，不影响现有功能

### 配置层次设计

```
Config (common/config.py)
├── database: DatabaseConfig         ← 已存在，复用
├── data_sources: DataSourceConfig   ← 已存在，复用
├── logging: LoggingConfig           ← 已存在，复用
└── stock_market: StockMarketConfig  ← 已存在，扩展
    ├── sync: dict
    │   ├── incremental: bool
    │   ├── concurrency: int
    │   ├── batch_size: int
    │   ├── interval: int
    │   ├── kline_workers: int       ← 新增
    │   ├── retry_times: int         ← 新增
    │   └── retry_delay: float       ← 新增
    ├── data_retention: dict         ← 已存在
    │   ├── kline_days: int
    │   └── fundamentals_days: int
    └── trading_hours: dict          ← 已存在
        ├── morning_open: str
        ├── morning_close: str
        ├── afternoon_open: str
        └── afternoon_close: str
```

---

## 配置依赖分析

### 现有配置文件映射

| 本地配置位置 | 配置项 | 建议迁移位置 | 状态 |
|------------|--------|------------|------|
| `database.json` → `database.url` | PostgreSQL 连接 URL | `Config.database.url` | ✅ 已有，复用 |
| `database.json` → `database.pool_size` | 连接池大小 | `Config.database.pool_size` | ✅ 已有，复用 |
| `database.json` → `database.max_overflow` | 最大溢出连接 | `Config.database.max_overflow` | ✅ 已有，复用 |
| `database.json` → `sync.kline.max_workers` | 并发工作线程数 | `Config.stock_market.sync.concurrency` | ⚠️ 需调整 |
| `database.json` → `sync.kline.batch_size` | 批次大小 | `Config.stock_market.sync.batch_size` | ✅ 已有 |
| `database.json` → `sync.kline.retry_times` | 重试次数 | `Config.stock_market.sync.retry_times` | 🔴 新增 |
| `database.json` → `sync.kline.retry_delay` | 重试延迟 | `Config.stock_market.sync.retry_delay` | 🔴 新增 |
| `stock_market/sync/concurrent_sync.py` | `max_workers=5` 默认值 | `Config.stock_market.sync.concurrency` | 🔴 需修改 |

### YAML 配置文件对应关系

| YAML 文件 | 对应 Config 模型 | 状态 |
|---------|----------------|------|
| `config/database.yaml` | `Config.database` | ✅ 已映射 |
| `config/data_sources.yaml` | `Config.data_sources` | ✅ 已映射 |
| `config/stock_market.yaml` | `Config.stock_market` | ✅ 已映射 |
| `config/app.yaml` | `Config.app_name`, `debug`, `environment` 等 | ✅ 已映射 |
| `stock_market/config/database.json` | - | ❌ 待删除 |

---

## 修改范围

### 1. 删除的文件

- [ ] `stock_market/config/database.json` ← **删除**

### 2. 修改的文件

#### A. `common/config.py`

**新增字段到 `StockMarketConfig` 模型**:

```python
class StockMarketConfig(BaseModel):
    """股票市场配置 / Stock market configuration"""

    sync: Dict[str, Any] = Field(default_factory=dict, description="数据同步配置 / Data sync config")
    # 添加以下字段（如果不存在）
    # - kline_workers: int = Field(default=5, ge=1, description="K线同步并发数 / K-line sync concurrency")
    # - retry_times: int = Field(default=3, ge=0, description="同步重试次数 / Sync retry attempts")
    # - retry_delay: float = Field(default=0.5, ge=0, description="重试延迟（秒）/ Retry delay (seconds)")

    data_retention: Dict[str, Any] = Field(default_factory=dict, description="数据保留策略 / Data retention")
    trading_hours: Dict[str, str] = Field(default_factory=dict, description="市场交易时间 / Trading hours")
```

#### B. `stock_market/config/__init__.py`

**完全重写，改为导出便捷函数**:

```python
"""
股票市场模块配置便捷函数
统一从 common.config 获取配置
"""

from common.config import get_config

def get_stock_market_config():
    """获取股票市场配置"""
    return get_config().stock_market

def get_sync_config():
    """获取同步配置"""
    return get_config().stock_market.sync

def get_trading_hours():
    """获取交易时间配置"""
    return get_config().stock_market.trading_hours

# 向后兼容（可选）
def load_config():
    """向后兼容的配置加载函数（已废弃）"""
    import warnings
    warnings.warn(
        "load_config() is deprecated. Use get_config() from common.config instead.",
        DeprecationWarning
    )
    return get_config().model_dump()
```

#### C. `stock_market/migrations/env.py`

**修改配置加载方式**:

```python
# BEFORE:
from stock_market.config import load_config
db_config = load_config()
url = db_config['database']['url']

# AFTER:
from common.config import get_config
url = get_config().database.url
```

#### D. `stock_market/sync/concurrent_sync.py`

**修改初始化参数**:

```python
# BEFORE:
def __init__(self, db_manager: DatabaseManager, max_workers: int = 5):
    self.max_workers = max_workers

# AFTER:
from common.config import get_config

def __init__(self, db_manager: DatabaseManager, max_workers: Optional[int] = None):
    self.db = db_manager
    # 从配置获取默认值
    self.max_workers = max_workers or get_config().stock_market.sync.get('concurrency', 5)
```

#### E. `config/stock_market.yaml`

**扩展配置文件**（如果需要添加新的配置项）:

```yaml
stock_market:
  sync:
    incremental: true
    concurrency: 5          # 并发同步数量
    batch_size: 100
    interval: 60

    # 新增字段（如果 common/config.py 的 StockMarketConfig 添加了）
    kline_workers: 5        # K线同步工作线程数
    retry_times: 3          # 重试次数
    retry_delay: 0.5        # 重试延迟（秒）

  data_retention:
    kline_days: 365
    fundamentals_days: 1825

  trading_hours:
    morning_open: "09:30"
    morning_close: "11:30"
    afternoon_open: "13:00"
    afternoon_close: "15:00"
```

#### F. `stock_market/config/database.json` → 删除

删除后需要检查是否有其他代码依赖此文件，确保全部迁移到 `common/config.py`。

### 3. 可能需要检查的文件

需要检查以下文件是否硬编码了配置值：

- [ ] `stock_market/services/kline_service.py` - 检查是否有硬编码的超时、重试等参数
- [ ] `stock_market/services/stock_service.py` - 同上
- [ ] `stock_market/managers/*.py` - 检查是否有硬编码配置
- [ ] `stock_market/repositories/*.py` - 检查是否有硬编码配置
- [ ] `stock_market/sync/*.py` - 检查并发、批次等配置
- [ ] `stock_market/containers.py` - 检查依赖注入配置
- [ ] 测试文件 - 确保测试也使用统一配置

---

## 实施步骤

### 阶段 1: 准备工作

1. **备份当前配置**
   - 备份 `stock_market/config/database.json`
   - 备份 `config/stock_market.yaml`
   - 记录当前的数据库连接信息（用于后续配置）

2. **审查现有配置**
   - 比较 `database.json` 和 `config/database.yaml` 中的数据库配置
   - 比较 `database.json` 中的 `sync` 配置和 `config/stock_market.yaml` 中的 `sync` 配置
   - 确保所有配置值都有对应的目标位置

3. **创建配置迁移脚本**（可选）
   - 编写脚本将 `database.json` 中的值合并到 YAML 配置文件

### 阶段 2: 扩展配置模型

1. **更新 `common/config.py`**
   - 检查 `StockMarketConfig` 模型
   - 添加缺失的字段（`kline_workers`, `retry_times`, `retry_delay`）
   - 确保字段类型、默认值和验证规则正确

2. **更新 `config/stock_market.yaml`**
   - 添加新的配置字段（如果在模型中新增了）
   - 确保配置值与 `database.json` 中的值一致

3. **测试配置加载**
   ```python
   from common.config import get_config
   config = get_config()
   print(config.stock_market.sync)  # 验证新字段
   ```

### 阶段 3: 修改代码

1. **修改 `stock_market/config/__init__.py`**
   - 删除 `load_config()` 的旧实现
   - 添加便捷函数 `get_stock_market_config()`, `get_sync_config()` 等
   - 添加向后兼容的 `load_config()`（带警告）

2. **修改 `stock_market/migrations/env.py`**
   - 替换 `from stock_market.config import load_config` 为 `from common.config import get_config`
   - 使用 `get_config().database.url` 替代 `load_config()['database']['url']`

3. **修改 `stock_market/sync/concurrent_sync.py`**
   - 更新 `__init__` 方法，从配置获取 `max_workers` 默认值
   - 删除硬编码的默认值

4. **检查并修改其他文件**
   - 搜索 `stock_market/config` 的导入
   - 搜索硬编码的配置值（`max_workers=5`, `batch_size=1000` 等）
   - 替换为从配置获取

### 阶段 4: 删除旧配置文件

1. **确认所有使用点已迁移**
   - 确保没有代码再使用 `stock_market/config/database.json`
   - 确保所有配置都从 `common/config.py` 获取

2. **删除文件**
   ```bash
   rm stock_market/config/database.json
   git rm stock_market/config/database.json
   ```

3. **更新文档**
   - 更新 `docs/admin-guide/02-configuration.md`
   - 更新 `docs/admin-guide/config-migration-guide.md`
   - 更新 README 或其他配置文档

### 阶段 5: 测试

1. **单元测试**
   - 测试配置加载是否正确
   - 测试新字段是否可用
   - 测试向后兼容的 `load_config()` 是否正常工作

2. **集成测试**
   - 测试数据库连接是否正常
   - 测试迁移工具是否正常工作
   - 测试并发同步是否使用正确的配置

3. **功能测试**
   - 运行现有的股票同步功能
   - 验证配置是否按预期工作

---

## 迁移策略

### 向后兼容性

为确保平滑迁移，采用以下策略：

1. **渐进式迁移**
   - 第一步：添加新的配置模型字段，保持旧代码不变
   - 第二步：修改代码使用新配置，保留向后兼容接口
   - 第三步：删除旧配置文件

2. **弃用警告**
   ```python
   def load_config():
       import warnings
       warnings.warn(
           "load_config() is deprecated. Use get_config() from common.config instead.",
           DeprecationWarning,
           stacklevel=2
       )
       return get_config().model_dump()
   ```

3. **配置合并**
   - 如果 `database.json` 中有 `config/stock_market.yaml` 中没有的配置
   - 先将这些配置合并到 YAML 配置文件
   - 再删除 JSON 配置文件

### 配置值映射表

| `database.json` 字段 | `stock_market.yaml` 对应字段 | 处理方式 |
|---------------------|----------------------------|---------|
| `database.url` | - (使用 `database.yaml`) | 复制到 `config/database.yaml` 或环境变量 |
| `database.pool_size` | - (使用 `database.yaml`) | 复制到 `config/database.yaml` |
| `database.max_overflow` | - (使用 `database.yaml`) | 复制到 `config/database.yaml` |
| `database.echo` | - | 添加到 `Config.database` 模型（如果需要） |
| `sync.kline.max_workers` | `sync.concurrency` | 确保值一致 |
| `sync.kline.batch_size` | `sync.batch_size` | 确保值一致 |
| `sync.kline.retry_times` | `sync.retry_times` (新增) | 添加到模型和 YAML |
| `sync.kline.retry_delay` | `sync.retry_delay` (新增) | 添加到模型和 YAML |

---

## 测试计划

### 1. 单元测试

**测试配置加载**
```python
def test_config_loading():
    from common.config import get_config
    config = get_config()

    # 测试数据库配置
    assert hasattr(config.database, 'url')
    assert config.database.pool_size == 10

    # 测试 stock_market 配置
    assert hasattr(config.stock_market, 'sync')
    assert 'concurrency' in config.stock_market.sync
    assert 'batch_size' in config.stock_market.sync
```

**测试新字段**
```python
def test_new_sync_config_fields():
    from common.config import get_config
    config = get_config()

    sync_config = config.stock_market.sync
    assert 'retry_times' in sync_config
    assert 'retry_delay' in sync_config
```

**测试向后兼容接口**
```python
def test_backward_compatible_load_config():
    from stock_market.config import load_config

    # 应该触发警告，但不抛出异常
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        config = load_config()
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
```

### 2. 集成测试

**测试数据库连接**
```python
def test_database_connection_with_new_config():
    from common.config import get_config
    from stock_market.database import DatabaseManager

    config = get_config()
    db_url = config.database.url

    # 验证 URL 格式正确
    assert db_url.startswith('postgresql://')

    # 测试连接
    db_manager = DatabaseManager()
    # ... 测试连接
```

**测试迁移工具**
```python
def test_alembic_migrations_with_new_config():
    # 确保 alembic 能正常读取配置
    # 运行 alembic current 或其他命令
    pass
```

**测试并发同步配置**
```python
def test_concurrent_sync_uses_config():
    from common.config import get_config
    from stock_market.sync.concurrent_sync import ConcurrentSyncManager

    config = get_config()
    expected_workers = config.stock_market.sync.get('concurrency', 5)

    # 默认值应该从配置获取
    manager = ConcurrentSyncManager(db_manager=None)
    assert manager.max_workers == expected_workers
```

### 3. 功能测试

**端到端同步测试**
```python
def test_end_to_end_sync_with_config():
    # 1. 使用新配置初始化系统
    # 2. 运行股票数据同步
    # 3. 验证数据正确同步
    # 4. 验证使用的配置值与预期一致
    pass
```

**配置优先级测试**
```python
def test_config_priority():
    # 测试：环境变量 > YAML 配置
    import os
    os.environ['DATABASE__URL'] = 'postgresql://test:test@localhost/test_db'

    from common.config import reload_config, get_config
    reload_config()

    config = get_config()
    assert config.database.url == 'postgresql://test:test@localhost/test_db'
```

### 4. 手动测试清单

- [ ] 启动应用，验证无配置加载错误
- [ ] 运行数据库迁移，验证配置正确
- [ ] 执行股票同步，验证并发数、批次大小等配置生效
- [ ] 修改 YAML 配置文件，重启应用，验证新值生效
- [ ] 设置环境变量覆盖配置，验证优先级正确
- [ ] 运行所有现有测试，确保无回归

---

## 验收标准

### 功能验收

- [ ] ✅ `stock_market/config/database.json` 文件已删除
- [ ] ✅ 所有配置都从 `common/config.py` 获取
- [ ] ✅ `get_config().stock_market` 可以访问所有 stock_market 相关配置
- [ ] ✅ `get_config().database` 可以访问数据库配置
- [ ] ✅ `get_config().data_sources` 可以访问数据源配置
- [ ] ✅ 数据库迁移工具正常工作
- [ ] ✅ 并发同步使用配置中的 `concurrency` 值
- [ ] ✅ 向后兼容的 `load_config()` 函数带弃用警告

### 代码质量验收

- [ ] ✅ 无硬编码的配置值（除默认值外）
- [ ] ✅ 所有新增配置字段有类型注解
- [ ] ✅ 所有新增配置字段有验证规则
- [ ] ✅ 配置模型符合 Pydantic 最佳实践
- [ ] ✅ 代码符合项目编码规范

### 测试验收

- [ ] ✅ 所有单元测试通过
- [ ] ✅ 所有集成测试通过
- [ ] ✅ 所有现有测试通过（无回归）
- [ ] ✅ 新增测试覆盖配置加载和使用
- [ ] ✅ 测试覆盖率 ≥ 80%

### 文档验收

- [ ] ✅ 配置文档已更新
- [ ] ✅ 迁移指南已更新
- [ ] ✅ 代码注释清晰
- [ ] ✅ 示例配置文件已更新

---

## 回滚方案

### 如果遇到问题

1. **恢复配置文件**
   ```bash
   git checkout HEAD -- stock_market/config/database.json
   ```

2. **恢复代码修改**
   ```bash
   git checkout HEAD -- stock_market/config/__init__.py
   git checkout HEAD -- stock_market/migrations/env.py
   git checkout HEAD -- stock_market/sync/concurrent_sync.py
   git checkout HEAD -- common/config.py
   ```

3. **重新启动应用**
   - 确保使用旧的配置加载方式
   - 验证功能正常

### 回滚检查清单

- [ ] 本地 `database.json` 文件恢复
- [ ] `stock_market/config/__init__.py` 恢复旧的 `load_config()` 实现
- [ ] `stock_market/migrations/env.py` 恢复旧的配置导入
- [ ] 应用能正常启动
- [ ] 数据库迁移正常工作
- [ ] 股票同步正常工作

---

## 附录

### 配置模型字段详细说明

#### DatabaseConfig (已存在)

```python
class DatabaseConfig(BaseModel):
    url: str = "postgresql://postgres:postgres@localhost:5432/stock_market"
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=20, ge=0)
    pool_pre_ping: bool = True
    pool_recycle: int = Field(default=3600, ge=0)
    connect_timeout: int = Field(default=30, ge=1)
```

#### StockMarketConfig (已存在，可能需要扩展)

```python
class SyncConfig(BaseModel):
    """同步配置 / Sync configuration"""
    incremental: bool = Field(default=True, description="是否启用增量同步 / Incremental sync")
    concurrency: int = Field(default=5, ge=1, description="并发同步数量 / Concurrency")
    kline_workers: int = Field(default=5, ge=1, description="K线同步工作线程数 / K-line workers")
    retry_times: int = Field(default=3, ge=0, description="同步重试次数 / Retry attempts")
    retry_delay: float = Field(default=0.5, ge=0, description="重试延迟（秒）/ Retry delay (seconds)")

class DataRetentionConfig(BaseModel):
    """数据保留配置 / Data retention configuration"""
    kline_days: int = Field(default=365, ge=0, description="K线数据保留天数 / K-line days")
    fundamentals_days: int = Field(default=1825, ge=0, description="基本面数据保留天数 / Fundamentals days")

class TradingHoursConfig(BaseModel):
    """交易时间配置 / Trading hours configuration"""
    morning_open: str = Field(default="09:30", description="上午开盘时间 / Morning open")
    morning_close: str = Field(default="11:30", description="上午收盘时间 / Morning close")
    afternoon_open: str = Field(default="13:00", description="下午开盘时间 / Afternoon open")
    afternoon_close: str = Field(default="15:00", description="下午收盘时间 / Afternoon close")

    @field_validator('morning_open', 'morning_close', 'afternoon_open', 'afternoon_close')
    @classmethod
    def validate_time_format(cls, v):
        import re
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError(f"Invalid time format: {v}")
        return v

class StockMarketConfig(BaseModel):
    """股票市场配置 / Stock market configuration"""
    sync: SyncConfig = Field(default_factory=SyncConfig, description="数据同步配置 / Data sync config")
    data_retention: DataRetentionConfig = Field(default_factory=DataRetentionConfig, description="数据保留策略 / Data retention")
    trading_hours: TradingHoursConfig = Field(default_factory=TradingHoursConfig, description="市场交易时间 / Trading hours")
```

### 配置文件示例

#### config/app.yaml

```yaml
app_name: alpha-quant-trader-pro
debug: false
environment: development
timezone: Asia/Shanghai
```

#### config/database.yaml

```yaml
database:
  url: postgresql://stock_user:stock_pass@localhost:5432/stock_db
  pool_size: 10
  max_overflow: 20
  pool_pre_ping: true
  pool_recycle: 3600
  connect_timeout: 30
```

#### config/stock_market.yaml

```yaml
stock_market:
  sync:
    incremental: true
    concurrency: 5
    batch_size: 100
    interval: 60
    kline_workers: 5
    retry_times: 3
    retry_delay: 0.5

  data_retention:
    kline_days: 365
    fundamentals_days: 1825

  trading_hours:
    morning_open: "09:30"
    morning_close: "11:30"
    afternoon_open: "13:00"
    afternoon_close: "15:00"
```

---

**文档结束**
