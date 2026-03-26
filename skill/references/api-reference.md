# API 参考文档

> **版本**: v1.0 | **基础路径**: `/api/v1`

---

## 目录

1. [健康检查](#健康检查)
2. [数据源聚合](#数据源聚合)
3. [新闻资讯](#新闻资讯)
4. [财务数据](#财务数据)
5. [资金流向](#资金流向)
6. [技术分析](#技术分析)
7. [持仓管理](#持仓管理)
8. [模拟交易](#模拟交易)
9. [风险控制](#风险控制)
10. [回测系统](#回测系统)

---

## 健康检查

### GET /health

检查 API 服务是否正常运行。

**响应示例**:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {"status": "ok"}
}
```

---

## 数据源聚合

### GET /stock/list

分页获取股票列表。

**参数**:
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100
- `exchange` (str, 可选): 交易所 (SH/SZ)
- `category` (str, 可选): 股票分类

**示例**:
```bash
curl "http://localhost:8000/api/v1/stock/list?page=1&page_size=20"
```

### GET /stock/info/{stock_code}

获取单只股票的详细信息。

### GET /quote/realtime/{stock_code}

获取单只股票的实时行情。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "ts_code": "600519.SH",
    "symbol": "600519",
    "name": "示例股票",
    "current_price": 10.0,
    "change": 0.5,
    "change_pct": 5.0,
    "open": 9.8,
    "high": 10.2,
    "low": 9.7,
    "close": 9.5,
    "volume": 100000
  }
}
```

### POST /quote/batch

批量获取多只股票的实时行情。

**请求体**:
```json
{
  "symbols": ["600519", "000001", "601318"],
  "fields": ["price", "change", "volume"]
}
```

### GET /quote/top-list

获取涨跌幅排行榜。

**参数**:
- `type` (str): 排行类型 (gain/loss)
- `date` (str, 可选): 日期 (YYYY-MM-DD)

### GET /kline/{stock_code}

获取单只股票的历史K线数据。

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1m/5m/15m/30m/60m/1d/1w/1M)
- `start_date` (str): 开始日期 (YYYY-MM-DD)
- `end_date` (str): 结束日期 (YYYY-MM-DD)
- `limit` (int, 可选): 限制返回数量

**示例**:
```bash
curl "http://localhost:8000/api/v1/kline/600519?interval=1d&start_date=2023-01-01&end_date=2023-12-31"
```

### POST /kline/batch

批量获取多只股票的K线数据。

### GET /kline/stats/{stock_code}

获取K线统计数据（价格区间、成交量、波动率等）。

**参数**:
- `stock_code` (str): 股票代码
- `period` (str): 统计周期 (如 "1y", "6m", "3m")

### GET /financial/indicators/{stock_code}

获取股票的财务指标。

---

## 新闻资讯

### GET /news/list

分页获取新闻列表。

**参数**:
- `page` (int): 页码
- `page_size` (int): 每页数量
- `category` (str, 可选): 新闻分类
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期

### GET /news/{news_id}

获取新闻详细内容。

### GET /news/search

按关键词搜索新闻。

**参数**:
- `query` (str): 搜索关键词
- `page` (int): 页码
- `page_size` (int): 每页数量

---

## 财务数据

### GET /financial/balance-sheet/{stock_code}

获取资产负债表。

**参数**:
- `stock_code` (str): 股票代码
- `year` (int): 年份
- `quarter` (int): 季度 (1-4)

### GET /financial/income-statement/{stock_code}

获取利润表。

### GET /financial/cash-flow/{stock_code}

获取现金流量表。

### GET /financial/indicators/{stock_code}

分页获取财务指标数据。

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `page` (int): 页码
- `page_size` (int): 每页数量

### GET /financial/dupont/{stock_code}

分页获取杜邦分析数据。

### GET /financial/per-share/{stock_code}

分页获取每股指标数据。

---

## 资金流向

### GET /fundflow/{stock_code}

分页获取资金流向数据。

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `page` (int): 页码
- `page_size` (int): 每页数量

### GET /fundflow/dragon-tiger/{stock_code}

分页获取龙虎榜数据。

---

## 技术分析

### POST /indicators/base

计算多种基础技术指标。

**支持的指标**:
- 趋势指标：MA5/10/20/50/200, EMA, MACD, ADX
- 动量指标：RSI, Stochastic, CCI, Williams %R
- 波动率指标：布林带, ATR, 标准差
- 成交量指标：OBV, 量比

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120,
  "indicators": ["ma", "macd", "rsi"]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "stock_code": "600519",
    "indicators": {
      "ma5": 1680.0,
      "ma10": 1675.5,
      "ma20": 1670.0,
      "macd": 15.5,
      "macd_signal": 10.0,
      "rsi": 55.5,
      "bb_upper": 1700.0,
      "bb_middle": 1680.0,
      "bb_lower": 1660.0
    }
  }
}
```

### GET /indicators/base/{stock_code}

GET 方式计算基础技术指标。

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 1，最大值 365

### POST /indicators/vcp

检测波动收缩形态 (VCP)。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120,
  "min_drops": 2,
  "max_drops": 4
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "is_vcp": false,
    "stage": "unknown",
    "stage_description": "未知阶段",
    "contraction_ratio": 0,
    "drop_count": 0,
    "breakout_detected": false
  }
}
```

### POST /indicators/td-sequential

计算 TD 序列（神奇九转）。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 30,
  "period": 9,
  "compare_period": 4
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "td_buy_count": 0,
    "td_sell_count": 0,
    "td_buy_signal": false,
    "td_sell_signal": false,
    "status": "neutral"
  }
}
```

### POST /indicators/zigzag

计算 ZigZag 之字转向指标。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120,
  "threshold": 0.05
}
```

### POST /indicators/divergence

检测价格与指标之间的背离信号。

**背离类型**:
- 顶背离：价格创新高，但指标未创新高 (看跌信号)
- 底背离：价格创新低，但指标未创新低 (看涨信号)

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 60,
  "indicator": "macd"
}
```

### POST /analysis/five-dimension

执行五维共振分析。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120
}
```

### GET /analysis/strategies/{stock_code}

使用 VCP、九转、背离三大策略进行综合分析。

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1d/1w/1m)
- `days` (int): 回溯天数，最小值 30

### GET /analysis/indicator/{stock_code}

获取技术指标数据。

**参数**:
- `stock_code` (str): 股票代码
- `indicator_name` (str): 指标名称 (ma/macd/rsi/boll/td)

### GET /analysis/report/{stock_code}

生成完整的股票分析报告。

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1d/1w/1m)
- `days` (int): 回溯天数，最小值 30

### GET /analysis/strategy/vcp/{stock_code}

执行 VCP 策略分析。

### GET /analysis/strategy/td/{stock_code}

执行九转黄金坑策略分析。

### GET /analysis/strategy/divergence/{stock_code}

执行顶部背离策略分析。

---

## 持仓管理

### GET /portfolio/account/summary

获取账户的汇总信息。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_market_value": 100000,
    "stock_market_value": 50000,
    "cash": 50000,
    "total_floating_pl": 0,
    "total_realized_pl": 0,
    "positions_count": 1
  }
}
```

### GET /portfolio/positions

分页获取持仓列表。

**参数**:
- `page` (int): 页码
- `page_size` (int): 每页数量

### GET /portfolio/positions/{stock_code}

获取单只股票的持仓详情。

### POST /portfolio/trade/buy

记录买入交易。

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "price": 1688.5,
  "trade_type": "buy",
  "transaction_date": "2026-03-25"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "600519",
    "transaction_type": "buy",
    "quantity": 100,
    "price": 1688.5,
    "amount": 168850.0,
    "fee": 50.65
  }
}
```

