# Investoday 接口能力分析

## 概述
Investoday 提供了约 20 个金融数据接口，覆盖股票、基金等数据，具有数据质量高、接口丰富等特点。

---

## 1. 核心市场数据接口

### 1.1 实时行情
- **接口**: `get_realtime(symbol: str) -> Quote`
- **用途**: 获取单个股票实时行情
- **参数**: 股票代码
- **返回**: Quote 对象

### 1.2 批量实时行情
- **接口**: `batch_get_realtime(symbols: List[str]) -> List[Quote]`
- **用途**: 批量获取实时行情
- **参数**: 股票代码列表
- **返回**: Quote 对象列表

### 1.3 K线数据
- **接口**: `get_kline(symbol: str, interval: str, start_date: str, end_date: str) -> List[KLine]`
- **用途**: 获取K线数据（支持多种周期）
- **参数**:
  - symbol: 股票代码
  - interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
  - start_date: 开始日期 "YYYY-MM-DD"
  - end_date: 结束日期 "YYYY-MM-DD"
- **返回**: KLine 对象列表
- **分页**: 支持分页（pageNum/pageSize），内部自动处理

---

## 2. 基本面数据接口

### 2.1 资产负债表
- **接口**: `get_balance_sheet(symbol: str, year: int, quarter: int) -> BalanceSheet`
- **用途**: 获取指定年份和季度的资产负债表
- **参数**:
  - symbol: 股票代码
  - year: 年份
  - quarter: 季度 (1-4)
- **返回**: BalanceSheet 对象

### 2.2 利润表
- **接口**: `get_income_statement(symbol: str, year: int, quarter: int) -> IncomeStatement`
- **用途**: 获取指定年份和季度的利润表
- **参数**: 同上
- **返回**: IncomeStatement 对象

### 2.3 现金流量表
- **接口**: `get_cash_flow_statement(symbol: str, year: int, quarter: int) -> CashFlowStatement`
- **用途**: 获取指定年份和季度的现金流量表
- **参数**: 同上
- **返回**: CashFlowStatement 对象

