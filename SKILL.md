# API 服务器 - 完整接口文档

> **版本**: v1.0
> **作者**: Alpha Quant Team
> **最后更新**: 2026-03-25
> **API 基础路径**: `/api/v1`
> **认证方式**: API Key (部分接口需要)

基于 FastAPI 构建的量化交易系统 RESTful API，提供完整的数据、分析、交易、回测和风控功能。

---

## 📋 目录

- [一、服务与数据获取](#一服务与数据获取)
  - [健康检查](#健康检查)
  - [数据源聚合](#数据源聚合)
  - [新闻资讯](#新闻资讯)
  - [财务数据](#财务数据)
  - [资金流向](#资金流向)
  - [市场数据同步](#市场数据同步)
- [二、技术分析](#二技术分析)
  - [基础技术指标](#基础技术指标)
  - [VCP 形态](#vcp-形态)
  - [九转序列](#九转序列)
  - [ZigZag 转向](#zigzag-转向)
  - [背离检测](#背离检测)
  - [五维共振分析](#五维共振分析)
  - [策略分析](#策略分析)
- [三、交易管理](#三交易管理)
  - [持仓管理](#持仓管理)
- [四、模拟交易](#四模拟交易)
  - [账户管理](#账户管理)
  - [交易操作](#交易操作)
  - [持仓与历史](#持仓与历史)
  - [收益统计](#收益统计)
- [五、风险控制](#五风险控制)
  - [风险控制](#风险控制接口)
  - [预警系统](#预警系统)
- [六、回测系统](#六回测系统)
  - [回测系统](#回测系统接口)

---

# 一、服务与数据获取

## 🏥 健康检查

### 1. 服务健康检查

**接口**: `GET /api/v1/health`
**用途**: 检查 API 服务是否正常运行

**请求示例**:
```bash
curl http://localhost:8000/api/v1/health
```

**响应示例**:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "ok"
  }
}
```

---

## 📊 数据源聚合

提供统一的数据访问接口，支持多源数据聚合和自动降级。

### 1. 获取股票列表

**接口**: `GET /api/v1/stock/list`
**用途**: 分页获取股票列表

**参数**:
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100
- `exchange` (str, 可选): 交易所 (SH/SZ)
- `category` (str, 可选): 股票分类

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/stock/list?page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Stock list retrieved successfully",
  "data": {
    "stocks": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 2. 股票详情

**接口**: `GET /api/v1/stock/info/{stock_code}`
**用途**: 获取单只股票的详细信息

**参数**:
- `stock_code` (str): 股票代码 (如 "600519")

**请求示例**:
```bash
curl http://localhost:8000/api/v1/stock/info/600519
```

**响应示例**:
```json
{
  "success": true,
  "message": "Stock info retrieved successfully",
  "data": {}
}
```

### 3. 单股实时行情

**接口**: `GET /api/v1/quote/realtime/{stock_code}`
**用途**: 获取单只股票的实时行情

**参数**:
- `stock_code` (str): 股票代码

**请求示例**:
```bash
curl http://localhost:8000/api/v1/quote/realtime/600519
```

**响应示例**:
```json
{
  "success": true,
  "message": "Realtime quote retrieved successfully",
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
    "volume": 100000,
    "amount": 1000.0,
    "update_time": "2026-03-25T14:30:00"
  }
}
```

### 4. 批量获取行情

**接口**: `POST /api/v1/quote/batch`
**用途**: 批量获取多只股票的实时行情

**请求体**:
```json
{
  "symbols": ["600519", "000001", "601318"],
  "fields": ["price", "change", "volume"]
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/quote/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["600519", "000001", "601318"]}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Batch quotes retrieved successfully",
  "data": {
    "quotes": [],
    "timestamp": "2026-03-25T14:30:00"
  }
}
```

### 5. 涨跌幅排行

**接口**: `GET /api/v1/quote/top-list`
**用途**: 获取涨跌幅排行榜

**参数**:
- `type` (str): 排行类型 (gain/loss)
- `date` (str, 可选): 日期 (YYYY-MM-DD)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/quote/top-list?type=gain"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Top list retrieved successfully",
  "data": {
    "type": "gain",
    "date": "2026-03-25",
    "items": [],
    "total": 0
  }
}
```

### 6. K线数据

**接口**: `GET /api/v1/kline/{stock_code}`
**用途**: 获取单只股票的历史K线数据

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1m/5m/15m/30m/60m/1d/1w/1M)
- `start_date` (str): 开始日期 (YYYY-MM-DD)
- `end_date` (str): 结束日期 (YYYY-MM-DD)
- `limit` (int, 可选): 限制返回数量

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/kline/600519?interval=1d&start_date=2023-01-01&end_date=2023-12-31"
```

**响应示例**:
```json
{
  "success": true,
  "message": "KLine data retrieved successfully",
  "data": {
    "symbol": "600519",
    "name": "示例股票",
    "interval": "1d",
    "klines": [],
    "total": 0,
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }
}
```

### 7. 批量K线

**接口**: `POST /api/v1/kline/batch`
**用途**: 批量获取多只股票的K线数据

**请求体**:
```json
{
  "symbols": ["600519", "000001"],
  "interval": "1d",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/kline/batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["600519", "000001"],
    "interval": "1d",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Batch KLine data retrieved successfully",
  "data": {
    "data": {},
    "timestamp": "2026-03-25T14:30:00"
  }
}
```

### 8. K线统计

**接口**: `GET /api/v1/kline/stats/{stock_code}`
**用途**: 获取K线统计数据（价格区间、成交量、波动率等）

**参数**:
- `stock_code` (str): 股票代码
- `period` (str): 统计周期 (如 "1y", "6m", "3m")

**请求示例**:
```bash
curl http://localhost:8000/api/v1/kline/stats/600519?period=1y
```

**响应示例**:
```json
{
  "success": true,
  "message": "KLine stats retrieved successfully",
  "data": {
    "symbol": "600519",
    "name": "示例股票",
    "period": "1y",
    "total_trading_days": 0,
    "price_range": {"min": 0, "max": 0, "avg": 0},
    "volume_stats": {"min": 0, "max": 0, "avg": 0, "total": 0},
    "volatility": 0.0,
    "highest_price": {"price": 0, "date": ""},
    "lowest_price": {"price": 0, "date": ""}
  }
}
```

### 9. 财务指标（简化版）

**接口**: `GET /api/v1/financial/indicators/{stock_code}`
**用途**: 获取股票的财务指标（简化版，适用于快速查询）

> **注意**: 如需分页查询和更详细的财务指标数据，请使用 [财务数据 - 财务指标](#4-财务指标) 接口。

**参数**:
- `stock_code` (str): 股票代码

**请求示例**:
```bash
curl http://localhost:8000/api/v1/financial/indicators/600519
```

**响应示例**:
```json
{
  "success": true,
  "message": "Financial indicators retrieved successfully",
  "data": {}
}
```

---

## 📰 新闻资讯

### 1. 新闻列表

**接口**: `GET /api/v1/news/list`
**用途**: 分页获取新闻列表

**参数**:
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100
- `category` (str, 可选): 新闻分类
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/news/list?page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "新闻列表获取成功",
  "data": {
    "news": [],
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "query_params": {}
  }
}
```

### 2. 新闻详情

**接口**: `GET /api/v1/news/{news_id}`
**用途**: 获取新闻详细内容

**参数**:
- `news_id` (str): 新闻ID

**请求示例**:
```bash
curl http://localhost:8000/api/v1/news/123456
```

**响应示例**:
```json
{
  "success": true,
  "message": "新闻详情获取成功",
  "data": {}
}
```

### 3. 搜索新闻

**接口**: `GET /api/v1/news/search`
**用途**: 按关键词搜索新闻

**参数**:
- `query` (str): 搜索关键词
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/news/search?query=AI芯片&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "搜索 'AI芯片' 完成",
  "data": {
    "results": [],
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "query": "AI芯片"
  }
}
```

---

## 💰 财务数据

### 1. 资产负债表

**接口**: `GET /api/v1/financial/balance-sheet/{stock_code}`
**用途**: 获取资产负债表

**参数**:
- `stock_code` (str): 股票代码
- `year` (int): 年份
- `quarter` (int): 季度 (1-4)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/balance-sheet/600519?year=2023&quarter=3"
```

**响应示例**:
```json
{
  "success": true,
  "message": "资产负债表获取成功",
  "data": {}
}
```

### 2. 利润表

**接口**: `GET /api/v1/financial/income-statement/{stock_code}`
**用途**: 获取利润表

**参数**:
- `stock_code` (str): 股票代码
- `year` (int): 年份
- `quarter` (int): 季度 (1-4)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/income-statement/600519?year=2023&quarter=3"
```

**响应示例**:
```json
{
  "success": true,
  "message": "利润表获取成功",
  "data": {}
}
```

### 3. 现金流量表

**接口**: `GET /api/v1/financial/cash-flow/{stock_code}`
**用途**: 获取现金流量表

**参数**:
- `stock_code` (str): 股票代码
- `year` (int): 年份
- `quarter` (int): 季度 (1-4)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/cash-flow/600519?year=2023&quarter=3"
```

**响应示例**:
```json
{
  "success": true,
  "message": "现金流量表获取成功",
  "data": {}
}
```

### 4. 财务指标

**接口**: `GET /api/v1/financial/indicators/{stock_code}`
**用途**: 分页获取财务指标数据

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/indicators/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "财务指标获取成功",
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "indicators": [],
    "query_params": {}
  }
}
```

### 5. 杜邦分析

**接口**: `GET /api/v1/financial/dupont/{stock_code}`
**用途**: 分页获取杜邦分析数据

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/dupont/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "杜邦分析获取成功",
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "dupont_data": [],
    "query_params": {}
  }
}
```

### 6. 每股指标

**接口**: `GET /api/v1/financial/per-share/{stock_code}`
**用途**: 分页获取每股指标数据

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/per-share/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "每股指标获取成功",
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "per_share_indicators": [],
    "query_params": {}
  }
}
```

---

## 💹 资金流向

### 1. 资金流向数据

**接口**: `GET /api/v1/fundflow/{stock_code}`
**用途**: 分页获取资金流向数据

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/fundflow/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "资金流向获取成功",
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "fund_flows": [],
    "query_params": {}
  }
}
```

### 2. 龙虎榜数据

**接口**: `GET /api/v1/fundflow/dragon-tiger/{stock_code}`
**用途**: 分页获取龙虎榜数据

**参数**:
- `stock_code` (str): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/fundflow/dragon-tiger/600519?start_date=2023-01-01&end_date=2023-12-31&page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "龙虎榜数据获取成功",
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "dragon_tiger_data": [],
    "query_params": {}
  }
}
```

---

## 🔄 市场数据同步

### 1. 同步股票列表

**接口**: `POST /api/v1/market/stock/sync`
**用途**: 同步股票列表到数据库

**请求体**:
```json
{
  "exchanges": ["SH", "SZ"],
  "force_update": false
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/market/stock/sync \
  -H "Content-Type: application/json" \
  -d '{"exchanges": ["SH", "SZ"]}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Stock sync task created",
  "data": {
    "task_id": "task_123",
    "sync_type": "stock",
    "status": {
      "status": "pending",
      "progress": 0,
      "total_count": 0,
      "completed_count": 0,
      "failed_count": 0
    }
  }
}
```

### 2. 同步状态

**接口**: `GET /api/v1/market/stock/sync-status`
**用途**: 获取股票同步状态

**请求示例**:
```bash
curl http://localhost:8000/api/v1/market/stock/sync-status
```

**响应示例**:
```json
{
  "success": true,
  "message": "Sync status retrieved",
  "data": {}
}
```

### 3. 同步单股K线

**接口**: `POST /api/v1/market/kline/sync/{stock_code}`
**用途**: 同步单只股票的历史K线数据

**参数**:
- `stock_code` (str): 股票代码

**请求体**:
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "force_update": false
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/market/kline/sync/600519 \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "KLine sync task created for 600519",
  "data": {
    "task_id": "task_600519",
    "sync_type": "kline",
    "status": {
      "status": "pending",
      "progress": 0,
      "total_count": 0,
      "completed_count": 0,
      "failed_count": 0
    }
  }
}
```

---

# 二、技术分析

## 📊 基础技术指标

### 1. 计算基础技术指标 (POST)

**接口**: `POST /api/v1/indicators/base`
**用途**: 计算多种基础技术指标

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

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/indicators/base \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "基础技术指标计算成功",
  "data": {
    "stock_code": "600519",
    "days": 120,
    "data_points": 120,
    "latest_date": "2026-03-25",
    "latest_price": 1688.5,
    "signals": {},
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

### 2. 计算基础技术指标 (GET)

**接口**: `GET /api/v1/indicators/base/{stock_code}`
**用途**: GET 方式计算基础技术指标

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 1，最大值 365

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/indicators/base/600519?days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "基础技术指标计算成功",
  "data": {}
}
```

---

## 📐 VCP 形态

### 1. 检测 VCP 形态

**接口**: `POST /api/v1/indicators/vcp`
**用途**: 检测波动收缩形态 (VCP - Volatility Contraction Pattern)

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120,
  "min_drops": 2,
  "max_drops": 4
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/indicators/vcp \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "VCP 形态检测完成",
  "data": {
    "stock_code": "600519",
    "days": 120,
    "analysis_date": "2026-03-25T14:30:00",
    "is_vcp": false,
    "stage": "unknown",
    "stage_description": "未知阶段",
    "contraction_ratio": 0,
    "drop_count": 0,
    "breakout_detected": false,
    "drops": []
  }
}
```

---

## 🔢 九转序列

### 1. 计算九转序列

**接口**: `POST /api/v1/indicators/td-sequential`
**用途**: 计算 TD 序列（神奇九转）

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 30,
  "period": 9,
  "compare_period": 4
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/indicators/td-sequential \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 30}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "TD 序列计算成功",
  "data": {
    "stock_code": "600519",
    "days": 30,
    "period": 9,
    "compare_period": 4,
    "analysis_date": "2026-03-25T14:30:00",
    "td_buy_count": 0,
    "td_sell_count": 0,
    "td_buy_signal": false,
    "td_sell_signal": false,
    "status": "neutral",
    "interpretation": "⚪ 无信号"
  }
}
```

---

## 📉 ZigZag 转向

### 1. 计算 ZigZag 指标

**接口**: `POST /api/v1/indicators/zigzag`
**用途**: 计算 ZigZag 之字转向指标，识别主要价格转折点

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120,
  "threshold": 0.05
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/indicators/zigzag \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "ZigZag 计算成功",
  "data": {
    "stock_code": "600519",
    "days": 120,
    "threshold": 0.05,
    "analysis_date": "2026-03-25T14:30:00",
    "trend": "neutral",
    "trend_direction": "⚪ 横盘整理",
    "is_uptrend": false,
    "is_downtrend": false,
    "recent_pivots": []
  }
}
```

---

## 🔄 背离检测

### 1. 检测背离信号

**接口**: `POST /api/v1/indicators/divergence`
**用途**: 检测价格与指标之间的背离信号

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

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/indicators/divergence \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 60}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "未检测到背离",
  "data": {
    "stock_code": "600519",
    "days": 60,
    "indicator": "macd",
    "analysis_date": "2026-03-25T14:30:00",
    "divergences": {}
  }
}
```

---

## 📈 五维共振分析

### 1. 五维共振分析

**接口**: `POST /api/v1/analysis/five-dimension`
**用途**: 执行五维共振分析

**请求体**:
```json
{
  "stock_code": "600519",
  "days": 120
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/analysis/five-dimension \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Five dimension analysis completed successfully",
  "data": {}
}
```

### 2. 三大策略分析

**接口**: `GET /api/v1/analysis/strategies/{stock_code}`
**用途**: 使用 VCP、九转、背离三大策略进行综合分析

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1d/1w/1m)
- `days` (int): 回溯天数，最小值 30

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategies/600519?interval=1d&days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Strategies analysis completed successfully",
  "data": {}
}
```

### 3. 技术指标

**接口**: `GET /api/v1/analysis/indicator/{stock_code}`
**用途**: 获取技术指标数据

**参数**:
- `stock_code` (str): 股票代码
- `indicator_name` (str): 指标名称 (ma/macd/rsi/boll/td)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/indicator/600519?indicator_name=macd"
```

**响应示例**:
```json
{
  "success": true,
  "message": "macd indicator retrieved successfully",
  "data": {
    "stock_code": "600519",
    "indicator_name": "macd",
    "current_price": 10.0,
    "signals": {},
    "data_points": []
  }
}
```

### 4. 生成分析报告

**接口**: `GET /api/v1/analysis/report/{stock_code}`
**用途**: 生成完整的股票分析报告

**参数**:
- `stock_code` (str): 股票代码
- `interval` (str): K线周期 (1d/1w/1m)
- `days` (int): 回溯天数，最小值 30

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/report/600519?interval=1d&days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Analysis report generated successfully",
  "data": {
    "stock_code": "600519",
    "interval": "1d",
    "days": 120,
    "report": {}
  }
}
```

---

## 🎯 策略分析

### 1. VCP 策略分析

**接口**: `GET /api/v1/analysis/strategy/vcp/{stock_code}`
**用途**: 执行 VCP 策略分析

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 30

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/vcp/600519?days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "VCP analysis completed successfully",
  "data": {
    "strategy_name": "VCP",
    "stock_code": "600519",
    "signal": "",
    "score": 0,
    "confidence": 0,
    "details": {}
  }
}
```

### 2. 九转策略分析

**接口**: `GET /api/v1/analysis/strategy/td/{stock_code}`
**用途**: 执行九转黄金坑策略分析

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 30

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/td/600519?days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "TD Golden Pit analysis completed successfully",
  "data": {
    "strategy_name": "TD Golden Pit",
    "stock_code": "600519",
    "signal": "",
    "score": 0,
    "td_count": 0,
    "details": {}
  }
}
```

### 3. 背离策略分析

**接口**: `GET /api/v1/analysis/strategy/divergence/{stock_code}`
**用途**: 执行顶部背离策略分析

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 30

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/divergence/600519?days=120"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Top Divergence analysis completed successfully",
  "data": {
    "strategy_name": "Top Divergence",
    "stock_code": "600519",
    "signal": "",
    "score": 0,
    "divergence_type": "",
    "details": {}
  }
}
```

---

# 三、交易管理

## 💼 持仓管理

### 1. 账户汇总

**接口**: `GET /api/v1/portfolio/account/summary`
**用途**: 获取账户的汇总信息

**请求示例**:
```bash
curl http://localhost:8000/api/v1/portfolio/account/summary
```

**响应示例**:
```json
{
  "success": true,
  "message": "Account summary retrieved successfully",
  "data": {
    "total_market_value": 100000,
    "total_profit": 0,
    "total_cost": 0,
    "win_rate": 0,
    "positions_count": 0
  }
}
```

### 2. 持仓列表

**接口**: `GET /api/v1/portfolio/positions`
**用途**: 分页获取持仓列表

**参数**:
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/positions?page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Positions retrieved successfully",
  "data": {
    "positions": [],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0
  }
}
```

### 3. 单股持仓

**接口**: `GET /api/v1/portfolio/positions/{stock_code}`
**用途**: 获取单只股票的持仓详情

**参数**:
- `stock_code` (str): 股票代码

**请求示例**:
```bash
curl http://localhost:8000/api/v1/portfolio/positions/600519
```

**响应示例**:
```json
{
  "success": true,
  "message": "Position retrieved successfully",
  "data": {}
}
```

### 4. 买入股票

**接口**: `POST /api/v1/portfolio/trade/buy`
**用途**: 记录买入交易

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "price": 1688.5,
  "transaction_date": "2026-03-25"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/portfolio/trade/buy \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "quantity": 100,
    "price": 1688.5,
    "transaction_date": "2026-03-25"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Buy transaction recorded successfully",
  "data": {}
}
```

### 5. 卖出股票

**接口**: `POST /api/v1/portfolio/trade/sell`
**用途**: 记录卖出交易

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "price": 1700.0,
  "transaction_date": "2026-03-25"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/portfolio/trade/sell \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "quantity": 100,
    "price": 1700.0,
    "transaction_date": "2026-03-25"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Sell transaction recorded successfully",
  "data": {}
}
```

### 6. 充值

**接口**: `POST /api/v1/portfolio/account/cash/add`
**用途**: 向账户充值

**请求体**:
```json
{
  "amount": 100000
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/portfolio/account/cash/add \
  -H "Content-Type: application/json" \
  -d '{"amount": 100000}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Added 100000 to account",
  "data": {
    "amount": 100000
  }
}
```

### 7. 现金余额

**接口**: `GET /api/v1/portfolio/account/cash`
**用途**: 获取账户现金余额

**请求示例**:
```bash
curl http://localhost:8000/api/v1/portfolio/account/cash
```

**响应示例**:
```json
{
  "success": true,
  "message": "Cash balance retrieved successfully",
  "data": {}
}
```

### 8. 交易历史

**接口**: `GET /api/v1/portfolio/transactions`
**用途**: 分页获取交易历史

**参数**:
- `stock_code` (str, 可选): 股票代码
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `page` (int): 页码，最小值 1
- `page_size` (int): 每页数量，范围 1-100

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/transactions?page=1&page_size=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Transaction history retrieved successfully",
  "data": {
    "transactions": [],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0
  }
}
```

### 9. 同步持仓

**接口**: `POST /api/v1/portfolio/positions/sync`
**用途**: 同步持仓信息（存在则覆盖，不存在则新增）

**请求体**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "cost_price": 1688.5,
  "current_price": 1700.0
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/portfolio/positions/sync \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "quantity": 100,
    "cost_price": 1688.5,
    "current_price": 1700.0
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Position synced successfully",
  "data": {
    "symbol": "600519",
    "quantity": 100,
    "cost_price": 1688.5,
    "current_price": 1700.0,
    "market_value": 170000.0,
    "floating_pl": 1150.0
  }
}
```

---

# 四、模拟交易

## 🏦 账户管理

### 1. 创建模拟账户

**接口**: `POST /api/v1/simulation/account`
**用途**: 创建新的模拟交易账户

**请求体**:
```json
{
  "account_name": "测试账户1",
  "initial_capital": 100000,
  "commission_rate": 0.0003
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/simulation/account \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "测试账户1",
    "initial_capital": 100000,
    "commission_rate": 0.0003
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "账户创建成功",
  "data": {
    "account_id": "acc_12345",
    "account_name": "测试账户1",
    "initial_capital": 100000,
    "current_balance": 100000,
    "commission_rate": 0.0003
  }
}
```

### 2. 获取账户信息

**接口**: `GET /api/v1/simulation/account/{account_id}`
**用途**: 获取模拟账户的详细信息

**参数**:
- `account_id` (str): 账户ID

**请求示例**:
```bash
curl http://localhost:8000/api/v1/simulation/account/acc_12345
```

**响应示例**:
```json
{
  "success": true,
  "message": "账户信息获取成功",
  "data": {
    "account_id": "acc_12345",
    "account_name": "测试账户1",
    "initial_capital": 100000,
    "current_balance": 100000,
    "total_profit": 0,
    "win_rate": 0,
    "positions": []
  }
}
```

### 3. 列出所有账户

**接口**: `GET /api/v1/simulation/accounts`
**用途**: 获取所有模拟账户列表

**请求示例**:
```bash
curl http://localhost:8000/api/v1/simulation/accounts
```

**响应示例**:
```json
{
  "success": true,
  "message": "账户列表获取成功",
  "data": [
    {
      "account_id": "acc_12345",
      "account_name": "测试账户1",
      "current_balance": 100000
    }
  ]
}
```

### 4. 删除账户

**接口**: `DELETE /api/v1/simulation/account/{account_id}`
**用途**: 删除模拟账户

**参数**:
- `account_id` (str): 账户ID

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/simulation/account/acc_12345
```

**响应示例**:
```json
{
  "success": true,
  "message": "账户删除成功",
  "data": {
    "account_id": "acc_12345",
    "deleted_at": "2026-03-25T14:40:00"
  }
}
```

---

## 💱 交易操作

### 1. 买入股票

**接口**: `POST /api/v1/simulation/buy`
**用途**: 执行买入操作

**请求体**:
```json
{
  "account_id": "acc_12345",
  "symbol": "600519",
  "price": 1688.5,
  "quantity": 100
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/simulation/buy \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acc_12345",
    "symbol": "600519",
    "price": 1688.5,
    "quantity": 100
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "买入成功",
  "data": {
    "trade_id": "trade_001",
    "account_id": "acc_12345",
    "symbol": "600519",
    "action": "buy",
    "price": 1688.5,
    "quantity": 100,
    "amount": 168850,
    "commission": 50.65,
    "total_cost": 168900.65,
    "timestamp": "2026-03-25T14:30:00",
    "account_balance": 831099.35
  }
}
```

### 2. 卖出股票

**接口**: `POST /api/v1/simulation/sell`
**用途**: 执行卖出操作

**请求体**:
```json
{
  "account_id": "acc_12345",
  "symbol": "600519",
  "price": 1700.0,
  "quantity": 100
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/simulation/sell \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acc_12345",
    "symbol": "600519",
    "price": 1700.0,
    "quantity": 100
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "卖出成功",
  "data": {
    "trade_id": "trade_002",
    "account_id": "acc_12345",
    "symbol": "600519",
    "action": "sell",
    "price": 1700.0,
    "quantity": 100,
    "amount": 170000,
    "commission": 51.0,
    "pnl": 1150,
    "total_revenue": 169949,
    "timestamp": "2026-03-25T14:35:00",
    "account_balance": 1001048.35
  }
}
```

---

## 📋 持仓与历史

### 1. 持仓列表

**接口**: `GET /api/v1/simulation/positions/{account_id}`
**用途**: 获取账户的持仓列表

**参数**:
- `account_id` (str): 账户ID

**请求示例**:
```bash
curl http://localhost:8000/api/v1/simulation/positions/acc_12345
```

**响应示例**:
```json
{
  "success": true,
  "message": "持仓列表获取成功",
  "data": {
    "account_id": "acc_12345",
    "positions": [],
    "total_positions": 0
  }
}
```

### 2. 交易历史

**接口**: `GET /api/v1/simulation/trades/{account_id}`
**用途**: 获取账户的交易历史

**参数**:
- `account_id` (str): 账户ID
- `limit` (int): 返回数量限制，最小值 1

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/simulation/trades/acc_12345?limit=20"
```

**响应示例**:
```json
{
  "success": true,
  "message": "交易历史获取成功",
  "data": {
    "account_id": "acc_12345",
    "trades": [],
    "total_trades": 0
  }
}
```

---

## 📊 收益统计

### 1. 账户收益汇总

**接口**: `GET /api/v1/performance/account/summary`
**用途**: 获取账户的收益汇总统计

**请求示例**:
```bash
curl http://localhost:8000/api/v1/performance/account/summary
```

**响应示例**:
```json
{
  "success": true,
  "message": "Account performance retrieved successfully",
  "data": {
    "metrics": {
      "total_return": 0.0,
      "annualized_return": 0.0,
      "max_drawdown": 0.05,
      "volatility": 0.18,
      "sharpe_ratio": 1.3,
      "sortino_ratio": 1.8,
      "win_rate": 0.0,
      "profit_factor": 1.8,
      "avg_holding_days": 15.5
    },
    "transactions_count": 0,
    "positions_count": 0,
    "calculation_time": "2026-03-25T14:30:00"
  }
}
```

### 2. 单股收益统计

**接口**: `GET /api/v1/performance/stock/{stock_code}`
**用途**: 获取单只股票的收益统计

**参数**:
- `stock_code` (str): 股票代码

**请求示例**:
```bash
curl http://localhost:8000/api/v1/performance/stock/600519
```

**响应示例**:
```json
{
  "success": true,
  "message": "600519 performance retrieved successfully",
  "data": {
    "stock_code": "600519",
    "total_buys": 0,
    "total_sells": 0,
    "total_fees": 0,
    "profit": 0,
    "profit_rate": 0,
    "transactions_count": 0,
    "win_count": 0
  }
}
```

### 3. 历史收益曲线

**接口**: `GET /api/v1/performance/history`
**用途**: 获取历史收益曲线

**参数**:
- `start_date` (str, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (str, 可选): 结束日期 (YYYY-MM-DD)
- `period` (str): 统计周期 (daily/weekly/monthly)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/performance/history?period=monthly"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Performance history retrieved successfully",
  "data": {
    "period": "monthly",
    "history": [],
    "total_periods": 0,
    "start_date": null,
    "end_date": null
  }
}
```

### 4. 收益对比分析

**接口**: `GET /api/v1/performance/compare`
**用途**: 与基准指数对比收益表现

**请求示例**:
```bash
curl http://localhost:8000/api/v1/performance/compare
```

**响应示例**:
```json
{
  "success": true,
  "message": "Performance comparison retrieved successfully",
  "data": {
    "account_return": 0.0,
    "benchmark_return": 0.1,
    "alpha": -0.1,
    "total_market_value": 0,
    "total_profit": 0,
    "benchmark": "沪深300 (模拟)"
  }
}
```

---

# 五、风险控制

## 🛡️ 风险控制接口

### 1. 波动率分析

**接口**: `GET /api/v1/risk/volatility/{stock_code}`
**用途**: 计算股票的波动率和风险指标

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 回溯天数，最小值 1

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/risk/volatility/600519?days=30"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Volatility analysis for 600519 completed successfully",
  "data": {
    "stock_code": "600519",
    "risk_metrics": {
      "var_95": 0.02,
      "var_99": 0.03,
      "volatility": 0.15,
      "max_drawdown": 0.10,
      "sharpe_ratio": 1.5,
      "beta": 1.2,
      "analysis_days": 30,
      "data_points": 30
    },
    "current_price": 1688.5,
    "analysis_time": "2026-03-25T14:30:00"
  }
}
```

### 2. 计算止损位

**接口**: `POST /api/v1/risk/stop-loss/calculate`
**用途**: 根据不同方法计算止损位

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

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/risk/stop-loss/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "risk_tolerance": 0.05,
    "method": "atr"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "Stop loss calculated successfully",
  "data": {
    "stock_code": "600519",
    "current_price": 1688.5,
    "stop_loss": 1600.0,
    "risk_tolerance": 0.05,
    "method": "atr",
    "risk_reward_ratio": 2.5,
    "potential_loss_pct": 5.24,
    "calculation_time": "2026-03-25T14:30:00"
  }
}
```

### 3. 投资组合分散度分析

**接口**: `GET /api/v1/risk/diversification`
**用途**: 分析投资组合的分散度，计算赫芬达尔-赫希曼指数 (HHI)

**请求示例**:
```bash
curl http://localhost:8000/api/v1/risk/diversification
```

**响应示例**:
```json
{
  "success": true,
  "message": "Portfolio diversification analysis completed successfully",
  "data": {
    "diversification_score": 75.5,
    "concentration_risk": "LOW",
    "hhi_index": 0.12,
    "positions_count": 5,
    "top_position_ratio": 0.3,
    "top5_ratio": 0.8,
    "recommendation": "持仓分散度良好",
    "calculation_time": "2026-03-25T14:30:00"
  }
}
```

### 4. 投资组合 VaR

**接口**: `GET /api/v1/risk/portfolio/value-at-risk`
**用途**: 计算投资组合的风险价值 (Value at Risk)

**参数**:
- `confidence_level` (float): 置信水平 (0.9-0.99)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/risk/portfolio/value-at-risk?confidence_level=0.95"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Portfolio VaR calculated successfully",
  "data": {
    "var": 5000.0,
    "var_pct": 5.0,
    "confidence_level": 0.95,
    "total_portfolio_value": 100000.0,
    "positions_count": 5,
    "method": "Historical Simulation (Simplified)",
    "calculation_time": "2026-03-25T14:30:00"
  }
}
```

---

## ⚠️ 预警系统

### 1. 获取已触发预警

**接口**: `GET /api/v1/alerts/triggered`
**用途**: 获取所有已触发的预警（包括投资组合风险和持仓预警）

**请求示例**:
```bash
curl http://localhost:8000/api/v1/alerts/triggered
```

**响应示例**:
```json
{
  "success": true,
  "message": "Triggered alerts retrieved successfully",
  "data": {
    "alerts": [],
    "total_count": 0,
    "critical_count": 0,
    "warning_count": 0,
    "info_count": 0,
    "check_time": "2026-03-25T14:30:00"
  }
}
```

### 2. 单股预警

**接口**: `GET /api/v1/alerts/stock/{stock_code}`
**用途**: 获取单只股票的预警信息

**参数**:
- `stock_code` (str): 股票代码
- `check_types` (str): 检查类型 (price/technical/all)

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/alerts/stock/600519?check_types=all"
```

**响应示例**:
```json
{
  "success": true,
  "message": "Alerts for 600519 retrieved successfully",
  "data": {
    "stock_code": "600519",
    "current_price": 1688.5,
    "alerts": [],
    "total_count": 0,
    "check_time": "2026-03-25T14:30:00"
  }
}
```

### 3. 监控投资组合风险

**接口**: `POST /api/v1/alerts/portfolio/monitor`
**用途**: 主动监控投资组合风险，生成风险建议

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/alerts/portfolio/monitor
```

**响应示例**:
```json
{
  "success": true,
  "message": "Portfolio risk monitoring completed successfully",
  "data": {
    "alerts": [],
    "summary": {
      "total_alerts": 0,
      "critical_alerts": 0,
      "warning_alerts": 0,
      "info_alerts": 0,
      "check_time": "2026-03-25T14:30:00",
      "recommendations": ["✅ 投资组合风险状况良好"]
    }
  }
}
```

---

# 六、回测系统

## 🧪 回测系统接口

### 1. 单股回测

**接口**: `POST /api/v1/backtest/single`
**用途**: 对单只股票执行回测

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

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/backtest/single \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "strategy": "five_dimension",
    "config": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 100000,
      "commission_rate": 0.0003,
      "slippage_rate": 0.001
    }
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "回测完成",
  "data": {
    "task_id": "bt_600519_1710860400",
    "symbol": "600519",
    "strategy": "five_dimension",
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

### 2. 组合回测

**接口**: `POST /api/v1/backtest/portfolio`
**用途**: 对多只股票组合执行回测

**请求体**:
```json
{
  "symbols": ["600519", "000001", "601318"],
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

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/backtest/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["600519", "000001", "601318"],
    "strategy": "five_dimension",
    "config": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 100000,
      "commission_rate": 0.0003,
      "slippage_rate": 0.001
    }
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "组合回测完成",
  "data": {
    "task_id": "bt_portfolio_1710860400",
    "symbols_count": 3,
    "strategy": "five_dimension",
    "status": "completed",
    "results": {
      "600519": {
        "annual_return": 15.5,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.2,
        "total_return": 15.5
      }
    }
  }
}
```

### 3. 策略比较

**接口**: `POST /api/v1/backtest/compare`
**用途**: 比较同一股票在不同策略下的表现

**请求体**:
```json
{
  "symbol": "600519",
  "config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000,
    "commission_rate": 0.0003,
    "slippage_rate": 0.001
  }
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/backtest/compare \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "config": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 100000,
      "commission_rate": 0.0003,
      "slippage_rate": 0.001
    }
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "策略比较完成",
  "data": {
    "symbol": "600519",
    "comparison": {
      "five_dimension": {
        "annual_return": 15.5,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.2,
        "win_rate": 58.5
      },
      "vcp": {
        "annual_return": 12.3,
        "sharpe_ratio": 1.0,
        "max_drawdown": -10.5,
        "win_rate": 52.1
      }
    },
    "best_strategy": "five_dimension",
    "recommendation": "five_dimension 策略表现最优"
  }
}
```

### 4. 回测结果

**接口**: `GET /api/v1/backtest/result/{task_id}`
**用途**: 获取回测的详细结果

**参数**:
- `task_id` (str): 回测任务ID

**请求示例**:
```bash
curl http://localhost:8000/api/v1/backtest/result/bt_600519_1710860400
```

**响应示例**:
```json
{
  "success": true,
  "message": "回测结果获取成功",
  "data": {}
}
```

### 5. 生成回测报告

**接口**: `POST /api/v1/backtest/report`
**用途**: 生成回测报告（支持 JSON/Text/HTML 格式）

**请求体**:
```json
{
  "task_id": "bt_600519_1710860400",
  "format": "html"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/backtest/report \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "bt_600519_1710860400",
    "format": "html"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "HTML 报告生成成功",
  "data": {
    "task_id": "bt_600519_1710860400",
    "format": "html",
    "report_content": "<html>...</html>",
    "download_url": "/api/v1/backtest/report/download/bt_600519_1710860400.html"
  }
}
```

---

## 📝 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 (需要 API Key) |
| 404 | 资源不存在 |
| 429 | 超出请求频率限制 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

---

## 🚀 使用示例

### 完整工作流示例

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health

# 2. 获取股票实时行情
curl http://localhost:8000/api/v1/quote/realtime/600519

# 3. 获取历史K线
curl "http://localhost:8000/api/v1/kline/600519?interval=1d&start_date=2023-01-01&end_date=2023-12-31"

# 4. 技术分析
curl -X POST http://localhost:8000/api/v1/analysis/five-dimension \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'

# 5. VCP 形态检测
curl -X POST http://localhost:8000/api/v1/indicators/vcp \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'

# 6. 创建模拟账户
curl -X POST http://localhost:8000/api/v1/simulation/account \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "测试账户",
    "initial_capital": 100000,
    "commission_rate": 0.0003
  }'

# 7. 回测策略
curl -X POST http://localhost:8000/api/v1/backtest/single \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "strategy": "five_dimension",
    "config": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 100000,
      "commission_rate": 0.0003,
      "slippage_rate": 0.001
    }
  }'
```

---

## 🔐 认证 (可选)

部分接口可能需要 API Key 认证:

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/v1/stock/list
```

---

## 📞 支持

- **文档问题**: [Issues](https://github.com/your-org/alpha-quant-trader-pro/issues)
- **API 反馈**: [Discussions](https://github.com/your-org/alpha-quant-trader-pro/discussions)
- **项目主页**: [GitHub](https://github.com/your-org/alpha-quant-trader-pro)

---

*最后更新：2026-03-25*
