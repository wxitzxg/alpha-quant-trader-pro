---
name: 量化交易系统
description: Alpha Quant Trader Pro 量化交易系统 API，提供股票数据、技术分析、持仓管理、模拟交易、回测等功能。当用户询问技术分析（VCP、九转序列、背离、MACD、RSI）、持仓管理（仓位、交易记录、现金余额、收藏）、模拟交易（买卖、账户管理）、回测策略、风险控制（VaR、止损、波动率）、收益统计、市场数据同步、市场情绪（7维度评分）、股票推荐（短线/中长线策略）时触发。触发词包括：股票分析、持仓管理、回测、技术指标、模拟交易、风险控制、资金流向、财务数据、市场情绪、情绪评分、股票推荐、选股、短线策略、中长线策略、查行情、股价多少、K线图、分析一下这股票、看看指标、我买了什么、持仓情况、账户余额、模拟买入、模拟卖出、风险大不大、止损位、回测一下、财务状况、业绩怎么样、主力资金、龙虎榜、今天大盘怎么样、市场行情、帮我选股、推荐几只股票、有什么好票。
---

# Alpha Quant Trader Pro

量化交易系统 RESTful API，提供股票数据、技术分析、持仓管理、模拟交易和回测功能。

**API 基础路径**: `http://localhost:8000/api/v1`

## 快速开始

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

### 获取实时行情
```bash
curl http://localhost:8000/api/v1/quote/realtime/600519
```

### 技术分析
```bash
curl -X POST http://localhost:8000/api/v1/analysis/five-dimension \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'
```

## 核心功能模块

### 1. 数据获取
| 接口 | 说明 |
|------|------|
| `GET /stock/list` | 股票列表 |
| `GET /stock/info/{stock_code}` | 股票详情 |
| `GET /quote/realtime/{stock_code}` | 实时行情 |
| `POST /quote/batch` | 批量行情 |
| `GET /quote/top-list` | 涨跌幅排行 |
| `GET /kline/{stock_code}` | K线数据（从数据库读取） |
| `POST /kline/batch` | 批量K线 |
| `GET /kline/stats/{stock_code}` | K线统计 |

### 2. 股票市场同步
| 接口 | 说明 |
|------|------|
| `POST /market/stock/sync` | 同步股票列表 |
| `GET /market/stock/sync-status` | 获取股票同步状态 |
| `POST /market/kline/sync/{stock_code}` | 同步单股K线 |
| `POST /market/kline/sync-realtime` | 从实时行情同步今日K线 |

### 3. 技术指标
| 接口 | 说明 |
|------|------|
| `POST /indicators/base` | 基础指标 (MA/MACD/RSI/布林带) |
| `GET /indicators/base/{stock_code}` | GET方式获取基础指标 |
| `POST /indicators/vcp` | VCP 形态检测 |
| `GET /indicators/vcp/{stock_code}` | GET方式VCP检测 |
| `POST /indicators/td-sequential` | 九转序列 |
| `GET /indicators/td-sequential/{stock_code}` | GET方式TD序列 |
| `POST /indicators/divergence` | 背离检测 |
| `GET /indicators/divergence/{stock_code}` | GET方式背离检测 |
| `POST /indicators/zigzag` | ZigZag 转向 |
| `GET /indicators/zigzag/{stock_code}` | GET方式ZigZag |

### 4. 综合分析
| 接口 | 说明 |
|------|------|
| `POST /analysis/five-dimension` | 五维共振分析 |
| `GET /analysis/strategies/{stock_code}` | 三大策略综合分析 |
| `GET /analysis/indicator/{stock_code}` | 获取技术指标 |
| `GET /analysis/report/{stock_code}` | 完整分析报告 |
| `GET /analysis/strategy/vcp/{stock_code}` | VCP 策略分析 |
| `GET /analysis/strategy/td/{stock_code}` | 九转黄金坑策略分析 |
| `GET /analysis/strategy/divergence/{stock_code}` | 顶部背离策略分析 |

