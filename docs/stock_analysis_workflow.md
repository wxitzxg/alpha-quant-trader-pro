# 个股详细分析流程

> 版本: 1.0  
> 更新时间: 2026-03-26  
> 适用范围: A股个股分析

---

## 概述

本文档定义了个股详细分析的完整流程，包含持仓数据、基础信息、技术面、基本面、策略分析、风险分析、新闻资讯和市場情绪等模块。

---

## 分析流程图

```
┌─────────────┐
│  持仓数据   │ ← 成本价、盈亏、持仓比例
└──────┬──────┘
       ↓
┌─────────────┐
│  基础信息   │ ← 股票信息、实时行情、涨跌排行
└──────┬──────┘
       ↓
┌─────────────┐
│  技术面     │ ← 技术指标、K线、资金流向、龙虎榜
└──────┬──────┘
       ↓
┌─────────────┐
│  基本面     │ ← 财务报表、财务指标、杜邦分析
└──────┬──────┘
       ↓
┌─────────────┐
│  策略分析   │ ← 综合报告、TD序列、VCP形态
└──────┬──────┘
       ↓
┌─────────────┐
│  风险分析   │ ← 波动率、止损计算
└──────┬──────┘
       ↓
┌─────────────┐
│  新闻资讯   │ ← 相关新闻、公告
└──────┬──────┘
       ↓
┌─────────────┐
│  市场情绪   │ ← 大盘指数、涨跌家数
└─────────────┘
```

---

## 第零步：持仓数据

### 0.1 持仓查询

**接口**: `GET /api/v1/portfolio/positions/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| symbol | 股票代码 |
| quantity | 持仓数量 |
| cost_price | 成本价 |
| current_price | 当前价 |
| market_value | 市值 |
| cost_value | 成本 |
| floating_pl | 浮动盈亏 |
| position_ratio | 持仓比例 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/positions/600745"
```

**分析要点**:
- 计算盈亏比例: `(current_price - cost_price) / cost_price * 100%`
- 判断是否需要止损/止盈
- 评估持仓比例是否合理

---

### 0.2 账户概览

**接口**: `GET /api/v1/portfolio/account/summary`

**返回字段**:
| 字段 | 说明 |
|------|------|
| total_assets | 总资产 |
| available_cash | 可用资金 |
| total_profit | 总盈亏 |
| profit_ratio | 收益率 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/portfolio/account/summary"
```

**分析要点**:
- 了解当前可用资金
- 评估整体投资组合表现

---

## 第一步：基础信息

### 1.1 股票基本信息

**接口**: `GET /api/v1/stock/info/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| symbol | 股票代码 |
| name | 股票名称 |
| industry | 所属行业 |
| market | 交易所 |
| list_date | 上市日期 |
| total_shares | 总股本 |
| float_shares | 流通股本 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/stock/info/600745"
```

---

### 1.2 实时行情

**接口**: `GET /api/v1/quote/realtime/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| price | 当前价 |
| change | 涨跌额 |
| change_pct | 涨跌幅 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| pre_close | 昨收价 |
| volume | 成交量 |
| amount | 成交额 |
| turnover_rate | 换手率 |
| bid/ask | 五档盘口 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/quote/realtime/600745"
```

**分析要点**:
- 当日涨跌幅及趋势
- 成交量是否放大
- 五档买卖盘力量对比

---

### 1.3 涨跌排行

**接口**: `GET /api/v1/quote/top-list?type={gain|loss}`

**参数**:
| 参数 | 说明 |
|------|------|
| type | gain(涨幅榜) / loss(跌幅榜) |
| date | 日期 (可选) |

**调用示例**:
```bash
# 涨幅榜
curl "http://localhost:8000/api/v1/quote/top-list?type=gain"

