# 数据源实现能力评估

## 概述
评估 AKShare 和 Tushare 两个数据源能够实现 Investoday 的哪些接口，标记不支持的接口用于抛出异常。

---

## 1. AKShare 实现能力

### 1.1 核心市场数据

#### ✅ 可实现
- `get_realtime(symbol)` - 已实现
- `batch_get_realtime(symbols)` - 已实现
- `get_kline(symbol, interval, start_date, end_date)` - 已实现

#### 📊 实现方式
- 使用 `ak.stock_zh_a_spot_em()` 获取实时行情
- 使用 `ak.stock_zh_a_hist()` 获取日线、周线、月线
- 使用 `ak.stock_zh_a_minute()` 获取分钟线

---

### 1.2 基本面数据

#### ✅ 已部分实现（需完善）
- `get_balance_sheet(symbol, year, quarter)` - 需完善
- `get_income_statement(symbol, year, quarter)` - 需完善
- `get_cash_flow_statement(symbol, year, quarter)` - 需完善
- `get_financial_indicators(symbol, year, quarter)` - 需完善

#### 📊 可用函数
- `ak.stock_balance_sheet_by_report_em()` - 资产负债表（按报告期）
- `ak.stock_cash_flow_sheet_by_report_em()` - 现金流量表（按报告期）
- `ak.stock_financial_analysis_indicator()` - 财务分析指标

#### ⚠️ 注意事项
- 需要将 year/quarter 转换为具体日期
- 部分数据可能需要清洗和格式化

---

### 1.3 技术指标

#### ✅ 可实现
- `get_tech_indicators(symbol, start_date, end_date)`

#### 📊 可用数据
- AKShare 本身不直接提供技术指标计算
- 需要从 K 线数据计算（使用 ta-lib 或自行实现）
- 或使用 `ak.stock_zh_a_hist()` 获取历史数据后计算

#### 🔧 实现策略
- 从 K 线数据计算常用指标（MA、MACD、KDJ、RSI）
- 返回格式：`[{"date": "2023-01-01", "ma5": 10.5, "ma10": 10.8, ...}]`

---

### 1.4 资金流向

#### ✅ 可实现
- `get_fund_flows(symbol, start_date, end_date)`

#### 📊 可用函数
- `ak.stock_individual_fund_flow()` - 个股资金流
- `ak.stock_fund_flow_concept()` - 概念资金流
- `ak.stock_fund_flow_industry()` - 行业资金流
- `ak.stock_hsgt_hist_em()` - 沪深港通资金流

#### 🔧 实现策略
- 使用 `ak.stock_individual_fund_flow()` 获取主力、散户资金
- 返回格式：`[{"date": "2023-01-01", "main_net_inflow": 1000000, ...}]`

---

### 1.5 龙虎榜

#### ✅ 可实现
- `get_dragon_tiger(symbol, start_date, end_date)`

#### 📊 可用函数
- `ak.stock_lhb_detail_em()` - 龙虎榜详情
- `ak.stock_lhb_stock_detail_em()` - 个股龙虎榜
- `ak.stock_lhb_jgmmtj_em()` - 机构买卖统计

#### 🔧 实现策略
- 使用日期范围筛选龙虎榜数据
- 返回格式：`[{"date": "2023-01-01", "buy_departments": [...], ...}]`

---

### 1.6 估值指标

#### ⚠️ 部分实现
- `get_valuation(symbol, start_date, end_date)`

#### 📊 可用数据
- AKShare 没有直接的估值接口
- 可从财务数据计算（PE = price / eps）
- 或使用新浪等其他接口间接获取

#### 🔧 实现策略
- 从财务数据和股价计算估值指标
- 或标记为不支持

---

### 1.7 每股指标

#### ✅ 可实现
- `get_per_share_indicators(symbol, start_date, end_date)`

#### 📊 可用数据
- 从财务数据提取（EPS、BVPS 等）
- 或使用 `ak.stock_financial_abstract()` 获取摘要数据

---

### 1.8 涨跌停数据

