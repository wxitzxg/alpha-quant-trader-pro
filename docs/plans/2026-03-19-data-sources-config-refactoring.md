# 数据源配置系统重构方案

**日期**: 2026-03-19
**分支**: datasource
**评审**: /plan-eng-review
**状态**: ✅ 方案确认，待实施

---

## 📋 问题概述

`data_sources/` 模块存在配置割裂、验证缺失、代码不优雅等问题。

---

## 🎯 重构目标

1. **统一配置入口** - `DataSourceAggregator` 通过 `Config.py` 读取配置
2. **集中验证** - 在 `Config.py` 使用 Pydantic 统一验证
3. **代码优雅** - 使用 property setter 替代私有属性操作
4. **删除冗余** - 删除 aggregator 的所有文件加载逻辑

---

## 🔍 问题分析与解决方案

### 问题 1: 配置割裂（双配置系统）

**现状**:
- `config/data_sources.yaml` - YAML 格式配置文件
- `data_sources/aggregator.py` - 硬编码的 JSON 默认配置
- `aggregator` 只能加载 JSON，无法使用 YAML

**选择**: **B** - Config.py 读取 data_sources.yaml

**方案**:
1. 保留 `config/data_sources.yaml`
2. 修改 `common/config.py`，添加 `DataSourceConfig` 模型
3. `Config.py` 读取 `config/data_sources.yaml`
4. `DataSourceAggregator` 从 `Config.py` 获取配置（不读文件）

**优点**:
- 配置文件保持分离（关注点分离）
- 通过统一配置系统访问（单一入口）
- 避免用户困惑

---

### 问题 2: 配置验证缺失

**现状**:
```python
self.config = json.load(f)  # ❌ 无验证
```

**选择**: **A** - 在 Config.py 中添加 Pydantic 验证 + 删除 JSON 加载

**方案**:
1. 在 `common/config.py` 定义 Pydantic 模型
2. 配置加载时自动验证
3. **删除 `aggregator.py` 中的所有文件加载代码**

**优点**:
- 配置错误立即报错
- 有清晰的错误信息
- 类型安全

---

### 问题 3: 优先级设置方式不优雅

**现状**:
```python
if hasattr(adapter, '_priority'):
    adapter._priority = source_cfg.get('priority', 100)  # ❌ 私有属性
```

**选择**: **A** - 在基类中添加 priority setter

**方案**:
```python
# base.py
class DataSourceAdapter(ABC):
    def __init__(self):
        self._priority = 100  # 默认优先级

    @property
    def priority(self) -> int:
        return self._priority

    @priority.setter  # ✅ 添加 setter
    def priority(self, value: int):
        self._priority = value
```

```python
# aggregator.py
adapter.priority = source_cfg.get('priority', 100)  # ✅ 使用 property
```

**优点**:
- Pythonic，符合面向对象原则
- 代码更清晰
- 易于测试

---

### 问题 4: 配置文件格式不一致

**现状**:
- 项目其他配置用 YAML
- `aggregator.py` 只支持 JSON

**选择**: **删除所有文件加载** - aggregator 从 config.py 读取，不加载任何文件

**方案**:
- **删除 `aggregator.py` 中的所有文件加载逻辑**
- 改为从 `Config.py` 读取配置
- 删除 `config_path` 参数
- 无需关心 JSON/YAML 格式

**优点**:
- 简化代码
- 与项目其他模块一致
- 配置验证统一

---

## 📝 实施步骤

### 步骤 1: 修改 common/config.py

**任务**:
1. 添加 `DataSourceItem` Pydantic 模型
2. 添加 `DataSourcesConfig` 模型
3. 更新 `DataSourceConfig` 模型
4. 修改 `Config` 类，读取 `config/data_sources.yaml`
5. 添加配置验证逻辑