### 5. 持仓管理
| 接口 | 说明 |
|------|------|
| `GET /portfolio/account/summary` | 账户汇总 |
| `GET /portfolio/account/cash` | 现金余额 |
| `POST /portfolio/account/cash/add` | 充值 |
| `GET /portfolio/positions` | 持仓列表 |
| `GET /portfolio/positions/{stock_code}` | 单股持仓信息 |
| `POST /portfolio/positions/sync` | 同步持仓 |
| `POST /portfolio/trade/buy` | 买入 |
| `POST /portfolio/trade/sell` | 卖出 |
| `GET /portfolio/transactions` | 交易历史 |

### 6. 收藏管理
| 接口 | 说明 |
|------|------|
| `GET /portfolio/favorites` | 收藏列表 |
| `POST /portfolio/favorites/add` | 添加收藏 |
| `POST /portfolio/favorites/remove` | 移除收藏 |
| `POST /portfolio/favorites/update` | 更新收藏 |

### 7. 模拟交易
| 接口 | 说明 |
|------|------|
| `POST /simulation/account` | 创建账户 |
| `GET /simulation/accounts` | 账户列表 |
| `GET /simulation/account/{account_id}` | 账户详情 |
| `DELETE /simulation/account/{account_id}` | 删除账户 |
| `POST /simulation/buy` | 模拟买入 |
| `POST /simulation/sell` | 模拟卖出 |
| `GET /simulation/positions/{account_id}` | 持仓列表 |
| `GET /simulation/trades/{account_id}` | 交易历史 |

### 8. 风险控制
| 接口 | 说明 |
|------|------|
| `GET /risk/volatility/{stock_code}` | 波动率分析 |
| `POST /risk/stop-loss/calculate` | 止损位计算 |
| `GET /risk/diversification` | 分散度分析 |
| `GET /risk/portfolio/value-at-risk` | 组合 VaR |

### 9. 风险提示
| 接口 | 说明 |
|------|------|
| `GET /alerts/triggered` | 已触发预警 |
| `GET /alerts/stock/{stock_code}` | 单股预警 |
| `POST /alerts/portfolio/monitor` | 监控投资组合风险 |

### 10. 收益统计
| 接口 | 说明 |
|------|------|
| `GET /performance/account/summary` | 账户收益汇总 |
| `GET /performance/stock/{stock_code}` | 单股收益统计 |
| `GET /performance/history` | 历史收益曲线 |
| `GET /performance/compare` | 收益对比分析 |

### 11. 回测系统
| 接口 | 说明 |
|------|------|
| `POST /backtest/single` | 单股回测 |
| `POST /backtest/portfolio` | 组合回测 |
| `POST /backtest/compare` | 策略比较 |
| `GET /backtest/result/{task_id}` | 回测结果 |
| `POST /backtest/report` | 生成报告 |

### 12. 财务数据
| 接口 | 说明 |
|------|------|
| `GET /financial/indicators/{stock_code}` | 财务指标 |
| `GET /financial/balance-sheet/{stock_code}` | 资产负债表 |
| `GET /financial/income-statement/{stock_code}` | 利润表 |
| `GET /financial/cash-flow/{stock_code}` | 现金流量表 |
| `GET /financial/dupont/{stock_code}` | 杜邦分析 |
| `GET /financial/per-share/{stock_code}` | 每股指标 |

### 13. 资金流向
| 接口 | 说明 |
|------|------|
| `GET /fundflow/{stock_code}` | 资金流向 |
| `GET /fundflow/dragon-tiger/{stock_code}` | 龙虎榜 |

### 14. 新闻资讯
| 接口 | 说明 |
|------|------|
| `GET /news/list` | 新闻列表 |
| `GET /news/{news_id}` | 新闻详情 |
| `GET /news/search` | 搜索新闻 |

