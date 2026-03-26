---
name: alpha-quant-trader-pro
description: Alpha Quant Trader Pro API integration for stock analysis, portfolio management, and trading simulation. Use when the user asks about stock technical analysis (VCP, TD Sequential, Divergence, MACD, RSI), portfolio management (positions, transactions, cash balance), trading simulation (buy/sell, account management), backtesting strategies, or risk management (VaR, stop-loss, volatility). Triggers on phrases like "股票分析", "持仓管理", "回测", "技术指标", "模拟交易", "风险控制".
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
curl http://localhost:8000/api/v1/quote/realtime/{stock_code}
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
| `GET /quote/realtime/{stock_code}` | 实时行情 |
| `POST /quote/batch` | 批量行情 |
| `GET /kline/{stock_code}` | K线数据 |
| `GET /financial/indicators/{stock_code}` | 财务指标 |

### 2. 技术分析
| 接口 | 说明 |
|------|------|
| `POST /indicators/base` | 基础指标 (MA/MACD/RSI/布林带) |
| `POST /indicators/vcp` | VCP 形态检测 |
| `POST /indicators/td-sequential` | 九转序列 |
| `POST /indicators/divergence` | 背离检测 |
| `POST /indicators/zigzag` | ZigZag 转向 |
| `POST /analysis/five-dimension` | 五维共振分析 |
| `GET /analysis/strategies/{stock_code}` | 三大策略综合分析 |
| `GET /analysis/report/{stock_code}` | 完整分析报告 |

### 3. 持仓管理
| 接口 | 说明 |
|------|------|
| `GET /portfolio/account/summary` | 账户汇总 |
| `GET /portfolio/positions` | 持仓列表 |
| `POST /portfolio/trade/buy` | 买入 |
| `POST /portfolio/trade/sell` | 卖出 |
| `POST /portfolio/account/cash/add` | 充值 |
| `POST /portfolio/positions/sync` | 同步持仓 |
| `GET /portfolio/transactions` | 交易历史 |

### 4. 模拟交易
| 接口 | 说明 |
|------|------|
| `POST /simulation/account` | 创建账户 |
| `GET /simulation/account/{account_id}` | 账户详情 |
| `POST /simulation/buy` | 模拟买入 |
| `POST /simulation/sell` | 模拟卖出 |
| `GET /simulation/positions/{account_id}` | 持仓列表 |

### 5. 风险控制
| 接口 | 说明 |
|------|------|
| `GET /risk/volatility/{stock_code}` | 波动率分析 |
| `POST /risk/stop-loss/calculate` | 止损位计算 |
| `GET /risk/diversification` | 分散度分析 |
| `GET /risk/portfolio/value-at-risk` | 组合 VaR |
| `GET /alerts/triggered` | 已触发预警 |
| `GET /alerts/stock/{stock_code}` | 单股预警 |

### 6. 回测系统
| 接口 | 说明 |
|------|------|
| `POST /backtest/single` | 单股回测 |
| `POST /backtest/portfolio` | 组合回测 |
| `POST /backtest/compare` | 策略比较 |
| `GET /backtest/result/{task_id}` | 回测结果 |
| `POST /backtest/report` | 生成报告 |

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

# 2. 买入
curl -X POST http://localhost:8000/api/v1/portfolio/trade/buy \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 100, "price": 1688.5, "trade_type": "buy"}'

# 3. 查看持仓
curl http://localhost:8000/api/v1/portfolio/positions

# 4. 卖出
curl -X POST http://localhost:8000/api/v1/portfolio/trade/sell \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 100, "price": 1700.0, "trade_type": "sell"}'
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

## 详细 API 参考

完整的接口文档请参阅 [api-reference.md](references/api-reference.md)。