# 跌幅榜
curl "http://localhost:8000/api/v1/quote/top-list?type=loss"
```

**分析要点**:
- 判断个股在市场中的相对位置
- 了解市场热点板块

---

## 第二步：技术面分析

### 2.1 技术指标

**接口**: `GET /api/v1/indicators/base/{stock_code}?days=120`

**返回字段**:

**趋势指标**:
| 指标 | 说明 |
|------|------|
| ma5/ma10/ma20/ma50/ma200 | 均线 |
| macd | MACD线 |
| macd_signal | 信号线 |
| macd_histogram | 柱状图 |
| adx | 趋势强度 |

**动量指标**:
| 指标 | 说明 |
|------|------|
| rsi | 相对强弱指数 |
| stoch_k/stoch_d | KDJ随机指标 |
| cci | 顺势指标 |
| williams_r | 威廉指标 |

**波动率指标**:
| 指标 | 说明 |
|------|------|
| bb_upper/bb_middle/bb_lower | 布林带 |
| bb_width | 布林带宽度 |
| atr | 真实波动幅度 |

**成交量指标**:
| 指标 | 说明 |
|------|------|
| obv | 能量潮 |
| volume_ratio | 量比 |

**技术信号**:
| 信号 | 取值 |
|------|------|
| ma_trend | uptrend/downtrend/weak_uptrend/weak_downtrend/sideways |
| macd_signal | bullish/bearish/neutral |
| adx_strength | strong_trend/weak_trend |
| rsi_condition | overbought/oversold/neutral |
| stoch_condition | bullish_crossover/bearish_crossover |
| bb_position | upper_half/lower_half |
| volatility_level | high/normal/low |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/indicators/base/600745?days=120"
```

**分析要点**:
- MA趋势判断多空方向
- MACD金叉/死叉信号
- RSI超买超卖区间
- 布林带位置判断支撑压力

---

### 2.2 K线数据

**接口**: `GET /api/v1/kline/{stock_code}?interval=1d&limit=100`

**参数**:
| 参数 | 说明 |
|------|------|
| interval | 周期 (1d/1w/1M) |
| start_date | 开始日期 |
| end_date | 结束日期 |
| limit | 数据条数 |

**返回字段**:
| 字段 | 说明 |
|------|------|
| trade_date | 交易日期 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| amount | 成交额 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/kline/600745?interval=1d&limit=100"
```

---

### 2.3 K线统计

**接口**: `GET /api/v1/kline/stats/{stock_code}?period=1y`

**参数**:
| 参数 | 说明 |
|------|------|
| period | 周期 (1y/6m/3m/1m) |

**返回字段**:
| 字段 | 说明 |
|------|------|
| total_days | 交易天数 |
| up_days | 上涨天数 |
| down_days | 下跌天数 |
| max_price | 最高价 |
| min_price | 最低价 |
| avg_volume | 平均成交量 |
| volatility | 波动率 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/kline/stats/600745?period=1y"
```

---

### 2.4 资金流向

**接口**: `GET /api/v1/fundflow/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| main_net_inflow | 主力净流入 |
| retail_net_inflow | 散户净流入 |
| super_large_inflow | 超大单流入 |
| large_inflow | 大单流入 |
| medium_inflow | 中单流入 |
| small_inflow | 小单流入 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/fundflow/600745"
```

**分析要点**:
- 主力资金动向
- 主力与散户资金博弈
- 连续多日资金流向趋势

---

### 2.5 龙虎榜

**接口**: `GET /api/v1/fundflow/dragon-tiger/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| trade_date | 交易日期 |
| reason | 上榜原因 |
| buy_value | 买入金额 |
| sell_value | 卖出金额 |
| net_value | 净买入 |
| buyers | 买方营业部列表 |
| sellers | 卖方营业部列表 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/fundflow/dragon-tiger/600745"
```

**分析要点**:
- 机构/游资动向
- 知名营业部买卖情况
- 上榜原因分析

---

## 第三步：基本面分析

### 3.1 资产负债表

**接口**: `GET /api/v1/financial/balance-sheet/{stock_code}?year=2024&quarter=3`

**参数**:
| 参数 | 说明 |
|------|------|
| year | 年份 |
| quarter | 季度 (1-4) |

**返回字段**:
| 字段 | 说明 |
|------|------|
| total_assets | 总资产 |
| total_liabilities | 总负债 |
| shareholders_equity | 股东权益 |
| current_assets | 流动资产 |
| current_liabilities | 流动负债 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/balance-sheet/600745?year=2024&quarter=3"
```

**分析要点**:
- 资产负债率 = 总负债 / 总资产
- 流动比率 = 流动资产 / 流动负债
- 财务稳健性评估

---

### 3.2 利润表

**接口**: `GET /api/v1/financial/income-statement/{stock_code}?year=2024&quarter=3`

**返回字段**:
| 字段 | 说明 |
|------|------|
| revenue | 营业收入 |
| operating_profit | 营业利润 |
| net_profit | 净利润 |
| eps | 每股收益 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/income-statement/600745?year=2024&quarter=3"
```

