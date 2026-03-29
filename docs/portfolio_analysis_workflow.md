# 持仓分析流程

> 版本: 1.0  
> 更新时间: 2026-03-28  
> 适用范围: A股投资组合分析

---

## 概述

本文档定义了持仓组合分析的完整流程，包含账户概览、持仓明细、组合风险评估、个股深度分析、操作建议等模块。

---

## 分析流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         持仓分析流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ 1. 账户概览  │ →  │ 2. 持仓明细  │ →  │ 3. 组合风险  │          │
│  │   总资产     │    │   盈亏排行   │    │   集中度     │          │
│  │   收益率     │    │   持仓比例   │    │   行业分布   │          │
│  │   可用资金   │    │   成本分布   │    │   波动风险   │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         ↓                   ↓                   ↓                  │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                4. 个股深度分析                           │       │
│  │  ┌───────────┬───────────┬───────────┬───────────┐     │       │
│  │  │ 技术面    │ 基本面    │ 策略信号  │ 风险评估  │     │       │
│  │  │ MA/MACD   │ ROE/增长  │ TD序列    │ 止损位    │     │       │
│  │  │ RSI/KDJ   │ 估值/现金流│ VCP形态  │ 波动率    │     │       │
│  │  └───────────┴───────────┴───────────┴───────────┘     │       │
│  └─────────────────────────────────────────────────────────┘       │
│         ↓                                                          │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                5. 操作建议                               │       │
│  │  • 需要止损的股票                                        │       │
│  │  • 可以加仓的股票                                        │       │
│  │  • 建议减仓的股票                                        │       │
│  │  • 需要关注的信号                                        │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 第一步：账户概览

### 1.1 账户汇总

**接口**: `GET /api/v1/portfolio/account/summary`

**返回字段**:
| 字段 | 说明 |
|------|------|
| total_assets | 总资产 (市值 + 现金) |
| total_cost | 总成本 |
| market_value | 持仓市值 |
| available_cash | 可用资金 |
| total_profit | 总盈亏金额 |
| profit_ratio | 总收益率 (%) |
| today_profit | 今日盈亏 |
| today_profit_ratio | 今日收益率 (%) |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/account/summary"
```

**分析要点**:
- 总资产规模与变化趋势
- 现金占比评估资金利用效率
- 整体收益情况

---

### 1.2 账户指标计算

**建议新增接口**: `GET /api/v1/portfolio/account/metrics`

**期望返回**:
```json
{
  "total_assets": 500000.00,
  "cash_ratio": 15.5,
  "position_ratio": 84.5,
  "max_single_position": 25.3,
  "max_industry_exposure": 40.2,
  "portfolio_beta": 1.15,
  "portfolio_volatility": 18.5,
  "sharpe_ratio": 1.25,
  "max_drawdown": -12.5,
  "win_rate": 62.5
}
```

---

## 第二步：持仓明细

### 2.1 持仓列表

**接口**: `GET /api/v1/portfolio/positions`

**返回字段**:
| 字段 | 说明 |
|------|------|
| symbol | 股票代码 |
| name | 股票名称 |
| quantity | 持仓数量 |
| cost_price | 成本价 |
| current_price | 当前价 |
| market_value | 市值 |
| cost_value | 成本 |
| floating_pl | 浮动盈亏 |
| pl_ratio | 盈亏比例 (%) |
| position_ratio | 持仓比例 (%) |
| today_change | 今日涨跌 (%) |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/positions"
```

---

### 2.2 盈亏排行

**建议新增接口**: `GET /api/v1/portfolio/positions/ranking`

**参数**:
| 参数 | 说明 |
|------|------|
| sort_by | 排序字段: pl_ratio / market_value / today_change |
| order | asc / desc |
| limit | 返回数量 |

**返回示例**:
```json
{
  "top_gainers": [
    {"symbol": "600519", "name": "贵州茅台", "pl_ratio": 45.2, "market_value": 150000},
    {"symbol": "000858", "name": "五粮液", "pl_ratio": 32.1, "market_value": 80000}
  ],
  "top_losers": [
    {"symbol": "300750", "name": "宁德时代", "pl_ratio": -15.3, "market_value": 50000},
    {"symbol": "002594", "name": "比亚迪", "pl_ratio": -8.7, "market_value": 60000}
  ],
  "largest_positions": [
    {"symbol": "600519", "name": "贵州茅台", "position_ratio": 25.3, "market_value": 150000}
  ]
}
```

---

### 2.3 成本分布

**建议新增接口**: `GET /api/v1/portfolio/cost-distribution`