### 2.4 财务指标
- **接口**: `get_financial_indicators(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取财务指标历史数据
- **参数**:
  - symbol: 股票代码
  - start_date: 可选，开始日期
  - end_date: 可选，结束日期
- **返回**: 财务指标数据列表（dict）
- **字段**: 可能包含 ROE、毛利率、净利率、资产负债率等

---

## 3. 特色数据接口

### 3.1 技术指标
- **接口**: `get_tech_indicators(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取技术指标数据（MA、MACD、KDJ、RSI 等）
- **参数**:
  - symbol: 股票代码
  - start_date: 可选，开始日期
  - end_date: 可选，结束日期
- **返回**: 技术指标数据列表（dict）
- **字段**: 可能包含 ma5, ma10, ma20, macd, kdj_k, kdj_d, kdj_j, rsi 等

### 3.2 资金流向
- **接口**: `get_fund_flows(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取资金流向数据（主力、散户资金）
- **参数**: 同上
- **返回**: 资金流向数据列表（dict）
- **字段**: 可能包含 主力净流入、散户净流入、大单净流入等

### 3.3 估值指标
- **接口**: `get_valuation(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取估值指标数据（PE、PB、PS 等）
- **参数**: 同上
- **返回**: 估值指标数据列表（dict）
- **字段**: 可能包含 pe_ttm, pb, ps, pe_lyr 等

### 3.4 龙虎榜
- **接口**: `get_dragon_tiger(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取龙虎榜数据（机构买卖情况）
- **参数**: 同上
- **返回**: 龙虎榜数据列表（dict）
- **字段**: 可能包含 买入营业部、卖出营业部、买入金额、卖出金额等

### 3.5 杜邦分析
- **接口**: `get_dupont_analysis(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取杜邦分析数据（ROE 分解）
- **参数**: 同上
- **返回**: 杜邦分析数据列表（dict）
- **字段**: 可能包含 roe, 净利率, 资产周转率, 权益乘数 等

### 3.6 每股指标
- **接口**: `get_per_share_indicators(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取每股指标数据（每股收益、每股净资产等）
- **参数**: 同上
- **返回**: 每股指标数据列表（dict）
- **字段**: 可能包含 eps, bvps, cfps, dps 等

### 3.7 超买超卖指标
- **接口**: `get_osc_indicators(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取超买超卖指标（WR、BIAS 等）
- **参数**: 同上
- **返回**: 超买超卖指标数据列表（dict）
- **字段**: 可能包含 wr, bias, cci 等

### 3.8 量价指标
- **接口**: `get_price_vol_ind(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取量价指标（OBV、VR 等）
- **参数**: 同上
- **返回**: 量价指标数据列表（dict）
- **字段**: 可能包含 obv, vr, mfi 等

### 3.9 涨跌停数据
- **接口**: `get_limit_up_down(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取涨跌停数据
- **参数**: 同上
- **返回**: 涨跌停数据列表（dict）
- **字段**: 可能包含 涨停次数、跌停次数、连板天数 等

### 3.10 换手率
- **接口**: `get_turnover_rates(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取换手率数据
- **参数**: 同上
- **返回**: 换手率数据列表（dict）
- **字段**: 可能包含 换手率、量比 等

---

## 4. 基础信息接口

### 4.1 股票列表
- **接口**: `get_stock_list() -> List[Dict]`
- **用途**: 获取股票列表
- **参数**: 无
- **返回**: 股票列表，每个元素包含股票代码、名称等信息
- **状态**: 目前未实现（返回空列表）

### 4.2 股票详情
- **接口**: `get_stock_detail(symbol: str) -> Optional[Dict]`
- **用途**: 获取股票详细信息
- **参数**: 股票代码
- **返回**: 股票详细信息字典或 None
- **状态**: 目前未实现（返回 None）

---

## 5. 基金数据接口

### 5.1 基金净值
- **接口**: `get_fund_quotes(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> List[dict]`
- **用途**: 获取基金净值数据
- **参数**:
  - symbol: 基金代码
  - start_date: 可选，开始日期
  - end_date: 可选，结束日期
- **返回**: 基金净值数据列表（dict）

---

## 6. AI 功能接口

### 6.1 实体识别
- **接口**: `entity_recognition(text: str) -> Dict`
- **用途**: 金融文本实体识别（股票、概念、机构等）
- **参数**: 文本内容
- **返回**: 实体识别结果字典
- **方法**: POST
- **独特点**: Investoday 独家功能，其他数据源不支持

---

## 7. 搜索接口

### 7.1 综合搜索
- **接口**: `search(query: str, page_num: int, page_size: int) -> Dict`
- **用途**: 综合搜索股票、基金等
- **参数**:
  - query: 搜索关键词
  - page_num: 页码
  - page_size: 每页数量
- **返回**: 搜索结果字典

---

## 接口设计模式总结

### 时间参数模式
- **市场数据**（K线、技术指标、资金流向等）: 使用 `start_date` 和 `end_date`（可选）
- **财务数据**（三表）: 使用 `year` 和 `quarter`
- **基金数据**: 使用 `start_date` 和 `end_date`（可选）

### 返回格式模式
- **核心数据**（行情、K线、三表）: 返回模型对象（Quote, KLine, BalanceSheet 等）
- **特色数据**（技术指标、资金流向等）: 返回 `List[dict]`
- **基础信息**（股票列表、详情）: 返回 `List[Dict]` 或 `Optional[Dict]`

### 分页处理
- K线数据支持分页，内部自动处理
- 其他接口暂未发现分页参数

### 异常处理
- 使用 try-except 捕获异常
- 失败时返回空列表 `[]`（列表接口）或 `None`（单个对象接口）
- 记录错误日志

---

## 扩展建议

基于 Investoday 的接口设计，为 AKShare 和 Tushare 扩展时应：

1. **保持接口签名一致** - 使用相同的参数名和返回类型
2. **实现可支持的接口** - 根据数据源能力实现对应功能
3. **抛出异常提示** - 对不支持的接口抛出 `NotImplementedError` 并记录警告
4. **内部处理分页** - 如果数据源支持分页，适配器内部自动处理
5. **统一日期格式** - 输入和输出都使用 "YYYY-MM-DD" 格式