**分析要点**:
- 营收增长率
- 净利润增长率
- 毛利率趋势

---

### 3.3 现金流量表

**接口**: `GET /api/v1/financial/cash-flow/{stock_code}?year=2024&quarter=3`

**返回字段**:
| 字段 | 说明 |
|------|------|
| operating_cash_flow | 经营活动现金流 |
| investing_cash_flow | 投资活动现金流 |
| financing_cash_flow | 筹资活动现金流 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/cash-flow/600745?year=2024&quarter=3"
```

**分析要点**:
- 经营现金流是否为正
- 现金流质量评估
- 企业造血能力

---

### 3.4 财务指标

**接口**: `GET /api/v1/financial/indicators/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| roe | 净资产收益率 |
| roa | 总资产收益率 |
| gross_margin | 毛利率 |
| net_margin | 净利率 |
| debt_ratio | 资产负债率 |
| current_ratio | 流动比率 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/indicators/600745"
```

---

### 3.5 杜邦分析

**接口**: `GET /api/v1/financial/dupont/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| roe | 净资产收益率 |
| net_margin | 净利率 |
| asset_turnover | 资产周转率 |
| equity_multiplier | 权益乘数 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/dupont/600745"
```

**分析要点**:
- ROE = 净利率 × 资产周转率 × 权益乘数
- 分析ROE驱动因素
- 识别盈利模式

---

### 3.6 每股指标

**接口**: `GET /api/v1/financial/per-share/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| eps | 每股收益 |
| bvps | 每股净资产 |
| cfps | 每股现金流 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/financial/per-share/600745"
```

---

## 第四步：策略分析

### 4.1 综合分析报告

**接口**: `GET /api/v1/analysis/report/{stock_code}`

**返回内容**:
- 技术面综合评分
- 基本面综合评分
- 投资建议

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/report/600745"
```

---

### 4.2 TD序列

**接口**: `GET /api/v1/analysis/strategy/td/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| buy_setup | 买入计数 |
| sell_setup | 卖出计数 |
| buy_countdown | 买入倒计时 |
| sell_countdown | 卖出倒计时 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/td/600745"
```

**分析要点**:
- 买入计数 ≥ 9 触发买入信号
- 卖出计数 ≥ 9 触发卖出信号

---

### 4.3 VCP形态

**接口**: `GET /api/v1/analysis/strategy/vcp/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| detected | 是否检测到VCP |
| stage | 当前阶段 |
| breakout_price | 突破价位 |
| support_price | 支撑价位 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/vcp/600745"
```

---

### 4.4 背离检测

**接口**: `GET /api/v1/analysis/strategy/divergence/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| macd_divergence | MACD背离 |
| rsi_divergence | RSI背离 |
| type | 顶背离/底背离 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/analysis/strategy/divergence/600745"
```

---

## 第五步：风险分析

### 5.1 波动率

**接口**: `GET /api/v1/risk/volatility/{stock_code}`

**返回字段**:
| 字段 | 说明 |
|------|------|
| daily_volatility | 日波动率 |
| annual_volatility | 年化波动率 |
| var_95 | 95%置信度VaR |
| max_drawdown | 最大回撤 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/risk/volatility/600745"
```

---

### 5.2 止损计算

**接口**: `POST /api/v1/risk/stop-loss/calculate`

**请求体**:
```json
{
  "stock_code": "600745",
  "buy_price": 32.0,
  "stop_loss_type": "percent",
  "stop_loss_value": 5.0
}
```

**返回字段**:
| 字段 | 说明 |
|------|------|
| stop_loss_price | 止损价 |
| risk_amount | 风险金额 |
| risk_ratio | 风险比例 |

**调用示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/risk/stop-loss/calculate" \
  -H "Content-Type: application/json" \
  -d '{"stock_code":"600745","buy_price":32.0,"stop_loss_type":"percent","stop_loss_value":5.0}'
```

---

## 第六步：新闻资讯

### 6.1 新闻列表

**接口**: `GET /api/v1/news/list?page=1&page_size=20`

**参数**:
| 参数 | 说明 |
|------|------|
| page | 页码 |
| page_size | 每页数量 |
| category | 分类 (可选) |
| start_date | 开始日期 (可选) |
| end_date | 结束日期 (可选) |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/news/list?page_size=10"
```

---

### 6.2 新闻搜索

**接口**: `GET /api/v1/news/search?query={keyword}`

**参数**:
| 参数 | 说明 |
|------|------|
| query | 搜索关键词 |
| page | 页码 |
| page_size | 每页数量 |

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/news/search?query=闻泰科技&page_size=10"
```

