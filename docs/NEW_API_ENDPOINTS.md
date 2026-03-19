# API Endpoint 补充说明

## 📋 新增的 8 个模块 (2026-03-18)

本次补充了 8 个缺失的 API 模块，共新增 **27 个 API endpoint**。

---

## 🔧 新增模块详情

### 1. 基础技术指标 (`/api/v1/indicators/base`)

**路由文件**: `api_server/routers/base_indicators.py`

**Endpoint**:
- `POST /api/v1/indicators/base` - 计算所有基础技术指标
- `GET /api/v1/indicators/base/{stock_code}` - GET 版本

**支持的指标**:
- **趋势指标**: MA5/10/20/50/200, EMA, MACD, ADX
- **动量指标**: RSI, Stochastic, CCI, Williams %R
- **波动率指标**: 布林带, ATR, 标准差
- **成交量指标**: OBV, 量比

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/indicators/base" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "days": 120
  }'
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "days": 120,
    "data_points": 120,
    "latest_price": 1800.50,
    "signals": {
      "ma_trend": "strong_uptrend",
      "macd_signal": "bullish",
      "rsi_condition": "neutral",
      "volume_condition": "normal"
    },
    "indicators": {
      "ma5": 1795.20,
      "ma20": 1780.50,
      "macd": 15.3,
      "rsi": 58.5,
      "bb_upper": 1850.0,
      "bb_lower": 1750.0,
      "atr": 25.5,
      "obv": 12500000
    }
  },
  "message": "基础技术指标计算成功"
}
```

---

### 2. 背离检测 (`/api/v1/indicators/divergence`)

**路由文件**: `api_server/routers/divergence.py`

**Endpoint**:
- `POST /api/v1/indicators/divergence` - 检测价格与指标背离

**功能**:
- **顶背离**: 价格创新高，但指标未创新高 (看跌信号)
- **底背离**: 价格创新低，但指标未创新低 (看涨信号)

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/indicators/divergence?stock_code=600519&days=60&indicator=macd"
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "days": 60,
    "indicator": "macd",
    "divergences": {
      "bullish_divergence": {
        "detected": true,
        "details": {...},
        "message": "发现底背离，看涨信号"
      },
      "bearish_divergence": {
        "detected": false,
        "message": "无顶背离"
      }
    }
  },
  "message": "发现背离信号"
}
```

---

### 3. TD 序列 (`/api/v1/indicators/td-sequential`)

**路由文件**: `api_server/routers/td_sequential.py`

**Endpoint**:
- `POST /api/v1/indicators/td-sequential` - 计算 TD 神奇九转

**功能**:
- **低九**: 连续 9 日收盘价 < 4 日前收盘价 (下跌衰竭，买入信号)
- **高九**: 连续 9 日收盘价 > 4 日前收盘价 (上涨衰竭，卖出信号)

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/indicators/td-sequential?stock_code=600519&days=30&period=9&compare_period=4"
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "td_buy_count": 7,
    "td_sell_count": 0,
    "td_buy_signal": false,
    "td_sell_signal": false,
    "status": "counting_low_7",
    "interpretation": "📉 正在计数低九 (7/9)"
  },
  "message": "TD 序列计算成功"
}
```

---

### 4. VCP 形态检测 (`/api/v1/indicators/vcp`)

**路由文件**: `api_server/routers/vcp.py`

**Endpoint**:
- `POST /api/v1/indicators/vcp` - 检测波动收缩形态

**VCP 特征**:
1. 2-4 次回调，幅度依次减小 (如 -20% → -10% → -5%)
2. 成交量逐级萎缩
3. 最后一次回调的高点为枢轴点 (Pivot)
4. 突破确认：股价放量 (>1.5 倍均量) 突破枢轴点

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/indicators/vcp?stock_code=600519&days=120&min_drops=2&max_drops=4"
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "is_vcp": true,
    "stage": "ready_to_breakout",
    "stage_description": "VCP 形态已就绪，等待突破，收缩比率45%",
    "contraction_ratio": 0.45,
    "drop_count": 3,
    "breakout_detected": true,
    "breakout_price": 1850.50,
    "breakout_volume": true,
    "current_price": 1860.00,
    "drops": [...]
  },
  "message": "VCP 形态检测完成"
}
```

---

### 5. ZigZag 指标 (`/api/v1/indicators/zigzag`)

**路由文件**: `api_server/routers/zigzag.py`

**Endpoint**:
- `POST /api/v1/indicators/zigzag` - 计算之字转向指标

**功能**:
- 识别价格的主要转折点
- 过滤噪音，只保留重要的价格转折
- 判断当前趋势方向

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/indicators/zigzag?stock_code=600519&days=120&threshold=0.05"
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "trend": "up",
    "trend_direction": "📈 上升趋势",
    "trend_strength": 0.15,
    "is_uptrend": true,
    "is_downtrend": false,
    "last_change_date": "2026-02-15",
    "zigzag_points_count": 8,
    "current_price": 1860.00,
    "recent_pivots": [
      {"date": "2026-01-10", "price": 1700, "type": "low"},
      {"date": "2026-02-15", "price": 1850, "type": "high"}
    ]
  },
  "message": "ZigZag 计算成功"
}
```

---

### 6. 资金流向 (`/api/v1/fundflow`)

**路由文件**: `api_server/routers/fundflow.py`

**Endpoint**:
- `GET /api/v1/fundflow/{stock_code}` - 资金流向数据
- `GET /api/v1/fundflow/dragon-tiger/{stock_code}` - 龙虎榜数据

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/fundflow/600519?page=1&page_size=20"

curl "http://localhost:8000/api/v1/fundflow/dragon-tiger/600519?page=1&page_size=20"
```