#### ✅ 可实现
- `get_limit_up_down(symbol, start_date, end_date)`

#### 📊 可用函数
- `ak.stock_zh_a_hist()` 返回数据包含涨跌幅
- 需要自行判断是否涨停/跌停

#### 🔧 实现策略
- 从 K 线数据计算涨跌停
- 返回格式：`[{"date": "2023-01-01", "is_limit_up": true, ...}]`

---

### 1.9 换手率

#### ✅ 可实现
- `get_turnover_rates(symbol, start_date, end_date)`

#### 📊 可用数据
- `ak.stock_zh_a_hist()` 返回数据包含换手率

---

### 1.10 杜邦分析

#### ❌ 不支持
- `get_dupont_analysis(symbol, start_date, end_date)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

### 1.11 超买超卖指标 & 量价指标

#### ✅ 可实现（需计算）
- `get_osc_indicators()`
- `get_price_vol_ind()`

#### 🔧 实现策略
- 从 K 线数据计算技术指标
- 使用 ta-lib 或自行实现

---

### 1.12 基础信息

#### ⚠️ 部分支持
- `get_stock_list()` - 可从 `ak.stock_zh_a_spot_em()` 获取
- `get_stock_detail(symbol)` - 信息有限

---

### 1.13 基金数据

#### ✅ 可实现
- `get_fund_quotes(symbol, start_date, end_date)`

#### 📊 可用函数
- `ak.fund_open_fund_info_em()` - 开放式基金信息
- `ak.fund_etf_hist_em()` - ETF 历史净值

---

### 1.14 AI 实体识别

#### ❌ 不支持
- `entity_recognition(text)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

### 1.15 搜索