**代码示例**:
```python
# common/config.py

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class DataSourceItem(BaseModel):
    """数据源配置项"""
    name: str = Field(..., description="数据源名称")
    priority: int = Field(100, ge=0, description="优先级，越小越优先")
    enabled: bool = Field(True, description="是否启用")
    timeout: int = Field(5, ge=1, description="超时时间（秒）")

    @validator('name')
    def validate_name(cls, v):
        allowed = ['sina', 'akshare', 'tushare', 'investoday']
        if v not in allowed:
            raise ValueError(f"name 必须是 {allowed} 之一")
        return v

class DataSourcesConfig(BaseModel):
    """数据源优先级配置"""
    realtime: List[DataSourceItem] = Field(default_factory=list)
    kline: List[DataSourceItem] = Field(default_factory=list)
    fundamentals: List[DataSourceItem] = Field(default_factory=list)

class DataSourceConfig(BaseModel):
    """数据源主配置"""
    timeout: int = Field(10, ge=1, description="默认超时")
    max_retries: int = Field(3, ge=0, description="最大重试次数")
    retry_delay: float = Field(0.5, ge=0, description="重试延迟")
    log_failures: bool = Field(True, description="是否记录失败")
    sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)
    fallback: Dict[str, Any] = Field(default_factory=dict)

# 修改 Config.__init__
def __init__(self, config_file: Optional[str] = None, **kwargs):
    # ... 原有逻辑

    # 加载 data_sources.yaml
    data_sources_config = self._load_data_sources_config()
    if data_sources_config:
        # 合并数据源配置
        if 'data_sources' in merged_config:
            merged_config['data_sources'].update(data_sources_config)
        else:
            merged_config['data_sources'] = data_sources_config

    super().__init__(**merged_config)

def _load_data_sources_config(self) -> Dict[str, Any]:
    """加载数据源专用配置"""
    config_path = Path("config/data_sources.yaml")
    if not config_path.exists():
        logger.warning("config/data_sources.yaml 不存在，使用空配置")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载 data_sources.yaml 失败: {e}")
        return {}
```

---

### 步骤 2: 修改 data_sources/base.py

**任务**:
1. 在 `DataSourceAdapter` 基类中添加 `_priority` 属性
2. 添加 `priority` setter

**代码示例**:
```python
# data_sources/base.py

class DataSourceAdapter(ABC):
    """数据源适配器抽象基类"""

    def __init__(self):
        """初始化适配器"""
        self._priority = 100  # 默认优先级

    @property
    def priority(self) -> int:
        """数据源优先级"""
        return self._priority

    @priority.setter
    def priority(self, value: int):
        """设置数据源优先级"""
        self._priority = value

    # ... 其他抽象方法
```

---

### 步骤 3: 修改 data_sources/aggregator.py

**任务**:
1. **删除 `_load_config()` 方法**
2. **删除 `_get_default_config()` 方法**
3. **删除 `config_path` 参数**
4. 从 `Config.py` 直接获取配置
5. 使用 property setter 设置优先级

**修改后的代码**:
```python
# data_sources/aggregator.py

import logging
from typing import List, Optional, Dict, Any
from .base import DataSourceAdapter
from .registry import AdapterRegistry
from .executor import FallbackExecutor
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from common.config import get_config

logger = logging.getLogger(__name__)


class DataSourceAggregator:
    """数据源聚合器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式 - 删除 config_path 参数"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化聚合器 - 不再接受配置文件路径"""
        if self._initialized:
            return

        self.config: Dict[str, Any] = {}
        self.registry = AdapterRegistry()
        self.executor: Optional[FallbackExecutor] = None

        # 从统一配置系统加载配置
        self._load_config_from_config_system()

        # 创建执行器
        self.executor = FallbackExecutor(self.config)

        # 自动发现并初始化适配器
        self._initialize_adapters()

        self._initialized = True
        logger.info("DataSourceAggregator initialized successfully")

    def _load_config_from_config_system(self):
        """从统一配置系统加载配置 - 不加载任何文件"""
        config = get_config()

        # 从 Config.py 获取数据源配置
        data_sources_config = config.data_sources

        # 转换为 aggregator 需要的格式
        self.config = {
            "version": "2.0",
            "sources": {
                "realtime": [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data_sources_config.sources.realtime
                ],
                "kline": [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data_sources_config.sources.kline
                ],
                "fundamentals": [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data_sources_config.sources.fundamentals
                ]
            },
            "fallback": {
                "max_retries": data_sources_config.max_retries,
                "retry_delay": data_sources_config.retry_delay,
                "log_failures": data_sources_config.log_failures
            }
        }

        logger.info("从统一配置系统加载数据源配置成功")
```

**删除的代码**:
```python
# ❌ 完全删除以下内容：

# 1. 删除 config_path 参数
# def __init__(self, config_path: str = "config/sources.json"):

# 2. 删除整个 _load_config() 方法
# def _load_config(self):
#     config_file = Path(self.config_path)
#     ...

# 3. 删除 _get_default_config() 方法
# def _get_default_config(self) -> Dict[str, Any]:
#     return { ... }
```

---

### 步骤 4: 更新适配器实现