### 15. 市场情绪
| 接口 | 说明 |
|------|------|
| `GET /market/sentiment` | 市场情绪评分（7维度） |
| `GET /market/sentiment/stats` | 市场详细统计数据 |

### 16. 股票推荐
| 接口 | 说明 |
|------|------|
| `POST /recommendation/scan` | 扫描推荐股票 |
| `GET /recommendation/analyze/{stock_code}` | 分析单只股票 |
| `GET /recommendation/strategies` | 获取可用策略列表 |
| `GET /recommendation/config` | 获取推荐配置参数 |
| `PUT /recommendation/config` | 更新推荐配置 |
| `POST /recommendation/batch-scan` | 批量多策略扫描 |

## 支持的回测策略

| 策略 | 说明 |
|------|------|
| `five_dimension` | 五维共振策略 |
| `vcp` | VCP 形态策略 |
| `td_golden_pit` | 九转黄金坑策略 |
| `top_divergence` | 顶部背离策略 |

## 常用工作流

### 完整分析流程
```bash
# 1. 获取行情
curl http://localhost:8000/api/v1/quote/realtime/600519

# 2. 五维共振分析
curl -X POST http://localhost:8000/api/v1/analysis/five-dimension \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "days": 120}'

# 3. 三大策略分析
curl "http://localhost:8000/api/v1/analysis/strategies/600519?interval=1d&days=120"

# 4. 生成报告
curl "http://localhost:8000/api/v1/analysis/report/600519?interval=1d&days=120"
```

### 持仓管理流程
```bash
# 1. 充值
curl -X POST http://localhost:8000/api/v1/portfolio/account/cash/add \
  -H "Content-Type: application/json" \
  -d '{"amount": 100000}'

# 2. 查看现金余额
curl http://localhost:8000/api/v1/portfolio/account/cash

# 3. 买入
curl -X POST http://localhost:8000/api/v1/portfolio/trade/buy \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 100, "price": 1688.5}'

# 4. 查看持仓
curl http://localhost:8000/api/v1/portfolio/positions

# 5. 查看单股持仓
curl http://localhost:8000/api/v1/portfolio/positions/600519

# 6. 卖出
curl -X POST http://localhost:8000/api/v1/portfolio/trade/sell \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 100, "price": 1700.0}'
```

### 收藏管理流程
```bash
# 1. 添加收藏
curl -X POST http://localhost:8000/api/v1/portfolio/favorites/add \
  -H "Content-Type: application/json" \
  -d '{"symbol": "600519", "tag": "白酒", "note": "茅台"}'

# 2. 获取收藏列表
curl "http://localhost:8000/api/v1/portfolio/favorites?page=1&page_size=20"

# 3. 更新收藏
curl -X POST http://localhost:8000/api/v1/portfolio/favorites/update \
  -H "Content-Type: application/json" \
  -d '{"symbol": "600519", "tag": "消费", "note": "龙头股"}'

# 4. 移除收藏
curl -X POST http://localhost:8000/api/v1/portfolio/favorites/remove \
  -H "Content-Type: application/json" \
  -d '{"symbol": "600519"}'
```

### 模拟交易流程
```bash
# 1. 创建账户
curl -X POST http://localhost:8000/api/v1/simulation/account \
  -H "Content-Type: application/json" \
  -d '{"account_name": "测试账户", "initial_capital": 100000, "commission_rate": 0.0003}'

# 2. 获取账户列表
curl http://localhost:8000/api/v1/simulation/accounts

# 3. 买入
curl -X POST http://localhost:8000/api/v1/simulation/buy \
  -H "Content-Type: application/json" \
  -d '{"account_id": "acc_xxx", "symbol": "600519", "price": 1688.5, "quantity": 100}'

# 4. 查看持仓
curl http://localhost:8000/api/v1/simulation/positions/acc_xxx

# 5. 查看交易历史
curl http://localhost:8000/api/v1/simulation/trades/acc_xxx

# 6. 删除账户
curl -X DELETE http://localhost:8000/api/v1/simulation/account/acc_xxx
```

