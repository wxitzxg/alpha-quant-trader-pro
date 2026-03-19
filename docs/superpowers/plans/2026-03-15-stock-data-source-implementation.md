# 股票数据源聚合模块实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个统一的数据源聚合模块，支持多数据源自动降级和优先级配置

**Architecture:** 基于 Plugin/Adapter 模式，包含统一聚合器、降级执行器、适配器注册表和多个数据源适配器

**Tech Stack:** Python 3.9+, FastAPI (非必须，内部模块), Pydantic, Tushare, AKShare, requests

---

## 文件结构概览

```
data_sources/
├── __init__.py                      # 导出统一接口 (QuoteAPI, KLineAPI, ...)
├── base.py                          # DataSourceAdapter (ABC)
├── models.py                        # Pydantic 数据模型 (Quote, KLine, ...)
├── exceptions.py                    # DataSourceError
├── aggregator.py                    # DataSourceAggregator (单例)
├── executor.py                      # FallbackExecutor
├── registry.py                      # AdapterRegistry
└── adapters/
    ├── __init__.py
    ├── base_adapter.py             # 可选：共享基础适配器逻辑
    ├── tushare_adapter.py          # Tushare Pro 适配器
    ├── akshare_adapter.py          # AKShare 适配器
    ├── sina_adapter.py             # 新浪财经 适配器
    └── eastmoney_adapter.py        # 东方财富 适配器

config/
└── sources.json                     # 数据源优先级配置

tests/
├── test_base.py                    # 测试抽象接口
├── test_models.py                  # 测试数据模型
├── test_exceptions.py              # 测试异常
├── test_aggregator.py              # 测试聚合器
├── test_executor.py                # 测试降级执行器
├── test_registry.py                # 测试注册表
└── adapters/
    ├── test_tushare_adapter.py
    ├── test_akshare_adapter.py
    ├── test_sina_adapter.py
    └── test_eastmoney_adapter.py
```

---

## Chunk 1: 基础设施 (数据模型、异常、抽象接口)

### Task 1.1: 创建数据模型 (models.py)

**Files:**
- Create: `data_sources/models.py`

- [ ] **Step 1: 创建 models.py 文件**

```python
"""
数据模型模块

定义所有数据源返回的统一数据结构
使用 Pydantic 进行数据验证和序列化
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 实时行情数据模型 ==========

class Quote(BaseModel):
    """实时行情数据模型"""
    symbol: str = Field(..., description="股票代码，如 '600519'")
    price: float = Field(..., description="最新价格")
    change: float = Field(..., description="涨跌额")
    percent: float = Field(..., description="涨跌幅（小数形式，如 0.05 表示 5%）")
    volume: int = Field(..., description="成交量（股）")
    amount: float = Field(..., description="成交额（元）")
    bid_price: List[float] = Field(default_factory=list, description="五档买价")
    bid_volume: List[int] = Field(default_factory=list, description="五档买量")
    ask_price: List[float] = Field(default_factory=list, description="五档卖价")
    ask_volume: List[int] = Field(default_factory=list, description="五档卖量")
    timestamp: datetime = Field(..., description="数据时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ========== K线数据模型 ==========

class KLine(BaseModel):
    """K线数据模型"""
    symbol: str = Field(..., description="股票代码")
    datetime: datetime = Field(..., description="K线时间")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量（股）")
    amount: float = Field(..., description="成交额（元）")
    turnover: Optional[float] = Field(None, description="换手率（小数形式）")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ========== 财务报表基础模型 ==========

class FinancialStatement(BaseModel):
    """财务报表基础模型"""
    symbol: str = Field(..., description="股票代码")
    year: int = Field(..., description="年份")
    quarter: int = Field(..., ge=1, le=4, description="季度（1-4）")
    report_date: str = Field(..., description="报告期，格式 'YYYY-MM-DD'")


class BalanceSheet(FinancialStatement):
    """资产负债表"""
    total_assets: float = Field(..., description="资产总计")
    total_liabilities: float = Field(..., description="负债合计")
    shareholders_equity: float = Field(..., description="股东权益合计")
    # 可根据需要添加更多字段


class IncomeStatement(FinancialStatement):
    """利润表"""
    revenue: float = Field(..., description="营业收入")
    net_profit: float = Field(..., description="净利润")
    eps: float = Field(..., description="每股收益")
    # 可根据需要添加更多字段


class CashFlowStatement(FinancialStatement):
    """现金流量表"""
    operating_cash_flow: float = Field(..., description="经营活动现金流量净额")
    investing_cash_flow: float = Field(..., description="投资活动现金流量净额")
    financing_cash_flow: float = Field(..., description="筹资活动现金流量净额")
    # 可根据需要添加更多字段
```

- [ ] **Step 2: 创建 __init__.py 导出模型**

在 `data_sources/__init__.py` 中添加：

```python
"""股票数据源聚合模块"""

__version__ = "0.1.0"

from .models import (
    Quote,
    KLine,
    FinancialStatement,
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement
)

__all__ = [
    "Quote",
    "KLine",
    "FinancialStatement",
    "BalanceSheet",
    "IncomeStatement",
    "CashFlowStatement"
]
```

- [ ] **Step 3: 提交模型代码**

```bash
git add data_sources/models.py data_sources/__init__.py
git commit -m "feat: add Pydantic data models for stock data"
```

---

### Task 1.2: 创建异常定义 (exceptions.py)

**Files:**
- Create: `data_sources/exceptions.py`

- [ ] **Step 1: 创建 exceptions.py**

```python
"""
异常模块

定义数据源相关的异常类型
"""

from typing import Optional


class DataSourceError(Exception):
    """
    数据源异常基类

    所有数据源适配器抛出的异常都应该继承此类
    """

    def __init__(
        self,
        source: str,
        message: str,
        original_error: Optional[Exception] = None
    ):
        """
        Args:
            source: 数据源名称 (如 "tushare", "akshare")
            message: 错误描述
            original_error: 原始异常 (可选)
        """
        self.source = source
        self.message = message
        self.original_error = original_error

        full_message = f"[{source}] {message}"
        if original_error:
            full_message += f" | Original error: {original_error}"

        super().__init__(full_message)


class DataSourceTimeoutError(DataSourceError):
    """数据源超时异常"""
    pass


class DataSourceNotFoundError(DataSourceError):
    """数据未找到异常"""
    pass


class DataSourceConfigError(DataSourceError):
    """配置错误异常"""
    pass
```

- [ ] **Step 2: 更新 __init__.py 导出异常**

```python
# 追加到 data_sources/__init__.py
from .exceptions import (
    DataSourceError,
    DataSourceTimeoutError,
    DataSourceNotFoundError,
    DataSourceConfigError
)

__all__.extend([
    "DataSourceError",
    "DataSourceTimeoutError",
    "DataSourceNotFoundError",
    "DataSourceConfigError"
])
```

- [ ] **Step 3: 提交异常代码**

```bash
git add data_sources/exceptions.py
git commit -m "feat: add data source exception types"
```

---

### Task 1.3: 创建抽象接口 (base.py)

**Files:**
- Create: `data_sources/base.py`

- [ ] **Step 1: 创建 base.py**

```python
"""
抽象接口模块

定义所有数据源适配器必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from .exceptions import DataSourceError


class DataSourceAdapter(ABC):
    """
    数据源适配器抽象基类

    所有具体的数据源适配器都必须继承此类并实现所有抽象方法
    """

    @abstractmethod
    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """
        获取单个股票实时行情

        Args:
            symbol: 股票代码 (如 "600519")

        Returns:
            Quote 对象，失败返回 None

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表 (可能为空)

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_kline(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> List[KLine]:
        """
        获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            KLine 对象列表 (可能为空)

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """
        获取资产负债表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            BalanceSheet 对象，失败返回 None

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """
        获取利润表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            IncomeStatement 对象，失败返回 None

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """
        获取现金流量表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            CashFlowStatement 对象，失败返回 None

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """
        获取财务指标

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        数据源名称

        Returns:
            数据源唯一标识 (如 "tushare", "akshare")
        """
        pass

    @property
    def priority(self) -> int:
        """
        数据源优先级

        Returns:
            优先级数值，越小越优先，默认 100 (低优先级)
        """
        return 100

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        子类可以重写此方法实现健康检查

        Returns:
            True 表示可用
        """
        return True
```

- [ ] **Step 2: 更新 __init__.py 导出接口**

```python
# 追加到 data_sources/__init__.py
from .base import DataSourceAdapter

__all__.append("DataSourceAdapter")
```

- [ ] **Step 3: 提交接口代码**

```bash
git add data_sources/base.py
git commit -m "feat: add DataSourceAdapter abstract interface"
```

---

### Task 1.4: 为基础设施编写单元测试

**Files:**
- Create: `tests/test_models.py`
- Create: `tests/test_exceptions.py`
- Create: `tests/test_base.py`

- [ ] **Step 1: 创建测试目录和 __init__.py**

```bash
mkdir -p tests/adapters
touch tests/__init__.py
touch tests/adapters/__init__.py
```

- [ ] **Step 2: 编写 models 测试 (tests/test_models.py)**

```python
"""测试数据模型"""

import pytest
from datetime import datetime
from data_sources.models import Quote, KLine


def test_quote_model():
    """测试 Quote 模型"""
    quote = Quote(
        symbol="600519",
        price=1800.50,
        change=10.25,
        percent=0.0057,
        volume=1000000,
        amount=1800000000.0,
        bid_price=[1800.0, 1799.5, 1799.0, 1798.5, 1798.0],
        bid_volume=[100, 200, 300, 400, 500],
        ask_price=[1801.0, 1801.5, 1802.0, 1802.5, 1803.0],
        ask_volume=[150, 250, 350, 450, 550],
        timestamp=datetime.now()
    )

    assert quote.symbol == "600519"
    assert quote.price == 1800.50
    assert len(quote.bid_price) == 5
    assert len(quote.ask_price) == 5


def test_quote_validation():
    """测试 Quote 验证"""
    with pytest.raises(ValueError):
        Quote(
            symbol="600519",
            price=-100,  # 价格不能为负
            change=10.25,
            percent=0.0057,
            volume=1000000,
            amount=1800000000.0,
            timestamp=datetime.now()
        )


def test_kline_model():
    """测试 KLine 模型"""
    kline = KLine(
        symbol="600519",
        datetime=datetime(2023, 1, 1, 10, 0, 0),
        open=1800.0,
        high=1810.0,
        low=1795.0,
        close=1805.0,
        volume=500000,
        amount=900000000.0,
        turnover=0.01
    )

    assert kline.symbol == "600519"
    assert kline.open == 1800.0
    assert kline.close == 1805.0
    assert kline.turnover == 0.01
```

- [ ] **Step 3: 编写 exceptions 测试 (tests/test_exceptions.py)**

```python
"""测试异常"""

from data_sources.exceptions import (
    DataSourceError,
    DataSourceTimeoutError,
    DataSourceNotFoundError
)


def test_data_source_error():
    """测试 DataSourceError"""
    error = DataSourceError("tushare", "API timeout", Exception("Connection refused"))

    assert error.source == "tushare"
    assert "tushare" in str(error)
    assert error.original_error is not None


def test_data_source_timeout_error():
    """测试 DataSourceTimeoutError"""
    error = DataSourceTimeoutError("akshare", "Request timeout")

    assert isinstance(error, DataSourceError)
    assert error.source == "akshare"


def test_data_source_not_found_error():
    """测试 DataSourceNotFoundError"""
    error = DataSourceNotFoundError("sina", "Symbol not found")

    assert isinstance(error, DataSourceError)
    assert "not found" in error.message.lower()
```

- [ ] **Step 4: 编写 base 接口测试 (tests/test_base.py)**

```python
"""测试抽象接口"""

import pytest
from abc import ABCMeta
from data_sources.base import DataSourceAdapter


def test_abstract_class_cannot_instantiate():
    """测试不能实例化抽象类"""
    with pytest.raises(TypeError):
        adapter = DataSourceAdapter()


def test_abstract_class_has_required_methods():
    """测试抽象类定义了所有必需方法"""
    abstract_methods = DataSourceAdapter.__abstractmethods__

    assert 'get_realtime' in abstract_methods
    assert 'batch_get_realtime' in abstract_methods
    assert 'get_kline' in abstract_methods
    assert 'get_balance_sheet' in abstract_methods
    assert 'get_income_statement' in abstract_methods
    assert 'get_cash_flow_statement' in abstract_methods
    assert 'get_financial_indicators' in abstract_methods
    assert 'name' in abstract_methods
```

- [ ] **Step 5: 运行测试验证**

```bash
pytest tests/test_models.py -v
pytest tests/test_exceptions.py -v
pytest tests/test_base.py -v
```

预期输出：所有测试通过

- [ ] **Step 6: 提交测试代码**