### POST /portfolio/trade/sell

记录卖出交易。

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "price": 1700.0,
  "trade_type": "sell"
}
```

### POST /portfolio/account/cash/add

向账户充值。

**请求体**:
```json
{"amount": 100000}
```

### GET /portfolio/account/cash

获取账户现金余额。

### GET /portfolio/transactions

分页获取交易历史。

**参数**:
- `stock_code` (str, 可选): 股票代码
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `page` (int): 页码
- `page_size` (int): 每页数量

### POST /portfolio/positions/sync

同步持仓信息（存在则覆盖，不存在则新增）。

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "cost_price": 1688.5,
  "current_price": 1700.0
}
```

---

## 模拟交易

### POST /simulation/account

创建新的模拟交易账户。

**请求体**:
```json
{
  "account_name": "测试账户1",
  "initial_capital": 100000,
  "commission_rate": 0.0003
}
```

### GET /simulation/account/{account_id}

获取模拟账户的详细信息。

### GET /simulation/accounts

获取所有模拟账户列表。

### DELETE /simulation/account/{account_id}

删除模拟账户。

### POST /simulation/buy

执行买入操作。

**请求体**:
```json
{
  "account_id": "acc_12345",
  "symbol": "600519",
  "price": 1688.5,
  "quantity": 100
}
```

