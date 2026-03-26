# API 参考文档

> **版本**: v1.0 | **基础路径**: `/api/v1`

---

## 目录

1. [健康检查](#健康检查)
2. [数据源聚合](#数据源聚合)
3. [股票市场同步](#股票市场同步)
4. [技术指标](#技术指标)
5. [综合分析](#综合分析)
6. [持仓管理](#持仓管理)
7. [收藏管理](#收藏管理)
8. [模拟交易](#模拟交易)
9. [风险控制](#风险控制)
10. [风险提示](#风险提示)
11. [收益统计](#收益统计)
12. [回测系统](#回测系统)
13. [财务数据](#财务数据)
14. [资金流向](#资金流向)
15. [新闻资讯](#新闻资讯)

---

## 健康检查

### GET /health

检查 API 服务是否正常运行。

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00"
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
    "name": "贵州茅台",
    "current_price": 1688.0,
    "change": 5.0,
    "change_pct": 0.30,
    "open": 1683.0,
    "high": 1695.0,
    "low": 1680.0,
    "pre_close": 1683.0,
    "volume": 1234567
  }
}
```

### POST /quote/batch

批量获取多只股票的实时行情。

**请求体**:
```json
{
  "symbols": ["600519", "000001", "601318"]
}
```

### GET /quote/top-list

获取涨跌幅排行榜。

**参数**:
- `type` (str): 排行类型 (gain/loss)
- `date` (str, 可选): 日期 (YYYY-MM-DD)

### GET /kline/{stock_code}

获取单只股票的历史K线数据（从数据库读取）。

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期，默认 "1d"
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `limit` (int): 限制返回数量，默认 120

**示例**:
```bash
curl "http://localhost:8000/api/v1/kline/600519?interval=1d&limit=30"
```

### POST /kline/batch

批量获取多只股票的K线数据。

**请求体**:
```json
{
  "symbols": ["600519", "000001"],
  "interval": "1d",
  "limit": 120
}
```

### GET /kline/stats/{stock_code}

获取K线统计数据（价格区间、成交量、波动率等）。

**参数**:
- `stock_code` (str): 股票代码
- `period` (str): 统计周期 (1y/6m/3m/1m)

---

## 股票市场同步

### POST /market/stock/sync

同步股票列表。

**请求体**:
```json
{
  "force_update": false
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "stock_sync_20240101_120000",
    "sync_type": "stock",
    "status": {
      "status": "completed",
      "progress": 100,
      "total_count": 5000,
      "completed_count": 5000
    }
  }
}
```

### GET /market/stock/sync-status

获取股票同步状态。

### POST /market/kline/sync/{stock_code}

同步单只股票的K线数据。

**参数**:
- `stock_code` (str): 股票代码（路径参数）

**请求体**:
```json
{
  "stock_code": "600519",
  "interval": "1d",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "force_update": false
}
```

### POST /market/kline/sync-realtime

从实时行情同步今日K线（批量）。

**请求体**:
```json
{
  "stock_codes": ["600519", "000001"],
  "interval": "1d"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_count": 2,
    "success_count": 2,
    "failed_count": 0,
    "skipped_count": 0,
    "details": [
      {"symbol": "600519", "status": "success", "reason": null},
      {"symbol": "000001", "status": "success", "reason": null}
    ]
  }
}
```

---

## 技术指标

### POST /indicators/base

计算多种基础技术指标。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120
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
- `days` (int): 回溯天数

### POST /indicators/vcp

检测波动收缩形态 (VCP)。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120
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

### GET /indicators/vcp/{stock_code}

GET 方式检测 VCP 形态。

### POST /indicators/td-sequential

计算 TD 序列（神奇九转）。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 30
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

### GET /indicators/td-sequential/{stock_code}

GET 方式计算 TD 序列。

### POST /indicators/divergence

检测价格与指标之间的背离信号。

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 60,
  "indicator": "macd"
}
```

### GET /indicators/divergence/{stock_code}

GET 方式检测背离。

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

### GET /indicators/zigzag/{stock_code}

GET 方式计算 ZigZag。

---

## 综合分析

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

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数

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
    "total_profit": 0,
    "positions_count": 1
  }
}
```

### GET /portfolio/account/cash

获取账户现金余额。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "cash": 50000
  }
}
```

### POST /portfolio/account/cash/add

向账户充值。

**请求体**:
```json
{"amount": 100000}
```

### GET /portfolio/positions

分页获取持仓列表。

**参数**:
- `page` (int): 页码
- `page_size` (int): 每页数量

### GET /portfolio/positions/{stock_code}

获取单只股票的持仓详情。

**参数**:
- `stock_code` (str): 股票代码

### POST /portfolio/trade/buy

记录买入交易。

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "price": 1688.5,
  "transaction_date": "2024-01-01"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "symbol": "600519",
    "transaction_type": "BUY",
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
  "price": 1700.0
}
```

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

## 收藏管理

### GET /portfolio/favorites

分页获取收藏列表。

**参数**:
- `page` (int): 页码
- `page_size` (int): 每页数量

**响应示例**:
```json
{
  "success": true,
  "data": {
    "favorites": [
      {
        "symbol": "600519",
        "name": "贵州茅台",
        "tag": "白酒",
        "note": "龙头股",
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### POST /portfolio/favorites/add

添加收藏。

**请求体**:
```json
{
  "symbol": "600519",
  "tag": "白酒",
  "note": "龙头股"
}
```

### POST /portfolio/favorites/remove

移除收藏。

**请求体**:
```json
{
  "symbol": "600519"
}
```

### POST /portfolio/favorites/update

更新收藏信息。

**请求体**:
```json
{
  "symbol": "600519",
  "tag": "消费",
  "note": "核心持仓"
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

### GET /simulation/accounts

获取所有模拟账户列表。

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "account_id": "acc_xxx",
      "account_name": "测试账户1",
      "initial_capital": 100000,
      "current_balance": 95000,
      "total_market_value": 50000
    }
  ]
}
```

### GET /simulation/account/{account_id}

获取模拟账户的详细信息。

### DELETE /simulation/account/{account_id}

删除模拟账户。

### POST /simulation/buy

执行买入操作。

**请求体**:
```json
{
  "account_id": "acc_xxx",
  "symbol": "600519",
  "price": 1688.5,
  "quantity": 100
}
```

### POST /simulation/sell

执行卖出操作。

**请求体**:
```json
{
  "account_id": "acc_xxx",
  "symbol": "600519",
  "price": 1700.0,
  "quantity": 100
}
```

### GET /simulation/positions/{account_id}

获取账户的持仓列表。

### GET /simulation/trades/{account_id}

获取账户的交易历史。

**参数**:
- `limit` (int): 返回条数，默认 20

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
    "stock_code": "600519",
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

**请求体**:
```json
{
  "stock_code": "600519",
  "risk_tolerance": 0.05,
  "method": "atr"
}
```

**支持的方法**:
- `atr`: 平均真实波幅
- `volatility`: 波动率
- `percentage`: 固定百分比

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

---

## 风险提示

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

## 收益统计

### GET /performance/account/summary

账户收益汇总。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "metrics": {
      "total_return": 0.15,
      "annualized_return": 0.15,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.3,
      "win_rate": 0.6
    },
    "transactions_count": 20,
    "positions_count": 5
  }
}
```

### GET /performance/stock/{stock_code}

单只股票收益统计。

### GET /performance/history

历史收益曲线。

**参数**:
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `period` (str): 统计周期 (daily/weekly/monthly)

### GET /performance/compare

收益对比分析。

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

## 财务数据

### GET /financial/indicators/{stock_code}

获取财务指标数据（分页）。

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `page` (int): 页码
- `page_size` (int): 每页数量

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

### GET /financial/dupont/{stock_code}

获取杜邦分析数据（分页）。

### GET /financial/per-share/{stock_code}

获取每股指标数据（分页）。

---

## 资金流向

### GET /fundflow/{stock_code}

获取资金流向数据（分页）。

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期
- `end_date` (str, 可选): 结束日期
- `page` (int): 页码
- `page_size` (int): 每页数量

### GET /fundflow/dragon-tiger/{stock_code}

获取龙虎榜数据（分页）。

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
