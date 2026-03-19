# Investoday 数据源适配器实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 alpha-quant-trader-pro 项目中集成 Investoday 数据源，实现 20 个核心+特色接口，支持多源降级机制。

**Architecture:** 遵循现有的适配器模式，创建 `InvestodayAdapter` 继承 `DataSourceAdapter`，实现 6 个核心接口保持架构一致，新增 14 个特色接口发挥 Investoday 数据优势。使用环境变量认证，配置驱动优先级。

**Tech Stack:** Python 3.9+, Pydantic, Requests, pytest, Investoday API

---

## 文件结构概览

### 新建文件
- `data_sources/adapters/investoday_adapter.py` - Investoday 适配器实现
- `tests/adapters/test_investoday_adapter.py` - Investoday 适配器测试

### 修改文件
- `config/sources.json` - 添加 Investoday 配置
- `.env.example` - 添加 INVESTODAY_API_KEY 示例
- `requirements.txt` - 确保 requests 已包含

### 可选更新
- `README.md` - 添加 Investoday 使用说明

---

## Chunk 1: 环境准备与配置

### Task 1.1: 环境变量配置

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: 添加 INVESTODAY_API_KEY 配置**

```bash
# 在 .env.example 末尾添加
INVESTODAY_API_KEY=your_investoday_api_key_here
```

- [ ] **Step 2: 更新 .gitignore**

确保 `.env` 已在 `.gitignore` 中：
```
.env
```

- [ ] **Step 3: 提交配置更新**

```bash
git add .env.example .gitignore
git commit -m "feat: add Investoday API Key configuration"
```

---

### Task 1.2: 更新 JSON 配置

**Files:**
- Modify: `config/sources.json`

- [ ] **Step 1: 备份原配置文件**

```bash
cp config/sources.json config/sources.json.backup
```

- [ ] **Step 2: 更新配置文件**

将以下内容替换到 `config/sources.json`：

```json
{
  "version": "1.1",
  "default_priority": 100,

  "sources": {
    "realtime": [
      {"name": "sina", "priority": 10, "enabled": true, "timeout": 3},
      {"name": "investoday", "priority": 20, "enabled": true, "timeout": 5},
      {"name": "akshare", "priority": 30, "enabled": true, "timeout": 5},
      {"name": "tushare", "priority": 40, "enabled": true, "timeout": 5}
    ],
    "kline": [
      {"name": "investoday", "priority": 10, "enabled": true, "timeout": 10},
      {"name": "tushare", "priority": 20, "enabled": true, "timeout": 10},
      {"name": "akshare", "priority": 30, "enabled": true, "timeout": 10}
    ],
    "fundamentals": [
      {"name": "investoday", "priority": 10, "enabled": true, "timeout": 15},
      {"name": "tushare", "priority": 20, "enabled": true, "timeout": 15},
      {"name": "akshare", "priority": 30, "enabled": true, "timeout": 15}
    ],
    "tech_analysis": [
      {"name": "investoday", "priority": 10, "enabled": true, "timeout": 10}
    ],
    "fund_flows": [
      {"name": "investoday", "priority": 10, "enabled": true, "timeout": 10}
    ],
    "valuation": [
      {"name": "investoday", "priority": 10, "enabled": true, "timeout": 10}
    ]
  },

  "fallback": {
    "max_retries": 2,
    "retry_delay": 0.5,
    "log_failures": true
  }
}
```

- [ ] **Step 3: 验证配置格式**

```bash
python -c "import json; json.load(open('config/sources.json'))"
```
Expected: No error

- [ ] **Step 4: 提交配置更新**

```bash
git add config/sources.json
git commit -m "feat: add Investoday to data sources configuration"
```

---

## Chunk 2: Investoday 适配器核心实现

### Task 2.1: 创建 Investoday 适配器基础类

**Files:**
- Create: `data_sources/adapters/investoday_adapter.py`

- [ ] **Step 1: 创建基础文件**

```python
# data_sources/adapters/investoday_adapter.py

"""
Investoday 数据源适配器

今日投资 (Investoday) 是专业的金融数据平台，提供 180+ 个金融数据接口。
本适配器实现了 20 个核心+特色接口，支持实时行情、历史K线、财务数据、
技术指标、资金流向、龙虎榜等丰富数据。

API 文档: https://data-api.investoday.net/hub?url=%2Fapidocs%2Fai-native-financial-data
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests

from data_sources.base import DataSourceAdapter
from data_sources.models import (
    Quote,
    KLine,
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
)
from data_sources.exceptions import DataSourceError

logger = logging.getLogger(__name__)


class InvestodayAdapter(DataSourceAdapter):
    """
    今日投资 (Investoday) 数据源适配器

    特性:
    - 环境变量认证 (INVESTODAY_API_KEY)
    - 20个核心+特色接口实现
    - 遵循 DataSourceAdapter 统一接口规范
    - 支持配置优先级和超时控制
    """

    BASE_URL = "https://data-api.investoday.net/data"

    def __init__(self, api_key: str = None, timeout: int = 10, **kwargs):
        """
        初始化 Investoday 适配器

        Args:
            api_key: API Key (优先级: 参数 > 环境变量 > 抛出异常)
            timeout: HTTP 请求超时时间 (秒)
            **kwargs: 预留扩展参数
        """
        self.api_key = api_key or os.getenv("INVESTODAY_API_KEY")
        if not self.api_key:
            raise DataSourceError(
                "investoday",
                "API Key is required. Set INVESTODAY_API_KEY environment variable."
            )

        self.timeout = timeout
        self._priority = kwargs.get("priority", 50)
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "apiKey": self.api_key
        })

    @property
    def name(self) -> str:
        """数据源唯一标识"""
        return "investoday"

    @property
    def priority(self) -> int:
        """数据源优先级"""
        return self._priority

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        通用 API 调用方法

        Args:
            endpoint: 接口路径 (如 "stock-quote/realtime")
            method: HTTP 方法 ("GET" 或 "POST")
            params: GET 参数 (query string)
            json_data: POST 数据 (JSON body)

        Returns:
            API 返回的 data 字段

        Raises:
            DataSourceError: API 调用失败或返回错误
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            if method.upper() == "POST":
                response = self._session.post(
                    url,
                    json=json_data,
                    timeout=self.timeout
                )
            else:
                response = self._session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

            response.raise_for_status()

            result = response.json()
            code = result.get("code")

            if code != 0:
                message = result.get("message", "Unknown error")
                raise DataSourceError(
                    "investoday",
                    f"API returned error [{code}]: {message}"
                )

            return result.get("data", {})

        except requests.Timeout:
            raise DataSourceError(
                "investoday",
                f"Request timeout after {self.timeout}s"
            )
        except requests.RequestException as e:
            raise DataSourceError(
                "investoday",
                f"Request failed: {e}"
            )
        except ValueError as e:
            raise DataSourceError(
                "investoday",
                f"Invalid JSON response: {e}"
            )

    def _get_report_date(self, year: int, quarter: int) -> str:
        """
        根据年份和季度推导报告期日期

        Args:
            year: 年份 (如 2023)
            quarter: 季度 (1-4)

        Returns:
            报告期日期 (格式: "YYYY-MM-DD")
        """
        quarter_end_dates = {
            1: f"{year}-03-31",
            2: f"{year}-06-30",
            3: f"{year}-09-30",
            4: f"{year}-12-31"
        }
        return quarter_end_dates.get(quarter, f"{year}-12-31")
```