### POST /simulation/sell

执行卖出操作。

### GET /simulation/positions/{account_id}

获取账户的持仓列表。

### GET /simulation/trades/{account_id}

获取账户的交易历史。

---

## 风险控制

### GET /risk/volatility/{stock_code}

计算股票的波动率和风险指标。

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数

**响应示例**:
```json
{
  "success": true,
  "data": {
    "risk_metrics": {
      "var_95": 0.02,
      "var_99": 0.03,
      "volatility": 0.15,
      "max_drawdown": 0.10,
      "sharpe_ratio": 1.5,
      "beta": 1.2
    }
  }
}
```

### POST /risk/stop-loss/calculate

根据不同方法计算止损位。

**支持的方法**:
- `atr`: 平均真实波幅
- `volatility`: 波动率
- `percentage`: 固定百分比

**请求体**:
```json
{
  "stock_code": "600519",
  "risk_tolerance": 0.05,
  "method": "atr"
}
```

### GET /risk/diversification

分析投资组合的分散度，计算 HHI 指数。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "diversification_score": 75.5,
    "concentration_risk": "LOW",
    "hhi_index": 0.12,
    "positions_count": 5,
    "top_position_ratio": 0.3,
    "recommendation": "持仓分散度良好"
  }
}
```

### GET /risk/portfolio/value-at-risk

计算投资组合的风险价值 (VaR)。

**参数**:
- `confidence_level` (float): 置信水平 (0.9-0.99)

### GET /alerts/triggered

获取所有已触发的预警。

### GET /alerts/stock/{stock_code}

获取单只股票的预警信息。

**参数**:
- `stock_code` (str): 股票代码
- `check_types` (str): 检查类型 (price/technical/all)

### POST /alerts/portfolio/monitor

主动监控投资组合风险，生成风险建议。

---

## 回测系统

### POST /backtest/single

对单只股票执行回测。

**支持的策略**:
- `five_dimension`: 五维共振策略
- `vcp`: VCP 形态策略
- `td_golden_pit`: 九转黄金坑策略
- `top_divergence`: 顶部背离策略

**请求体**:
```json
{
  "symbol": "600519",
  "strategy": "five_dimension",
  "config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000,
    "commission_rate": 0.0003,
    "slippage_rate": 0.001
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "bt_600519_1710860400",
    "status": "completed",
    "result_summary": {
      "total_return": 15.5,
      "annual_return": 15.5,
      "max_drawdown": -8.2,
      "sharpe_ratio": 1.2,
      "win_rate": 58.5,
      "total_trades": 23
    }
  }
}
```

### POST /backtest/portfolio

对多只股票组合执行回测。

**请求体**:
```json
{
  "symbols": ["600519", "000001", "601318"],
  "strategy": "five_dimension",
  "config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000
  }
}
```

### POST /backtest/compare

比较同一股票在不同策略下的表现。

### GET /backtest/result/{task_id}

获取回测的详细结果。

### POST /backtest/report

生成回测报告（支持 JSON/Text/HTML 格式）。

**请求体**:
```json
{
  "task_id": "bt_600519_1710860400",
  "format": "html"
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |
