# Python 代码审查报告 - data_sources 模块

**审查日期**: 2026-03-22
**审查范围**: `data_sources/` 目录
**审查工具**: Python Reviewer

---

## 总体评价

这是一个设计良好的数据源抽象层，实现了适配器模式，支持多数据源降级策略。代码结构清晰，接口定义规范。

---

## 问题汇总

### 🔴 CRITICAL (必须修复)

#### 1. InvestodayAdapter 中的重复方法定义
**文件**: `data_sources/adapters/investoday_adapter.py:632-637`

```python
def get_financial_indicators(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Dict[str, float]:
```

**冲突方法** (第798行):
```python
def get_financial_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
```

**问题**: 同一个类中有两个同名但签名不同的方法，后面的会覆盖前面的。

**影响**:
- `get_financial_indicators(symbol, year, quarter)` 方法无法使用
- 返回类型不一致导致类型检查失败
- 违反 Liskov 替换原则

**修复建议**: 重命名其中一个方法：
- 保留 `get_financial_indicators(symbol, year, quarter) -> Dict[str, float]` 用于获取单季度指标
- 将列表返回的方法重命名为 `get_financial_indicators_history(symbol, start_date, end_date) -> list[dict]`

**优先级**: 🔴 立即修复

---

### 🟡 HIGH (强烈建议修复)

#### 1. 缺失类型注解
**文件**: `data_sources/exceptions.py:17-37`

```python
def __init__(
    self,
    source: str,
    message: str,
    original_error: Optional[Exception] = None  # 缺少返回类型注解
):
```

**问题**: `__init__` 方法缺少返回类型注解 (`-> None`)

**修复建议**:
```python
def __init__(
    self,
    source: str,
    message: str,
    original_error: Optional[Exception] = None
) -> None:
```

---

#### 2. 未使用上下文管理器/连接池
**文件**: `data_sources/adapters/sina_adapter.py:61-195`

**问题**:
- 多次调用 `requests.get()` 但未复用连接
- 每次请求都创建新的连接，性能低下
- 未设置超时可能导致阻塞

**修复建议**:
```python
class SinaAdapter(DataSourceAdapter):
    def __init__(self, timeout: int = 5):
        super().__init__()
        self.timeout = timeout
        self.base_url = "http://hq.sinajs.cn/list="
        self._session = requests.Session()  # 创建 Session 复用连接
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })
        logger.info("SinaAdapter initialized")

    def __del__(self):
        """清理连接"""
        if hasattr(self, '_session'):
            self._session.close()
```

---

#### 3. 硬编码敏感信息验证
**文件**: `data_sources/adapters/tushare_adapter.py:26-36`

**问题**: Token 作为必填参数传入，但未验证是否为空

**修复建议**:
```python
def __init__(self, token: str, timeout: int = 10):
    super().__init__()
    if not token or not token.strip():
        raise DataSourceConfigError(
            "tushare",
            "API token cannot be empty"
        )
    self.token = token.strip()
    self.timeout = timeout
    self.pro = ts.pro_api(token)
    logger.info("TushareAdapter initialized")
```

---

#### 4. 竞态条件风险 - 单例模式
**文件**: `data_sources/aggregator.py:26-61`

**问题**: 单例模式中 `_initialized` 标志未使用锁保护，多线程环境下可能创建多个实例

**修复建议**:
```python
import threading

class DataSourceAggregator:
    _instance = None
    _initialized = False
    _lock = threading.Lock()  # 添加锁

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
```

---

#### 5. 不安全的属性访问
**文件**: `data_sources/registry.py:78-86`

**问题**: 使用 `adapter_class.__new__()` 创建临时对象访问 property，可能触发未预期的初始化逻辑

**修复建议**:
```python
def register_class(self, adapter_class: Type[DataSourceAdapter]):
    """注册适配器类"""
    # 方法1: 使用 inspect 获取 property 名称
    import inspect
    adapter_name = None

    for name, prop in inspect.getmembers(adapter_class, lambda x: isinstance(x, property)):
        if name == 'name':
            try:
                # 尝试直接访问类属性
                adapter_name = getattr(adapter_class, name)
            except:
                pass
            break

    # 方法2: 约定命名规则 (推荐)
    if adapter_name is None:
        adapter_name = adapter_class.__name__.lower().replace('adapter', '')
```