- [ ] **Step 2: 验证语法正确性**

```bash
python -m py_compile data_sources/adapters/investoday_adapter.py
```
Expected: No error

- [ ] **Step 3: 提交基础类**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: add InvestodayAdapter base class with API client"
```

---

### Task 2.2: 实现核心接口 - 实时行情

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:145-200`

- [ ] **Step 1: 添加辅助方法 `_parse_quote`**

在 `InvestodayAdapter` 类中添加：

```python
    def _parse_quote(self, data: Dict[str, Any]) -> Optional[Quote]:
        """
        解析实时行情数据

        Args:
            data: API 返回的数据

        Returns:
            Quote 对象或 None
        """
        try:
            return Quote(
                symbol=data.get("stockCode"),
                price=float(data.get("latestPrice", 0)),
                change=float(data.get("change", 0)),
                percent=float(data.get("changePercent", 0)),
                volume=int(data.get("volume", 0)),
                amount=float(data.get("amount", 0)),
                bid_price=[float(data.get("bidPrice1", 0))],
                bid_volume=[int(data.get("bidVolume1", 0))],
                ask_price=[float(data.get("askPrice1", 0))],
                ask_volume=[int(data.get("askVolume1", 0))],
                timestamp=datetime.now()
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse quote: {e}, data={data}")
            return None
```

- [ ] **Step 2: 实现 `get_realtime` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """
        获取单个股票实时行情

        Args:
            symbol: 股票代码 (如 "600519")

        Returns:
            Quote 对象或 None
        """
        try:
            data = self._call_api(
                endpoint="stock-quote/realtime",
                method="GET",
                params={"stockCode": symbol}
            )

            return self._parse_quote(data)

        except DataSourceError as e:
            logger.error(f"Investoday get_realtime failed for {symbol}: {e}")
            return None
```

- [ ] **Step 3: 实现 `batch_get_realtime` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表
        """
        results = []
        for symbol in symbols:
            quote = self.get_realtime(symbol)
            if quote:
                results.append(quote)
        return results
```

- [ ] **Step 4: 验证实现**

```bash
python -c "
from data_sources.adapters.investoday_adapter import InvestodayAdapter
import os
os.environ['INVESTODAY_API_KEY'] = 'test_key'
adapter = InvestodayAdapter(timeout=2)
print('InvestodayAdapter initialized successfully')
print('Methods:', [m for m in dir(adapter) if not m.startswith('_')])
"
```
Expected: Prints adapter methods

- [ ] **Step 5: 提交实现实时行情**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday realtime quote methods"
```

---

### Task 2.3: 实现核心接口 - 历史K线

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:200-250`

- [ ] **Step 1: 添加辅助方法 `_parse_kline`**

在 `InvestodayAdapter` 类中添加：

```python
    def _parse_kline(self, data: Dict[str, Any]) -> Optional[KLine]:
        """
        解析K线数据

        Args:
            data: API 返回的数据

        Returns:
            KLine 对象或 None
        """
        try:
            return KLine(
                symbol=data.get("stockCode"),
                datetime=datetime.strptime(data.get("tradeDate"), "%Y-%m-%d"),
                open=float(data.get("openPrice", 0)),
                high=float(data.get("highestPrice", 0)),
                low=float(data.get("lowestPrice", 0)),
                close=float(data.get("closePrice", 0)),
                volume=int(data.get("volume", 0)),
                amount=float(data.get("amount", 0)),
                turnover=None  # Investoday 未提供换手率
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse kline: {e}, data={data}")
            return None
```