**任务**:
1. 更新所有适配器的 `__init__`，调用父类 `__init__`

**代码示例**:
```python
# data_sources/adapters/akshare_adapter.py

class AKShareAdapter(DataSourceAdapter):
    """AKShare 数据源适配器"""

    def __init__(self, timeout: int = 10, **kwargs):
        super().__init__()  # ✅ 调用父类 __init__，初始化 _priority
        self.timeout = timeout
        logger.info("AKShareAdapter initialized")

    @property
    def name(self) -> str:
        return "akshare"

    # priority 属性继承自父类，无需重写
```

其他适配器同理，确保都调用 `super().__init__()`。

---

### 步骤 5: 更新简化 API

**任务**:
保持 `QuoteAPI`、`KLineAPI`、`FundamentalsAPI` 不变，它们会自动使用新的单例。

---

## 🧪 测试计划

### 单元测试

1. **配置加载测试**
```python
def test_config_loading_from_yaml():
    """测试从 YAML 加载配置"""
    config = get_config()
    assert config.data_sources.timeout == 10
    assert len(config.data_sources.sources.realtime) > 0
```

2. **配置验证测试**
```python
def test_invalid_priority():
    """测试无效的优先级"""
    with pytest.raises(ValidationError):
        DataSourceItem(name="sina", priority=-1)  # 优先级不能为负数
```

3. **优先级设置测试**
```python
def test_priority_setter():
    """测试 priority setter"""
    adapter = MockAdapter()
    adapter.priority = 50
    assert adapter.priority == 50
```

4. **Aggregator 初始化测试**
```python
def test_aggregator_from_config():
    """测试 Aggregator 从 Config.py 读取配置"""
    aggregator = DataSourceAggregator()
    assert aggregator.config is not None
    assert 'sources' in aggregator.config
```

---

## 📊 预期收益

| 改进项 | 收益 |
|--------|------|
| 统一配置入口 | ✅ 避免配置割裂，用户不再困惑 |
| 集中验证 | ✅ 配置错误立即报错，易于排查 |
| 代码优雅 | ✅ 使用 property，符合 Python 习惯 |
| 删除冗余 | ✅ 代码更简洁，维护成本降低 |

---

## ⚠️ 风险与应对

| 风险 | 应对措施 |
|------|---------|
| 配置加载失败 | Config.py 会返回安全的默认配置 |
| 适配器未实现 | 记录警告日志，跳过初始化 |
| 向后兼容性 | 修改了 `__init__` 签名，需要更新调用代码 |

---

## ✅ 验收标准

- [ ] `Config.py` 能正确读取 `config/data_sources.yaml`
- [ ] 配置验证正常工作，无效配置会报错
- [ ] `DataSourceAggregator` 能从 `Config.py` 获取配置
- [ ] `DataSourceAggregator.__init__` 不再接受 `config_path` 参数
- [ ] `DataSourceAggregator` 不再加载任何文件
- [ ] `priority` setter 正常工作
- [ ] 所有适配器都能正确初始化
- [ ] 单元测试全部通过

---

## 📅 时间估算

- **CC+gstack 时间**: ~30 分钟
- **人力时间**: ~4 小时
- **压缩比**: ~8 倍

---

## 👤 决策记录

| 问题 | 选择 | 理由 |
|------|------|------|
| 配置割裂 | B | 保留配置文件分离，通过统一入口访问 |
| 配置验证 | A | 使用 Pydantic，类型安全，错误信息清晰 |
| 优先级设置 | A | 使用 property setter，代码更优雅 |
| 文件格式 | 删除所有文件加载 | aggregator 不加载文件，从 config.py 读取 |

---

## 🎯 关键变更点

### 1. DataSourceAggregator.__init__

**之前**:
```python
def __init__(self, config_path: str = "config/sources.json"):
    self.config_path = config_path
    self._load_config()  # 从 JSON 文件加载
```

**之后**:
```python
def __init__(self):
    self._load_config_from_config_system()  # 从 Config.py 获取
```

### 2. 不再有文件加载

**之前**: 读取 `config/sources.json` 或硬编码默认值
**之后**: 直接从 `Config.py` 获取，`Config.py` 读取 `config/data_sources.yaml`

### 3. 单例模式简化

**之前**: `DataSourceAggregator(config_path="config/sources.json")`
**之后**: `DataSourceAggregator()` - 无需参数

---

**方案制定**: 2026-03-19
**最后更新**: 2026-03-19
**制定人**: Claude Code