---

### 🟠 MEDIUM (建议优化)

#### 1. Magic Numbers (魔法数字)
**文件**: `data_sources/constants.py`

```python
LIMIT_UP_THRESHOLD = 9.9  # 涨停阈值
LIMIT_DOWN_THRESHOLD = -9.9  # 跌停阈值
DEFAULT_TIMEOUT = 10
```

**问题**: 数字缺少注释说明含义和单位

**优化建议**:
```python
# 涨跌停阈值 (%)
LIMIT_UP_THRESHOLD = 9.9  # A股涨停板限制 (10% - 浮点误差)
LIMIT_DOWN_THRESHOLD = -9.9  # A股跌停板限制 (-10% - 浮点误差)

# 超时配置 (秒)
DEFAULT_TIMEOUT = 10  # 单次请求默认超时
BATCH_TIMEOUT = 20  # 批量请求超时
```

---

#### 2. 未使用的导入
**文件**: `data_sources/adapters/investoday_adapter.py:14, 493`

```python
from datetime import datetime  # 第10行已导入
```

**问题**: 第493行重复导入

**修复建议**: 删除第493行的重复导入

---

#### 3. 过长函数
**文件**: `data_sources/adapters/akshare_adapter.py:429-503`

`get_tech_indicators()` 函数超过75行，包含多个指标计算逻辑。

**优化建议**: 拆分为多个小函数
```python
def _calculate_ma(self, prices: np.ndarray, period: int, index: int) -> Optional[float]:
    """计算移动平均线"""
    if index < period - 1:
        return None
    return np.mean(prices[max(0, index-period+1):index+1])

def _calculate_rsi(self, prices: np.ndarray, index: int) -> Optional[float]:
    """计算RSI指标"""
    if index < 14:
        return None
    gains = np.maximum(0, np.diff(prices[index-14:index+1]))
    losses = np.abs(np.minimum(0, np.diff(prices[index-14:index+1])))
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

---

#### 4. 日志级别不当
**文件**: 多处

```python
logger.warning(f"Tushare balance sheet not supported")
```

**问题**: 使用 `warning` 级别表示功能未实现，会导致日志中大量警告

**优化建议**:
```python
logger.debug(f"Tushare balance sheet not supported")  # 开发调试用
# 或
logger.info(f"Tushare balance sheet requires VIP access")  # 用户信息
```

---

#### 5. 缺少文档字符串
**文件**: 多个适配器的私有方法

如 `SinaAdapter._format_symbol()`, `TushareAdapter._parse_symbol()` 等缺少 docstring

**优化建议**:
```python
def _format_symbol(self, symbol: str) -> str:
    """
    格式化股票代码为新浪格式

    Args:
        symbol: 标准股票代码 (如 "600519")

    Returns:
        新浪格式代码 (如 "sh600519" 或 "sz000001")

    Examples:
        >>> adapter._format_symbol("600519")
        'sh600519'
        >>> adapter._format_symbol("000001")
        'sz000001'
    """
    if symbol.startswith(('6', '9', '7')):
        return f"sh{symbol}"
    else:
        return f"sz{symbol}"