#### ❌ 不支持
- `search(query, page_num, page_size)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

## 2. Tushare Pro 实现能力

### 2.1 核心市场数据

#### ✅ 可实现
- `get_realtime(symbol)` - 已实现
- `batch_get_realtime(symbols)` - 已实现
- `get_kline(symbol, interval, start_date, end_date)` - 已实现

#### 📊 实现方式
- 使用 `pro.daily_basic()` 获取实时行情
- 使用 `pro.daily()` 获取日线
- 使用 `pro.stk_mins()` 获取分钟线（需权限）

---

### 2.2 基本面数据

#### ✅ 已实现（需 VIP）
- `get_balance_sheet(symbol, year, quarter)` - 已实现（VIP）
- `get_income_statement(symbol, year, quarter)` - 已实现（VIP）
- `get_cash_flow_statement(symbol, year, quarter)` - 已实现（VIP）
- `get_financial_indicators(symbol, year, quarter)` - 已实现

#### 📊 可用接口
- `pro.balancesheet_vip()` - 资产负债表
- `pro.income_vip()` - 利润表
- `pro.cashflow_vip()` - 现金流量表
- `pro.fina_indicator()` - 财务指标

---

### 2.3 技术指标

#### ⚠️ 部分支持
- `get_tech_indicators(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.stk_factor()` - 量价因子（包含部分技术指标）
- 需要自行计算或使用其他工具

---

### 2.4 资金流向

#### ✅ 可实现
- `get_fund_flows(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.moneyflow()` - 个股资金流向
- `pro.moneyflow_hsgt()` - 沪深港通资金流向

---

### 2.5 龙虎榜

#### ✅ 可实现
- `get_dragon_tiger(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.top_list()` - 龙虎榜每日明细
- `pro.top_inst()` - 龙虎榜机构明细

---

### 2.6 估值指标

#### ✅ 可实现
- `get_valuation(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.daily_basic()` - 包含 PE、PB 等估值指标
- `pro.stk_factor()` - 估值因子

---

### 2.7 每股指标

#### ✅ 可实现
- `get_per_share_indicators(symbol, start_date, end_date)`

#### 📊 可用数据
- 从财务数据提取（EPS 等）
- `pro.daily_basic()` 包含部分每股指标

---

### 2.8 涨跌停数据

#### ✅ 可实现
- `get_limit_up_down(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.limit_list_d()` - 每日涨跌停列表

---

### 2.9 换手率

#### ✅ 可实现
- `get_turnover_rates(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.daily_basic()` - 包含换手率
- `pro.stk_factor()` - 包含量比等

---

### 2.10 杜邦分析

#### ❌ 不支持
- `get_dupont_analysis(symbol, start_date, end_date)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

### 2.11 超买超卖指标 & 量价指标

#### ⚠️ 部分支持
- `get_osc_indicators()`
- `get_price_vol_ind()`

#### 📊 可用接口
- `pro.stk_factor()` - 包含部分量价指标
- 需要自行计算超买超卖指标

---

### 2.12 基础信息

#### ✅ 可实现
- `get_stock_list()` - 已实现
- `get_stock_detail(symbol)` - 已实现

---

### 2.13 基金数据

#### ⚠️ 有限支持
- `get_fund_quotes(symbol, start_date, end_date)`

#### 📊 可用接口
- `pro.fund_basic()` - 基金基础信息
- `pro.fund_nav()` - 基金净值（需权限）

---

### 2.14 AI 实体识别

#### ❌ 不支持
- `entity_recognition(text)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

### 2.15 搜索

#### ❌ 不支持
- `search(query, page_num, page_size)`

#### 🔧 处理方式
- 抛出 `NotImplementedError`
- 记录警告日志

---

## 3. 实现能力对比总结

| 接口 | AKShare | Tushare | 优先实现 |
|------|---------|---------|----------|
| get_realtime | ✅ | ✅ | - |
| batch_get_realtime | ✅ | ✅ | - |
| get_kline | ✅ | ✅ | - |
| get_balance_sheet | ✅ | ✅(VIP) | Tushare |
| get_income_statement | ✅ | ✅(VIP) | Tushare |
| get_cash_flow_statement | ✅ | ✅(VIP) | Tushare |
| get_financial_indicators | ✅ | ✅ | Tushare |
| get_tech_indicators | ✅(计算) | ⚠️(部分) | AKShare |
| get_fund_flows | ✅ | ✅ | 两者均可 |
| get_valuation | ⚠️(计算) | ✅ | Tushare |
| get_dragon_tiger | ✅ | ✅ | 两者均可 |
| get_dupont_analysis | ❌ | ❌ | 不实现 |
| get_per_share_indicators | ✅(提取) | ✅ | 两者均可 |
| get_osc_indicators | ✅(计算) | ⚠️(部分) | AKShare |
| get_price_vol_ind | ✅(计算) | ⚠️(部分) | AKShare |
| get_limit_up_down | ✅(计算) | ✅ | Tushare |
| get_turnover_rates | ✅ | ✅ | 两者均可 |
| get_stock_list | ⚠️(部分) | ✅ | Tushare |
| get_stock_detail | ⚠️(部分) | ✅ | Tushare |
| get_fund_quotes | ✅ | ⚠️(有限) | AKShare |
| entity_recognition | ❌ | ❌ | 不实现 |
| search | ❌ | ❌ | 不实现 |

---

## 4. 实现优先级建议

### 高优先级（核心功能）
1. 基本面三表（资产负债表、利润表、现金流量表）
2. 财务指标
3. 股票列表和详情
4. 资金流向

### 中优先级（常用功能）
5. 技术指标
6. 龙虎榜
7. 涨跌停数据
8. 换手率
9. 估值指标

### 低优先级（特色功能）
10. 每股指标
11. 超买超卖指标
12. 量价指标
13. 基金净值

### 不实现
- 杜邦分析（两个数据源都不支持）
- AI 实体识别（两个数据源都不支持）
- 搜索（两个数据源都不支持）

---

## 5. 异常处理策略

对于不支持的接口，统一处理方式：

```python
def get_dupont_analysis(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[dict]:
    """获取杜邦分析数据 - AKShare 不支持"""
    logger.warning(f"AKShare does not support dupont analysis for {symbol}")
    raise NotImplementedError("AKShare does not support dupont analysis. Use Investoday instead.")
```
