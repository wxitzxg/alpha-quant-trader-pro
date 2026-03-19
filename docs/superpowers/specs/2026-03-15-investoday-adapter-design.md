# Investoday 数据源适配器设计文档

> **日期**: 2026-03-15
> **版本**: v1.0
> **作者**: Alpha Quant Team
> **审核状态**: 待审核

---

## 一、需求概述

### 1.1 项目背景

**Alpha Quant Trader Pro** 是一个企业级量化交易系统框架，其 `data_sources` 模块已实现多源数据聚合能力，支持 Tushare Pro、AKShare、新浪财经三个数据源。为了扩充底层数据源覆盖，需要新增 **今日投资 (Investoday)** 数据源适配器。

### 1.2 Investoday 简介

**今日投资数据市场** 是专业的金融数据平台，提供 **186+ 个金融数据接口**，覆盖：
- 沪深京股票数据 (92个接口)
- 基金数据 (43个接口)
- 港股数据 (15个接口)
- 板块、指数、研报等特色数据

**核心优势**：
- 专业金融数据接口，数据质量高
- 丰富的技术指标、资金流向、龙虎榜等特色数据
- 支持实体识别等 AI 友好功能
- 20年金融数据积累，腾讯投资、毕马威认证

### 1.3 设计目标

**核心目标**：
1. ✅ **扩展数据源** - 将 Investoday 作为第四个数据源接入系统
2. ✅ **保持架构一致性** - 遵循现有的适配器接口规范和降级机制
3. ✅ **发挥数据优势** - 实现 20 个核心+特色接口，覆盖主流量化场景
4. ✅ **安全认证** - 使用环境变量管理 API Key，避免硬编码
5. ✅ **完整测试** - 单元测试覆盖率 80%+

---

## 二、架构设计

### 2.1 系统架构定位

