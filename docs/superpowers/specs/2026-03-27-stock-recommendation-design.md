# 股票推荐功能设计文档

## 概述

为 Alpha Quant Trader Pro 新增股票推荐功能，支持短线和中长线两种策略，基于多维度技术指标和基本面数据进行综合评分，生成买入/卖出信号及止损止盈建议。

## 需求摘要

| 项目 | 决策 |
|------|------|
| 推荐类型 | 短线 + 中长线 |
| 股票池 | 全市场扫描 + 用户自选池 |
| 结果展示 | 仅API返回JSON |
| 评分体系 | 完整版（短线6维度、中长线7维度+基本面） |
| 过滤规则 | 可配置（创业板/科创板等） |

## 模块结构

```
stock_recommendation/
├── __init__.py
├── engines/                    # 选股引擎
│   ├── __init__.py
│   ├── base_selector.py        # 基类：公共评分逻辑
│   ├── short_term_selector.py  # 短线选股引擎
│   └── long_term_selector.py   # 中长线选股引擎
├── strategies/                 # 策略配置
│   ├── __init__.py
│   └── strategy_config.py      # 短线/中长线策略参数
├── services/                   # 服务层
│   ├── __init__.py
│   └── recommendation_service.py
├── routers/                    # API路由
│   ├── __init__.py
│   └── recommendation.py
└── models.py                   # 数据模型
```

### 依赖关系

- 复用 `technical_analysis/indicators/base_indicators.py` 计算技术指标
- 复用 `api_server/services/financial_service.py` 获取基本面数据
- 复用 `stock_market/repositories/` 获取K线和股票信息
- 复用 `data_sources/aggregator.py` 获取资金流向

## 评分体系

### 短线评分（满分100分）

| 维度 | 分值 | 指标说明 |
|------|------|----------|
| RSI信号 | 20分 | 超卖(<30)得满分，超买(>70)扣分 |
| KDJ信号 | 20分 | 金叉+J<50得满分，死叉扣分 |
| MACD信号 | 15分 | 金叉/翻红得满分 |
| 布林带信号 | 15分 | 下轨反弹得满分 |
| 量价异动 | 15分 | 放量上涨得满分 |
| 资金流向 | 15分 | 主力流入>500万得满分 |

**推荐条件**：评分>=60 且 买入信号>=2个

### 中长线评分（满分130分，归一化到100分）

| 维度 | 分值 | 指标说明 |
|------|------|----------|
| 趋势评分 | 30分 | MA趋势+ADX强度 |
| 基本面评分 | 30分 | ROE+利润增长+股息率 |
| 估值评分 | 15分 | PEG估值 |
| 动量评分 | 15分 | 20日涨幅 |
| 量能评分 | 15分 | OBV趋势+量比 |
| DMI评分 | 15分 | 多头趋势确认 |
| 资金流评分 | 10分 | 主力净流入 |

**推荐条件**：评分>=65

### 基本面评分细则（30分）

| 指标 | 评分规则 |
|------|----------|
| ROE | >=20%得10分，>=15%得8分，>=10%得5分 |
| 利润增长率 | >=25%得10分，>=15%得7分，>=10%得5分 |
| 股息率 | >=4%得10分，>=2%得6分，>=1%得3分 |

### 估值评分细则（15分）

| PEG值 | 评分 | 评级 |
|-------|------|------|
| <0.8 | 15分 | 低估 |
| 0.8-1.2 | 10分 | 合理 |
| 1.2-2.0 | 5分 | 偏高 |
| >=2.0 | 0分 | 高估 |

### 评级标准

| 评分 | 评级 | 含义 |
|------|------|------|
| >=85 | A+ | 强烈推荐 |
| 70-84 | A | 推荐 |
| 60-69 | B+ | 可操作 |
| 50-59 | B | 关注 |
| 40-49 | C | 观望 |
| <40 | D | 不推荐 |

## API接口

### POST /api/recommendation/scan

扫描推荐股票（全市场或自选池）

**请求体**：
```json
{
    "strategy_type": "short",        // short | long | both
    "top_n": 10,                     // 返回前N只
    "stock_pool": "all",             // all | watchlist | custom
    "custom_codes": ["000001"],      // 自定义股票池（可选）
    "exclude_gem": true,             // 排除创业板
    "exclude_star": true,            // 排除科创板
    "min_score": 60                  // 最低评分过滤
}
```

**响应**：
```json
{
    "success": true,
    "data": {
        "strategy_type": "short",
        "scan_time": "2026-03-27 23:00:00",
        "total_analyzed": 3500,
        "recommendations": [
            {
                "code": "000001",
                "name": "平安银行",
                "price": 12.50,
                "change_pct": 2.35,
                "score": 85.0,
                "rating": "A+",
                "buy_signals": ["RSI超卖(25)", "KDJ金叉", "MACD金叉"],
                "sell_signals": [],
                "stop_loss": 11.88,
                "take_profit": 13.75,
                "stop_loss_pct": -4.96,
                "take_profit_pct": 10.0,
                "risk_reward_ratio": 2.5,
                "recommend": true
            }
        ]
    }
}
```

