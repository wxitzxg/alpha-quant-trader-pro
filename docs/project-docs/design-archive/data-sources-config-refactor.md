# Data Sources 配置系统重构方案

**文档版本**: 1.0
**创建日期**: 2026-03-19
**作者**: AI Assistant
**状态**: ✅ 已批准

---

## 一、背景和目标

### 1.1 问题背景

`data_sources/` 模块存在以下配置相关问题：

1. **配置文件格式不一致** - 系统同时存在 YAML 和 JSON 两套配置
2. **未使用统一配置系统** - `DataSourceAggregator` 硬编码 JSON 配置路径
3. **Priority 配置无效** - 基类未提供 priority 构造参数
4. **超时配置键名不匹配** - 代码使用 "get_realtime"，配置使用 "realtime"
5. **单例模式线程不安全** - 多线程环境下可能创建多个实例

### 1.2 重构目标

- ✅ 统一使用 YAML 配置系统
- ✅ 保持模块化配置文件结构
- ✅ 配置文件键名与代码属性名完全一致
- ✅ 支持环境变量覆盖
- ✅ 线程安全的单例模式
- ✅ 提升可读性和可维护性

---

## 二、详细方案

### 2.1 问题1: 配置文件格式不一致

**选择方案**: 完全迁移到YAML统一配置系统

**实施内容**:
- 删除 `config/sources.json` (JSON 配置)
- 保留现有的 `config/data_sources.yaml` (YAML 配置)
- 修改 `DataSourceAggregator` 使用 `common/config.py`

**配置文件结构**:
```yaml
# config/data_sources.yaml
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
```

---

### 2.2 问题2: 未使用统一配置系统

**选择方案**: 保持分散配置,修改代码支持多文件加载,用 `.env` 实现环境切换

**实施内容**:

1. **修改 `common/config.py` 支持多文件加载**:
```python
def _load_yaml_config(self) -> Dict[str, Any]:
    """加载多个YAML配置文件并合并"""
    config_dir = Path("config")
    merged_config = {}

    if config_dir.exists():
        # 加载所有 .yaml 文件 (除了环境配置文件)
        for config_file in sorted(config_dir.glob("*.yaml")):
            # 跳过环境配置文件
            if config_file.name.startswith('config.'):
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_content = yaml.safe_load(f) or {}
                    merged_config.update(config_content)
            except Exception as e:
                logger.warning(f"Failed to load {config_file}: {e}")

    return merged_config
```

2. **创建环境配置文件**:
```bash
# .env (开发环境)
APP_ENV=development
DEBUG=true
DATABASE__URL=postgresql://postgres:postgres@localhost:5432/stock_market

# .env.test (测试环境)
APP_ENV=testing
DEBUG=false
DATABASE__URL=postgresql://test:test@localhost:5432/stock_market_test

# .env.production (生产环境)
APP_ENV=production
DEBUG=false
DATABASE__URL=postgresql://user:password@prod-host:5432/stock_market_prod
```

3. **修改 `DataSourceAggregator` 使用统一配置**:
```python
from common.config import get_config

class DataSourceAggregator:
    def __init__(self):
        # 从统一配置获取
        config = get_config()
        self.config = config.data_sources.model_dump()
```

---

### 2.3 问题3: Priority 配置无效

**选择方案**: 基类提供构造函数参数

**实施内容**:

1. **修改 `DataSourceAdapter` 基类**:
```python
class DataSourceAdapter(ABC):
    def __init__(self, priority: int = 100, timeout: int = 5):
        """
        Args:
            priority: 优先级 (数值越小越优先)
            timeout: 超时时间 (秒)
        """
        self._priority = priority
        self._timeout = timeout

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def timeout(self) -> int:
        return self._timeout
```

2. **修改所有适配器子类**:
```python
class SinaAdapter(DataSourceAdapter):
    def __init__(self, priority: int = 10, timeout: int = 3):
        super().__init__(priority=priority, timeout=timeout)

class TushareAdapter(DataSourceAdapter):
    def __init__(self, priority: int = 20, timeout: int = 5):
        super().__init__(priority=priority, timeout=timeout)

class AkshareAdapter(DataSourceAdapter):
    def __init__(self, priority: int = 30, timeout: int = 5):
        super().__init__(priority=priority, timeout=timeout)
```

3. **修改 `registry.py` 移除冗余设置**:
```python
def create_adapter(self, name: str, **kwargs) -> DataSourceAdapter:
    adapter_class = self._adapter_classes[name]
    # 直接传递配置参数
    adapter = adapter_class(**kwargs)
    self._adapters[name] = adapter
    return adapter
```

---

### 2.4 问题4: 超时配置键名不匹配

**选择方案**: 修改方法命名与配置键一致

**实施内容**:

1. **修改 `DataSourceAggregator` 方法命名**:

| 旧方法名 | 新方法名 | 配置键 |
|---------|---------|--------|
| `get_realtime()` | `realtime()` | `realtime` |
| `batch_get_realtime()` | `realtime_batch()` | `realtime` |
| `get_kline()` | `kline()` | `kline` |
| `get_balance_sheet()` | `fundamentals_balance_sheet()` | `fundamentals` |
| `get_income_statement()` | `fundamentals_income_statement()` | `fundamentals` |
| `get_cash_flow_statement()` | `fundamentals_cash_flow_statement()` | `fundamentals` |
| `get_financial_indicators()` | `fundamentals_indicators()` | `fundamentals` |

2. **更新 `aggregator.py`**:
```python
class DataSourceAggregator:
    def realtime(self, symbol: str) -> Optional[Quote]:
        adapters = self._get_sorted_adapters('realtime')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_realtime(symbol),
            "realtime"  # ✅ 与配置键一致
        )

    def realtime_batch(self, symbols: List[str]) -> List[Quote]:
        adapters = self._get_sorted_adapters('realtime')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.batch_get_realtime(symbols),
            "realtime"  # ✅ 与配置键一致
        )

    def kline(self, symbol: str, interval: str = "1d",
              start_date: str = "", end_date: str = "") -> List[KLine]:
        adapters = self._get_sorted_adapters('kline')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_kline(symbol, interval, start_date, end_date),
            "kline"  # ✅ 与配置键一致
        )

    def fundamentals_balance_sheet(self, symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        adapters = self._get_sorted_adapters('fundamentals')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_balance_sheet(symbol, year, quarter),
            "fundamentals"  # ✅ 与配置键一致
        )

    # ... 其他方法类似
```

3. **更新 `FallbackExecutor`**:
```python
def _get_source_timeout(self, source_name: str, category: str) -> int:
    """
    获取数据源的超时配置

    Args:
        source_name: 数据源名称 (如 "sina")
        category: 配置分类 (如 "realtime", "kline", "fundamentals")

    Returns:
        超时时间 (秒)
    """
    sources_config = self.config.get('sources', {})
    category_config = sources_config.get(category, [])  # ✅ 直接使用配置键

    for cfg in category_config:
        if cfg.get('name') == source_name:
            return cfg.get('timeout', 5)

    return 5
```

4. **更新简化调用接口 (API类)**:
```python
class QuoteAPI:
    @staticmethod
    def get(symbol: str) -> Optional[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.realtime(symbol)  # ✅ 调用新方法名

    @staticmethod
    def batch_get(symbols: List[str]) -> List[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.realtime_batch(symbols)

class KLineAPI:
    @staticmethod
    def get(symbol: str, interval: str = "1d",
            start_date: str = "", end_date: str = "") -> List[KLine]:
        aggregator = DataSourceAggregator()
        return aggregator.kline(symbol, interval, start_date, end_date)

class FundamentalsAPI:
    @staticmethod
    def get_balance_sheet(symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        aggregator = DataSourceAggregator()
        return aggregator.fundamentals_balance_sheet(symbol, year, quarter)

    @staticmethod
    def get_income_statement(symbol: str, year: int, quarter: int) -> Optional[IncomeStatement]:
        aggregator = DataSourceAggregator()
        return aggregator.fundamentals_income_statement(symbol, year, quarter)
```

---

### 2.5 问题5: 单例模式线程不安全

**选择方案**: 使用线程锁 (双重检查锁定)

**实施内容**:

```python
import threading

class DataSourceAggregator:
    _instance = None
    _lock = threading.Lock()  # ✅ 线程锁

    def __new__(cls):
        """
        线程安全的单例模式 (双重检查锁定)
        """
        if cls._instance is None:
            with cls._lock:  # ✅ 加锁
                if cls._instance is None:  # ✅ 双重检查
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # 初始化代码
        self.config = {}
        self.registry = AdapterRegistry()
        self.executor = None

        # 加载配置
        self._load_config()
        self.executor = FallbackExecutor(self.config)
        self._initialize_adapters()

        self._initialized = True
        logger.info("DataSourceAggregator initialized successfully")

    def _load_config(self):
        """从统一配置系统加载配置"""
        from common.config import get_config
        config = get_config()
        self.config = config.data_sources.model_dump()
```

---

## 三、实施步骤

### 3.1 第一阶段: 配置系统改造 (预计 1-2 小时)

1. ✅ 修改 `common/config.py` 支持多文件加载
2. ✅ 创建 `.env`, `.env.test`, `.env.production` 文件
3. ✅ 测试配置加载是否正常

### 3.2 第二阶段: 基类和适配器改造 (预计 1 小时)

1. ✅ 修改 `DataSourceAdapter` 基类添加构造参数
2. ✅ 修改所有适配器子类 (`SinaAdapter`, `TushareAdapter`, `AkshareAdapter`)
3. ✅ 修改 `AdapterRegistry` 移除冗余代码
4. ✅ 测试适配器创建和优先级是否正常

### 3.3 第三阶段: Aggregator 改造 (预计 1-2 小时)

1. ✅ 修改 `DataSourceAggregator` 使用统一配置
2. ✅ 修改方法命名与配置键一致
3. ✅ 更新简化 API 类
4. ✅ 添加线程锁实现线程安全单例
5. ✅ 删除 JSON 配置加载逻辑
6. ✅ 删除 `config/sources.json` 文件