```bash
git add tests/
git commit -m "test: add unit tests for models, exceptions, and base interface"
```

---

## Chunk 2: 核心引擎 (注册表、执行器、聚合器)

### Task 2.1: 创建适配器注册表 (registry.py)

**Files:**
- Create: `data_sources/registry.py`

- [ ] **Step 1: 创建 registry.py**

```python
"""
适配器注册表模块

自动发现和管理所有数据源适配器
"""

import importlib
import os
import logging
from typing import Dict, Type, List, Optional
from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    适配器注册表

    负责自动发现、注册和管理所有数据源适配器
    """

    def __init__(self):
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._adapter_classes: Dict[str, Type[DataSourceAdapter]] = {}

    def auto_discover(self, package: str = "data_sources.adapters"):
        """
        自动发现适配器

        扫描 adapters 目录，自动导入所有适配器类

        Args:
            package: 适配器包路径
        """
        # 获取适配器目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        adapter_dir = os.path.join(current_dir, "adapters")

        if not os.path.exists(adapter_dir):
            logger.warning(f"Adapter directory not found: {adapter_dir}")
            return

        # 遍历目录中的所有文件
        for filename in os.listdir(adapter_dir):
            # 只处理以 _adapter.py 结尾的文件，排除 __init__.py
            if (filename.endswith("_adapter.py") and
                not filename.startswith("__")):

                module_name = filename[:-3]  # 去掉 .py 后缀
                module_path = f"{package}.{module_name}"

                try:
                    logger.info(f"Loading adapter module: {module_name}")
                    module = importlib.import_module(module_path)

                    # 查找继承自 DataSourceAdapter 的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, DataSourceAdapter) and
                            attr != DataSourceAdapter):

                            self.register_class(attr)
                            logger.info(f"  Registered adapter class: {attr_name}")

                except Exception as e:
                    logger.error(f"Failed to load adapter {module_name}: {e}", exc_info=True)

    def register_class(self, adapter_class: Type[DataSourceAdapter]):
        """
        注册适配器类

        Args:
            adapter_class: 适配器类
        """
        # 使用类的 name 属性作为唯一标识
        adapter_name = adapter_class.name  # type: ignore

        if adapter_name in self._adapter_classes:
            logger.warning(f"Adapter {adapter_name} already registered, overwriting")

        self._adapter_classes[adapter_name] = adapter_class
        logger.debug(f"Registered adapter class: {adapter_name}")

    def create_adapter(self, name: str, **kwargs) -> DataSourceAdapter:
        """
        创建适配器实例

        Args:
            name: 适配器名称
            **kwargs: 传递给适配器构造函数的参数

        Returns:
            适配器实例

        Raises:
            ValueError: 适配器类不存在
        """
        if name not in self._adapter_classes:
            raise ValueError(f"Adapter class '{name}' not found. "
                           f"Available: {list(self._adapter_classes.keys())}")

        adapter_class = self._adapter_classes[name]
        adapter = adapter_class(**kwargs)

        # 存储实例
        self._adapters[name] = adapter
        logger.debug(f"Created adapter instance: {name}")

        return adapter

    def get_adapter(self, name: str) -> Optional[DataSourceAdapter]:
        """
        获取适配器实例

        Args:
            name: 适配器名称

        Returns:
            适配器实例，如果不存在返回 None
        """
        return self._adapters.get(name)

    def get_all_adapters(self) -> List[DataSourceAdapter]:
        """
        获取所有适配器实例

        Returns:
            适配器实例列表
        """
        return list(self._adapters.values())

    def get_adapter_names(self) -> List[str]:
        """
        获取所有已注册的适配器名称

        Returns:
            适配器名称列表
        """
        return list(self._adapter_classes.keys())
```

- [ ] **Step 2: 创建 adapters/__init__.py**

```python
"""数据源适配器包"""

from .tushare_adapter import TushareAdapter
from .akshare_adapter import AKShareAdapter
from .sina_adapter import SinaAdapter
from .eastmoney_adapter import EastMoneyAdapter

__all__ = [
    "TushareAdapter",
    "AKShareAdapter",
    "SinaAdapter",
    "EastMoneyAdapter"
]
```

- [ ] **Step 3: 更新主 __init__.py**

```python
# 追加到 data_sources/__init__.py
from .registry import AdapterRegistry

__all__.append("AdapterRegistry")
```

- [ ] **Step 4: 提交注册表代码**

```bash
mkdir -p data_sources/adapters
touch data_sources/adapters/__init__.py
git add data_sources/registry.py data_sources/adapters/__init__.py
git commit -m "feat: add AdapterRegistry for auto-discovery"
```

---

### Task 2.2: 创建降级执行器 (executor.py)

**Files:**
- Create: `data_sources/executor.py`

- [ ] **Step 1: 创建 executor.py**

```python
"""
降级执行器模块

按优先级执行数据源，失败时自动降级到备用源
"""

import time
import logging
from typing import List, Callable, Optional, TypeVar, Dict, Any
from .base import DataSourceAdapter
from .exceptions import DataSourceError

T = TypeVar('T')

logger = logging.getLogger(__name__)


class FallbackExecutor:
    """
    降级执行器

    根据配置的优先级顺序执行数据源
    当某个数据源失败时，自动降级到下一个数据源
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 配置字典，包含 fallback 和 sources 配置
        """
        self.config = config
        self.logger = logger

    def execute_with_fallback(
        self,
        adapters: List[DataSourceAdapter],
        operation: Callable[[DataSourceAdapter], T],
        operation_name: str
    ) -> Optional[T]:
        """
        执行操作，失败时降级到下一个数据源

        Args:
            adapters: 已排序的适配器列表（按优先级）
            operation: 要执行的操作函数，接受一个适配器参数
            operation_name: 操作名称（用于日志）

        Returns:
            操作结果，所有数据源都失败返回 None
        """
        fallback_config = self.config.get('fallback', {})
        max_retries = fallback_config.get('max_retries', 2)
        retry_delay = fallback_config.get('retry_delay', 0.5)
        log_failures = fallback_config.get('log_failures', True)

        # 遍历所有适配器（按优先级）
        for adapter in adapters:
            # 检查适配器是否可用
            if not adapter.is_available():
                self.logger.debug(f"Skipping unavailable adapter: {adapter.name}")
                continue

            # 获取该数据源的配置
            timeout = self._get_source_timeout(adapter.name, operation_name)

            # 对每个适配器进行重试
            for attempt in range(max_retries):
                try:
                    self.logger.info(
                        f"Executing {operation_name} on {adapter.name} "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    # 执行操作
                    result = operation(adapter)

                    # 检查结果
                    if result is not None:
                        self.logger.info(
                            f"✓ {operation_name} succeeded on {adapter.name}"
                        )
                        return result

                    self.logger.warning(
                        f"{operation_name} returned None on {adapter.name}"
                    )

                except DataSourceError as e:
                    if log_failures:
                        self.logger.error(
                            f"✗ {operation_name} failed on {adapter.name}: {e}"
                        )

                    # 最后一次重试，继续降级
                    if attempt >= max_retries - 1:
                        break

                    # 等待后重试
                    time.sleep(retry_delay)

                except Exception as e:
                    if log_failures:
                        self.logger.error(
                            f"✗ {operation_name} crashed on {adapter.name}: {e}",
                            exc_info=True
                        )

                    # 非预期异常，直接降级
                    break

            # 当前数据源所有重试都失败，继续降级到下一个
            continue

        # 所有数据源都失败
        self.logger.error(f"All sources failed for {operation_name}")
        return None

    def _get_source_timeout(self, source_name: str, operation_name: str) -> int:
        """
        获取数据源的超时配置

        Args:
            source_name: 数据源名称
            operation_name: 操作类别

        Returns:
            超时时间（秒），默认 5
        """
        sources_config = self.config.get('sources', {})
        category_config = sources_config.get(operation_name, [])

        for cfg in category_config:
            if cfg.get('name') == source_name:
                return cfg.get('timeout', 5)

        return 5
```