**返回示例**:
```json
{
  "by_profit_range": {
    "high_profit": {"range": ">30%", "count": 3, "value": 120000},
    "moderate_profit": {"range": "10%-30%", "count": 5, "value": 150000},
    "slight_profit": {"range": "0%-10%", "count": 4, "value": 80000},
    "slight_loss": {"range": "-10%-0%", "count": 2, "value": 40000},
    "moderate_loss": {"range": "-30%-10%", "count": 1, "value": 20000},
    "high_loss": {"range": "<-30%", "count": 0, "value": 0}
  },
  "average_cost_date": "2025-06-15",
  "holding_period_stats": {
    "avg_days": 120,
    "max_days": 365,
    "min_days": 15
  }
}
```

---

## 第三步：组合风险评估

### 3.1 集中度风险

**建议新增接口**: `GET /api/v1/portfolio/risk/concentration`

**返回示例**:
```json
{
  "top1_ratio": 25.3,
  "top3_ratio": 55.8,
  "top5_ratio": 78.2,
  "herfindahl_index": 0.152,
  "risk_level": "medium",
  "warnings": [
    {"type": "single_high", "symbol": "600519", "ratio": 25.3, "threshold": 20},
    {"type": "top3_high", "ratio": 55.8, "threshold": 50}
  ]
}
```

**分析要点**:
- 单只股票持仓 > 20% 预警
- 前三大持仓 > 50% 预警
- 赫芬达尔指数 > 0.25 表示高度集中

---

### 3.2 行业分布

**建议新增接口**: `GET /api/v1/portfolio/risk/industry`

**返回示例**:
```json
{
  "industries": [
    {"name": "白酒", "ratio": 35.5, "value": 177500, "stocks": ["600519", "000858"]},
    {"name": "新能源", "ratio": 22.0, "value": 110000, "stocks": ["300750", "002594"]},
    {"name": "银行", "ratio": 15.0, "value": 75000, "stocks": ["601398"]},
    {"name": "医药", "ratio": 12.0, "value": 60000, "stocks": ["000661"]}
  ],
  "max_industry_ratio": 35.5,
  "warnings": [
    {"type": "industry_high", "industry": "白酒", "ratio": 35.5, "threshold": 30}
  ]
}
```

**分析要点**:
- 单行业占比 > 30% 预警
- 行业分散度评估
- 行业轮动机会分析

---

### 3.3 波动风险

**建议新增接口**: `GET /api/v1/portfolio/risk/volatility`

**返回示例**:
```json
{
  "portfolio_volatility": 18.5,
  "benchmark_volatility": 15.2,
  "beta": 1.15,
  "var_95": {
    "daily": -2.5,
    "weekly": -5.8,
    "monthly": -12.3
  },
  "expected_shortfall_95": -3.8,
  "max_drawdown": {
    "current": -8.5,
    "historical_max": -15.2
  },
  "risk_rating": "medium_high"
}
```

**分析要点**:
- Beta > 1.2 表示高波动
- VaR 评估最大可能损失
- 最大回撤监控

---

### 3.4 止损监控

**建议新增接口**: `GET /api/v1/portfolio/risk/stop-loss-monitor`

**返回示例**:
```json
{
  "positions_at_risk": [
    {
      "symbol": "300750",
      "name": "宁德时代",
      "current_price": 180.50,
      "cost_price": 210.00,
      "loss_ratio": -14.0,
      "stop_loss_price": 189.00,
      "distance_to_stop": -4.7,
      "suggestion": "已跌破止损位，建议止损"
    },
    {
      "symbol": "002594",
      "name": "比亚迪",
      "current_price": 250.00,
      "cost_price": 270.00,
      "loss_ratio": -7.4,
      "stop_loss_price": 243.00,
      "distance_to_stop": 2.8,
      "suggestion": "接近止损位，密切关注"
    }
  ],
  "summary": {
    "total_at_risk": 2,
    "total_value_at_risk": 110000,
    "potential_loss": -24500
  }
}
```

---

## 第四步：个股深度分析

对每只持仓股执行完整分析流程：

### 4.1 分析维度

