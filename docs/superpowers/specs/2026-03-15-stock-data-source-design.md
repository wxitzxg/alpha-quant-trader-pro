# 股票数据源聚合模块设计文档

**日期：** 2026-03-15
**模块名称：** data_sources
**状态：** ✅ 设计完成，等待评审

---

## 1. 需求概述

### 1.1 业务背景
量化交易系统需要从多个数据源获取股票市场数据，不同数据源在实时性、稳定性、覆盖范围、数据质量等方面各有优劣。

### 1.2 设计目标
- ✅ **统一接口**：对上层业务提供统一的数据访问接口
- ✅ **自动降级**：支持配置数据源优先级，失败时自动降级到备用源
- ✅ **可扩展性**：方便新增数据源适配器，无需修改核心逻辑
- ✅ **模块化**：作为系统内部模块，易于集成到量化交易系统

### 1.3 支持的数据源
| 数据源 | 优势 | 劣势 |
|--------|------|------|
| Tushare Pro | 数据规范、稳定、基本面数据强 | 收费/积分制、高频受限 |
| AKShare | 免费、覆盖广、特色数据丰富 | 依赖源站变动、需频繁升级 |
| 新浪财经 | 实时性强、免费、速度快 | 无官方文档、历史数据少 |
| 东方财富 | 数据全面、复权数据好 | 反爬严格、加密参数多 |

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────┐
│              量化交易系统 (alpha-quant-trader-pro)  │
│  ┌─────────────┬─────────────┬──────────────────┐  │
│  │  策略引擎    │   回测模块    │   风控模块        │  │
│  └──────┬──────┴──────┬──────┴────────┬─────────┘  │
│         │              │               │            │
│         └──────────────┼───────────────┘            │
│                        │                            │
│         ┌──────────────▼────────────────┐          │
│         │   数据源聚合模块 (data_sources) │          │
│         │  ┌─────────────────────────┐  │          │
│         │  │  降级执行器              │  │          │
│         │  │  - sources.json 优先级   │  │          │
│         │  │  - 自动重试 + 降级       │  │          │
│         │  └──────────┬──────────────┘  │          │
│         │             │                  │          │
│         │  ┌──────────▼──────────────┐  │          │
│         │  │  适配器注册表            │  │          │
│         │  │  - 自动发现适配器        │  │          │
│         │  │  - 验证 ABC 接口         │  │          │
│         │  └──────────┬──────────────┘  │          │
│         │             │                  │          │
│         │  ┌──────────┴──────────────────┐         │
│         │  │  适配器实现                 │         │
│         │  │  Tushare | AKShare | Sina  │         │
│         │  │  | EastMoney               │         │
│         │  └─────────────────────────────┘         │
│         └─────────────────────────────────────────┘
└─────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 关键特性 |
|------|------|----------|
| **DataSourceAggregator** | 统一入口，对外提供数据访问 | 单例模式、初始化配置 |
| **FallbackExecutor** | 按优先级执行 + 自动降级 | 可配置重试次数、超时控制 |
| **AdapterRegistry** | 插件系统管理所有数据源 | 自动发现、验证接口 |
| **DataSourceAdapter** | 抽象基类定义统一接口 | ABC 强制实现、类型安全 |
| **TushareAdapter** | Tushare Pro 数据源适配器 | 积分/Token 管理 |
| **AKShareAdapter** | AKShare 数据源适配器 | 多源切换、异常处理 |
| **SinaAdapter** | 新浪财经数据源适配器 | HTTP 直连、快速解析 |
| **EastMoneyAdapter** | 东方财富数据源适配器 | 反爬策略处理 |
| **sources.json** | 数据源优先级配置 | 可热加载、支持注释 |

---

## 3. 详细设计

### 3.1 抽象接口定义

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# ========== 数据模型 ==========