- [ ] **Step 2: 更新主 __init__.py**

```python
# 追加到 data_sources/__init__.py
from .executor import FallbackExecutor

__all__.append("FallbackExecutor")
```

- [ ] **Step 3: 提交执行器代码**

```bash
git add data_sources/executor.py
git commit -m "feat: add FallbackExecutor with automatic retry and fallback"
```

---

### Task 2.3: 创建数据源聚合器 (aggregator.py)

**Files:**
- Create: `data_sources/aggregator.py`

- [ ] **Step 1: 创建 aggregator.py**

```python
"""
数据源聚合器模块

统一入口，对外提供数据访问接口
"""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from .base import DataSourceAdapter
from .registry import AdapterRegistry
from .executor import FallbackExecutor
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement

logger = logging.getLogger(__name__)


class DataSourceAggregator:
    """
    数据源聚合器

    单例模式，提供统一的数据访问接口
    自动处理数据源降级和优先级
    """

    _instance = None
    _initialized = False

    def __new__(cls, config_path: str = "config/sources.json"):
        """
        单例模式

        Args:
            config_path: 配置文件路径
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/sources.json"):
        """
        初始化聚合器

        Args:
            config_path: 配置文件路径
        """
        if self._initialized:
            return

        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.registry = AdapterRegistry()
        self.executor: Optional[FallbackExecutor] = None

        # 加载配置
        self._load_config()

        # 创建执行器
        self.executor = FallbackExecutor(self.config)

        # 自动发现并初始化适配器
        self._initialize_adapters()

        self._initialized = True
        logger.info("DataSourceAggregator initialized successfully")

    def _load_config(self):
        """加载配置文件"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}, using default config")
            self.config = self._get_default_config()
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "sources": {
                "realtime": [
                    {"name": "sina", "priority": 10, "enabled": True, "timeout": 3},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 5},
                    {"name": "tushare", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "kline": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 10},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 10},
                    {"name": "sina", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "fundamentals": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 15},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 15}
                ]
            },
            "fallback": {
                "max_retries": 2,
                "retry_delay": 0.5,
                "log_failures": True
            }
        }

    def _initialize_adapters(self):
        """初始化所有适配器"""
        # 自动发现适配器类
        self.registry.auto_discover()

        # 根据配置创建适配器实例
        for category, sources in self.config.get('sources', {}).items():
            for source_cfg in sources:
                if source_cfg.get('enabled', True):
                    source_name = source_cfg['name']

                    # 跳过尚未实现的适配器
                    if source_name not in self.registry.get_adapter_names():
                        logger.warning(f"Adapter {source_name} not implemented, skipping")
                        continue

                    try:
                        # 创建适配器实例
                        adapter = self.registry.create_adapter(
                            source_name,
                            timeout=source_cfg.get('timeout', 5)
                        )

                        # 设置优先级（如果适配器支持）
                        if hasattr(adapter, '_priority'):
                            adapter._priority = source_cfg.get('priority', 100)  # type: ignore

                        logger.info(f"Initialized adapter: {source_name}")

                    except Exception as e:
                        logger.error(f"Failed to initialize {source_name}: {e}", exc_info=True)

    def _get_sorted_adapters(self, category: str) -> List[DataSourceAdapter]:
        """
        获取按优先级排序的适配器列表

        Args:
            category: 数据类别 (realtime, kline, fundamentals)

        Returns:
            排序后的适配器列表
        """
        sources = self.config.get('sources', {}).get(category, [])

        # 获取所有已启用的适配器
        adapters = []
        for source_cfg in sources:
            if source_cfg.get('enabled', True):
                adapter = self.registry.get_adapter(source_cfg['name'])
                if adapter:
                    adapters.append(adapter)

        # 按优先级排序
        adapters.sort(key=lambda a: getattr(a, 'priority', 100))

        return adapters

    # ========== 对外统一接口 ==========

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """
        获取单个股票实时行情

        Args:
            symbol: 股票代码

        Returns:
            Quote 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('realtime')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_realtime(symbol),
            "get_realtime"
        )

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表
        """
        if not self.executor:
            return []

        adapters = self._get_sorted_adapters('realtime')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.batch_get_realtime(symbols),
            "batch_get_realtime"
        )

        return result if result is not None else []

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """
        获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            KLine 对象列表
        """
        if not self.executor:
            return []

        adapters = self._get_sorted_adapters('kline')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_kline(symbol, interval, start_date, end_date),
            "get_kline"
        )

        return result if result is not None else []

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """
        获取资产负债表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            BalanceSheet 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_balance_sheet(symbol, year, quarter),
            "get_balance_sheet"
        )

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """
        获取利润表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            IncomeStatement 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_income_statement(symbol, year, quarter),
            "get_income_statement"
        )

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """
        获取现金流量表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            CashFlowStatement 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_cash_flow_statement(symbol, year, quarter),
            "get_cash_flow_statement"
        )

    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """
        获取财务指标

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}
        """
        if not self.executor:
            return {}

        adapters = self._get_sorted_adapters('fundamentals')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_financial_indicators(symbol, year, quarter),
            "get_financial_indicators"
        )

        return result if result is not None else {}


# ========== 简化调用接口 ==========

class QuoteAPI:
    """实时行情 API"""

    @staticmethod
    def get_realtime(symbol: str) -> Optional[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.get_realtime(symbol)

    @staticmethod
    def batch_get_realtime(symbols: List[str]) -> List[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.batch_get_realtime(symbols)


class KLineAPI:
    """K线数据 API"""

    @staticmethod
    def get(symbol: str, interval: str = "1d",
            start_date: str = "", end_date: str = "") -> List[KLine]:
        aggregator = DataSourceAggregator()
        return aggregator.get_kline(symbol, interval, start_date, end_date)


class FundamentalsAPI:
    """基本面数据 API"""

    @staticmethod
    def get_balance_sheet(symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        aggregator = DataSourceAggregator()
        return aggregator.get_balance_sheet(symbol, year, quarter)

    @staticmethod
    def get_income_statement(symbol: str, year: int, quarter: int) -> Optional[IncomeStatement]:
        aggregator = DataSourceAggregator()
        return aggregator.get_income_statement(symbol, year, quarter)

    @staticmethod
    def get_cash_flow_statement(symbol: str, year: int, quarter: int) -> Optional[CashFlowStatement]:
        aggregator = DataSourceAggregator()
        return aggregator.get_cash_flow_statement(symbol, year, quarter)

    @staticmethod
    def get_indicators(symbol: str, year: int, quarter: int) -> Dict[str, float]:
        aggregator = DataSourceAggregator()
        return aggregator.get_financial_indicators(symbol, year, quarter)
```