- [ ] **Step 2: 实现 `get_kline` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_kline(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> List[KLine]:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            interval: K线周期 (如 "1d", "1w")
            start_date: 开始日期 (格式: "YYYY-MM-DD")
            end_date: 结束日期 (格式: "YYYY-MM-DD")

        Returns:
            KLine 对象列表
        """
        all_klines = []
        page_num = 1
        page_size = 500

        # Investoday 的复权K线接口
        endpoint = "stock/adjusted-quotes"

        while True:
            try:
                data = self._call_api(
                    endpoint=endpoint,
                    method="GET",
                    params={
                        "stockCode": symbol,
                        "beginDate": start_date,
                        "endDate": end_date,
                        "pageNum": page_num,
                        "pageSize": page_size
                    }
                )

                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    kline = self._parse_kline(item)
                    if kline:
                        all_klines.append(kline)

                # 如果返回数据少于 pageSize，说明已获取完
                if len(items) < page_size:
                    break

                page_num += 1

            except DataSourceError as e:
                logger.error(f"Investoday get_kline failed (page {page_num}): {e}")
                break

        return all_klines
```

- [ ] **Step 3: 验证实现**

```bash
python -c "
from data_sources.adapters.investoday_adapter import InvestodayAdapter
import os
os.environ['INVESTODAY_API_KEY'] = 'test_key'
adapter = InvestodayAdapter(timeout=2)
print('get_kline method exists:', hasattr(adapter, 'get_kline'))
"
```

- [ ] **Step 4: 提交实现历史K线**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday KLine methods"
```

---

### Task 2.4: 实现核心接口 - 财务报表

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:250-350`

- [ ] **Step 1: 添加辅助方法 `_parse_balance_sheet`**

在 `InvestodayAdapter` 类中添加：

```python
    def _parse_balance_sheet(self, data: Dict[str, Any]) -> Optional[BalanceSheet]:
        """
        解析资产负债表

        Args:
            data: API 返回的数据

        Returns:
            BalanceSheet 对象或 None
        """
        try:
            report_date = data.get("reportDate", "")
            year = int(report_date.split("-")[0]) if report_date else 0
            quarter = self._date_to_quarter(report_date)

            return BalanceSheet(
                symbol=data.get("stockCode"),
                year=year,
                quarter=quarter,
                report_date=report_date,
                total_assets=float(data.get("totalAssets", 0)),
                total_liabilities=float(data.get("totalLiabilities", 0)),
                shareholders_equity=float(data.get("shareholdersEquity", 0))
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse balance sheet: {e}, data={data}")
            return None

    def _date_to_quarter(self, date_str: str) -> int:
        """
        将日期转换为季度

        Args:
            date_str: 日期字符串 (格式: "YYYY-MM-DD")

        Returns:
            季度 (1-4)
        """
        if not date_str:
            return 4
        month = int(date_str.split("-")[1])
        return (month - 1) // 3 + 1
```

- [ ] **Step 2: 添加辅助方法 `_parse_income_statement`**

在 `InvestodayAdapter` 类中添加：

```python
    def _parse_income_statement(self, data: Dict[str, Any]) -> Optional[IncomeStatement]:
        """
        解析利润表

        Args:
            data: API 返回的数据

        Returns:
            IncomeStatement 对象或 None
        """
        try:
            report_date = data.get("reportDate", "")
            year = int(report_date.split("-")[0]) if report_date else 0
            quarter = self._date_to_quarter(report_date)

            return IncomeStatement(
                symbol=data.get("stockCode"),
                year=year,
                quarter=quarter,
                report_date=report_date,
                revenue=float(data.get("revenue", 0)),
                net_profit=float(data.get("netProfit", 0)),
                eps=float(data.get("eps", 0))
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse income statement: {e}, data={data}")
            return None
```

- [ ] **Step 3: 添加辅助方法 `_parse_cash_flow_statement`**

在 `InvestodayAdapter` 类中添加：

```python
    def _parse_cash_flow_statement(self, data: Dict[str, Any]) -> Optional[CashFlowStatement]:
        """
        解析现金流量表

        Args:
            data: API 返回的数据

        Returns:
            CashFlowStatement 对象或 None
        """
        try:
            report_date = data.get("reportDate", "")
            year = int(report_date.split("-")[0]) if report_date else 0
            quarter = self._date_to_quarter(report_date)

            return CashFlowStatement(
                symbol=data.get("stockCode"),
                year=year,
                quarter=quarter,
                report_date=report_date,
                operating_cash_flow=float(data.get("operatingCashFlow", 0)),
                investing_cash_flow=float(data.get("investingCashFlow", 0)),
                financing_cash_flow=float(data.get("financingCashFlow", 0))
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse cash flow statement: {e}, data={data}")
            return None
```

- [ ] **Step 4: 实现财务报表获取方法**

在 `InvestodayAdapter` 类中添加：

```python
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
            BalanceSheet 对象或 None
        """
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/balance-sheets",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_balance_sheet(items[0])

            return None

        except DataSourceError as e:
            logger.error(f"Investoday get_balance_sheet failed: {e}")
            return None

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
            IncomeStatement 对象或 None
        """
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/income-statements",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_income_statement(items[0])

            return None

        except DataSourceError as e:
            logger.error(f"Investoday get_income_statement failed: {e}")
            return None

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
            CashFlowStatement 对象或 None
        """
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/cash-flows",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_cash_flow_statement(items[0])

            return None

        except DataSourceError as e:
            logger.error(f"Investoday get_cash_flow_statement failed: {e}")
            return None
```

- [ ] **Step 5: 验证实现**

```bash
python -c "
from data_sources.adapters.investoday_adapter import InvestodayAdapter
import os
os.environ['INVESTODAY_API_KEY'] = 'test_key'
adapter = InvestodayAdapter(timeout=2)
print('Financial methods exist:',
      hasattr(adapter, 'get_balance_sheet'),
      hasattr(adapter, 'get_income_statement'),
      hasattr(adapter, 'get_cash_flow_statement'))
"
```

- [ ] **Step 6: 提交实现财务报表**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday financial statement methods"
```

---

## Chunk 3: Investoday 特色接口实现

### Task 3.1: 实现技术分析接口

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:350-400`

- [ ] **Step 1: 实现 `get_tech_indicators` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_tech_indicators(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取技术指标

        包括: 5日/10日/20日/60日/120日/250日均线、MACD、DMI、DMA、MTM、TRIX

        Args:
            symbol: 股票代码
            start_date: 开始日期 (格式: "YYYY-MM-DD")
            end_date: 结束日期 (格式: "YYYY-MM-DD")

        Returns:
            技术指标数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/str-trend-ind",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_tech_indicators failed: {e}")
            return []
```

- [ ] **Step 2: 实现 `get_fund_flows` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_fund_flows(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取资金流向

        包括: 小单/中单/大单/超大单的资金流入、流出、净流入、占比

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            资金流向数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/daily-fund-flows",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_fund_flows failed: {e}")
            return []
```

- [ ] **Step 3: 提交技术分析接口**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday technical analysis methods"
```

---

### Task 3.2: 实现估值与财务指标接口

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:400-480`

- [ ] **Step 1: 实现 `get_valuation` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_valuation(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取估值指标

        包括: 总市值、流通市值、市盈率、市净率、市销率

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            估值指标数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/val-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_valuation failed: {e}")
            return []
```

- [ ] **Step 2: 实现 `get_financial_indicators` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, Any]:
        """
        获取财务指标

        包括: 销售毛利率、销售净利率、摊薄ROE、扣非摊薄ROE、平均ROA、平均ROIC

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            财务指标字典
        """
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/financial-indicators-profitab",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return items[0]

            return {}

        except DataSourceError as e:
            logger.error(f"Investoday get_financial_indicators failed: {e}")
            return {}