class Quote(BaseModel):
    """实时行情数据"""
    symbol: str
    price: float
    change: float
    percent: float
    volume: int
    amount: float
    bid_price: List[float]  # 五档买价
    bid_volume: List[int]   # 五档买量
    ask_price: List[float]  # 五档卖价
    ask_volume: List[int]   # 五档卖量
    timestamp: datetime

class KLine(BaseModel):
    """K线数据"""
    symbol: str
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover: Optional[float] = None  # 换手率

class FinancialStatement(BaseModel):
    """财务报表基础模型"""
    symbol: str
    year: int
    quarter: int
    report_date: str

class BalanceSheet(FinancialStatement):
    """资产负债表"""
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    # ... 其他字段

class IncomeStatement(FinancialStatement):
    """利润表"""
    revenue: float
    net_profit: float
    eps: float
    # ... 其他字段

class CashFlowStatement(FinancialStatement):
    """现金流量表"""
    operating_cash_flow: float
    investing_cash_flow: float
    financing_cash_flow: float
    # ... 其他字段


# ========== 抽象适配器接口 ==========

class DataSourceAdapter(ABC):
    """所有数据源适配器必须实现的接口"""

    @abstractmethod
    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取单个股票实时行情

        Args:
            symbol: 股票代码 (如 "600519")

        Returns:
            Quote 对象，失败返回 None
        """
        pass

    @abstractmethod
    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表 (可能为空)
        """
        pass

    @abstractmethod
    def get_kline(self, symbol: str, interval: str,
                  start_date: str, end_date: str) -> List[KLine]:
        """获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            KLine 对象列表 (可能为空)
        """
        pass

    @abstractmethod
    def get_balance_sheet(self, symbol: str, year: int,
                         quarter: int) -> Optional[BalanceSheet]:
        """获取资产负债表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            BalanceSheet 对象，失败返回 None
        """
        pass

    @abstractmethod
    def get_income_statement(self, symbol: str, year: int,
                            quarter: int) -> Optional[IncomeStatement]:
        """获取利润表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            IncomeStatement 对象，失败返回 None
        """
        pass

    @abstractmethod
    def get_cash_flow_statement(self, symbol: str, year: int,
                               quarter: int) -> Optional[CashFlowStatement]:
        """获取现金流量表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            CashFlowStatement 对象，失败返回 None
        """
        pass

    @abstractmethod
    def get_financial_indicators(self, symbol: str, year: int,
                                quarter: int) -> dict:
        """获取财务指标

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称

        Returns:
            数据源唯一标识 (如 "tushare", "akshare")
        """
        pass

    @property
    def priority(self) -> int:
        """数据源优先级

        Returns:
            优先级数值，越小越优先
        """
        return 100  # 默认低优先级

    def is_available(self) -> bool:
        """检查数据源是否可用

        Returns:
            True 表示可用
        """
        return True


# ========== 异常定义 ==========