| 维度 | 指标 | 接口 |
|------|------|------|
| **持仓状态** | 成本、盈亏、持仓比例 | `/api/v1/portfolio/positions/{code}` |
| **实时行情** | 价格、涨跌、成交量 | `/api/v1/quote/realtime/{code}` |
| **技术指标** | MA/MACD/RSI/KDJ/布林带 | `/api/v1/indicators/base/{code}` |
| **资金流向** | 主力流入、散户流向 | `/api/v1/fundflow/{code}` |
| **财务指标** | ROE/毛利率/增长率 | `/api/v1/financial/indicators/{code}` |
| **策略信号** | TD序列/VCP形态 | `/api/v1/analysis/strategy/td/{code}` |
| **推荐分析** | 短线/长线评分 | `/api/recommendation/analyze/{code}` |
| **止损止盈** | ATR动态止损 | 推荐分析返回 |

---

### 4.2 个股分析脚本

```bash
#!/bin/bash
# 持仓个股深度分析脚本
# 用法: ./analyze_position.sh 600519

STOCK_CODE=$1

echo "=========================================="
echo "持仓个股深度分析: $STOCK_CODE"
echo "=========================================="

echo ""
echo "=== 持仓状态 ==="
curl -s "http://localhost:8000/api/v1/portfolio/positions/$STOCK_CODE" | python3 -m json.tool

echo ""
echo "=== 实时行情 ==="
curl -s "http://localhost:8000/api/v1/quote/realtime/$STOCK_CODE" | python3 -m json.tool

echo ""
echo "=== 推荐分析 (短线+长线) ==="
curl -s "http://localhost:8000/api/recommendation/analyze/$STOCK_CODE?strategy_type=both" | python3 -m json.tool

echo ""
echo "=== 技术指标 ==="
curl -s "http://localhost:8000/api/v1/indicators/base/$STOCK_CODE?days=120" | python3 -m json.tool

echo ""
echo "=== 资金流向 ==="
curl -s "http://localhost:8000/api/v1/fundflow/$STOCK_CODE" | python3 -m json.tool

echo ""
echo "=== 财务指标 ==="
curl -s "http://localhost:8000/api/v1/financial/indicators/$STOCK_CODE" | python3 -m json.tool

echo ""
echo "=== TD序列 ==="
curl -s "http://localhost:8000/api/v1/analysis/strategy/td/$STOCK_CODE" | python3 -m json.tool
```

---

## 第五步：操作建议

### 5.1 建议生成接口

**建议新增接口**: `GET /api/v1/portfolio/recommendations`

**返回示例**:
```json
{
  "generated_at": "2026-03-28T09:30:00",
  "recommendations": {
    "need_stop_loss": [
      {
        "symbol": "300750",
        "name": "宁德时代",
        "reason": "跌破止损位 -14%",
        "action": "建议止损",
        "priority": "high"
      }
    ],
    "need_attention": [
      {
        "symbol": "002594",
        "name": "比亚迪",
        "reason": "接近止损位 (-7.4%)，RSI超卖",
        "action": "密切关注，考虑减仓",
        "priority": "medium"
      }
    ],
    "can_add_position": [
      {
        "symbol": "600519",
        "name": "贵州茅台",
        "reason": "技术面走强，MACD金叉，长线评分A",
        "action": "可考虑加仓",
        "priority": "low",
        "suggested_ratio": 5
      }
    ],
    "can_take_profit": [
      {
        "symbol": "000858",
        "name": "五粮液",
        "reason": "盈利 +32%，接近目标价",
        "action": "考虑部分止盈",
        "priority": "medium",
        "suggested_sell_ratio": 30
      }
    ],
    "hold": [
      {
        "symbol": "601398",
        "name": "工商银行",
        "reason": "走势正常，无明确信号",
        "action": "继续持有",
        "priority": "low"
      }
    ]
  },
  "summary": {
    "total_actions": 5,
    "high_priority": 1,
    "medium_priority": 2,
    "low_priority": 2
  }
}
```

---

### 5.2 建议规则引擎

```python
# 建议规则配置

RULES = {
    # 止损规则
    "stop_loss": {
        "conditions": [
            {"type": "loss_ratio", "threshold": -10, "action": "stop_loss"},
            {"type": "break_stop_price", "action": "stop_loss"},
            {"type": "td_sell_signal", "count": 9, "action": "consider_sell"}
        ]
    },
    
    # 加仓规则
    "add_position": {
        "conditions": [
            {"type": "profit_ratio", "min": 5, "max": 20},
            {"type": "rating", "min": "B+"},
            {"type": "buy_signals", "min_count": 3},
            {"type": "position_ratio", "max": 15}  # 单只不超过15%
        ]
    },
    
    # 减仓规则
    "reduce_position": {
        "conditions": [
            {"type": "profit_ratio", "min": 30},
            {"type": "rating", "max": "C"},
            {"type": "position_ratio", "min": 20}  # 超过20%需减仓
        ]
    },
    
    # 止盈规则
    "take_profit": {
        "conditions": [
            {"type": "profit_ratio", "min": 50},
            {"type": "td_sell_signal", "count": 9},
            {"type": "rsi_overbought", "threshold": 80}
        ]
    }
}
```