```

- [ ] **Step 3: 实现 `get_dragon_tiger` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据

        包括: 上榜日期、股票代码、异动类型、偏离值、成交量、成交金额

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            龙虎榜数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/dt-details",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_dragon_tiger failed: {e}")
            return []
```

- [ ] **Step 4: 实现 `entity_recognition` 方法**

在 `InvestodayAdapter` 类中添加：

```python
    def entity_recognition(self, text: str) -> Dict[str, Any]:
        """
        实体识别

        分析自然语言文本并提取出股票、行业、基金等实体信息

        Args:
            text: 待识别的自然语言文本

        Returns:
            识别结果字典

        示例:
            >>> adapter.entity_recognition("贵州茅台怎么样？")
            {"entities": [{"type": "STOCK", "code": "600519", "name": "贵州茅台"}]}
        """
        try:
            data = self._call_api(
                endpoint="entity-recognition",
                method="POST",
                json_data={"input": text}
            )
            return data

        except DataSourceError as e:
            logger.error(f"Investoday entity_recognition failed: {e}")
            return {"entities": []}
```

- [ ] **Step 5: 提交估值与财务指标接口**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday valuation and financial indicators"
```

---

### Task 3.3: 实现场景化接口

**Files:**
- Modify: `data_sources/adapters/investoday_adapter.py:480-600`

- [ ] **Step 1: 实现深度财务分析接口**

在 `InvestodayAdapter` 类中添加：

```python
    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取杜邦分析数据

        包括: 净资产收益率、归母净利率、资产周转率、权益乘数、营业收入、平均总资产

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            杜邦分析数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/dupont-analysis",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_dupont_analysis failed: {e}")
            return []

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取每股指标

        包括: 每股收益、每股营业收入、每股经营现金流、每股股东自由现金流

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            每股指标数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/per-share-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_per_share_indicators failed: {e}")
            return []
```

- [ ] **Step 2: 实现技术指标扩展接口**

在 `InvestodayAdapter` 类中添加：

```python
    def get_osc_indicators(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取超买超卖指标

        包括: RSI(5/14)、KDJ(K/D/J)、RC、ATR、佳庆离散指标、动态买卖气指标

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            超买超卖指标数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/osc-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_osc_indicators failed: {e}")
            return []

    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取量价指标

        包括: 布林带、多空布林线、ENV、MIKE、MFI、OBV、PVT、WVAD、AR、BR、PSY

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            量价指标数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/price-vol-ind",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_price_vol_ind failed: {e}")
            return []