### GET /api/recommendation/analyze/{stock_code}

分析单只股票，返回详细评分和信号

**响应**：
```json
{
    "success": true,
    "data": {
        "code": "000001",
        "name": "平安银行",
        "price": 12.50,
        "score": 85.0,
        "rating": "A+",
        "recommend": true,
        "details": {
            "rsi": {"score": 20, "value": 25, "signal": "RSI超卖"},
            "kdj": {"score": 20, "k": 30, "d": 25, "j": 40, "golden_cross": true},
            "macd": {"score": 15, "dif": 0.15, "dea": 0.10, "golden_cross": true},
            "bollinger": {"score": 15, "position_pct": 15, "signal": "下轨反弹"},
            "volume": {"score": 15, "volume_ratio": 2.1, "surge_type": "放量上涨"},
            "fund_flow": {"score": 15, "main_in": 850.5}
        },
        "buy_signals": ["RSI超卖(25)", "KDJ金叉", "MACD金叉"],
        "sell_signals": [],
        "stop_loss": 11.88,
        "take_profit": 13.75,
        "risk_reward_ratio": 2.5
    }
}
```

### GET /api/recommendation/strategies

获取可用策略列表

**响应**：
```json
{
    "success": true,
    "data": {
        "short_term": ["rsi_short", "kdj_short", "macd_short", "boll_breakout", "volume_surge"],
        "long_term": ["ma_trend", "macd_trend", "value_growth", "position_building", "trend_following"]
    }
}
```

### GET /api/recommendation/config

获取当前推荐配置参数

### PUT /api/recommendation/config

更新推荐配置（过滤规则、评分阈值等）

## 数据流

```
API Layer (recommendation.py)
        │
        ▼
RecommendationService
        │
        ├───────────────┬───────────────┐
        ▼               ▼               ▼
ShortTermSelector  LongTermSelector  (数据源)
        │               │               │
        └───────────────┴───────────────┤
                                        ▼
                    ┌─────────────────────────────────────┐
                    │ KLineRepository  │ FinancialService │
                    │ DataSourceAggr.  │ BaseIndicators   │
                    └─────────────────────────────────────┘
```

**分析流程**：
1. 获取股票池 -> 应用过滤规则
2. 获取K线数据 -> 计算技术指标
3. 获取基本面数据（仅中长线）
4. 各维度评分 -> 汇总计算总分
5. 生成买入/卖出信号列表
6. 计算止损止盈点位（ATR动态）
7. 排序返回TOP N

## 配置文件

```yaml
# config/recommendation.yaml
recommendation:
  # 过滤规则
  filter:
    exclude_gem: true          # 排除创业板(3开头)
    exclude_star: true         # 排除科创板(688开头)
    min_price: 2.0             # 最低股价
    min_volume: 1000000        # 最低成交量

  # 短线策略参数
  short_term:
    score_threshold: 60        # 推荐阈值
    min_buy_signals: 2         # 最少买入信号数
    atr_stop_multiplier: 2.0   # ATR止损倍数
    atr_profit_multiplier: 3.0 # ATR止盈倍数
    rsi_oversold: 30           # RSI超卖阈值
    rsi_overbought: 70         # RSI超买阈值

  # 中长线策略参数
  long_term:
    score_threshold: 65        # 推荐阈值
    atr_stop_multiplier: 2.5
    atr_profit_multiplier: 4.0
    min_roe: 10                # 最低ROE(%)
    min_profit_growth: 10      # 最低利润增长率(%)

  # 扫描配置
  scan:
    default_top_n: 10          # 默认返回数量
    max_workers: 10            # 并行分析线程数
    cache_ttl: 300             # 缓存有效期(秒)
```

## 风险控制

### 短线风险参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 单只最大仓位 | 30% | 控制单只股票风险 |
| 最多持仓数 | 5只 | 分散风险 |
| 日亏损限制 | -5% | 单日止损线 |

### 中长线风险参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 单只最大仓位 | 25% | 控制单只股票风险 |
| 最多持仓数 | 8只 | 分散风险 |
| 月亏损限制 | -15% | 月度止损线 |

## 参考实现

参考项目 `a-stock-monitor` 的选股引擎实现：
- `short_term_selector.py` - 短线选股逻辑
- `long_term_selector.py` - 中长线选股逻辑
- `enhanced_long_term_selector.py` - 增强版中长线（含基本面）
- `strategy_config.py` - 策略参数配置
