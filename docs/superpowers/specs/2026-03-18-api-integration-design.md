# API 集成设计文档

**日期:** 2026-03-18
**版本:** 1.0.0
**作者:** Claude Code
**状态:** 待批准

---

## 📋 目录

1. [概述](#概述)
2. [设计目标](#设计目标)
3. [架构设计](#架构设计)
4. [API 路由设计](#api-路由设计)
5. [数据模型](#数据模型)
6. [错误处理](#错误处理)
7. [实现细节](#实现细节)
8. [测试策略](#测试策略)
9. [部署计划](#部署计划)

---

## 概述

### 背景

当前项目存在以下问题：
- 技术分析有服务层但路由未集成
- 回测系统完整但完全没有 API
- 收益统计只有空壳路由
- 模拟交易完全缺失

### 目标

整合所有现有模块，提供完整的 API 访问接口，确保前端可以调用所有后端功能。

### 范围

- ✅ 启用并完善现有路由
- ✅ 为回测系统添加 API
- ✅ 创建模拟交易模块及 API
- ✅ 完善收益统计服务层
- ❌ 不修改现有服务层逻辑
- ❌ 不重构现有模块

---

## 设计目标

### 功能完整性

1. **技术分析** - 暴露所有分析功能
   - 五维共振分析
   - 技术指标查询
   - 三大策略信号
   - 完整报告生成

2. **回测系统** - 完整的回测功能
   - 单股票回测
   - 多股票组合回测
   - 策略比较
   - 报告生成（JSON + 文本 + HTML）

3. **模拟交易** - 基础交易功能
   - 虚拟账户管理
   - 买卖交易
   - 持仓查询
   - 盈亏计算

4. **收益统计** - 完整的绩效分析
   - 账户收益汇总
   - 绩效指标
   - 交易统计

### 设计原则

1. **最小改动** - 复用现有服务层，只添加路由和连接
2. **清晰边界** - 每个功能模块独立路由
3. **统一响应** - 所有 API 返回统一格式
4. **易测试** - 每个端点都有明确的输入输出

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│                  (api_server.main)                  │
└─────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
│   Routers     │     │  Middleware   │     │  Exception    │
│  (api_server/ │     │   (RateLimit, │     │  Handlers     │
│   routers/)   │     │   Auth, Log)  │     │               │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        │  ┌────────────────────────────────────────────────┐
        └──┤                    Services                    │
           │  (api_server/services/, backtest/, etc.)       │
           └────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
│  Core Logic   │     │  Data Access  │     │   External    │
│  (Engines,    │     │  (Repository, │     │   Sources     │
│  Strategies)  │     │   DataFeed)   │     │   (AkShare)   │
└───────────────┘     └───────────────┘     └───────────────┘
```

### 模块关系

```
api_server/
├── main.py                 # FastAPI 应用入口（集成所有路由）
├── routers/                # 路由层
│   ├── analysis.py        # 技术分析路由
│   ├── backtest.py        # 回测路由（新建）
│   ├── simulation.py      # 模拟交易路由（新建）
│   ├── performance.py     # 收益统计路由
│   └── ...                # 现有路由
├── services/               # 服务层
│   ├── analysis_service.py  # 连接 technical_analysis 模块
│   ├── backtest_service.py  # 连接 backtest 模块
│   ├── simulation_service.py # 模拟交易服务（新建）
│   └── ...                # 现有服务
└── models/                 # API 数据模型
    ├── analysis.py        # 技术分析模型
    ├── backtest.py        # 回测模型（新建）
    ├── simulation.py      # 模拟交易模型（新建）
    └── performance.py     # 收益统计模型

backtest/                   # 现有回测模块（不修改）
technical_analysis/         # 现有技术分析模块（不修改）
```

---

## API 路由设计

### 1. 技术分析 API (`/api/v1/analysis`)

#### 1.1 五维共振分析
**端点:** `POST /api/v1/analysis/five-dimension`
**权限:** 公开
**描述:** 执行完整的五维共振技术分析

**请求:**
```json
{
  "symbol": "600519",
  "interval": "1d",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "days": 120
}
```

**响应:**
```json
{
  "success": true,
  "message": "五维共振分析完成",
  "data": {
    "symbol": "600519",
    "total_score": 85,
    "max_score": 100,
    "score_percentage": 85.0,
    "action": "STRONG_BUY",
    "position_suggestion": 0.2,
    "confidence_level": "S",
    "dimension_scores": {
      "D1": 18,
      "D2": 28,
      "D3": 18,
      "D4": 9,
      "D5": 12
    },
    "dimension_details": {...},
    "analysis_date": "2024-12-31"
  }
}
```

#### 1.2 三大策略分析
**端点:** `GET /api/v1/analysis/strategies/{symbol}`
**权限:** 公开
**描述:** 使用 VCP、九转、背离三大策略进行分析

**请求:**
```
GET /api/v1/analysis/strategies/600519?interval=1d&days=120
```

**响应:**
```json
{
  "success": true,
  "message": "策略分析完成",
  "data": {
    "symbol": "600519",
    "strategies": {
      "vcp_breakout": {
        "signal": "buy",
        "score": 85,
        "confidence": 0.85,
        "pivot_price": 1800.0,
        "stop_loss": 1700.0,
        "take_profit": 2000.0
      },
      "td_golden_pit": {
        "signal": "hold",
        "score": 65,
        "buy_count": 7,
        "sell_count": 0
      },
      "top_divergence": {
        "signal": "sell",
        "score": 45,
        "detected": true,
        "confidence": 0.75
      }
    }
  }
}
```

#### 1.3 技术指标
**端点:** `GET /api/v1/analysis/indicators/{symbol}`
**权限:** 公开
**描述:** 获取技术指标数据（MA、MACD、RSI、BOLL）

**请求:**
```
GET /api/v1/analysis/indicators/600519?indicator=macd&days=60
```

**响应:**
```json
{
  "success": true,
  "message": "指标数据获取成功",
  "data": {
    "symbol": "600519",
    "indicator_name": "macd",
    "current_price": 1850.5,
    "latest_signals": {
      "macd": {
        "value": 25.8,
        "signal": "buy",
        "histogram": 5.2
      },
      "rsi": {
        "value": 65.3,
        "signal": "neutral"
      },
      "ma": {
        "ma5": 1830.0,
        "ma10": 1800.0,
        "ma20": 1750.0,
        "trend": "bullish"
      }
    }
  }
}
```

#### 1.4 完整分析报告
**端点:** `GET /api/v1/analysis/report/{symbol}`
**权限:** 公开
**描述:** 生成完整的文本分析报告

**请求:**
```
GET /api/v1/analysis/report/600519?interval=1d&days=120
```

**响应:**
```json
{
  "success": true,
  "message": "报告生成成功",
  "data": {
    "symbol": "600519",
    "report_type": "text",
    "content": "【五维共振分析】\n总分: 85/100 (S级)\n建议: 强烈买入，仓位20%\n...\n【策略信号概要】\nVCP 突破: buy (得分: 85)\n九转黄金坑: hold (得分: 65)\n顶部背离: sell (得分: 45)"
  }
}
```

---

### 2. 回测系统 API (`/api/v1/backtest`)

#### 2.1 单股票回测
**端点:** `POST /api/v1/backtest/single`
**权限:** 公开
**描述:** 对单只股票执行回测

**请求:**
```json
{
  "symbol": "600519",
  "strategy": "five_dimension",  // five_dimension, vcp, td_golden_pit, top_divergence
  "config": {
    "initial_capital": 100000,
    "commission_rate": 0.00025,
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "interval": "1d",
    "position_size": 0.1,
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.2
  }
}
```

**响应:**
```json
{
  "success": true,
  "message": "回测完成",
  "data": {
    "task_id": "bt_600519_1710758400",
    "symbol": "600519",
    "strategy": "five_dimension",
    "status": "completed",
    "result_summary": {
      "total_return": 45.8,
      "annual_return": 28.5,
      "max_drawdown": 12.3,
      "sharpe_ratio": 1.45,
      "win_rate": 68.2,
      "total_trades": 25
    }
  }
}
```

#### 2.2 多股票组合回测
**端点:** `POST /api/v1/backtest/portfolio`
**权限:** 公开
**描述:** 对多股票组合执行回测

**请求:**
```json
{
  "symbols": ["600519", "000001", "300750", "600036"],
  "strategy": "five_dimension",
  "config": {
    "initial_capital": 1000000,
    "commission_rate": 0.00025,
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "interval": "1d",
    "position_size": 0.1,
    "max_positions": 5
  }
}
```

**响应:**
```json
{
  "success": true,
  "message": "组合回测完成",
  "data": {
    "task_id": "bt_portfolio_1710758401",
    "symbols_count": 4,
    "strategy": "five_dimension",
    "status": "completed",
    "results": {
      "600519": {
        "annual_return": 28.5,
        "sharpe_ratio": 1.45
      },
      "000001": {
        "annual_return": 22.3,
        "sharpe_ratio": 1.28
      },
      ...
    },
    "portfolio_summary": {
      "total_return": 35.2,
      "annual_return": 24.8,
      "max_drawdown": 15.6,
      "sharpe_ratio": 1.32
    }
  }
}
```

#### 2.3 策略比较
**端点:** `POST /api/v1/backtest/compare`
**权限:** 公开
**描述:** 比较多个策略在同一股票上的表现

**请求:**
```json
{
  "symbol": "600519",
  "strategies": ["five_dimension", "vcp", "td_golden_pit"],
  "config": {
    "initial_capital": 100000,
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "interval": "1d"
  }
}
```

**响应:**
```json
{
  "success": true,
  "message": "策略比较完成",
  "data": {
    "symbol": "600519",
    "comparison": {
      "five_dimension": {
        "annual_return": 28.5,
        "sharpe_ratio": 1.45,
        "max_drawdown": 12.3,
        "win_rate": 68.2
      },
      "vcp": {
        "annual_return": 25.8,
        "sharpe_ratio": 1.38,
        "max_drawdown": 14.5,
        "win_rate": 65.4
      },
      "td_golden_pit": {
        "annual_return": 22.3,
        "sharpe_ratio": 1.25,
        "max_drawdown": 16.8,
        "win_rate": 62.1
      }
    },
    "best_strategy": "five_dimension",
    "recommendation": "五维共振策略表现最优"
  }
}
```

#### 2.4 获取回测结果
**端点:** `GET /api/v1/backtest/result/{task_id}`
**权限:** 公开
**描述:** 获取回测任务的完整结果

**请求:**
```
GET /api/v1/backtest/result/bt_600519_1710758400
```

**响应:**
```json
{
  "success": true,
  "message": "回测结果获取成功",
  "data": {
    "task_id": "bt_600519_1710758400",
    "symbol": "600519",
    "strategy": "five_dimension",
    "config": {...},
    "performance": {
      "total_return": 45.8,
      "annual_return": 28.5,
      "volatility": 18.2,
      "max_drawdown": 12.3,
      "sharpe_ratio": 1.45,
      "sortino_ratio": 1.85,
      "calmar_ratio": 2.32,
      "total_trades": 25,
      "winning_trades": 17,
      "losing_trades": 8,
      "win_rate": 68.2,
      "profit_factor": 1.85,
      "avg_holding_days": 15.5
    },
    "trades": [...],
    "equity_curve": [...],
    "dates": [...]
  }
}
```

#### 2.5 生成回测报告
**端点:** `POST /api/v1/backtest/report`
**权限:** 公开
**描述:** 生成回测报告（支持 JSON/文本/HTML 格式）

**请求:**
```json
{
  "task_id": "bt_600519_1710758400",
  "format": "html"  // json, text, html
}
```

**响应 (JSON):**
```json
{
  "success": true,
  "message": "报告生成成功",
  "data": {
    "task_id": "bt_600519_1710758400",
    "format": "json",
    "report": {
      "summary": {...},
      "performance": {...},
      "trades": [...]
    }
  }
}
```

**响应 (HTML/文本):**
```json
{
  "success": true,
  "message": "报告生成成功",
  "data": {
    "task_id": "bt_600519_1710758400",
    "format": "html",
    "report_content": "<!DOCTYPE html>...",
    "download_url": "/api/v1/backtest/report/download/bt_600519_1710758400.html"
  }
}
```

---

### 3. 模拟交易 API (`/api/v1/simulation`)

#### 3.1 创建虚拟账户
**端点:** `POST /api/v1/simulation/account`
**权限:** 公开
**描述:** 创建新的模拟交易账户

**请求:**
```json
{
  "account_name": "模拟账户1",
  "initial_capital": 100000,
  "commission_rate": 0.00025
}
```

**响应:**
```json
{
  "success": true,
  "message": "账户创建成功",
  "data": {
    "account_id": "sim_1710758402",
    "account_name": "模拟账户1",
    "initial_capital": 100000,
    "current_balance": 100000,
    "available_cash": 100000,
    "total_value": 100000,
    "created_at": "2026-03-18T10:00:00Z"
  }
}
```

#### 3.2 获取账户信息
**端点:** `GET /api/v1/simulation/account/{account_id}`
**权限:** 公开
**描述:** 获取模拟账户详细信息

**请求:**
```
GET /api/v1/simulation/account/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "账户信息获取成功",
  "data": {
    "account_id": "sim_1710758402",
    "account_name": "模拟账户1",
    "initial_capital": 100000,
    "current_balance": 98500,
    "available_cash": 88500,
    "total_value": 105000,
    "floating_pl": 5000,
    "total_return": 5.0,
    "positions_count": 2,
    "created_at": "2026-03-18T10:00:00Z",
    "updated_at": "2026-03-18T14:30:00Z"
  }
}
```

#### 3.3 买入股票
**端点:** `POST /api/v1/simulation/buy`
**权限:** 公开
**描述:** 执行买入交易

**请求:**
```json
{
  "account_id": "sim_1710758402",
  "symbol": "600519",
  "price": 1850.0,
  "quantity": 100,
  "order_type": "market"  // market, limit
}
```

**响应:**
```json
{
  "success": true,
  "message": "买入成功",
  "data": {
    "trade_id": "trade_1710758403",
    "account_id": "sim_1710758402",
    "symbol": "600519",
    "action": "buy",
    "price": 1850.0,
    "quantity": 100,
    "amount": 185000,
    "commission": 46.25,
    "total_cost": 185046.25,
    "timestamp": "2026-03-18T14:35:00Z",
    "account_balance": 88453.75
  }
}
```

#### 3.4 卖出股票
**端点:** `POST /api/v1/simulation/sell`
**权限:** 公开
**描述:** 执行卖出交易

**请求:**
```json
{
  "account_id": "sim_1710758402",
  "symbol": "600519",
  "price": 1900.0,
  "quantity": 50,
  "order_type": "market"
}
```

**响应:**
```json
{
  "success": true,
  "message": "卖出成功",
  "data": {
    "trade_id": "trade_1710758404",
    "account_id": "sim_1710758402",
    "symbol": "600519",
    "action": "sell",
    "price": 1900.0,
    "quantity": 50,
    "amount": 95000,
    "commission": 23.75,
    "pnl": 2450.0,
    "total_revenue": 94976.25,
    "timestamp": "2026-03-18T15:00:00Z",
    "account_balance": 97950.0
  }
}
```

#### 3.5 获取持仓列表
**端点:** `GET /api/v1/simulation/positions/{account_id}`
**权限:** 公开
**描述:** 获取账户所有持仓

**请求:**
```
GET /api/v1/simulation/positions/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "持仓列表获取成功",
  "data": {
    "account_id": "sim_1710758402",
    "positions": [
      {
        "symbol": "600519",
        "quantity": 50,
        "cost_price": 1850.0,
        "market_price": 1900.0,
        "market_value": 95000,
        "floating_pl": 2500,
        "floating_pl_pct": 2.7,
        "entry_date": "2026-03-18T14:35:00Z"
      },
      {
        "symbol": "000001",
        "quantity": 200,
        "cost_price": 15.5,
        "market_price": 15.8,
        "market_value": 3160,
        "floating_pl": 60,
        "floating_pl_pct": 1.9,
        "entry_date": "2026-03-18T13:20:00Z"
      }
    ],
    "total_market_value": 98160,
    "total_floating_pl": 2560,
    "total_floating_pl_pct": 2.6
  }
}
```

#### 3.6 获取交易历史
**端点:** `GET /api/v1/simulation/trades/{account_id}`
**权限:** 公开
**描述:** 获取账户交易历史

**请求:**
```
GET /api/v1/simulation/trades/sim_1710758402?limit=20
```

**响应:**
```json
{
  "success": true,
  "message": "交易历史获取成功",
  "data": {
    "account_id": "sim_1710758402",
    "trades": [
      {
        "trade_id": "trade_1710758403",
        "symbol": "600519",
        "action": "buy",
        "price": 1850.0,
        "quantity": 100,
        "amount": 185000,
        "commission": 46.25,
        "timestamp": "2026-03-18T14:35:00Z"
      },
      {
        "trade_id": "trade_1710758404",
        "symbol": "600519",
        "action": "sell",
        "price": 1900.0,
        "quantity": 50,
        "amount": 95000,
        "commission": 23.75,
        "pnl": 2450.0,
        "timestamp": "2026-03-18T15:00:00Z"
      }
    ],
    "total_count": 2,
    "winning_trades": 1,
    "losing_trades": 0,
    "total_pnl": 2450.0
  }
}
```

#### 3.7 删除账户
**端点:** `DELETE /api/v1/simulation/account/{account_id}`
**权限:** 公开
**描述:** 删除模拟账户

**请求:**
```
DELETE /api/v1/simulation/account/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "账户删除成功",
  "data": {
    "account_id": "sim_1710758402",
    "deleted_at": "2026-03-18T15:30:00Z"
  }
}
```

---

### 4. 收益统计 API (`/api/v1/performance`)

#### 4.1 账户收益汇总
**端点:** `GET /api/v1/performance/account/{account_id}`
**权限:** 公开
**描述:** 获取模拟账户的收益统计

**请求:**
```
GET /api/v1/performance/account/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "收益汇总获取成功",
  "data": {
    "account_id": "sim_1710758402",
    "metrics": {
      "total_return": 5.0,
      "total_return_amount": 5000,
      "annualized_return": 18.25,
      "max_drawdown": 3.2,
      "volatility": 12.5,
      "sharpe_ratio": 1.25,
      "sortino_ratio": 1.45,
      "calmar_ratio": 5.7,
      "win_rate": 66.7,
      "profit_factor": 1.8,
      "avg_holding_days": 7.5,
      "total_trades": 3,
      "winning_trades": 2,
      "losing_trades": 1
    },
    "time_period": {
      "start_date": "2026-03-18T10:00:00Z",
      "end_date": "2026-03-18T15:30:00Z",
      "days": 0.23
    }
  }
}
```

#### 4.2 持仓收益分析
**端点:** `GET /api/v1/performance/positions/{account_id}`
**权限:** 公开
**描述:** 分析持仓的收益表现

**请求:**
```
GET /api/v1/performance/positions/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "持仓收益分析完成",
  "data": {
    "account_id": "sim_1710758402",
    "positions_analysis": [
      {
        "symbol": "600519",
        "quantity": 50,
        "cost_basis": 92500,
        "current_value": 95000,
        "unrealized_pl": 2500,
        "unrealized_pl_pct": 2.7,
        "days_held": 1,
        "annualized_return": 985.5
      },
      {
        "symbol": "000001",
        "quantity": 200,
        "cost_basis": 3100,
        "current_value": 3160,
        "unrealized_pl": 60,
        "unrealized_pl_pct": 1.9,
        "days_held": 1,
        "annualized_return": 693.5
      }
    ],
    "summary": {
      "total_cost_basis": 95600,
      "total_current_value": 98160,
      "total_unrealized_pl": 2560,
      "total_unrealized_pl_pct": 2.68
    }
  }
}
```

#### 4.3 交易绩效分析
**端点:** `GET /api/v1/performance/trades/{account_id}`
**权限:** 公开
**描述:** 分析交易的绩效表现

**请求:**
```
GET /api/v1/performance/trades/sim_1710758402
```

**响应:**
```json
{
  "success": true,
  "message": "交易绩效分析完成",
  "data": {
    "account_id": "sim_1710758402",
    "trade_analysis": {
      "total_trades": 3,
      "buy_trades": 2,
      "sell_trades": 1,
      "winning_trades": 2,
      "losing_trades": 1,
      "win_rate": 66.7,
      "avg_win": 2475.0,
      "avg_loss": -50.0,
      "profit_factor": 1.8,
      "largest_win": 2500.0,
      "largest_loss": -50.0,
      "avg_holding_days": 7.5,
      "total_commission": 120.0
    },
    "realized_pl": 2450.0,
    "commission_paid": 120.0,
    "net_profit": 2330.0
  }
}
```

---

## 数据模型

### 1. 技术分析模型

```python
# api_server/models/analysis.py (现有)

class FiveDimensionResult(BaseModel):
    total_score: int
    max_score: int = 100
    score_percentage: float
    action: str  # STRONG_BUY/BUY/HOLD/WAIT
    position_suggestion: float
    confidence_level: str  # S/A/B/C
    dimension_scores: Dict[str, int]
    dimension_details: Dict[str, Dict]

class StrategySignal(BaseModel):
    strategy_name: str
    signal: str  # buy/sell/hold
    strength: float
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timestamp: datetime

class IndicatorResult(BaseModel):
    indicator_name: str
    values: List[float]
    dates: List[str]
    parameters: Optional[Dict]

class AnalysisRequest(BaseModel):
    symbol: str
    interval: str = "1d"
    start_date: Optional[str]
    end_date: Optional[str]
    days: int = 120
```

### 2. 回测模型

```python
# api_server/models/backtest.py (新建)

class BacktestConfigRequest(BaseModel):
    initial_capital: float = 100000.0
    commission_rate: float = 0.00025
    slippage_rate: float = 0.001
    stamp_duty_rate: float = 0.001
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    interval: str = "1d"
    position_size: float = 0.1
    max_positions: int = 5
    stop_loss_pct: float = 0.08
    take_profit_pct: float = 0.2

class BacktestTask(BaseModel):
    task_id: str
    symbol: Optional[str]
    symbols: Optional[List[str]]
    strategy: str
    status: str  # pending/running/completed/failed
    created_at: datetime
    completed_at: Optional[datetime]

class BacktestResultResponse(BaseModel):
    task_id: str
    symbol: Optional[str]
    strategy: str
    config: BacktestConfigRequest
    performance: PerformanceMetrics
    trades: List[Trade]
    equity_curve: List[float]
    dates: List[str]

class PerformanceMetrics(BaseModel):
    total_return: float
    annual_return: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_holding_days: float

class Trade(BaseModel):
    trade_id: int
    symbol: str
    date: str
    action: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float]

class ReportRequest(BaseModel):
    task_id: str
    format: str = "json"  # json, text, html
```

### 3. 模拟交易模型

```python
# api_server/models/simulation.py (新建)

class SimulationAccountCreate(BaseModel):
    account_name: str
    initial_capital: float = 100000.0
    commission_rate: float = 0.00025

class SimulationAccount(BaseModel):
    account_id: str
    account_name: str
    initial_capital: float
    current_balance: float
    available_cash: float
    total_value: float
    floating_pl: float
    total_return: float
    positions_count: int
    created_at: datetime
    updated_at: datetime

class TradeOrder(BaseModel):
    account_id: str
    symbol: str
    price: float
    quantity: int
    order_type: str = "market"  # market, limit

class TradeResult(BaseModel):
    trade_id: str
    account_id: str
    symbol: str
    action: str  # buy, sell
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float]
    total_cost: Optional[float]
    total_revenue: Optional[float]
    timestamp: datetime
    account_balance: float

class Position(BaseModel):
    symbol: str
    quantity: int
    cost_price: float
    market_price: float
    market_value: float
    floating_pl: float
    floating_pl_pct: float
    entry_date: str

class PositionsResponse(BaseModel):
    account_id: str
    positions: List[Position]
    total_market_value: float
    total_floating_pl: float
    total_floating_pl_pct: float
```

### 4. 收益统计模型

```python
# api_server/models/performance.py (现有+扩展)

class PerformanceMetrics(BaseModel):
    total_return: float
    total_return_amount: float
    annualized_return: float
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_holding_days: float
    total_trades: int
    winning_trades: int
    losing_trades: int

class PerformanceResponse(BaseModel):
    account_id: str
    metrics: PerformanceMetrics
    time_period: Optional[Dict]
```

---

## 错误处理

### 统一错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "股票代码无效或不存在",
    "details": {
      "symbol": "INVALID_CODE",
      "reason": "未找到该股票的数据"
    }
  }
}
```

### 错误代码定义

| 错误代码 | 说明 | HTTP 状态码 |
|---------|------|------------|
| INVALID_SYMBOL | 股票代码无效 | 400 |
| DATA_INSUFFICIENT | 数据不足 | 400 |
| ACCOUNT_NOT_FOUND | 账户不存在 | 404 |
| INSUFFICIENT_FUNDS | 余额不足 | 400 |
| INVALID_STRATEGY | 策略名称无效 | 400 |
| BACKTEST_FAILED | 回测失败 | 500 |
| INVALID_CONFIG | 配置参数无效 | 400 |

---

## 实现细节

### 1. 路由集成（main.py）

```python
# api_server/main.py

from .routers import (
    health_router,
    data_source_router,
    stock_market_router,
    portfolio_router,
    analysis_router,      # 已有，需要启用
    risk_control_router,
    performance_router,   # 已有，需要完善
    alerts_router,
    backtest_router,      # 新建
    simulation_router     # 新建
)

# 注册路由
app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])
app.include_router(data_source_router, prefix="/api/v1", tags=["数据源聚合"])
app.include_router(stock_market_router, prefix="/api/v1", tags=["股票市场"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["持仓管理"])
app.include_router(analysis_router, prefix="/api/v1", tags=["技术分析"])        # 启用
app.include_router(risk_control_router, prefix="/api/v1", tags=["风险控制"])
app.include_router(performance_router, prefix="/api/v1", tags=["收益统计"])     # 启用
app.include_router(alerts_router, prefix="/api/v1", tags=["风险提示"])
app.include_router(backtest_router, prefix="/api/v1", tags=["回测系统"])        # 新增
app.include_router(simulation_router, prefix="/api/v1", tags=["模拟交易"])      # 新增
```

### 2. 技术分析路由完善

```python
# api_server/routers/analysis.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database import get_db_session
from technical_analysis.services import AnalysisService

analysis_router = APIRouter()

@analysis_router.post("/analysis/five-dimension")
async def analyze_five_dimension(
    request: AnalysisRequest,
    db: Session = Depends(get_db_session)
):
    """五维共振分析"""
    service = AnalysisService(db)
    result = service.analyze_stock(
        symbol=request.symbol,
        interval=request.interval,
        start_date=request.start_date,
        end_date=request.end_date,
        days=request.days
    )
    return APIResponse(data=result, message="五维共振分析完成")
```

### 3. 回测路由实现

```python
# api_server/routers/backtest.py (新建)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database import get_db_session
from backtest.services import BacktestService
from backtest.config import BacktestConfig
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)

backtest_router = APIRouter()

STRATEGY_MAP = {
    "five_dimension": FiveDimensionStrategy,
    "vcp": VCPBreakoutStrategy,
    "td_golden_pit": TDGoldenPitStrategy,
    "top_divergence": TopDivergenceStrategy
}

@backtest_router.post("/backtest/single")
async def run_single_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db_session)
):
    """单股票回测"""
    # 创建配置
    config = BacktestConfig(**request.config.dict())

    # 创建策略
    strategy_class = STRATEGY_MAP.get(request.strategy)
    if not strategy_class:
        raise HTTPException(status_code=400, detail="无效的策略名称")

    service = BacktestService(db)
    analysis_service = AnalysisService(db) if request.strategy == "five_dimension" else None

    if request.strategy == "five_dimension":
        strategy = strategy_class(analysis_service)
    else:
        strategy = strategy_class()

    # 运行回测
    result = service.run_single_stock_backtest(
        symbol=request.symbol,
        strategy=strategy,
        config=config
    )

    return APIResponse(data=result, message="回测完成")
```

### 4. 模拟交易服务实现

```python
# api_server/services/simulation_service.py (新建)

from typing import Dict, List
from datetime import datetime
import uuid

class SimulationAccount:
    """模拟账户"""

    def __init__(
        self,
        account_name: str,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025
    ):
        self.account_id = f"sim_{int(datetime.now().timestamp())}"
        self.account_name = account_name
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.available_cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def buy(self, symbol: str, price: float, quantity: int) -> Trade:
        """买入"""
        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_cost = total_amount + commission

        if self.available_cash < total_cost:
            raise ValueError(f"余额不足，需要 {total_cost:.2f}，当前可用 {self.available_cash:.2f}")

        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_cost_price = (pos.cost_price * pos.quantity + total_amount) / new_quantity
            pos.quantity = new_quantity
            pos.cost_price = new_cost_price
        else:
            self.positions[symbol] = Position(symbol, quantity, price)

        # 更新账户
        self.available_cash -= total_cost
        self.current_balance -= total_cost

        # 记录交易
        trade = Trade(self.account_id, symbol, "buy", price, quantity, commission)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

    def sell(self, symbol: str, price: float, quantity: int) -> Trade:
        """卖出"""
        if symbol not in self.positions:
            raise ValueError(f"没有持仓 {symbol}")

        pos = self.positions[symbol]
        if pos.quantity < quantity:
            raise ValueError(f"持仓不足，当前 {pos.quantity}，卖出 {quantity}")

        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_revenue = total_amount - commission

        # 计算盈亏
        pnl = (price - pos.cost_price) * quantity

        # 更新持仓
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]

        # 更新账户
        self.available_cash += total_revenue
        self.current_balance += total_revenue

        # 记录交易
        trade = Trade(self.account_id, symbol, "sell", price, quantity, commission, pnl)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

class SimulationService:
    """模拟交易服务"""

    def __init__(self):
        self.accounts: Dict[str, SimulationAccount] = {}

    def create_account(self, account_name: str, initial_capital: float) -> SimulationAccount:
        """创建账户"""
        account = SimulationAccount(account_name, initial_capital)
        self.accounts[account.account_id] = account
        return account

    def get_account(self, account_id: str) -> SimulationAccount:
        """获取账户"""
        if account_id not in self.accounts:
            raise ValueError(f"账户 {account_id} 不存在")
        return self.accounts[account_id]

    def delete_account(self, account_id: str):
        """删除账户"""
        if account_id in self.accounts:
            del self.accounts[account_id]
```

### 5. 收益统计服务实现

```python
# api_server/services/performance_service.py (新建)

from typing import List
from api_server.services.simulation_service import SimulationAccount

class PerformanceService:
    """收益统计服务"""

    def calculate_metrics(self, account: SimulationAccount) -> Dict:
        """计算绩效指标"""
        # 总收益
        total_return = account.current_balance - account.initial_capital
        total_return_pct = (total_return / account.initial_capital) * 100

        # 年化收益（假设为 1 天）
        days = (datetime.now() - account.created_at).days or 1
        annualized_return = total_return_pct * (365 / days)

        # 胜率
        winning_trades = sum(1 for t in account.trades if t.pnl and t.pnl > 0)
        total_trades = len([t for t in account.trades if t.action == "sell"])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 盈亏比
        profits = [t.pnl for t in account.trades if t.pnl and t.pnl > 0]
        losses = [abs(t.pnl) for t in account.trades if t.pnl and t.pnl < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = avg_profit / avg_loss if avg_loss > 0 else 0

        return {
            "total_return": total_return_pct,
            "total_return_amount": total_return,
            "annualized_return": annualized_return,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades
        }
```

---

## 测试策略

### 单元测试覆盖

1. **技术分析路由**
   - [ ] 五维共振分析
   - [ ] 三大策略分析
   - [ ] 技术指标查询
   - [ ] 完整报告生成

2. **回测路由**
   - [ ] 单股票回测
   - [ ] 多股票组合回测
   - [ ] 策略比较
   - [ ] 回测结果获取
   - [ ] 报告生成（JSON/文本/HTML）

3. **模拟交易路由**
   - [ ] 账户创建
   - [ ] 账户查询
   - [ ] 买入交易
   - [ ] 卖出交易
   - [ ] 持仓查询
   - [ ] 交易历史
   - [ ] 账户删除

4. **收益统计路由**
   - [ ] 账户收益汇总
   - [ ] 持仓收益分析
   - [ ] 交易绩效分析

### 集成测试场景

1. **完整回测流程**
   ```
   创建回测任务 → 获取结果 → 生成报告 → 验证数据
   ```

2. **模拟交易完整流程**
   ```
   创建账户 → 买入 → 查询持仓 → 卖出 → 查询收益 → 删除账户
   ```

3. **技术分析完整流程**
   ```
   五维共振分析 → 策略信号 → 指标查询 → 生成报告
   ```

---

## 部署计划

### 阶段 1: 路由集成和启用（1天）

- [ ] 解除 main.py 中现有路由的注释
- [ ] 为 analysis_router 添加服务层集成
- [ ] 为 performance_router 实现服务层
- [ ] 测试现有路由功能

### 阶段 2: 回测 API 开发（2天）

- [ ] 创建 backtest 路由文件
- [ ] 实现单股票回测端点
- [ ] 实现多股票组合回测端点
- [ ] 实现策略比较端点
- [ ] 实现报告生成端点
- [ ] 编写回测路由测试

### 阶段 3: 模拟交易开发（2天）

- [ ] 创建 simulation 服务
- [ ] 创建 simulation 路由
- [ ] 实现账户管理端点
- [ ] 实现交易端点
- [ ] 实现持仓和历史查询
- [ ] 编写模拟交易测试

### 阶段 4: 收益统计完善（1天）

- [ ] 完善 performance 路由
- [ ] 连接模拟交易数据
- [ ] 实现收益计算逻辑
- [ ] 编写收益统计测试

### 阶段 5: 集成测试和文档（1天）

- [ ] 端到端测试
- [ ] 性能测试
- [ ] 更新 API 文档
- [ ] 编写使用示例

**总预计时间:** 7 天

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 回测执行时间过长 | API 超时 | 异步任务 + 轮询机制 |
| 数据不足导致失败 | 用户体验差 | 前置数据检查 + 友好提示 |
| 模拟交易数据丢失 | 数据完整性 | 定期持久化到数据库 |
| 策略性能不稳定 | 结果不准确 | 使用现有测试验证 |

---

## 附录

### 相关文档

- [技术分析模块文档](../technical_analysis/README.md)
- [回测模块文档](../backtest/README.md)
- [现有 API 路由设计](../docs/superpowers/specs/)

### 依赖模块

- `technical_analysis` - 技术分析引擎和策略
- `backtest` - 回测引擎和策略
- `stock_market` - K线数据访问
- `common.database` - 数据库连接管理

---

**设计完成 ✅**

请审核此设计文档，确认无误后我将开始实施计划的编写！