### 3.4 第四阶段: Executor 改造 (预计 30 分钟)

1. ✅ 修改 `FallbackExecutor._get_source_timeout()` 使用配置键
2. ✅ 移除映射逻辑
3. ✅ 测试超时配置是否生效

### 3.5 第五阶段: 测试验证 (预计 1 小时)

1. ✅ 单元测试 - 配置加载、适配器创建、优先级排序
2. ✅ 集成测试 - 数据源调用、降级逻辑
3. ✅ 线程安全测试 - 多线程并发创建单例
4. ✅ 环境变量覆盖测试

---

## 四、文件清单

### 4.1 修改的文件

| 文件路径 | 修改内容 | 优先级 |
|---------|---------|--------|
| `common/config.py` | 支持多文件 YAML 配置加载 | 🔴 高 |
| `data_sources/base.py` | 添加 priority/timeout 构造参数 | 🔴 高 |
| `data_sources/registry.py` | 移除冗余 priority 设置 | 🟡 中 |
| `data_sources/aggregator.py` | 使用统一配置 + 方法重命名 + 线程锁 | 🔴 高 |
| `data_sources/executor.py` | 简化超时查找逻辑 | 🟡 中 |
| `data_sources/adapters/sina_adapter.py` | 更新 `__init__` 签名 | 🟡 中 |
| `data_sources/adapters/tushare_adapter.py` | 更新 `__init__` 签名 | 🟡 中 |
| `data_sources/adapters/akshare_adapter.py` | 更新 `__init__` 签名 | 🟡 中 |
| `data_sources/adapters/investoday_adapter.py` | 更新 `__init__` 签名 | 🟡 中 |

### 4.2 新增的文件

| 文件路径 | 说明 | 优先级 |
|---------|------|--------|
| `.env` | 开发环境配置 | 🔴 高 |
| `.env.test` | 测试环境配置 | 🟡 中 |
| `.env.production` | 生产环境配置 | 🟡 中 |
| `.env.example` | 环境配置示例 | 🟡 中 |
| `.gitignore` (更新) | 添加 `.env*` 忽略规则 | 🔴 高 |

### 4.3 删除的文件

| 文件路径 | 说明 | 优先级 |
|---------|------|--------|
| `config/sources.json` | 废弃的 JSON 配置文件 | 🔴 高 |

---

## 五、风险评估

### 5.1 风险点

| 风险 | 严重性 | 概率 | 缓解措施 |
|------|--------|------|---------|
| 现有代码调用旧方法名 | 高 | 高 | 保持 API 类向后兼容 |
| 配置文件加载失败 | 中 | 低 | 添加错误处理和日志 |
| 线程锁性能问题 | 低 | 低 | 双重检查锁定,只在首次加锁 |
| 环境变量冲突 | 低 | 中 | 清晰的命名规范和文档 |

### 5.2 回滚方案

如果迁移过程中遇到问题:

1. **恢复旧代码**: 从 git 恢复修改的文件
2. **保留 JSON 配置**: 恢复 `config/sources.json`
3. **旧代码继续运行**: 现有代码无需修改即可正常运行

---

## 六、测试计划

### 6.1 单元测试

```python
# tests/test_config.py
def test_load_multiple_yaml_files():
    """测试加载多个YAML配置文件"""
    config = get_config()
    assert config.data_sources.timeout == 10
    assert config.data_sources.max_retries == 3

# tests/data_sources/test_adapter.py
def test_adapter_priority():
    """测试适配器优先级"""
    adapter = SinaAdapter(priority=10, timeout=3)
    assert adapter.priority == 10
    assert adapter.timeout == 3

# tests/data_sources/test_aggregator.py
def test_aggregator_singleton_threadsafe():
    """测试线程安全的单例模式"""
    import threading

    instances = []
    def create_instance():
        instances.append(DataSourceAggregator())

    threads = [threading.Thread(target=create_instance) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    # 所有线程应该获得同一个实例
    assert all(inst is instances[0] for inst in instances)
```

### 6.2 集成测试

```python
def test_data_source_fallback():
    """测试数据源降级逻辑"""
    aggregator = DataSourceAggregator()

    # 实时行情
    quote = aggregator.realtime("600519")
    assert quote is not None

    # K线数据
    klines = aggregator.kline("600519", interval="1d")
    assert len(klines) > 0

    # 基本面数据
    balance_sheet = aggregator.fundamentals_balance_sheet("600519", 2023, 4)
    assert balance_sheet is not None
```

---

## 七、验收标准

- ✅ 所有 YAML 配置文件正确加载
- ✅ 环境变量能够覆盖配置
- ✅ 适配器优先级配置生效
- ✅ 超时配置正确应用
- ✅ 单例模式线程安全
- ✅ 旧的 API 接口保持向后兼容
- ✅ 单元测试通过率 100%
- ✅ 集成测试通过

---

## 八、审批记录

| 日期 | 审批人 | 状态 | 备注 |
|-----|--------|------|------|
| 2026-03-19 | 用户确认 | ✅ 批准 | 所有方案已确认 |

---

**文档结束**