**返回数据**:
```json
{
  "data": {
    "stock_code": "600519",
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3,
    "fund_flows": [...],
    "query_params": {
      "start_date": null,
      "end_date": null
    }
  },
  "message": "资金流向获取成功"
}
```

---

### 7. 新闻资讯 (`/api/v1/news`)

**路由文件**: `api_server/routers/news.py`

**Endpoint**:
- `GET /api/v1/news/list` - 新闻列表
- `GET /api/v1/news/{news_id}` - 新闻详情
- `GET /api/v1/news/search` - 新闻搜索

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/news/list?page=1&page_size=20&category=财经"

curl "http://localhost:8000/api/v1/news/12345"

curl "http://localhost:8000/api/v1/news/search?query=茅台&page=1&page_size=20"
```

**注意**: 新闻服务目前暂未启用，需要配置新闻数据源后才能使用。

---

### 8. 财务数据 (`/api/v1/financial`)

**路由文件**: `api_server/routers/financial.py`

**Endpoint**:
- `GET /api/v1/financial/balance-sheet/{stock_code}` - 资产负债表
- `GET /api/v1/financial/income-statement/{stock_code}` - 利润表
- `GET /api/v1/financial/cash-flow/{stock_code}` - 现金流量表
- `GET /api/v1/financial/indicators/{stock_code}` - 财务指标
- `GET /api/v1/financial/dupont/{stock_code}` - 杜邦分析
- `GET /api/v1/financial/per-share/{stock_code}` - 每股指标

**请求示例**:
```bash
curl "http://localhost:8000/api/v1/financial/balance-sheet/600519?year=2025&quarter=4"

curl "http://localhost:8000/api/v1/financial/indicators/600519?page=1&page_size=20"

curl "http://localhost:8000/api/v1/financial/dupont/600519?start_date=2025-01-01&end_date=2025-12-31"
```

**返回数据**:
```json
{
  "data": {
    "symbol": "600519",
    "year": 2025,
    "quarter": 4,
    "report_date": "2025-12-31",
    "total_assets": 125000000000,
    "total_liabilities": 35000000000,
    "shareholders_equity": 90000000000
  },
  "message": "资产负债表获取成功"
}
```

---

## 📊 完整的 API 模块统计

### 已实现的模块 (共 18 个)

| 模块 | 路由 | Endpoint 数量 |
|------|------|--------------|
| 健康检查 | `/api/v1` | 2 |
| 数据源聚合 | `/api/v1` | 7 |
| 股票市场 | `/api/v1/market` | 2 |
| 持仓管理 | `/api/v1/portfolio` | 6 |
| 技术分析 | `/api/v1/analysis` | 6 |
| 风险控制 | `/api/v1/risk` | 3 |
| 收益统计 | `/api/v1/performance` | 4 |
| 风险提示 | `/api/v1/alerts` | 3 |
| 回测系统 | `/api/v1/backtest` | 5 |
| 模拟交易 | `/api/v1/simulation` | 7 |
| **基础指标** | **`/api/v1/indicators`** | **2** |
| **背离检测** | **`/api/v1/indicators`** | **1** |
| **TD序列** | **`/api/v1/indicators`** | **1** |
| **VCP形态** | **`/api/v1/indicators`** | **1** |
| **ZigZag** | **`/api/v1/indicators`** | **1** |
| **资金流向** | **`/api/v1/fundflow`** | **2** |
| **新闻资讯** | **`/api/v1/news`** | **3** |
| **财务数据** | **`/api/v1/financial`** | **6** |

**总计**: 50+ API endpoint

---

## 🔍 测试建议

### 1. 启动 API Server
```bash
cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/repair-api
python -m api_server.main
```

### 2. 访问 API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 测试新增的 endpoint
建议按以下顺序测试：

1. **基础指标**: `/api/v1/indicators/base`
2. **背离检测**: `/api/v1/indicators/divergence`
3. **TD序列**: `/api/v1/indicators/td-sequential`
4. **VCP形态**: `/api/v1/indicators/vcp`
5. **ZigZag**: `/api/v1/indicators/zigzag`
6. **资金流向**: `/api/v1/fundflow/{stock_code}`
7. **财务数据**: `/api/v1/financial/balance-sheet/{stock_code}`

### 4. 注意事项
- 确保数据库中有足够的 K 线数据
- 新闻服务暂未启用，需要配置数据源
- 所有接口都支持分页和日期过滤

---

## ✅ 完成清单

- [x] 创建基础技术指标路由 (`base_indicators.py`)
- [x] 创建背离检测路由 (`divergence.py`)
- [x] 创建 TD 序列路由 (`td_sequential.py`)
- [x] 创建 VCP 检测路由 (`vcp.py`)
- [x] 创建 ZigZag 路由 (`zigzag.py`)
- [x] 创建资金流向路由 (`fundflow.py`)
- [x] 创建新闻路由 (`news.py`)
- [x] 创建财务数据路由 (`financial.py`)
- [x] 更新 `routers/__init__.py` 导入所有新路由
- [x] 更新 `main.py` 注册所有新路由
- [x] 编写 API 使用文档

---

**创建日期**: 2026-03-18
**版本**: v1.0