class DataSourceError(Exception):
    """数据源异常基类"""
    def __init__(self, source: str, message: str, original_error: Optional[Exception] = None):
        self.source = source
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{source}] {message}")
```

---

### 3.2 配置文件设计

**文件位置：** `config/sources.json`

```json
{
  "version": "1.0",
  "default_priority": 100,

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

**配置说明：**
- `sources.<category>`: 不同数据类别的优先级列表
- `priority`: 数值越小越优先
- `timeout`: 单个数据源超时时间（秒）
- `fallback.max_retries`: 每个数据源最大重试次数
- `fallback.retry_delay`: 重试间隔（秒）

---

### 3.3 降级执行器设计

```python
from typing import List, Callable, Optional, TypeVar
import time
import logging

T = TypeVar('T')

class FallbackExecutor:
    """降级执行器 - 按优先级执行，失败自动降级"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def execute_with_fallback(
        self,
        adapters: List[DataSourceAdapter],
        operation: Callable[[DataSourceAdapter], T],
        operation_name: str
    ) -> Optional[T]:
        """执行操作，失败时降级到下一个数据源

        Args:
            adapters: 已排序的适配器列表（按优先级）
            operation: 要执行的操作函数
            operation_name: 操作名称（用于日志）

        Returns:
            操作结果，所有数据源都失败返回 None
        """
        max_retries = self.config['fallback']['max_retries']
        retry_delay = self.config['fallback']['retry_delay']

        for adapter in adapters:
            if not adapter.is_available():
                continue

            source_config = self._get_source_config(adapter.name, operation_name)
            timeout = source_config.get('timeout', 5)

            for attempt in range(max_retries):
                try:
                    self.logger.info(
                        f"Executing {operation_name} on {adapter.name} "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    # 执行操作（可添加超时控制）
                    result = operation(adapter)

                    if result is not None:
                        self.logger.info(
                            f"✓ {operation_name} succeeded on {adapter.name}"
                        )
                        return result

                    self.logger.warning(
                        f"{operation_name} returned None on {adapter.name}"
                    )

                except Exception as e:
                    self.logger.error(
                        f"✗ {operation_name} failed on {adapter.name}: {e}"
                    )

                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

            # 当前数据源所有重试都失败，继续降级
            continue

        # 所有数据源都失败
        self.logger.error(f"All sources failed for {operation_name}")
        return None

    def _get_source_config(self, source_name: str, category: str) -> dict:
        """获取数据源配置"""
        sources_config = self.config['sources'].get(category, [])
        for cfg in sources_config:
            if cfg['name'] == source_name:
                return cfg
        return {}
```

---

### 3.4 适配器注册表设计

```python
from typing import Dict, Type, List
import importlib
import os

class AdapterRegistry:
    """适配器注册表 - 自动发现和管理适配器"""

    def __init__(self):
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._adapter_classes: Dict[str, Type[DataSourceAdapter]] = {}

    def auto_discover(self, package: str = "data_sources.adapters"):
        """自动发现适配器

        Args:
            package: 适配器包路径
        """
        # 动态导入所有适配器模块
        adapter_dir = os.path.join(os.path.dirname(__file__), "adapters")

        for filename in os.listdir(adapter_dir):
            if filename.endswith("_adapter.py") and not filename.startswith("__"):
                module_name = filename[:-3]
                module_path = f"{package}.{module_name}"

                try:
                    module = importlib.import_module(module_path)
                    # 查找继承自 DataSourceAdapter 的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, DataSourceAdapter) and attr != DataSourceAdapter:
                            self.register_class(attr)
                except Exception as e:
                    logging.warning(f"Failed to load adapter {module_name}: {e}")

    def register_class(self, adapter_class: Type[DataSourceAdapter]):
        """注册适配器类"""
        self._adapter_classes[adapter_class.name] = adapter_class

    def create_adapter(self, name: str, **kwargs) -> DataSourceAdapter:
        """创建适配器实例"""
        if name not in self._adapter_classes:
            raise ValueError(f"Adapter {name} not found")

        adapter = self._adapter_classes[name](**kwargs)
        self._adapters[name] = adapter
        return adapter

    def get_adapter(self, name: str) -> Optional[DataSourceAdapter]:
        """获取适配器实例"""
        return self._adapters.get(name)

    def get_all_adapters(self) -> List[DataSourceAdapter]:
        """获取所有适配器实例"""
        return list(self._adapters.values())
```

---

### 3.5 数据源聚合器设计

```python
import json
from typing import List, Optional
from pathlib import Path

class DataSourceAggregator:
    """数据源聚合器 - 统一入口"""

    _instance = None

    def __new__(cls, config_path: str = "config/sources.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/sources.json"):
        if self._initialized:
            return

        self.config_path = config_path
        self.config = self._load_config()
        self.registry = AdapterRegistry()
        self.executor = FallbackExecutor(self.config)

        # 自动发现并初始化适配器
        self.registry.auto_discover()
        self._initialize_adapters()

        self._initialized = True

    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _initialize_adapters(self):
        """初始化所有适配器"""
        for category, sources in self.config['sources'].items():
            for source_cfg in sources:
                if source_cfg['enabled']:
                    try:
                        self.registry.create_adapter(
                            source_cfg['name'],
                            timeout=source_cfg['timeout']
                        )
                    except Exception as e:
                        logging.warning(f"Failed to initialize {source_cfg['name']}: {e}")

    def _get_sorted_adapters(self, category: str) -> List[DataSourceAdapter]:
        """获取按优先级排序的适配器列表"""
        sources = self.config['sources'].get(category, [])
        adapters = []

        for source_cfg in sources:
            if source_cfg['enabled']:
                adapter = self.registry.get_adapter(source_cfg['name'])
                if adapter:
                    adapters.append(adapter)

        # 按优先级排序
        adapters.sort(key=lambda a: getattr(a, 'priority', 100))
        return adapters

    # ========== 对外统一接口 ==========

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        adapters = self._get_sorted_adapters('realtime')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_realtime(symbol),
            "get_realtime"
        )

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        adapters = self._get_sorted_adapters('realtime')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.batch_get_realtime(symbols),
            "batch_get_realtime"
        )

    def get_kline(self, symbol: str, interval: str,
                  start_date: str, end_date: str) -> List[KLine]:
        """获取K线数据"""
        adapters = self._get_sorted_adapters('kline')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_kline(symbol, interval, start_date, end_date),
            "get_kline"
        )

    def get_balance_sheet(self, symbol: str, year: int,
                         quarter: int) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        adapters = self._get_sorted_adapters('fundamentals')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_balance_sheet(symbol, year, quarter),
            "get_balance_sheet"
        )

    def get_income_statement(self, symbol: str, year: int,
                            quarter: int) -> Optional[IncomeStatement]:
        """获取利润表"""
        adapters = self._get_sorted_adapters('fundamentals')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_income_statement(symbol, year, quarter),
            "get_income_statement"
        )

    def get_cash_flow_statement(self, symbol: str, year: int,
                               quarter: int) -> Optional[CashFlowStatement]:
        """获取现金流量表"""
        adapters = self._get_sorted_adapters('fundamentals')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_cash_flow_statement(symbol, year, quarter),
            "get_cash_flow_statement"
        )

    def get_financial_indicators(self, symbol: str, year: int,
                                quarter: int) -> dict:
        """获取财务指标"""
        adapters = self._get_sorted_adapters('fundamentals')
        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_financial_indicators(symbol, year, quarter),
            "get_financial_indicators"
        )
```

---

### 3.6 适配器实现示例（Tushare）

```python
import tushare as ts
from typing import List, Optional
from datetime import datetime

class TushareAdapter(DataSourceAdapter):
    """Tushare Pro 数据源适配器"""

    def __init__(self, token: str, timeout: int = 10):
        self.token = token
        self.timeout = timeout
        self.pro = ts.pro_api(token)
        self._priority = 30  # 可在配置中覆盖

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def priority(self) -> int:
        return self._priority

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            # Tushare 实时行情需要高积分，这里作为备用
            df = self.pro.daily_basic(
                ts_code=self._format_symbol(symbol),
                trade_date=datetime.now().strftime('%Y%m%d')
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]
            return Quote(
                symbol=symbol,
                price=row['close'],
                change=row['close'] - row['pre_close'],
                percent=(row['close'] - row['pre_close']) / row['pre_close'],
                volume=int(row['volume'] * 100),  # 手 -> 股
                amount=float(row['amount'] * 1000),  # 千元 -> 元
                bid_price=[],
                bid_volume=[],
                ask_price=[],
                ask_volume=[],
                timestamp=datetime.now()
            )
        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get realtime: {e}", e)

    def get_kline(self, symbol: str, interval: str,
                  start_date: str, end_date: str) -> List[KLine]:
        """获取K线数据"""
        try:
            freq_map = {
                "1m": "1min", "5m": "5min", "15m": "15min",
                "30m": "30min", "60m": "60min", "1d": "D",
                "1w": "W", "1M": "M"
            }
            freq = freq_map.get(interval, "D")

            df = self.pro.bar(
                ts_code=self._format_symbol(symbol),
                asset='E',
                adj='qfq',  # 前复权
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                freq=freq
            )

            return [
                KLine(
                    symbol=symbol,
                    datetime=datetime.strptime(row['trade_time'], '%Y-%m-%d %H:%M:%S'),
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=int(row['vol'] * 100),
                    amount=float(row['amount'] * 1000)
                )
                for _, row in df.iterrows()
            ]
        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get kline: {e}", e)

    def get_balance_sheet(self, symbol: str, year: int,
                         quarter: int) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        try:
            df = self.pro.balancesheet(
                ts_code=self._format_symbol(symbol),
                period=f"{year}{quarter}01"
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]
            return BalanceSheet(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                total_assets=row['total_assets'],
                total_liabilities=row['total_liab'],
                shareholders_equity=row['total_hldr_eqy_inc_min_int']
            )
        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get balance sheet: {e}", e)

    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码为 Tushare 格式"""
        if symbol.startswith(('6', '9')):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"
```

---

## 4. 使用示例

### 4.1 初始化模块

```python
# 在系统启动时初始化一次
from data_sources import DataSourceAggregator

# 单例模式，多次调用返回同一实例
aggregator = DataSourceAggregator(config_path="config/sources.json")
```

### 4.2 获取实时行情

```python
from data_sources import DataSourceAggregator

aggregator = DataSourceAggregator()

# 单个股票
quote = aggregator.get_realtime("600519")
print(f"贵州茅台: {quote.price} 元")

# 批量获取
quotes = aggregator.batch_get_realtime(["600519", "000001", "601318"])
for q in quotes:
    print(f"{q.symbol}: {q.price}")
```

### 4.3 获取历史K线

```python
# 日线数据
klines = aggregator.get_kline(
    symbol="600519",
    interval="1d",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 5分钟线
klines = aggregator.get_kline(
    symbol="600519",
    interval="5m",
    start_date="2023-01-01",
    end_date="2023-01-05"
)
```

### 4.4 获取财务数据

```python
# 资产负债表
balance = aggregator.get_balance_sheet("600519", year=2023, quarter=3)

# 利润表
income = aggregator.get_income_statement("600519", year=2023, quarter=3)

# 财务指标
indicators = aggregator.get_financial_indicators("600519", year=2023, quarter=3)
print(f"ROE: {indicators.get('roe', 0):.2%}")
```

---

## 5. 目录结构

```
data_sources/
├── __init__.py                 # 对外导出统一接口
├── aggregator.py              # DataSourceAggregator
├── executor.py                # FallbackExecutor
├── registry.py                # AdapterRegistry
├── base.py                    # DataSourceAdapter (ABC)
├── exceptions.py              # DataSourceError
├── models.py                  # Pydantic 数据模型
├── config/
│   └── sources.json          # 数据源配置
└── adapters/
    ├── __init__.py
    ├── tushare_adapter.py    # Tushare Pro 适配器
    ├── akshare_adapter.py    # AKShare 适配器
    ├── sina_adapter.py       # 新浪财经 适配器
    └── eastmoney_adapter.py  # 东方财富 适配器

tests/
├── test_aggregator.py
├── test_executor.py
├── test_registry.py
└── adapters/
    ├── test_tushare_adapter.py
    ├── test_akshare_adapter.py
    ├── test_sina_adapter.py
    └── test_eastmoney_adapter.py
```

---

## 6. 测试策略

### 6.1 单元测试覆盖
- ✅ `DataSourceAdapter` 抽象类接口验证
- ✅ 每个适配器的独立功能测试
- ✅ 降级执行器的降级逻辑测试
- ✅ 适配器注册表的发现机制测试

### 6.2 集成测试覆盖
- ✅ 真实数据源调用测试（mock 网络请求）
- ✅ 降级场景测试（模拟数据源失败）
- ✅ 配置文件加载和热更新测试
- ✅ 并发访问测试

### 6.3 测试覆盖率目标
- **目标：** 80%+ 代码覆盖率
- **关键路径：** 降级逻辑、适配器转换、异常处理

---

## 7. 待实现的数据源适配器

### 7.1 Tushare Pro 适配器
- [x] 实时行情
- [x] 历史K线
- [ ] 基本面数据
- [ ] 财务指标

### 7.2 AKShare 适配器
- [ ] 实时行情
- [ ] 历史K线
- [ ] 基本面数据
- [ ] 特色数据（龙虎榜、北向资金等）

### 7.3 新浪财经 适配器
- [ ] 实时行情
- [ ] 买卖五档
- [ ] 历史K线

### 7.4 东方财富 适配器
- [ ] 实时行情
- [ ] 历史K线
- [ ] 基本面数据

---

## 8. 扩展性设计

### 8.1 新增数据源步骤
1. 在 `adapters/` 目录创建新的适配器文件（如 `mydata_adapter.py`）
2. 继承 `DataSourceAdapter` 并实现所有抽象方法
3. 在适配器类中定义 `@property name` 返回唯一标识
4. （可选）在 `sources.json` 中配置优先级
5. 重启系统，适配器自动被发现并注册

### 8.2 新增数据类型
1. 在 `models.py` 中定义新的 Pydantic 模型
2. 在 `DataSourceAdapter` 中添加新的抽象方法
3. 所有现有适配器需要实现新方法
4. 在 `DataSourceAggregator` 中添加统一接口

---

## 9. 性能优化建议

### 9.1 缓存策略
- 实时行情：内存缓存 1-3 秒
- 历史K线：Redis 缓存 1 小时
- 基本面数据：本地 SQLite 缓存 1 天

### 9.2 并发优化
- 批量查询使用 asyncio 并发请求
- 不同数据源的请求可以并行执行
- 使用连接池管理 HTTP 请求

### 9.3 降级优化
- 失败数据源自动降低优先级
- 连续失败的数据源临时禁用
- 成功数据源自动提升优先级

---

## 10. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 数据源 API 变更 | 高 | 适配器隔离，单一数据源变更不影响整体 |
| 数据源限流/封禁 | 高 | 自动降级、重试机制、多源备份 |
| 数据不一致 | 中 | 数据校验、日志记录、人工审核 |
| 性能瓶颈 | 中 | 缓存、并发、连接池优化 |
| 新增数据源复杂 | 低 | 清晰的接口定义、示例代码 |

---

## 11. 下一步计划

1. **Phase 1 - 基础框架 (1-2天)**
   - [ ] 实现抽象基类和数据模型
   - [ ] 实现降级执行器
   - [ ] 实现适配器注册表
   - [ ] 实现数据源聚合器

2. **Phase 2 - 核心适配器 (3-5天)**
   - [ ] 实现 Tushare 适配器
   - [ ] 实现 AKShare 适配器
   - [ ] 实现 新浪财经 适配器

3. **Phase 3 - 测试与优化 (2-3天)**
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] 性能测试
   - [ ] 文档完善

4. **Phase 4 - 扩展与集成 (持续)**
   - [ ] 实现 东方财富 适配器
   - [ ] 集成到量化交易系统
   - [ ] 监控和告警
   - [ ] 性能优化

---

**设计审批：**
- [ ] 架构设计 ✓
- [ ] 接口设计 ✓
- [ ] 配置设计 ✓
- [ ] 扩展性设计 ✓

**审批人：** _________________
**日期：** _________________