---

### 6.3 新闻详情

**接口**: `GET /api/v1/news/{news_id}`

**调用示例**:
```bash
curl "http://localhost:8000/api/v1/news/xxx"
```

---

## 第七步：市场情绪

### 7.1 涨跌排行

**接口**: `GET /api/v1/quote/top-list?type={gain|loss}`

**调用示例**:
```bash
# 涨幅榜
curl "http://localhost:8000/api/v1/quote/top-list?type=gain"

# 跌幅榜
curl "http://localhost:8000/api/v1/quote/top-list?type=loss"
```

**分析要点**:
- 涨跌家数对比
- 市场整体强弱判断

---

### 7.2 大盘指数 (待实现)

> ⚠️ 当前接口待开发

**建议接口**: `GET /api/v1/market/index`

**期望返回**:
| 指数 | 说明 |
|------|------|
| sh000001 | 上证指数 |
| sz399001 | 深证成指 |
| sz399006 | 创业板指 |

---

### 7.3 市场情绪指数 (待实现)

> ⚠️ 当前接口待开发

**建议接口**: `GET /api/v1/market/sentiment`

**期望返回**:
| 字段 | 说明 |
|------|------|
| up_count | 上涨家数 |
| down_count | 下跌家数 |
| flat_count | 平盘家数 |
| sentiment_score | 情绪指数 (0-100) |
| limit_up_count | 涨停家数 |
| limit_down_count | 跌停家数 |

---

## 一键调用脚本

```bash
#!/bin/bash
# 个股详细分析一键调用脚本
# 用法: ./analyze_stock.sh 600745

STOCK_CODE=$1

echo "=========================================="
echo "个股详细分析报告: $STOCK_CODE"
echo "=========================================="

echo ""
echo "=== 持仓数据 ==="
curl -s "http://localhost:8000/api/v1/portfolio/positions/$STOCK_CODE" | python3 -m json.tool

echo ""
echo "=== 实时行情 ==="
curl -s "http://localhost:8000/api/v1/quote/realtime/$STOCK_CODE" | python3 -m json.tool

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
echo "=== 资产负债表 (2024 Q3) ==="
curl -s "http://localhost:8000/api/v1/financial/balance-sheet/$STOCK_CODE?year=2024&quarter=3" | python3 -m json.tool

echo ""
echo "=== 利润表 (2024 Q3) ==="
curl -s "http://localhost:8000/api/v1/financial/income-statement/$STOCK_CODE?year=2024&quarter=3" | python3 -m json.tool

echo ""
echo "=== 现金流量表 (2024 Q3) ==="
curl -s "http://localhost:8000/api/v1/financial/cash-flow/$STOCK_CODE?year=2024&quarter=3" | python3 -m json.tool

echo ""
echo "=== 风险分析 ==="
curl -s "http://localhost:8000/api/v1/risk/volatility/$STOCK_CODE" | python3 -m json.tool
```

---

## 分析结论模板

### 技术面结论

```
1. 趋势判断: [上涨/下跌/震荡]
   - MA趋势: {ma_trend}
   - MACD信号: {macd_signal}

2. 动量分析:
   - RSI: {rsi} [超买/超卖/中性]
   - KDJ: {stoch_condition}

3. 支撑压力:
   - 支撑位: 布林下轨 {bb_lower}
   - 压力位: 布林上轨 {bb_upper}
```

### 基本面结论

```
1. 盈利能力:
   - ROE: {roe}%
   - 净利率: {net_margin}%

2. 成长性:
   - 营收增长: {revenue_growth}%
   - 利润增长: {profit_growth}%

3. 财务健康:
   - 资产负债率: {debt_ratio}%
   - 经营现金流: {operating_cash_flow}
```

### 综合建议

```
1. 持仓操作: [持有/加仓/减仓/清仓]
2. 止损价位: {stop_loss_price}
3. 目标价位: {target_price}
4. 风险等级: [高/中/低]
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-26 | 1.0 | 初版发布 |

---

## 相关文档

- [API接口文档](./API_REFERENCE.md)
- [数据源配置](./DATA_SOURCE_CONFIG.md)
- [技术指标说明](./TECHNICAL_INDICATORS.md)