```

- [ ] **Step 3: 实现行情衍生接口**

在 `InvestodayAdapter` 类中添加：

```python
    def get_limit_up_down(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取涨跌停数据

        包括: 涨停次数、跌停次数、昨收盘价、实际昨收盘价

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            涨跌停数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/limit-up-down",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_limit_up_down failed: {e}")
            return []

    def get_turnover_rates(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取换手率数据

        包括: 单日换手率、10日/1周/2周/4周/13周/26周/52周平均换手率

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            换手率数据列表
        """
        params = {"stockCode": symbol}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="stock/turnover-rates",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_turnover_rates failed: {e}")
            return []
```

- [ ] **Step 4: 实现基金与搜索接口**

在 `InvestodayAdapter` 类中添加：

```python
    def get_fund_quotes(
        self,
        fund_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取基金净值行情

        包括: 基金净值、累计净值、日增长率、成交金额

        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            基金净值数据列表
        """
        params = {"fundCode": fund_code}
        if start_date:
            params["beginDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        try:
            data = self._call_api(
                endpoint="fund/daily-quotes",
                method="POST",
                json_data=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday get_fund_quotes failed: {e}")
            return []

    def search(
        self,
        keyword: str,
        search_type: str = "11"
    ) -> List[Dict[str, Any]]:
        """
        综合搜索

        支持搜索: 股票、基金、ETF、港股、行业、概念

        Args:
            keyword: 搜索关键字
            search_type: 搜索类型 (多个用,隔开)
                - "11": 沪深京A股
                - "12": 基金
                - "13": ETF
                - "14": 港股

        Returns:
            搜索结果列表
        """
        params = {"type": search_type}
        if keyword:
            params["key"] = keyword

        try:
            data = self._call_api(
                endpoint="search",
                method="GET",
                params=params
            )
            return data.get("items", [])

        except DataSourceError as e:
            logger.error(f"Investoday search failed: {e}")
            return []
```

- [ ] **Step 5: 提交场景化接口**

```bash
git add data_sources/adapters/investoday_adapter.py
git commit -m "feat: implement Investoday scenario-based methods (dupont, indicators, fund, search)"
```

---

## Chunk 4: 单元测试

### Task 4.1: 创建 Investoday 适配器测试框架

**Files:**
- Create: `tests/adapters/test_investoday_adapter.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/adapters/test_investoday_adapter.py

"""
InvestodayAdapter 单元测试
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from data_sources.adapters.investoday_adapter import InvestodayAdapter
from data_sources.models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from data_sources.exceptions import DataSourceError


class TestInvestodayAdapterInitialization:
    """InvestodayAdapter 初始化测试"""

    def test_init_with_api_key_parameter(self):
        """测试通过参数传入 API Key"""
        adapter = InvestodayAdapter(api_key="test_key", timeout=5)
        assert adapter.name == "investoday"
        assert adapter.priority == 50

    def test_init_with_env_variable(self):
        """测试通过环境变量获取 API Key"""
        os.environ["INVESTODAY_API_KEY"] = "env_key"
        adapter = InvestodayAdapter(timeout=5)
        assert adapter.name == "investoday"

    def test_init_without_api_key_raises_error(self):
        """测试缺少 API Key 抛出异常"""
        if "INVESTODAY_API_KEY" in os.environ:
            del os.environ["INVESTODAY_API_KEY"]

        with pytest.raises(DataSourceError) as exc_info:
            InvestodayAdapter(timeout=5)

        assert "API Key is required" in str(exc_info.value)


class TestInvestodayAdapterCoreMethods:
    """InvestodayAdapter 核心方法测试"""

    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return InvestodayAdapter(api_key="test_key", timeout=2)
```

- [ ] **Step 2: 提交测试框架**

```bash
git add tests/adapters/test_investoday_adapter.py
git commit -m "test: add InvestodayAdapter test framework"
```

---

### Task 4.2: 测试核心接口

**Files:**
- Modify: `tests/adapters/test_investoday_adapter.py:45-200`

- [ ] **Step 1: 添加核心接口测试**

在 `TestInvestodayAdapterCoreMethods` 类中添加：

```python
    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_realtime_success(self, mock_call_api, adapter):
        """测试获取实时行情成功"""
        mock_call_api.return_value = {
            "stockCode": "600519",
            "latestPrice": 1688.50,
            "change": 35.20,
            "changePercent": 0.0213,
            "volume": 1234567,
            "amount": 2087654321.0,
            "bidPrice1": 1688.0,
            "bidVolume1": 100,
            "askPrice1": 1689.0,
            "askVolume1": 80
        }

        result = adapter.get_realtime("600519")

        assert result is not None
        assert isinstance(result, Quote)
        assert result.symbol == "600519"
        assert result.price == 1688.50
        assert result.percent == 0.0213

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_realtime_failure_returns_none(self, mock_call_api, adapter):
        """测试获取实时行情失败返回 None"""
        mock_call_api.side_effect = DataSourceError("investoday", "API Error")

        result = adapter.get_realtime("invalid_code")

        assert result is None

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter.get_realtime")
    def test_batch_get_realtime_success(self, mock_get_realtime, adapter):
        """测试批量获取实时行情成功"""
        mock_quote1 = Mock(spec=Quote)
        mock_quote1.symbol = "600519"
        mock_quote2 = Mock(spec=Quote)
        mock_quote2.symbol = "000001"

        mock_get_realtime.side_effect = [mock_quote1, mock_quote2]

        result = adapter.batch_get_realtime(["600519", "000001"])

        assert len(result) == 2
        assert result[0].symbol == "600519"
        assert result[1].symbol == "000001"

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_kline_success(self, mock_call_api, adapter):
        """测试获取历史K线成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "tradeDate": "2024-01-03",
                    "openPrice": 1500.0,
                    "highestPrice": 1520.0,
                    "lowestPrice": 1495.0,
                    "closePrice": 1515.0,
                    "volume": 1234567,
                    "amount": 1865432100.0
                },
                {
                    "stockCode": "600519",
                    "tradeDate": "2024-01-04",
                    "openPrice": 1515.0,
                    "highestPrice": 1530.0,
                    "lowestPrice": 1510.0,
                    "closePrice": 1525.0,
                    "volume": 1345678,
                    "amount": 1923456700.0
                }
            ]
        }

        result = adapter.get_kline("600519", "1d", "2024-01-01", "2024-01-31")

        assert len(result) == 2
        assert all(isinstance(k, KLine) for k in result)
        assert result[0].symbol == "600519"
        assert result[0].close == 1515.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_balance_sheet_success(self, mock_call_api, adapter):
        """测试获取资产负债表成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "totalAssets": 10000000000.0,
                    "totalLiabilities": 4000000000.0,
                    "shareholdersEquity": 6000000000.0
                }
            ]
        }

        result = adapter.get_balance_sheet("600519", 2023, 3)

        assert result is not None
        assert isinstance(result, BalanceSheet)
        assert result.symbol == "600519"
        assert result.total_assets == 10000000000.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_income_statement_success(self, mock_call_api, adapter):
        """测试获取利润表成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "revenue": 8000000000.0,
                    "netProfit": 2000000000.0,
                    "eps": 16.0
                }
            ]
        }

        result = adapter.get_income_statement("600519", 2023, 3)

        assert result is not None
        assert isinstance(result, IncomeStatement)
        assert result.symbol == "600519"
        assert result.revenue == 8000000000.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_cash_flow_statement_success(self, mock_call_api, adapter):
        """测试获取现金流量表成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "operatingCashFlow": 2500000000.0,
                    "investingCashFlow": -800000000.0,
                    "financingCashFlow": -300000000.0
                }
            ]
        }

        result = adapter.get_cash_flow_statement("600519", 2023, 3)

        assert result is not None
        assert isinstance(result, CashFlowStatement)
        assert result.symbol == "600519"
        assert result.operating_cash_flow == 2500000000.0
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/adapters/test_investoday_adapter.py::TestInvestodayAdapterCoreMethods -v
```
Expected: All tests pass

- [ ] **Step 3: 提交核心接口测试**

```bash
git add tests/adapters/test_investoday_adapter.py
git commit -m "test: add InvestodayAdapter core methods tests"
```

---

### Task 4.3: 测试特色接口

**Files:**
- Modify: `tests/adapters/test_investoday_adapter.py:200-350`

- [ ] **Step 1: 添加特色接口测试类**

在文件末尾添加：

```python
class TestInvestodayAdapterFeatureMethods:
    """InvestodayAdapter 特色方法测试"""

    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return InvestodayAdapter(api_key="test_key", timeout=2)

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_tech_indicators_success(self, mock_call_api, adapter):
        """测试获取技术指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2024-01-03",
                    "ma5": 1500.0,
                    "ma10": 1490.0,
                    "macd": 5.0,
                    "diff": 10.0,
                    "dea": 8.0
                }
            ]
        }

        result = adapter.get_tech_indicators("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["stockCode"] == "600519"
        assert result[0]["macd"] == 5.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_fund_flows_success(self, mock_call_api, adapter):
        """测试获取资金流向成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "tradeDate": "2024-01-03",
                    "mainNetInflow": 100000000.0,
                    "retailNetInflow": 50000000.0
                }
            ]
        }

        result = adapter.get_fund_flows("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["mainNetInflow"] == 100000000.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_valuation_success(self, mock_call_api, adapter):
        """测试获取估值指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "tradeDate": "2024-01-03",
                    "pe": 30.5,
                    "pb": 5.2,
                    "ps": 8.0
                }
            ]
        }

        result = adapter.get_valuation("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["pe"] == 30.5

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_financial_indicators_success(self, mock_call_api, adapter):
        """测试获取财务指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "roe": 0.25,
                    "grossMargin": 0.45,
                    "netMargin": 0.20
                }
            ]
        }

        result = adapter.get_financial_indicators("600519", 2023, 3)

        assert result["roe"] == 0.25
        assert result["grossMargin"] == 0.45

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_dragon_tiger_success(self, mock_call_api, adapter):
        """测试获取龙虎榜成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "002594",
                    "tradeDate": "2024-01-03",
                    "abnormalType": "连续三个交易日内涨幅偏离值累计达到20%",
                    "turnover": 1000000000.0
                }
            ]
        }

        result = adapter.get_dragon_tiger("002594", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["abnormalType"].startswith("连续")

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_entity_recognition_success(self, mock_call_api, adapter):
        """测试实体识别成功"""
        mock_call_api.return_value = {
            "entities": [
                {"type": "STOCK", "code": "600519", "name": "贵州茅台"}
            ]
        }

        result = adapter.entity_recognition("贵州茅台怎么样？")

        assert len(result["entities"]) == 1
        assert result["entities"][0]["code"] == "600519"
        assert result["entities"][0]["name"] == "贵州茅台"
```

- [ ] **Step 2: 运行特色接口测试**

```bash
pytest tests/adapters/test_investoday_adapter.py::TestInvestodayAdapterFeatureMethods -v
```

- [ ] **Step 3: 提交特色接口测试**

```bash
git add tests/adapters/test_investoday_adapter.py
git commit -m "test: add InvestodayAdapter feature methods tests"
```

---

### Task 4.4: 测试场景化接口

**Files:**
- Modify: `tests/adapters/test_investoday_adapter.py:350-450`

- [ ] **Step 1: 添加场景化接口测试**

在文件末尾添加：

```python
class TestInvestodayAdapterScenarioMethods:
    """InvestodayAdapter 场景化方法测试"""

    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return InvestodayAdapter(api_key="test_key", timeout=2)

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_dupont_analysis_success(self, mock_call_api, adapter):
        """测试获取杜邦分析成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "roe": 0.25,
                    "netProfitMargin": 0.20,
                    "assetTurnover": 0.8,
                    "equityMultiplier": 1.56
                }
            ]
        }

        result = adapter.get_dupont_analysis("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["roe"] == 0.25

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_per_share_indicators_success(self, mock_call_api, adapter):
        """测试获取每股指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2023-09-30",
                    "eps": 16.0,
                    "operatingCashFlowPerShare": 20.0
                }
            ]
        }

        result = adapter.get_per_share_indicators("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["eps"] == 16.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_osc_indicators_success(self, mock_call_api, adapter):
        """测试获取超买超卖指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2024-01-03",
                    "rsi5": 65.0,
                    "rsi14": 58.0,
                    "kdjK": 70.0,
                    "kdjD": 65.0,
                    "kdjJ": 80.0
                }
            ]
        }

        result = adapter.get_osc_indicators("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["rsi5"] == 65.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_price_vol_ind_success(self, mock_call_api, adapter):
        """测试获取量价指标成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "reportDate": "2024-01-03",
                    "bollUpper": 1550.0,
                    "bollMiddle": 1500.0,
                    "bollLower": 1450.0,
                    "obv": 10000000
                }
            ]
        }

        result = adapter.get_price_vol_ind("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["bollUpper"] == 1550.0

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_limit_up_down_success(self, mock_call_api, adapter):
        """测试获取涨跌停数据成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "002594",
                    "tradeDate": "2024-01-03",
                    "limitUpCount": 5,
                    "limitDownCount": 2
                }
            ]
        }

        result = adapter.get_limit_up_down("002594", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["limitUpCount"] == 5

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_turnover_rates_success(self, mock_call_api, adapter):
        """测试获取换手率成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "stockCode": "600519",
                    "tradeDate": "2024-01-03",
                    "turnoverRate": 2.5,
                    "turnoverRate10D": 2.8,
                    "turnoverRate1W": 2.6
                }
            ]
        }

        result = adapter.get_turnover_rates("600519", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["turnoverRate"] == 2.5

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_get_fund_quotes_success(self, mock_call_api, adapter):
        """测试获取基金净值成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "fundCode": "000001",
                    "navDate": "2024-01-03",
                    "nav": 1.5,
                    "accumulativeNav": 2.0,
                    "dailyGrowthRate": 0.015
                }
            ]
        }

        result = adapter.get_fund_quotes("000001", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["nav"] == 1.5

    @patch("data_sources.adapters.investoday_adapter.InvestodayAdapter._call_api")
    def test_search_success(self, mock_call_api, adapter):
        """测试综合搜索成功"""
        mock_call_api.return_value = {
            "items": [
                {
                    "code": "002594",
                    "shortName": "比亚迪",
                    "fullName": "比亚迪股份有限公司",
                    "type": "11"
                }
            ]
        }

        result = adapter.search("比亚迪", search_type="11")

        assert len(result) == 1
        assert result[0]["code"] == "002594"
        assert result[0]["shortName"] == "比亚迪"
```

- [ ] **Step 2: 运行场景化接口测试**

```bash
pytest tests/adapters/test_investoday_adapter.py::TestInvestodayAdapterScenarioMethods -v
```

- [ ] **Step 3: 提交场景化接口测试**

```bash
git add tests/adapters/test_investoday_adapter.py
git commit -m "test: add InvestodayAdapter scenario methods tests"
```

---

### Task 4.5: 测试异常场景

**Files:**
- Modify: `tests/adapters/test_investoday_adapter.py:450-500`

- [ ] **Step 1: 添加异常场景测试**

在 `TestInvestodayAdapterCoreMethods` 类中添加：

```python
    @patch("data_sources.adapters.investoday_adapter.requests.Session.get")
    def test_network_timeout_handled(self, mock_get, adapter):
        """测试网络超时处理"""
        mock_get.side_effect = TimeoutError("Timeout")

        result = adapter.get_realtime("600519")

        assert result is None

    @patch("data_sources.adapters.investoday_adapter.requests.Session.get")
    def test_invalid_response_returns_none(self, mock_get, adapter):
        """测试无效响应返回 None"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 1, "message": "Invalid"}
        mock_get.return_value = mock_response

        result = adapter.get_realtime("600519")

        assert result is None

    def test_empty_response_returns_none(self, adapter):
        """测试空响应返回 None"""
        with patch.object(adapter, '_call_api') as mock_call:
            mock_call.return_value = {}
            result = adapter._parse_quote({})
            assert result is None
```

- [ ] **Step 2: 运行所有测试**

```bash
pytest tests/adapters/test_investoday_adapter.py -v --tb=short
```

- [ ] **Step 3: 检查测试覆盖率**

```bash
pytest tests/adapters/test_investoday_adapter.py -v --cov=data_sources.adapters.investoday_adapter --cov-report=term-missing
```

Expected: Coverage ≥ 80%

- [ ] **Step 4: 提交异常场景测试**

```bash
git add tests/adapters/test_investoday_adapter.py
git commit -m "test: add InvestodayAdapter error handling tests"
```

---

## Chunk 5: 集成测试与文档

### Task 5.1: 运行完整测试套件

**Files:**
- Modify: None

- [ ] **Step 1: 运行 Investoday 适配器所有测试**

```bash
pytest tests/adapters/test_investoday_adapter.py -v
```
Expected: All tests pass

- [ ] **Step 2: 运行整个数据源模块测试**

```bash
pytest tests/ -v --tb=short
```
Expected: No regressions

- [ ] **Step 3: 提交测试结果**

```bash
git add .
git commit -m "test: complete InvestodayAdapter test suite (20 methods, 80%+ coverage)"
```

---

### Task 5.2: 更新 README 文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在数据源支持表中添加 Investoday**

在 README.md 的 "数据源支持" 表格中添加：

```markdown
| 数据源 | 类型 | 优势 | 适用场景 | 优先级 |
|--------|------|------|----------|--------|
| **Tushare Pro** | 付费/积分 | 数据规范、基本面强、稳定性高 | 历史K线、财务数据 | 高 |
| **AKShare** | 免费 | 覆盖广、特色数据、更新频繁 | 多维度数据、特色指标 | 中 |
| **新浪财经** | 免费 | 实时性强、响应快、无需认证 | 实时行情、五档数据 | 高 |
| **东方财富** | 免费 | 数据全面、复权准确 | 历史数据、复权处理 | 中 |
| **今日投资** | 商业 | 专业金融数据、接口丰富、特色指标 | 全场景、技术分析、龙虎榜 | 高 |
```

- [ ] **Step 2: 添加 Investoday 使用示例**

在 "快速开始" 部分后添加：

```markdown
### 6. 使用 Investoday 数据源

Investoday 提供 20+ 个专业金融数据接口，包括实时行情、历史K线、财务报表、技术指标、资金流向、龙虎榜等。

#### 6.1 配置 API Key

```bash
export INVESTODAY_API_KEY=your_investoday_api_key
```

或在 `.env` 文件中：

```bash
INVESTODAY_API_KEY=your_investoday_api_key
```

#### 6.2 获取实时行情

```python
from data_sources import DataSourceAggregator

aggregator = DataSourceAggregator()
quote = aggregator.get_realtime("600519")
print(f"贵州茅台: ¥{quote.price:.2f}")
```

#### 6.3 获取技术指标

```python
investoday_adapter = aggregator._get_adapter("investoday")
tech_data = investoday_adapter.get_tech_indicators("600519", "2024-01-01", "2024-12-31")
```

#### 6.4 实体识别（独家功能）

```python
result = investoday_adapter.entity_recognition("贵州茅台怎么样？")
# 返回: {"entities": [{"type": "STOCK", "code": "600519", "name": "贵州茅台"}]}
```

完整示例请参考 `docs/superpowers/specs/2026-03-15-investoday-adapter-design.md`
```

- [ ] **Step 3: 提交文档更新**

```bash
git add README.md
git commit -m "docs: update README with Investoday data source usage"
```

---

### Task 5.3: 创建使用示例脚本

**Files:**
- Create: `examples/investoday_example.py`

- [ ] **Step 1: 创建示例脚本**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Investoday 数据源使用示例

运行前请确保已配置 INVESTODAY_API_KEY 环境变量：
    export INVESTODAY_API_KEY=your_api_key
"""

import os
import sys

# 确保可以导入 data_sources 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_sources import DataSourceAggregator


def main():
    # 检查 API Key
    if not os.getenv("INVESTODAY_API_KEY"):
        print("错误: 请先配置 INVESTODAY_API_KEY 环境变量")
        print("示例: export INVESTODAY_API_KEY=your_api_key")
        sys.exit(1)

    # 初始化聚合器
    aggregator = DataSourceAggregator(config_path="config/sources.json")

    print("=" * 60)
    print("Investoday 数据源使用示例")
    print("=" * 60)

    # ========== 1. 核心功能 ==========
    print("\n1. 核心功能示例")
    print("-" * 60)

    # 实时行情
    print("\n1.1 获取实时行情")
    quote = aggregator.get_realtime("600519")
    if quote:
        print(f"  股票: {quote.symbol}")
        print(f"  价格: ¥{quote.price:.2f}")
        print(f"  涨幅: {quote.percent:.2%}")
        print(f"  成交量: {quote.volume:,}")

    # 批量行情
    print("\n1.2 批量获取实时行情")
    symbols = ["600519", "000001", "601318"]
    quotes = aggregator.batch_get_realtime(symbols)
    for q in quotes:
        print(f"  {q.symbol}: ¥{q.price:.2f} ({q.percent:+.2%})")

    # 历史K线
    print("\n1.3 历史K线 (最近5天)")
    klines = aggregator.get_kline("600519", "1d", "2024-12-01", "2024-12-31")
    print(f"  共获取 {len(klines)} 条K线")
    if klines:
        for k in klines[:5]:
            print(f"  {k.datetime.date()}: O={k.open:.2f}, C={k.close:.2f}")

    # 财务报表
    print("\n1.4 财务报表 (2023年Q3)")
    balance = aggregator.get_balance_sheet("600519", 2023, 3)
    income = aggregator.get_income_statement("600519", 2023, 3)
    if balance:
        print(f"  总资产: {balance.total_assets:,.2f}")
        print(f"  总负债: {balance.total_liabilities:,.2f}")
    if income:
        print(f"  营业收入: {income.revenue:,.2f}")
        print(f"  净利润: {income.net_profit:,.2f}")
        print(f"  每股收益: {income.eps:.2f}")

    # ========== 2. 特色功能 ==========
    print("\n\n2. 特色功能示例 (需要获取 InvestodayAdapter 实例)")
    print("-" * 60)

    investoday_adapter = aggregator._get_adapter("investoday")

    if investoday_adapter:
        # 技术指标
        print("\n2.1 技术指标 (最近3天)")
        tech_data = investoday_adapter.get_tech_indicators("600519", "2024-12-01", "2024-12-31")
        if tech_data:
            for item in tech_data[:3]:
                print(f"  日期: {item.get('reportDate')}")
                print(f"    MACD: {item.get('macd')}")
                print(f"    5日均线: {item.get('ma5')}")

        # 资金流向
        print("\n2.2 资金流向")
        fund_flows = investoday_adapter.get_fund_flows("600519", "2024-12-01", "2024-12-31")
        if fund_flows:
            for item in fund_flows[:3]:
                print(f"  日期: {item.get('tradeDate')}")
                print(f"    主力净流入: {item.get('mainNetInflow'):,.2f} 万元")

        # 估值指标
        print("\n2.3 估值指标")
        valuation = investoday_adapter.get_valuation("600519", "2024-12-01", "2024-12-31")
        if valuation:
            for item in valuation[:3]:
                print(f"  日期: {item.get('tradeDate')}")
                print(f"    市盈率(PE): {item.get('pe'):.2f}")
                print(f"    市净率(PB): {item.get('pb'):.2f}")

        # 龙虎榜
        print("\n2.4 龙虎榜 (比亚迪)")
        dragon_tiger = investoday_adapter.get_dragon_tiger("002594", "2024-01-01", "2024-12-31")
        if dragon_tiger:
            for item in dragon_tiger[:3]:
                print(f"  日期: {item.get('tradeDate')}")
                print(f"    异动类型: {item.get('abnormalType')}")

        # 独家功能：实体识别
        print("\n2.5 独家功能：实体识别")
        result = investoday_adapter.entity_recognition("贵州茅台怎么样？")
        entities = result.get("entities", [])
        if entities:
            for entity in entities:
                print(f"  类型: {entity.get('type')}")
                print(f"  代码: {entity.get('code')}")
                print(f"  名称: {entity.get('name')}")

        # 杜邦分析
        print("\n2.6 杜邦分析")
        dupont = investoday_adapter.get_dupont_analysis("600519", "2024-01-01", "2024-12-31")
        if dupont:
            for item in dupont[:3]:
                print(f"  日期: {item.get('reportDate')}")
                print(f"    ROE: {item.get('roe'):.2%}")
                print(f"    净利率: {item.get('netProfitMargin'):.2%}")

        # 基金净值
        print("\n2.7 基金净值")
        fund_data = investoday_adapter.get_fund_quotes("000001", "2024-12-01", "2024-12-31")
        if fund_data:
            for item in fund_data[:3]:
                print(f"  日期: {item.get('navDate')}")
                print(f"    净值: {item.get('nav'):.4f}")
                print(f"    涨幅: {item.get('dailyGrowthRate'):.2%}")

        # 综合搜索
        print("\n2.8 综合搜索")
        search_results = investoday_adapter.search("比亚迪", search_type="11")
        if search_results:
            for item in search_results[:3]:
                print(f"  代码: {item.get('code')}")
                print(f"  简称: {item.get('shortName')}")
                print(f"  全称: {item.get('fullName')}")

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试示例脚本**

```bash
export INVESTODAY_API_KEY=your_test_key
python examples/investoday_example.py
```

- [ ] **Step 3: 提交示例脚本**

```bash
git add examples/investoday_example.py
git commit -m "docs: add Investoday usage example script"
```

---

### Task 5.4: 最终验证与提交

**Files:**
- Modify: None

- [ ] **Step 1: 运行完整测试套件**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass, no regressions

- [ ] **Step 2: 检查代码质量**

```bash
# 检查语法
python -m py_compile data_sources/adapters/investoday_adapter.py

# 检查类型注解
mypy data_sources/adapters/investoday_adapter.py --ignore-missing-imports

# 检查代码风格 (可选)
flake8 data_sources/adapters/investoday_adapter.py
```

- [ ] **Step 3: 最终提交**

```bash
git add .
git commit -m "feat: complete Investoday data source adapter implementation

- Implement InvestodayAdapter with 20 methods
- Core methods: get_realtime, get_kline, financial statements
- Feature methods: tech indicators, fund flows, valuation, dragon tiger
- Scenario methods: dupont analysis, fund quotes, search, etc.
- Entity recognition (unique feature)
- Complete test suite (80%+ coverage)
- Update configuration and documentation
- Add usage example script"
```

---

## 实施计划完成

**计划完整保存至**：`docs/superpowers/plans/2026-03-15-investoday-adapter-implementation.md`

**计划包含**：
- ✅ 5个 Chunk，共 20 个任务
- ✅ 投资日适配器完整实现（20个接口）
- ✅ 单元测试（80%+覆盖率）
- ✅ 配置更新与文档
- ✅ 使用示例脚本

**下一步**：准备好执行了吗？