- [ ] **Step 2: 更新主 __init__.py 导出聚合器**

```python
# 追加到 data_sources/__init__.py
from .aggregator import (
    DataSourceAggregator,
    QuoteAPI,
    KLineAPI,
    FundamentalsAPI
)

__all__.extend([
    "DataSourceAggregator",
    "QuoteAPI",
    "KLineAPI",
    "FundamentalsAPI"
])
```

- [ ] **Step 3: 提交聚合器代码**

```bash
git add data_sources/aggregator.py
git commit -m "feat: add DataSourceAggregator with unified API"
```

---

### Task 2.4: 为核心引擎编写单元测试

**Files:**
- Create: `tests/test_registry.py`
- Create: `tests/test_executor.py`
- Create: `tests/test_aggregator.py`

- [ ] **Step 1: 编写 registry 测试 (tests/test_registry.py)**

```python
"""测试适配器注册表"""

import pytest
from unittest.mock import Mock, MagicMock
from data_sources.registry import AdapterRegistry
from data_sources.base import DataSourceAdapter


class MockAdapter(DataSourceAdapter):
    """模拟适配器用于测试"""

    @property
    def name(self) -> str:
        return "mock"

    def get_realtime(self, symbol: str):
        return None

    def batch_get_realtime(self, symbols):
        return []

    def get_kline(self, symbol, interval, start_date, end_date):
        return []

    def get_balance_sheet(self, symbol, year, quarter):
        return None

    def get_income_statement(self, symbol, year, quarter):
        return None

    def get_cash_flow_statement(self, symbol, year, quarter):
        return None

    def get_financial_indicators(self, symbol, year, quarter):
        return {}


def test_registry_can_register_class():
    """测试注册表可以注册适配器类"""
    registry = AdapterRegistry()
    registry.register_class(MockAdapter)

    assert "mock" in registry.get_adapter_names()


def test_registry_can_create_instance():
    """测试注册表可以创建实例"""
    registry = AdapterRegistry()
    registry.register_class(MockAdapter)

    adapter = registry.create_adapter("mock", timeout=5)

    assert adapter is not None
    assert adapter.name == "mock"


def test_registry_returns_none_for_unknown_adapter():
    """测试获取未知适配器返回 None"""
    registry = AdapterRegistry()

    adapter = registry.get_adapter("unknown")

    assert adapter is None
```

- [ ] **Step 2: 编写 executor 测试 (tests/test_executor.py)**

```python
"""测试降级执行器"""

import pytest
from unittest.mock import Mock, MagicMock
from data_sources.executor import FallbackExecutor
from data_sources.base import DataSourceAdapter
from data_sources.exceptions import DataSourceError


class MockAdapter(DataSourceAdapter):
    """模拟适配器"""

    def __init__(self, name: str, should_fail: bool = False):
        self._name = name
        self._should_fail = should_fail
        self._priority = 100

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def get_realtime(self, symbol: str):
        if self._should_fail:
            raise DataSourceError(self.name, "Mock error")
        return Mock(symbol=symbol, price=100.0)


def test_executor_succeeds_on_first_adapter():
    """测试执行器在第一个适配器成功时返回结果"""
    config = {
        "fallback": {"max_retries": 1, "retry_delay": 0.1}
    }

    executor = FallbackExecutor(config)
    adapter1 = MockAdapter("success", should_fail=False)
    adapters = [adapter1]

    result = executor.execute_with_fallback(
        adapters,
        lambda a: a.get_realtime("600519"),
        "test_operation"
    )

    assert result is not None


def test_executor_falls_back_on_failure():
    """测试执行器在第一个适配器失败时降级"""
    config = {
        "fallback": {"max_retries": 1, "retry_delay": 0.1}
    }

    executor = FallbackExecutor(config)
    adapter1 = MockAdapter("fail", should_fail=True)
    adapter2 = MockAdapter("success", should_fail=False)
    adapters = [adapter1, adapter2]

    result = executor.execute_with_fallback(
        adapters,
        lambda a: a.get_realtime("600519"),
        "test_operation"
    )

    assert result is not None


def test_executor_returns_none_when_all_fail():
    """测试所有适配器都失败时返回 None"""
    config = {
        "fallback": {"max_retries": 1, "retry_delay": 0.1}
    }

    executor = FallbackExecutor(config)
    adapter1 = MockAdapter("fail1", should_fail=True)
    adapter2 = MockAdapter("fail2", should_fail=True)
    adapters = [adapter1, adapter2]

    result = executor.execute_with_fallback(
        adapters,
        lambda a: a.get_realtime("600519"),
        "test_operation"
    )

    assert result is None
```

- [ ] **Step 3: 编写 aggregator 测试 (tests/test_aggregator.py)**

```python
"""测试数据源聚合器"""

import pytest
from unittest.mock import Mock, patch
from data_sources.aggregator import DataSourceAggregator
from data_sources.models import Quote


def test_aggregator_is_singleton():
    """测试聚合器是单例"""
    aggregator1 = DataSourceAggregator.__new__(DataSourceAggregator)
    aggregator1._initialized = True

    aggregator2 = DataSourceAggregator()

    assert aggregator1 is aggregator2


@patch('data_sources.aggregator.FallbackExecutor')
@patch('data_sources.aggregator.AdapterRegistry')
def test_aggregator_initializes(mock_registry, mock_executor):
    """测试聚合器初始化"""
    # 重置单例
    DataSourceAggregator._instance = None
    DataSourceAggregator._initialized = False

    aggregator = DataSourceAggregator(config_path="tests/test_config.json")

    assert aggregator.config is not None
    assert aggregator.registry is not None
    assert aggregator.executor is not None


# 注意：更多集成测试将在适配器实现后添加
```

- [ ] **Step 4: 创建测试配置文件**

```bash
mkdir -p config
```

创建 `config/sources.json`:

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

- [ ] **Step 5: 运行核心引擎测试**

```bash
pytest tests/test_registry.py -v
pytest tests/test_executor.py -v
pytest tests/test_aggregator.py -v
```

- [ ] **Step 6: 提交测试和配置**

```bash
git add config/sources.json tests/test_registry.py tests/test_executor.py tests/test_aggregator.py
git commit -m "test: add unit tests for core engine (registry, executor, aggregator)"
```

---

## Chunk 3: 数据源适配器实现

### Task 3.1: 实现 Tushare 适配器

**Files:**
- Create: `data_sources/adapters/tushare_adapter.py`

- [ ] **Step 1: 安装依赖**

```bash
pip install tushare
```

更新 `requirements.txt`:

```txt
tushare>=1.2.87
```

- [ ] **Step 2: 创建 tushare_adapter.py**

```python
"""
Tushare Pro 数据源适配器
"""

import tushare as ts
import logging
from typing import List, Optional, Dict
from datetime import datetime
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError

logger = logging.getLogger(__name__)


class TushareAdapter(DataSourceAdapter):
    """
    Tushare Pro 数据源适配器

    官网: https://tushare.pro
    特点: 数据规范、稳定、基本面数据强
    限制: 需要 Token，高频受限
    """

    def __init__(self, token: str, timeout: int = 10):
        """
        Args:
            token: Tushare API Token
            timeout: 超时时间（秒）
        """
        self.token = token
        self.timeout = timeout
        self.pro = ts.pro_api(token)
        self._priority = 30  # 默认优先级，可在配置中覆盖
        logger.info("TushareAdapter initialized")

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def priority(self) -> int:
        return self._priority

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            # Tushare 的 daily_basic 提供当日行情
            ts_code = self._format_symbol(symbol)
            today = datetime.now().strftime('%Y%m%d')

            df = self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=today
            )

            if len(df) == 0:
                logger.warning(f"No realtime data found for {symbol}")
                return None

            row = df.iloc[0]

            return Quote(
                symbol=symbol,
                price=float(row['close']),
                change=float(row['close']) - float(row['pre_close']),
                percent=(float(row['close']) - float(row['pre_close'])) / float(row['pre_close']),
                volume=int(row['volume']) * 100,  # 手 -> 股
                amount=float(row['amount']) * 1000,  # 千元 -> 元
                bid_price=[],
                bid_volume=[],
                ask_price=[],
                ask_volume=[],
                timestamp=datetime.now()
            )

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get realtime: {e}", e)

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        quotes = []

        try:
            # Tushare 支持批量查询
            ts_codes = [self._format_symbol(s) for s in symbols]
            ts_codes_str = ','.join(ts_codes)
            today = datetime.now().strftime('%Y%m%d')

            df = self.pro.daily_basic(
                ts_code=ts_codes_str,
                trade_date=today
            )

            for _, row in df.iterrows():
                symbol = self._parse_symbol(row['ts_code'])
                quote = Quote(
                    symbol=symbol,
                    price=float(row['close']),
                    change=float(row['close']) - float(row['pre_close']),
                    percent=(float(row['close']) - float(row['pre_close'])) / float(row['pre_close']),
                    volume=int(row['volume']) * 100,
                    amount=float(row['amount']) * 1000,
                    bid_price=[],
                    bid_volume=[],
                    ask_price=[],
                    ask_volume=[],
                    timestamp=datetime.now()
                )
                quotes.append(quote)

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to batch get realtime: {e}", e)

        return quotes

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """获取K线数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # Tushare 的 bar 接口支持分钟线
            freq_map = {
                "1m": "1min", "5m": "5min", "15m": "15min",
                "30m": "30min", "60m": "60min", "1d": "D",
                "1w": "W", "1M": "M"
            }
            freq = freq_map.get(interval, "D")

            # 转换日期格式 YYYYMMDD
            start_date_fmt = start_date.replace('-', '') if start_date else ''
            end_date_fmt = end_date.replace('-', '') if end_date else ''

            df = self.pro.bar(
                ts_code=ts_code,
                asset='E',  # 股票
                adj='qfq',  # 前复权
                start_date=start_date_fmt,
                end_date=end_date_fmt,
                freq=freq
            )

            klines = []
            for _, row in df.iterrows():
                # Tushare 的 trade_time 格式可能是 "2023-01-01" 或 "2023-01-01 10:30:00"
                try:
                    dt = datetime.strptime(row['trade_time'], '%Y-%m-%d %H:%M:%S')
                except:
                    dt = datetime.strptime(row['trade_time'], '%Y-%m-%d')

                kline = KLine(
                    symbol=symbol,
                    datetime=dt,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['vol']) * 100,  # 手 -> 股
                    amount=float(row['amount']) * 1000  # 千元 -> 元
                )
                klines.append(kline)

            return klines

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get kline: {e}", e)

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        try:
            ts_code = self._format_symbol(symbol)

            # Tushare 的 period 格式: YYYYQQDD (如 20230331 表示 2023年一季度)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.balancesheet(
                ts_code=ts_code,
                period=period
            )

            if len(df) == 0:
                logger.warning(f"No balance sheet found for {symbol} {year}Q{quarter}")
                return None

            row = df.iloc[0]

            return BalanceSheet(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                total_assets=float(row['total_assets']),
                total_liabilities=float(row['total_liab']),
                shareholders_equity=float(row['total_hldr_eqy_inc_min_int'])
            )

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get balance sheet: {e}", e)

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """获取利润表"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.income(
                ts_code=ts_code,
                period=period
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]

            return IncomeStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                revenue=float(row['revenue']),
                net_profit=float(row['n_income']),
                eps=float(row['basic_eps']) if 'basic_eps' in row else 0.0
            )

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get income statement: {e}", e)

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """获取现金流量表"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.cashflow(
                ts_code=ts_code,
                period=period
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]

            return CashFlowStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                operating_cash_flow=float(row['net_cashflow_oper_act']),
                investing_cash_flow=float(row['net_cashflow_inv_act']),
                financing_cash_flow=float(row['net_cashflow_fnc_act'])
            )

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get cash flow statement: {e}", e)

    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """获取财务指标"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.fina_indicator(
                ts_code=ts_code,
                period=period
            )

            if len(df) == 0:
                return {}

            row = df.iloc[0]

            return {
                "roe": float(row['roe']) if 'roe' in row and not row['roe'] is None else 0.0,
                "gross_margin": float(row['grossprofit_margin']) if 'grossprofit_margin' in row else 0.0,
                "net_profit_margin": float(row['netprofit_margin']) if 'netprofit_margin' in row else 0.0,
                "asset_liability_ratio": float(row['asset_liab_ratio']) if 'asset_liab_ratio' in row else 0.0
            }

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get financial indicators: {e}", e)

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为 Tushare 格式

        Tushare 格式: 600519.SH (沪市) 或 000001.SZ (深市)
        """
        if symbol.startswith(('6', '9', '7')):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"

    def _parse_symbol(self, ts_code: str) -> str:
        """
        从 Tushare 代码解析股票代码

        Tushare 格式: 600519.SH -> 600519
        """
        return ts_code.split('.')[0]
```