### 数据同步流程
```bash
# 1. 同步股票列表
curl -X POST http://localhost:8000/api/v1/market/stock/sync \
  -H "Content-Type: application/json" \
  -d '{"force_update": false}'

# 2. 查看同步状态
curl http://localhost:8000/api/v1/market/stock/sync-status

# 3. 同步单股K线
curl -X POST http://localhost:8000/api/v1/market/kline/sync/600519 \
  -H "Content-Type: application/json" \
  -d '{"interval": "1d", "force_update": false}'

# 4. 从实时行情同步今日K线
curl -X POST http://localhost:8000/api/v1/market/kline/sync-realtime \
  -H "Content-Type: application/json" \
  -d '{"stock_codes": ["600519", "000001"], "interval": "1d"}'
```

### 风险分析流程
```bash
# 1. 波动率分析
curl "http://localhost:8000/api/v1/risk/volatility/600519?days=30"

# 2. 止损位计算
curl -X POST http://localhost:8000/api/v1/risk/stop-loss/calculate \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "risk_tolerance": 0.05, "method": "atr"}'

# 3. 分散度分析
curl http://localhost:8000/api/v1/risk/diversification

# 4. 组合VaR
curl "http://localhost:8000/api/v1/risk/portfolio/value-at-risk?confidence_level=0.95"

# 5. 预警监控
curl http://localhost:8000/api/v1/alerts/triggered
```

### 回测流程
```bash
# 单股回测
curl -X POST http://localhost:8000/api/v1/backtest/single \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "strategy": "five_dimension",
    "config": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 100000
    }
  }'

# 查看结果
curl http://localhost:8000/api/v1/backtest/result/{task_id}
```

### 收益统计流程
```bash
# 1. 账户收益汇总
curl http://localhost:8000/api/v1/performance/account/summary

# 2. 单股收益统计
curl http://localhost:8000/api/v1/performance/stock/600519

# 3. 历史收益曲线
curl "http://localhost:8000/api/v1/performance/history?period=daily"

# 4. 收益对比分析
curl http://localhost:8000/api/v1/performance/compare
```

### 市场情绪分析流程
```bash
# 1. 获取市场情绪评分
curl "http://localhost:8000/api/v1/market/sentiment?use_realtime=true"

# 2. 排除创业板和科创板
curl "http://localhost:8000/api/v1/market/sentiment?exclude_gem=true&exclude_star=true"

# 3. 获取详细统计数据
curl "http://localhost:8000/api/v1/market/sentiment/stats"
```

### 股票推荐扫描流程
```bash
# 1. 短线策略扫描
curl -X POST http://localhost:8000/api/v1/recommendation/scan \
  -H "Content-Type: application/json" \
  -d '{"strategy_type": "short", "top_n": 10, "min_score": 60}'

# 2. 中长线策略扫描
curl -X POST http://localhost:8000/api/v1/recommendation/scan \
  -H "Content-Type: application/json" \
  -d '{"strategy_type": "long", "top_n": 10, "min_score": 65}'

# 3. 批量多策略扫描
curl -X POST http://localhost:8000/api/v1/recommendation/batch-scan \
  -H "Content-Type: application/json" \
  -d '{"strategies": ["short", "long"], "top_n_per_strategy": 5}'
```

### 单股深度分析流程
```bash
# 1. 分析单只股票（综合策略）
curl "http://localhost:8000/api/v1/recommendation/analyze/600519?strategy_type=both"

# 2. 仅短线分析
curl "http://localhost:8000/api/v1/recommendation/analyze/600519?strategy_type=short"

# 3. 查看可用策略
curl http://localhost:8000/api/v1/recommendation/strategies

# 4. 查看当前配置
curl http://localhost:8000/api/v1/recommendation/config
```

## 详细 API 参考

完整的接口文档请参阅 [api-reference.md](references/api-reference.md)。