```

---

### 🟢 优点 (值得表扬)

1. **良好的抽象设计**: `DataSourceAdapter` 基类定义清晰，强制实现所有必需方法
2. **完善的异常体系**: 自定义异常层次结构合理，包含源信息
3. **降级策略实现**: `FallbackExecutor` 提供可靠的故障转移机制
4. **配置分离**: `constants.py` 统一管理魔法数字
5. **单例模式**: `DataSourceAggregator` 确保全局唯一实例
6. **类型提示完整**: 大部分公共接口都有良好的类型注解
7. **健康检查**: 所有适配器实现 `is_available()` 方法
8. **优先级系统**: 支持动态调整数据源优先级

---

## 详细修复代码示例

### 修复 InvestodayAdapter 重复方法

**原代码** (冲突):
```python
# 第632行
def get_financial_indicators(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Dict[str, float]:
    """获取财务指标"""
    # ... 实现

# 第798行
def get_financial_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
    """获取财务指标数据"""
    # ... 实现 (会覆盖前面的方法)
```

**修复后**:
```python
def get_financial_indicators(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Dict[str, float]:
    """
    获取指定季度的财务指标

    Args:
        symbol: 股票代码
        year: 年份
        quarter: 季度 (1-4)

    Returns:
        指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}
    """
    try:
        report_date = self._get_report_date(year, quarter)
        # ... 原实现逻辑
    except Exception as e:
        logger.error(f"Investoday get_financial_indicators failed for {symbol}: {e}")
        return {}

def get_financial_indicators_history(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
    """
    获取财务指标历史数据

    Args:
        symbol: 股票代码
        start_date: 开始日期 "YYYY-MM-DD" (可选)
        end_date: 结束日期 "YYYY-MM-DD" (可选)

    Returns:
        财务指标数据列表
    """
    try:
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        data = self._call_api(
            endpoint="stock/financial-indicators",
            method="GET",
            params=params
        )
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Investoday get_financial_indicators_history failed for {symbol}: {e}")
        return []
```

---

### 完整的单例模式线程安全修复

**原代码**:
```python
class DataSourceAggregator:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

**修复后**:
```python
import threading

class DataSourceAggregator:
    """
    数据源聚合器 - 线程安全单例

    提供统一的数据访问接口，自动处理数据源降级和优先级
    """
    _instance = None
    _initialized = False
    _lock = threading.Lock()  # 线程锁

    def __new__(cls):
        """
        线程安全的单例模式 (Double-Checked Locking)
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
```

---

### 连接池优化 (SinaAdapter)

**原代码**:
```python
def get_realtime(self, symbol: str) -> Optional[Quote]:
    try:
        sina_symbol = self._format_symbol(symbol)
        url = f"{self.base_url}{sina_symbol}"
        response = requests.get(url, timeout=self.timeout)  # 每次新建连接
        # ...
```

**优化后**:
```python
class SinaAdapter(DataSourceAdapter):
    def __init__(self, timeout: int = 5):
        super().__init__()
        self.timeout = timeout
        self.base_url = "http://hq.sinajs.cn/list="

        # 创建 Session 复用 TCP 连接
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; StockDataBot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "keep-alive"
        })
        logger.info("SinaAdapter initialized")

    def __del__(self):
        """析构函数 - 清理连接"""
        if hasattr(self, '_session'):
            self._session.close()

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        try:
            sina_symbol = self._format_symbol(symbol)
            url = f"{self.base_url}{sina_symbol}"
            response = self._session.get(url, timeout=self.timeout)  # 复用连接
            # ...
```

---

## 优先级排序

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🔴 P0 | Investoday 方法重复 | 功能失效 |
| 🟡 P1 | 单例线程安全 | 多线程崩溃风险 |
| 🟡 P1 | Token 验证缺失 | 安全性问题 |
| 🟡 P2 | 连接池未复用 | 性能问题 |
| 🟡 P2 | 类型注解不完整 | 可维护性 |
| 🟠 P3 | 文档不完整 | 开发体验 |
| 🟠 P3 | 日志级别不当 | 运维困扰 |

---

## 总结统计

- **CRITICAL**: 1 个
- **HIGH**: 5 个
- **MEDIUM**: 5 个
- **优点**: 8 个

**代码质量评分**: 85/100

**推荐行动**:
1. ✅ **立即修复**: InvestodayAdapter 方法冲突
2. ✅ **高优先级**: 单例线程安全、Token 验证
3. ⚠️ **中优先级**: 连接池优化、类型注解完善
4. 💡 **低优先级**: 文档补充、日志优化

---

## 后续建议

1. **添加单元测试**: 覆盖多数据源降级场景
2. **性能测试**: 测试批量请求和并发访问
3. **监控集成**: 添加指标收集 (请求次数、失败率、响应时间)
4. **配置验证**: 启动时验证所有必需配置项

---

**审查人**: Python Code Reviewer
**下次审查**: 建议在修复后进行回归测试