---

## 完整分析脚本

### 一键持仓分析脚本

```bash
#!/bin/bash
# 持仓一键分析脚本
# 用法: ./portfolio_analysis.sh

echo "=========================================="
echo "         持仓组合分析报告                "
echo "=========================================="
echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

echo "=== 1. 账户概览 ==="
curl -s "http://localhost:8000/api/v1/portfolio/account/summary" | python3 -m json.tool
echo ""

echo "=== 2. 持仓列表 ==="
curl -s "http://localhost:8000/api/v1/portfolio/positions" | python3 -m json.tool
echo ""

echo "=== 3. 市场情绪 ==="
curl -s "http://localhost:8000/api/v1/market/sentiment" | python3 -m json.tool
echo ""

echo "=== 4. 个股分析 ==="
POSITIONS=$(curl -s "http://localhost:8000/api/v1/portfolio/positions" | python3 -c "
import json, sys
data = json.load(sys.stdin)
positions = data.get('data', {}).get('positions', [])
for p in positions:
    print(p['symbol'])
")

for CODE in $POSITIONS; do
    echo "--- $CODE ---"
    curl -s "http://localhost:8000/api/recommendation/analyze/$CODE?strategy_type=both" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('data', {})
short = result.get('short_term', {})
long = result.get('long_term', {})

print(f'短线评分: {short.get(\"score\", \"N/A\")} ({short.get(\"rating\", \"N/A\")})')
print(f'长线评分: {long.get(\"score\", \"N/A\")} ({long.get(\"rating\", \"N/A\")})')
if short.get('error'):
    print(f'短线错误: {short[\"error\"]}')
if long.get('error'):
    print(f'长线错误: {long[\"error\"]}')
"
    echo ""
done

echo "=========================================="
echo "分析完成"
echo "=========================================="
```

---

## 分析报告模板

### 持仓分析日报

```
┌──────────────────────────────────────────────────────────────┐
│                    持仓分析日报                               │
│                    2026-03-28                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  【账户概览】                                                 │
│  总资产: ¥500,000    总盈亏: +¥35,000 (+7.5%)               │
│  持仓市值: ¥425,000  可用资金: ¥75,000                       │
│  今日盈亏: +¥5,200   今日收益: +1.04%                        │
│                                                              │
│  【持仓分布】                                                 │
│  持仓数量: 8 只                                               │
│  最大持仓: 贵州茅台 (25.3%)                                  │
│  行业集中: 白酒 (35.5%)                                      │
│                                                              │
│  【风险提示】                                                 │
│  ⚠️ 宁德时代 跌破止损位 -14%，建议止损                       │
│  ⚠️ 白酒行业占比过高 (35.5%)，建议分散                       │
│  ⚡ 比亚迪 接近止损位 (-7.4%)，密切关注                      │
│                                                              │
│  【操作建议】                                                 │
│  🔴 止损: 宁德时代 (300750)                                  │
│  🟡 关注: 比亚迪 (002594)                                    │
│  🟢 加仓: 贵州茅台 (600519) - 评分A，技术走强                │
│  🔵 止盈: 五粮液 (000858) - 盈利32%，考虑部分止盈            │
│                                                              │
│  【市场情绪】                                                 │
│  综合评分: 72 (乐观 📈)                                      │
│  上涨: 4156  下跌: 966  涨停: 101                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 实现计划

### Phase 1: 基础功能 ✅
- [x] 账户汇总接口
- [x] 持仓列表接口
- [x] 个股分析接口

### Phase 2: 风险监控 (待实现)
- [ ] 集中度风险接口
- [ ] 行业分布接口
- [ ] 波动风险接口
- [ ] 止损监控接口

### Phase 3: 智能建议 (待实现)
- [ ] 建议生成引擎
- [ ] 规则配置系统
- [ ] 一键分析脚本

### Phase 4: 可视化 (待实现)
- [ ] 持仓分析看板
- [ ] 盈亏曲线图
- [ ] 行业分布饼图

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-28 | 1.0 | 初版发布 |

---

## 相关文档

- [个股详细分析流程](./stock_analysis_workflow.md)
- [API接口文档](./API_REFERENCE.md)
- [技术指标说明](./TECHNICAL_INDICATORS.md)