- [ ] **Step 3: 更新 adapters/__init__.py**

```python
# 追加到 data_sources/adapters/__init__.py
from .tushare_adapter import TushareAdapter

__all__.append("TushareAdapter")
```

- [ ] **Step 4: 提交 Tushare 适配器**

```bash
git add data_sources/adapters/tushare_adapter.py requirements.txt
git commit -m "feat: add Tushare Pro data source adapter"
```

---

### Task 3.2: 为 Tushare 适配器编写测试

**Files:**
- Create: `tests/adapters/test_tushare_adapter.py`

- [ ] **Step 1: 编写测试文件**

```python
"""测试 Tushare 适配器"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from data_sources.adapters.tushare_adapter import TushareAdapter
from data_sources.models import Quote, KLine


@pytest.fixture
def mock_tushare_adapter():
    """创建模拟的 TushareAdapter"""
    with patch('data_sources.adapters.tushare_adapter.ts') as mock_ts:
        mock_pro = Mock()
        mock_ts.pro_api.return_value = mock_pro

        adapter = TushareAdapter(token="test_token", timeout=1)
        adapter.pro = mock_pro

        return adapter, mock_pro


def test_tushare_adapter_name():
    """测试适配器名称"""
    adapter = TushareAdapter(token="test", timeout=1)
    assert adapter.name == "tushare"


@patch('data_sources.adapters.tushare_adapter.ts')
def test_format_symbol_shanghai(mock_ts):
    """测试沪市股票代码格式化"""
    adapter = TushareAdapter(token="test", timeout=1)

    assert adapter._format_symbol("600519") == "600519.SH"
    assert adapter._format_symbol("601318") == "601318.SH"


@patch('data_sources.adapters.tushare_adapter.ts')
def test_format_symbol_shenzhen(mock_ts):
    """测试深市股票代码格式化"""
    adapter = TushareAdapter(token="test", timeout=1)

    assert adapter._format_symbol("000001") == "000001.SZ"
    assert adapter._format_symbol("300750") == "300750.SZ"


# 注意：更多集成测试需要真实的 Tushare Token
# 建议在 CI/CD 中使用环境变量注入测试 Token
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/adapters/test_tushare_adapter.py -v
```

- [ ] **Step 3: 提交测试**

```bash
git add tests/adapters/test_tushare_adapter.py
git commit -m "test: add unit tests for Tushare adapter"
```

---

### Task 3.3: 实现 AKShare 适配器

**Files:**
- Create: `data_sources/adapters/akshare_adapter.py`

- [ ] **Step 1: 安装依赖**

```bash
pip install akshare
```

更新 `requirements.txt`:

```txt
akshare>=1.11.0
```

- [ ] **Step 2: 创建 akshare_adapter.py** (部分实现)

```python
"""
AKShare 数据源适配器
"""

import akshare as ak
import logging
from typing import List, Optional, Dict
from datetime import datetime
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError

logger = logging.getLogger(__name__)


class AKShareAdapter(DataSourceAdapter):
    """
    AKShare 数据源适配器

    官网: https://akshare.akfamily.xyz
    特点: 免费、覆盖广、特色数据丰富
    限制: 依赖源站变动、需频繁升级
    """

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout
        self._priority = 20
        logger.info("AKShareAdapter initialized")

    @property
    def name(self) -> str:
        return "akshare"

    @property
    def priority(self) -> int:
        return self._priority

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            # 使用东方财富源
            df = ak.stock_zh_a_spot_em()

            stock_data = df[df['代码'] == symbol]

            if len(stock_data) == 0:
                return None

            row = stock_data.iloc[0]

            return Quote(
                symbol=symbol,
                price=float(row['最新价']),
                change=float(row['涨跌额']),
                percent=float(row['涨跌幅']) / 100,
                volume=int(row['成交量']),
                amount=float(row['成交额']),
                bid_price=[],
                bid_volume=[],
                ask_price=[],
                ask_volume=[],
                timestamp=datetime.now()
            )

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to get realtime: {e}", e)

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        quotes = []

        try:
            df = ak.stock_zh_a_spot_em()

            for symbol in symbols:
                stock_data = df[df['代码'] == symbol]

                if len(stock_data) > 0:
                    row = stock_data.iloc[0]
                    quote = Quote(
                        symbol=symbol,
                        price=float(row['最新价']),
                        change=float(row['涨跌额']),
                        percent=float(row['涨跌幅']) / 100,
                        volume=int(row['成交量']),
                        amount=float(row['成交额']),
                        bid_price=[],
                        bid_volume=[],
                        ask_price=[],
                        ask_volume=[],
                        timestamp=datetime.now()
                    )
                    quotes.append(quote)

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to batch get realtime: {e}", e)

        return quotes

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """获取K线数据"""
        try:
            # AKShare 支持多周期
            period_map = {
                "1m": "1", "5m": "5", "15m": "15",
                "30m": "30", "60m": "60", "1d": "daily"
            }
            period = period_map.get(interval, "daily")

            if period == "daily":
                # 日线
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', '') if start_date else "",
                    end_date=end_date.replace('-', '') if end_date else "",
                    adjust="qfq"  # 前复权
                )
            else:
                # 分钟线
                df = ak.stock_zh_a_minute(
                    symbol=symbol,
                    period=period,
                    adjust="qfq"
                )

            klines = []
            for _, row in df.iterrows():
                # 日期格式转换
                if '日期' in row:
                    dt = datetime.strptime(row['日期'], '%Y-%m-%d')
                elif 'day' in row:
                    dt = datetime.strptime(row['day'], '%Y-%m-%d %H:%M:%S')
                else:
                    continue

                kline = KLine(
                    symbol=symbol,
                    datetime=dt,
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    volume=int(row['成交量']),
                    amount=float(row['成交额'])
                )
                klines.append(kline)

            return klines

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to get kline: {e}", e)

    # 基本面数据方法暂未实现（需要更多清洗）
    # 可在后续迭代中完善

    def get_balance_sheet(self, symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        raise NotImplementedError("AKShare balance sheet not implemented yet")

    def get_income_statement(self, symbol: str, year: int, quarter: int) -> Optional[IncomeStatement]:
        raise NotImplementedError("AKShare income statement not implemented yet")

    def get_cash_flow_statement(self, symbol: str, year: int, quarter: int) -> Optional[CashFlowStatement]:
        raise NotImplementedError("AKShare cash flow statement not implemented yet")

    def get_financial_indicators(self, symbol: str, year: int, quarter: int) -> Dict[str, float]:
        return {}
```