```
┌─────────────────────────────────────────────────────────────┐
│          data_sources 模块 - 多源数据聚合系统                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         DataSourceAggregator (统一入口)              │    │
│  │  - 配置管理                                          │    │
│  │  - 优先级调度                                        │    │
│  └──────────────┬──────────────────────────────────────┘    │
│                 │                                           │
│  ┌──────────────▼──────────────────────────────────────┐    │
│  │         FallbackExecutor (自动降级)                   │    │
│  │  - 失败重试 + 备用源切换                             │    │
│  └──────────────┬──────────────────────────────────────┘    │
│                 │                                           │
│  ┌──────────────▼──────────────────────────────────────┐    │
│  │         AdapterRegistry (适配器注册表)                │    │
│  │  - 自动发现 adapters/ 目录                           │    │
│  └──────────────┬──────────────────────────────────────┘    │
│                 │                                           │
│  ┌──────────────┴──────────────────────────────────────┐    │
│  │  适配器实现层 (遵循统一接口)                          │    │
│  │  ┌──────────┬──────────┬──────────┬────────────┐    │    │
│  │  │ Tushare  │ AKShare  │  Sina    │ Investoday │    │    │
│  │  │ Adapter  │ Adapter  │ Adapter  │  Adapter   │    │    │
│  │  │          │          │          │  (新增)    │    │    │
│  │  └──────────┴──────────┴──────────┴────────────┘    │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

| 模块 | 依赖 | 说明 |
|------|------|------|
| `investoday_adapter.py` | `base.py` (DataSourceAdapter) | 继承抽象接口 |
| | `exceptions.py` (DataSourceError) | 异常处理 |
| | `models.py` (Quote, KLine, ...) | 数据模型 |
| | `requests` | HTTP 请求 |
| | `os` | 环境变量读取 |

### 2.3 类图设计

```python
class InvestodayAdapter(DataSourceAdapter):
    """
    今日投资数据源适配器

    特性:
    - 环境变量认证 (INVESTODAY_API_KEY)
    - 20个核心+特色接口实现
    - 遵循 DataSourceAdapter 统一接口规范
    - 支持配置优先级和超时控制
    """

    # ========== 属性 ==========
    base_url: str = "https://data-api.investoday.net/data"
    api_key: str  # API Key
    timeout: int  # 超时时间 (秒)
    _priority: int  # 优先级
    _session: requests.Session  # HTTP 会话

    # ========== 抽象方法实现 (6个核心接口) ==========
    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取单个股票实时行情"""
        pass

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        pass

    def get_kline(self, symbol: str, interval: str,
                  start_date: str, end_date: str) -> List[KLine]:
        """获取历史K线数据"""
        pass

    def get_balance_sheet(self, symbol: str, year: int,
                          quarter: int) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        pass

    def get_income_statement(self, symbol: str, year: int,
                             quarter: int) -> Optional[IncomeStatement]:
        """获取利润表"""
        pass

    def get_cash_flow_statement(self, symbol: str, year: int,
                                quarter: int) -> Optional[CashFlowStatement]:
        """获取现金流量表"""
        pass

    @property
    def name(self) -> str:
        """数据源唯一标识"""
        return "investoday"

    @property
    def priority(self) -> int:
        """数据源优先级"""
        return self._priority

    # ========== Investoday 特色接口 (14个) ==========
    def get_tech_indicators(self, symbol: str,
                           start_date: str = None,
                           end_date: str = None) -> List[dict]:
        """获取技术指标 (MACD、DMI、均线等)"""
        pass

    def get_fund_flows(self, symbol: str,
                      start_date: str = None,
                      end_date: str = None) -> List[dict]:
        """获取资金流向 (大单/中单/小单)"""
        pass

    def get_valuation(self, symbol: str,
                     start_date: str = None,
                     end_date: str = None) -> List[dict]:
        """获取估值指标 (市盈率、市净率、市销率)"""
        pass

    def get_financial_indicators(self, symbol: str,
                                 year: int,
                                 quarter: int) -> dict:
        """获取财务指标 (ROE、毛利率、净利率)"""
        pass

    def get_dragon_tiger(self, symbol: str,
                        start_date: str = None,
                        end_date: str = None) -> List[dict]:
        """获取龙虎榜数据"""
        pass

    def entity_recognition(self, text: str) -> dict:
        """实体识别 (自然语言 → 股票代码) - 独家功能"""
        pass

    def get_dupont_analysis(self, symbol: str,
                           start_date: str = None,
                           end_date: str = None) -> List[dict]:
        """获取杜邦分析数据"""
        pass

    def get_per_share_indicators(self, symbol: str,
                                 start_date: str = None,
                                 end_date: str = None) -> List[dict]:
        """获取每股指标"""
        pass

    def get_osc_indicators(self, symbol: str,
                          start_date: str = None,
                          end_date: str = None) -> List[dict]:
        """获取超买超卖指标 (RSI、KDJ)"""
        pass

    def get_price_vol_ind(self, symbol: str,
                         start_date: str = None,
                         end_date: str = None) -> List[dict]:
        """获取量价指标 (布林带、OBV)"""
        pass

    def get_limit_up_down(self, symbol: str,
                         start_date: str = None,
                         end_date: str = None) -> List[dict]:
        """获取涨跌停数据"""
        pass

    def get_turnover_rates(self, symbol: str,
                          start_date: str = None,
                          end_date: str = None) -> List[dict]:
        """获取换手率数据"""
        pass

    def get_fund_quotes(self, fund_code: str,
                       start_date: str = None,
                       end_date: str = None) -> List[dict]:
        """获取基金净值行情"""
        pass

    def search(self, keyword: str,
              search_type: str = "11") -> List[dict]:
        """综合搜索 (股票/基金/行业)"""
        pass

    # ========== 内部方法 ==========
    def _call_api(self, endpoint: str,
                 method: str = "GET",
                 params: dict = None,
                 json_data: dict = None) -> dict:
        """
        通用 API 调用方法

        Args:
            endpoint: 接口路径 (如 "stock-quote/realtime")
            method: HTTP 方法 ("GET" 或 "POST")
            params: GET 参数 (query string)
            json_data: POST 数据 (JSON body)

        Returns:
            API 返回的 data 字段
        """
        pass

    def _parse_quote(self, data: dict) -> Quote:
        """解析实时行情数据"""
        pass

    def _parse_kline(self, data: dict) -> KLine:
        """解析K线数据"""
        pass

    def _parse_balance_sheet(self, data: dict) -> BalanceSheet:
        """解析资产负债表"""
        pass

    def _parse_income_statement(self, data: dict) -> IncomeStatement:
        """解析利润表"""
        pass

    def _parse_cash_flow_statement(self, data: dict) -> CashFlowStatement:
        """解析现金流量表"""
        pass
```

---

## 三、接口详细设计

### 3.1 核心接口实现 (6个)

#### 3.1.1 get_realtime(symbol)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock-quote/realtime` |
| 必填参数 | `stockCode` (股票代码) |
| 可选参数 | 无 |
| 返回类型 | `Optional[Quote]` |
| 异常处理 | 股票代码无效时返回 `None` |

**实现逻辑**：
```python
def get_realtime(self, symbol: str) -> Optional[Quote]:
    try:
        data = self._call_api(
            endpoint="stock-quote/realtime",
            method="GET",
            params={"stockCode": symbol}
        )
        return self._parse_quote(data)
    except Exception as e:
        logger.error(f"Investoday get_realtime failed for {symbol}: {e}")
        return None
```

---

#### 3.1.2 batch_get_realtime(symbols)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock-quote/realtime` (循环调用) |
| 必填参数 | `stockCodes` (股票代码列表) |
| 可选参数 | 无 |
| 返回类型 | `List[Quote]` |
| 异常处理 | 单个股票失败不影响其他股票 |

**实现逻辑**：
```python
def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
    results = []
    for symbol in symbols:
        quote = self.get_realtime(symbol)
        if quote:
            results.append(quote)
    return results
```

---

#### 3.1.3 get_kline(symbol, interval, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/adjusted-quotes` |
| 必填参数 | `stockCode` (股票代码) |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[KLine]` |
| 异常处理 | 自动分页获取全部数据 |

**实现逻辑**：
```python
def get_kline(self, symbol: str, interval: str,
              start_date: str, end_date: str) -> List[KLine]:
    all_klines = []
    page_num = 1
    page_size = 500

    while True:
        data = self._call_api(
            endpoint="stock/adjusted-quotes",
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
            all_klines.append(kline)

        if len(items) < page_size:
            break
        page_num += 1

    return all_klines
```

---

#### 3.1.4 get_balance_sheet(symbol, year, quarter)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/balance-sheets` |
| 必填参数 | `stockCode` (股票代码) |
| 可选参数 | `beginDate`, `endDate` (推导出年/季度) |
| 返回类型 | `Optional[BalanceSheet]` |
| 异常处理 | 找不到对应季度数据返回 `None` |

**实现逻辑**：
```python
def get_balance_sheet(self, symbol: str, year: int,
                      quarter: int) -> Optional[BalanceSheet]:
    # 推导报告期日期范围
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
```

---

#### 3.1.5 get_income_statement(symbol, year, quarter)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/income-statements` |
| 必填参数 | `stockCode` (股票代码) |
| 可选参数 | `beginDate`, `endDate` |
| 返回类型 | `Optional[IncomeStatement]` |
| 异常处理 | 找不到对应季度数据返回 `None` |

**实现逻辑**：
```python
def get_income_statement(self, symbol: str, year: int,
                         quarter: int) -> Optional[IncomeStatement]:
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
```

---

#### 3.1.6 get_cash_flow_statement(symbol, year, quarter)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/cash-flows` |
| 必填参数 | `stockCode` (股票代码) |
| 可选参数 | `beginDate`, `endDate` |
| 返回类型 | `Optional[CashFlowStatement]` |
| 异常处理 | 找不到对应季度数据返回 `None` |

**实现逻辑**：
```python
def get_cash_flow_statement(self, symbol: str, year: int,
                            quarter: int) -> Optional[CashFlowStatement]:
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
```

---

### 3.2 特色接口实现 (14个)

#### 3.2.1 get_tech_indicators(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/str-trend-ind` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 5日/10日/20日/60日/120日/250日均线、MACD、DMI、DMA、MTM、TRIX |

**使用场景**：技术分析、趋势判断

---

#### 3.2.2 get_fund_flows(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/daily-fund-flows` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 小单/中单/大单/超大单的资金流入、流出、净流入、占比 |

**使用场景**：主力资金动向分析

---

#### 3.2.3 get_valuation(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/val-indicators` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 总市值、流通市值、市盈率、市净率、市销率 |

**使用场景**：估值分析、价值投资

---

#### 3.2.4 get_financial_indicators(symbol, year, quarter)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/financial-indicators-profitab` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate` |
| 返回类型 | `dict` |
| 数据内容 | 销售毛利率、销售净利率、摊薄ROE、扣非摊薄ROE、平均ROA、平均ROIC |

**使用场景**：盈利能力评估

---

#### 3.2.5 get_dragon_tiger(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/dt-details` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 上榜日期、股票代码、异动类型、偏离值、成交量、成交金额 |

**使用场景**：游资动向跟踪、短线交易

---

#### 3.2.6 entity_recognition(text)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `POST /entity-recognition` |
| 必填参数 | `input` (自然语言文本) |
| 可选参数 | 无 |
| 返回类型 | `dict` |
| 数据内容 | 识别出的实体（股票、行业、基金等） |

**使用场景**：自然语言查询、AI Agent 交互

**示例**：
```python
result = adapter.entity_recognition("贵州茅台怎么样？")
# 返回: {
#     "entities": [
#         {"type": "STOCK", "code": "600519", "name": "贵州茅台"}
#     ]
# }
```

---

#### 3.2.7 get_dupont_analysis(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/dupont-analysis` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 净资产收益率、归母净利率、资产周转率、权益乘数、营业收入、平均总资产 |

**使用场景**：深度财务分析、盈利能力分解

---

#### 3.2.8 get_per_share_indicators(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/per-share-indicators` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 每股收益、每股营业收入、每股经营现金流、每股股东自由现金流 |

**使用场景**：每股指标分析、股东回报评估

---

#### 3.2.9 get_osc_indicators(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/osc-indicators` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | RSI(5/14)、KDJ(K/D/J)、RC、ATR、佳庆离散指标、动态买卖气指标 |

**使用场景**：超买超卖判断、技术分析

---

#### 3.2.10 get_price_vol_ind(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/price-vol-ind` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 布林带、多空布林线、ENV、MIKE、MFI、OBV、PVT、WVAD、AR、BR、PSY |

**使用场景**：量价分析、压力支撑判断

---

#### 3.2.11 get_limit_up_down(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/limit-up-down` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 涨停次数、跌停次数、昨收盘价、实际昨收盘价 |

**使用场景**：极端波动分析、短线交易

---

#### 3.2.12 get_turnover_rates(symbol, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /stock/turnover-rates` |
| 必填参数 | `stockCode` |
| 可选参数 | `beginDate`, `endDate`, `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 单日换手率、10日/1周/2周/4周/13周/26周/52周平均换手率 |

**使用场景**：流动性分析、市场活跃度

---

#### 3.2.13 get_fund_quotes(fund_code, start_date, end_date)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `POST /fund/daily-quotes` |
| 必填参数 | `fundCode` (基金代码) |
| 可选参数 | `beginDate`, `endDate` |
| 返回类型 | `List[dict]` |
| 数据内容 | 基金净值、累计净值、日增长率、成交金额 |

**使用场景**：基金行情分析、基金策略

---

#### 3.2.14 search(keyword, search_type)

| 属性 | 值 |
|------|-----|
| Investoday 路径 | `GET /search` |
| 必填参数 | `type` (搜索类型) |
| 可选参数 | `key` (关键字), `pageNum`, `pageSize` |
| 返回类型 | `List[dict]` |
| 数据内容 | 产品代码、简称、全称、拼音、市场类型、行业级别 |

**搜索类型**：
- `11` - 沪深京A股
- `12` - 基金
- `13` - ETF
- `14` - 港股

**使用场景**：产品搜索、模糊查询

---

## 四、配置设计

### 4.1 环境变量配置

```bash
# .env.example (新增)
INVESTODAY_API_KEY=your_investoday_api_key_here

# 使用说明
export INVESTODAY_API_KEY=sk_xxx_yyy_zzz
```

### 4.2 JSON 配置文件更新

```json
{
  "version": "1.0",
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
    "retry_delay": 0.5
  }
}
```

### 4.3 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `sources.realtime` | 实时行情数据源优先级 | sina > investoday > akshare > tushare |
| `sources.kline` | 历史K线数据源优先级 | investoday > tushare > akshare |
| `sources.fundamentals` | 财务数据源优先级 | investoday > tushare > akshare |
| `sources.tech_analysis` | 技术分析数据源 | investoday (独家) |
| `sources.fund_flows` | 资金流向数据源 | investoday (独家) |
| `sources.valuation` | 估值数据源 | investoday (独家) |

---

## 五、测试设计

### 5.1 测试文件结构

```python
# tests/adapters/test_investoday_adapter.py

class TestInvestodayAdapter:
    """Investoday 适配器测试"""

    # ========== 第一阶段：核心接口 (6个) ==========
    def test_get_realtime_success(self):
        """测试获取实时行情成功"""
        pass

    def test_batch_get_realtime_success(self):
        """测试批量获取实时行情成功"""
        pass

    def test_get_kline_success(self):
        """测试获取历史K线成功"""
        pass

    def test_get_balance_sheet_success(self):
        """测试获取资产负债表成功"""
        pass

    def test_get_income_statement_success(self):
        """测试获取利润表成功"""
        pass

    def test_get_cash_flow_statement_success(self):
        """测试获取现金流量表成功"""
        pass

    # ========== 第二阶段：特色接口 (6个) ==========
    def test_get_tech_indicators_success(self):
        """测试获取技术指标成功"""
        pass

    def test_get_fund_flows_success(self):
        """测试获取资金流向成功"""
        pass

    def test_get_valuation_success(self):
        """测试获取估值指标成功"""
        pass

    def test_get_financial_indicators_success(self):
        """测试获取财务指标成功"""
        pass

    def test_get_dragon_tiger_success(self):
        """测试获取龙虎榜成功"""
        pass

    def test_entity_recognition_success(self):
        """测试实体识别成功"""
        pass

    # ========== 第三阶段：场景接口 (8个) ==========
    def test_get_dupont_analysis_success(self):
        """测试获取杜邦分析成功"""
        pass

    def test_get_per_share_indicators_success(self):
        """测试获取每股指标成功"""
        pass

    def test_get_osc_indicators_success(self):
        """测试获取超买超卖指标成功"""
        pass

    def test_get_price_vol_ind_success(self):
        """测试获取量价指标成功"""
        pass

    def test_get_limit_up_down_success(self):
        """测试获取涨跌停数据成功"""
        pass

    def test_get_turnover_rates_success(self):
        """测试获取换手率成功"""
        pass

    def test_get_fund_quotes_success(self):
        """测试获取基金净值成功"""
        pass

    def test_search_success(self):
        """测试综合搜索成功"""
        pass

    # ========== 异常场景 ==========
    def test_missing_api_key_raises_error(self):
        """测试缺少 API Key 抛出异常"""
        pass

    def test_invalid_symbol_returns_none(self):
        """测试无效股票代码返回 None"""
        pass

    def test_network_timeout_handled(self):
        """测试网络超时处理"""
        pass

    def test_empty_response_returns_none(self):
        """测试空响应返回 None"""
        pass
```

### 5.2 测试覆盖率目标

| 测试类型 | 覆盖率目标 |
|---------|----------|
| 单元测试 | 80%+ |
| 核心接口 | 100% |
| 特色接口 | 100% |
| 异常处理 | 100% |

### 5.3 测试运行命令

```bash
# 运行 Investoday 适配器测试
pytest tests/adapters/test_investoday_adapter.py -v

# 查看测试覆盖率
pytest tests/adapters/test_investoday_adapter.py -v --cov=data_sources.adapters.investoday_adapter --cov-report=html

# 打开覆盖率报告
open htmlcov/index.html
```

---

## 六、使用示例

### 6.1 初始化配置

```python
import os
from data_sources import DataSourceAggregator

# 配置环境变量
os.environ["INVESTODAY_API_KEY"] = "sk_xxx_yyy_zzz"

# 初始化聚合器
aggregator = DataSourceAggregator(config_path="config/sources.json")
```

### 6.2 核心功能示例

```python
# ========== 1. 实时行情 ==========
quote = aggregator.get_realtime("600519")
print(f"贵州茅台: ¥{quote.price:.2f}, 涨幅: {quote.percent:.2%}")

# 批量获取
symbols = ["600519", "000001", "601318"]
quotes = aggregator.batch_get_realtime(symbols)
for q in quotes:
    print(f"{q.symbol}: ¥{q.price:.2f} ({q.percent:+.2%})")

# ========== 2. 历史K线 ==========
klines = aggregator.get_kline("600519", "1d", "2024-01-01", "2024-12-31")
print(f"共获取 {len(klines)} 条K线数据")

# ========== 3. 财务报表 ==========
balance = aggregator.get_balance_sheet("600519", 2023, 3)
income = aggregator.get_income_statement("600519", 2023, 3)
cash_flow = aggregator.get_cash_flow_statement("600519", 2023, 3)

print(f"总资产: {balance.total_assets:,.2f}")
print(f"营业收入: {income.revenue:,.2f}")
print(f"经营现金流: {cash_flow.operating_cash_flow:,.2f}")
```

### 6.3 特色功能示例

```python
# 获取 Investoday 适配器实例
investoday_adapter = aggregator._get_adapter("investoday")

# ========== 4. 技术指标 ==========
tech_data = investoday_adapter.get_tech_indicators("600519", "2024-01-01", "2024-12-31")
for item in tech_data[:3]:  # 查看前3条
    print(f"日期: {item['reportDate']}, MACD: {item.get('macd')}")

# ========== 5. 资金流向 ==========
fund_flows = investoday_adapter.get_fund_flows("600519", "2024-01-01", "2024-12-31")
for item in fund_flows[:3]:
    print(f"主力净流入: {item['mainNetInflow']:,.2f} 万元")

# ========== 6. 估值指标 ==========
valuation = investoday_adapter.get_valuation("600519", "2024-01-01", "2024-12-31")
for item in valuation[:3]:
    print(f"PE: {item['pe']:.2f}, PB: {item['pb']:.2f}")

# ========== 7. 龙虎榜 ==========
dragon_tiger = investoday_adapter.get_dragon_tiger("002594", "2024-01-01", "2024-12-31")
for item in dragon_tiger[:3]:
    print(f"上榜日期: {item['tradeDate']}, 异动类型: {item['abnormalType']}")

# ========== 8. 实体识别 (独家功能) ==========
result = investoday_adapter.entity_recognition("贵州茅台怎么样？")
print(f"识别结果: {result}")
# 输出: {"entities": [{"type": "STOCK", "code": "600519", "name": "贵州茅台"}]}

# ========== 9. 杜邦分析 ==========
dupont = investoday_adapter.get_dupont_analysis("600519", "2024-01-01", "2024-12-31")
for item in dupont[:3]:
    print(f"ROE: {item['roe']:.2%}, 净利率: {item['netProfitMargin']:.2%}")

# ========== 10. 基金净值 ==========
fund_data = investoday_adapter.get_fund_quotes("000001", "2024-01-01", "2024-12-31")
for item in fund_data[:3]:
    print(f"净值: {item['nav']:.4f}, 涨幅: {item['dailyGrowthRate']:.2%}")

# ========== 11. 综合搜索 ==========
search_results = investoday_adapter.search("比亚迪")
for item in search_results[:3]:
    print(f"代码: {item['code']}, 简称: {item['shortName']}")
```

---

## 七、风险与应对

### 7.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| API Key 泄露 | 高 | 使用环境变量，.env 加入 .gitignore |
| 网络请求失败 | 中 | 自动降级机制，重试 + 备用源 |
| 接口变更 | 中 | 封装 `_call_api`，集中管理接口路径 |
| 限流问题 | 低 | 配置合理超时，避免高频调用 |

### 7.2 业务风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 部分接口无数据 | 低 | 返回 `None` 或空列表，不抛异常 |
| 数据格式不一致 | 低 | 数据解析层统一处理 |
| 股票代码格式差异 | 低 | 内部统一转换为标准格式 |

---

## 八、验收标准

### 8.1 功能验收

- [ ] 6个核心接口正常工作，返回数据符合模型规范
- [ ] 14个特色接口正常工作，覆盖主要业务场景
- [ ] 环境变量认证正常工作，缺少 Key 时抛出明确异常
- [ ] 自动降级机制正常工作，Investoday 失败时切换到备用源

### 8.2 代码质量

- [ ] 代码符合 PEP 8 规范
- [ ] 所有公共方法有 docstring
- [ ] 类型注解完整
- [ ] 无硬编码的敏感信息

### 8.3 测试覆盖

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 核心接口测试覆盖 100%
- [ ] 异常场景测试覆盖 100%
- [ ] 通过 `pytest` 运行无失败

### 8.4 文档完善

- [ ] 适配器代码注释完整
- [ ] 使用示例清晰可运行
- [ ] 配置文件更新完整
- [ ] API Key 使用说明清晰

---

## 九、后续扩展

### 9.1 可选扩展接口

Investoday 还有 **166+ 个未实现的接口**，可根据需求后续扩展：

| 分类 | 接口数量 | 优先级 |
|------|---------|--------|
| 沪深京数据 - 公司行为 | 29个 | 低 |
| 沪深京数据 - 特色数据 | 18个 | 低 |
| 板块数据 | 11个 | 低 |
| 指数数据 | 5个 | 低 |
| 港股数据 | 15个 | 低 |
| 研报数据 | 4个 | 低 |
| 宏观经济 | 2个 | 低 |

### 9.2 性能优化方向

- [ ] 连接池复用 (`requests.Session`)
- [ ] 批量接口优化 (减少循环调用)
- [ ] 本地缓存 (高频数据)
- [ ] 异步并发 (批量查询)

### 9.3 功能增强方向

- [ ] 支持 WebSocket 实时推送
- [ ] 数据订阅机制
- [ ] 历史数据增量同步
- [ ] 数据质量监控

---

## 十、参考文档

- [Investoday 官方文档](https://data-api.investoday.net/hub?url=%2Fapidocs%2Fai-native-financial-data)
- [Alpha Quant Trader Pro README](../../README.md)
- [data_sources 模块文档](../plans/2026-03-15-stock-data-source-implementation.md)

---

## 附录

### A. Investoday API Endpoints 映射表

| 适配器方法 | Investoday 路径 | HTTP 方法 |
|-----------|----------------|----------|
| `get_realtime()` | `stock-quote/realtime` | GET |
| `get_kline()` | `stock/adjusted-quotes` | GET |
| `get_balance_sheet()` | `stock/balance-sheets` | GET |
| `get_income_statement()` | `stock/income-statements` | GET |
| `get_cash_flow_statement()` | `stock/cash-flows` | GET |
| `get_tech_indicators()` | `stock/str-trend-ind` | GET |
| `get_fund_flows()` | `stock/daily-fund-flows` | GET |
| `get_valuation()` | `stock/val-indicators` | GET |
| `get_financial_indicators()` | `stock/financial-indicators-profitab` | GET |
| `get_dragon_tiger()` | `stock/dt-details` | GET |
| `entity_recognition()` | `entity-recognition` | POST |
| `get_dupont_analysis()` | `stock/dupont-analysis` | GET |
| `get_per_share_indicators()` | `stock/per-share-indicators` | GET |
| `get_osc_indicators()` | `stock/osc-indicators` | GET |
| `get_price_vol_ind()` | `stock/price-vol-ind` | GET |
| `get_limit_up_down()` | `stock/limit-up-down` | GET |
| `get_turnover_rates()` | `stock/turnover-rates` | GET |
| `get_fund_quotes()` | `fund/daily-quotes` | POST |
| `search()` | `search` | GET |

---

**文档版本**: v1.0
**最后更新**: 2026-03-15
**审核人**: 待审核