- [ ] **Step 3: 更新 adapters/__init__.py**

```python
# 追加到 data_sources/adapters/__init__.py
from .akshare_adapter import AKShareAdapter

__all__.append("AKShareAdapter")
```

- [ ] **Step 4: 提交 AKShare 适配器**

```bash
git add data_sources/adapters/akshare_adapter.py
git commit -m "feat: add AKShare data source adapter (realtime and kline)"
```

---

### Task 3.4-3.5: 实现新浪财经和东方财富适配器

由于篇幅限制，这两个适配器的实现类似，主要区别在于：

**新浪财经适配器 (sina_adapter.py):**
- 使用 HTTP 直连新浪 API
- 优势：实时性最强、免费
- 实现 `get_realtime`, `batch_get_realtime`, `get_kline`

**东方财富适配器 (eastmoney_adapter.py):**
- 可能需要网页抓取或逆向 APP 接口
- 优势：数据全面
- 实现部分核心方法

建议按以下顺序完成：
1. 先完成 Tushare 和 AKShare（覆盖大部分需求）
2. 再实现新浪财经（用于实时行情降级）
3. 最后实现东方财富（可选，用于特色数据）

---

## Chunk 4: 集成测试和文档

### Task 4.1: 编写集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
"""集成测试 - 测试完整的数据源聚合流程"""

import pytest
from unittest.mock import Mock, patch
from data_sources import DataSourceAggregator, QuoteAPI, KLineAPI


def test_end_to_end_mock():
    """端到端测试（使用 mock）"""
    with patch('data_sources.adapters.tushare_adapter.ts') as mock_ts:
        # 模拟 Tushare 返回数据
        mock_pro = Mock()
        mock_ts.pro_api.return_value = mock_pro

        mock_df = Mock()
        mock_df.__len__ = Mock(return_value=1)
        mock_df.iloc = Mock()
        mock_row = Mock()
        mock_row.close = 100.0
        mock_row.pre_close = 99.0
        mock_row.volume = 10000
        mock_row.amount = 1000000
        mock_df.iloc.__getitem__ = Mock(return_value=mock_row)

        mock_pro.daily_basic.return_value = mock_df

        # 测试聚合器
        aggregator = DataSourceAggregator.__new__(DataSourceAggregator)
        aggregator._initialized = False
        aggregator.config = {
            "sources": {
                "realtime": [{"name": "tushare", "priority": 10, "enabled": True, "timeout": 5}]
            },
            "fallback": {"max_retries": 1, "retry_delay": 0.1}
        }

        # 初始化
        from data_sources.registry import AdapterRegistry
        from data_sources.executor import FallbackExecutor

        aggregator.registry = AdapterRegistry()
        aggregator.executor = FallbackExecutor(aggregator.config)

        # 注册 mock 适配器
        from data_sources.adapters.tushare_adapter import TushareAdapter
        mock_adapter = TushareAdapter(token="test", timeout=1)
        mock_adapter.pro = mock_pro
        aggregator.registry._adapters["tushare"] = mock_adapter

        # 调用 API
        from data_sources.aggregator import QuoteAPI
        quote = QuoteAPI.get_realtime("600519")

        assert quote is not None
        assert quote.symbol == "600519"


# 更多集成测试...
```

- [ ] **Step 2: 运行所有测试**

```bash
pytest tests/ -v --tb=short
pytest tests/ -v --cov=data_sources --cov-report=html
```

- [ ] **Step 3: 检查覆盖率**

确保达到 80%+ 覆盖率

---

### Task 4.2: 编写使用文档

**Files:**
- Create: `data_sources/README.md`

创建详细的使用文档，包括：
- 安装说明
- 快速开始
- API 参考
- 配置说明
- 常见问题

---

## 实施检查清单

- [ ] Chunk 1: 基础设施完成
  - [ ] 数据模型 (models.py)
  - [ ] 异常定义 (exceptions.py)
  - [ ] 抽象接口 (base.py)
  - [ ] 单元测试

- [ ] Chunk 2: 核心引擎完成
  - [ ] 适配器注册表 (registry.py)
  - [ ] 降级执行器 (executor.py)
  - [ ] 数据源聚合器 (aggregator.py)
  - [ ] 单元测试

- [ ] Chunk 3: 数据源适配器完成
  - [ ] Tushare 适配器
  - [ ] AKShare 适配器
  - [ ] 新浪财经适配器
  - [ ] 东方财富适配器
  - [ ] 单元测试

- [ ] Chunk 4: 集成测试和文档
  - [ ] 集成测试
  - [ ] 使用文档
  - [ ] 部署文档

---

**计划完成，准备执行？**