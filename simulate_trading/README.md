# 模拟交易模块

## 概述

模拟交易模块实现了三种不同风格的交易策略并行运行，基于实时行情进行模拟交易（非回测），并生成交易日报进行策略对比分析。

### 核心特性

- ✅ **三种策略并行**
  - 激进型：高仓位（9成）追涨杀跌，短线操作
  - 稳健型：中等仓位（7成）趋势跟踪，波段操作
  - 保守型：低仓位（5成）价值投资，长期持有

- ✅ **实时行情监控**
  - 集成 data_sources 模块
  - 每 5 分钟执行一次交易决策
  - 自动获取实时股价

- ✅ **独立进程架构**
  - 每种策略独立进程运行
  - 进程隔离，互不影响
  - 主控制器统一管理

- ✅ **完整的数据持久化**
  - PostgreSQL 数据库存储
  - 账户资金管理
  - 交易记录追踪
  - 每日报告生成

- ✅ **灵活的配置管理**
  - YAML 配置文件
  - 策略参数独立配置
  - 支持动态启用/禁用策略

## 快速开始

### 1. 数据库准备

```bash
# 创建数据库表（首次运行）
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from simulate_trading.models import StrategyAccount, StrategyTrade, DailyReport

engine = create_engine('postgresql://localhost/stock_market')
StrategyAccount.metadata.create_all(engine)
StrategyTrade.metadata.create_all(engine)
DailyReport.metadata.create_all(engine)
"
```

### 2. 配置环境变量

```bash
export DATABASE__URL="postgresql://localhost/stock_market"
```

### 3. 运行模拟交易

```bash
# 启动所有策略
python -m simulate_trading.cli start

# 执行单次交易周期
python -m simulate_trading.cli cycle

# 查看策略状态
python -m simulate_trading.cli status

# 生成对比报告
python -m simulate_trading.cli report

# 生成每日报告
python -m simulate_trading.cli daily
```

## 目录结构

```
simulate_trading/
├── __init__.py                 # 模块入口
├── config/                     # 配置文件
│   ├── strategies.yaml        # 策略配置
│   └── simulate_trading.yaml  # 系统配置
├── strategies/                 # 策略实现
│   ├── __init__.py
│   ├── base_strategy.py       # 策略基类
│   ├── aggressive_strategy.py # 激进型
│   ├── moderate_strategy.py   # 稳健型
│   └── conservative_strategy.py # 保守型
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── strategy_account.py    # 账户模型
│   ├── strategy_trade.py      # 交易模型
│   └── daily_report.py        # 报告模型
├── repositories/               # 数据仓库
│   ├── __init__.py
│   ├── strategy_account_repo.py
│   ├── strategy_trade_repo.py
│   └── daily_report_repo.py
├── services/                   # 业务服务（待实现）
│   ├── __init__.py
│   ├── data_service.py
│   ├── trade_executor.py
│   └── report_generator.py
├── processes/                  # 进程管理（待实现）
│   ├── __init__.py
│   ├── process_manager.py
│   └── strategy_worker.py
├── controller.py               # 主控制器
├── cli.py                      # 命令行接口
├── exceptions.py               # 异常定义
└── utils/                      # 工具函数
```

## 配置说明

### 策略配置 (`config/strategies.yaml`)

```yaml
strategies:
  aggressive:  # 激进型
    name: "激进型"
    enabled: true              # 是否启用
    initial_cash: 80000        # 初始资金
    max_position: 0.9          # 最大仓位
    min_position: 0.5          # 最小仓位
    stop_loss: -0.08           # 止损比例
    take_profit: 0.15          # 止盈比例
    trade_ratio: 0.5           # 每次交易比例
    chase_threshold: 0.05      # 追涨阈值
    cut_loss_threshold: -0.03  # 杀跌阈值
```

### 系统配置 (`config/simulate_trading.yaml`)

```yaml
trading:
  execution_interval: 300      # 执行间隔（秒）
  market_close_time: "15:00"   # 收盘时间
  market_open_time: "09:30"    # 开盘时间
```

## 策略说明

### 激进型策略

**特点：**
- 高仓位运行（最高 9 成）
- 追涨杀跌，短线操作
- 追涨阈值：涨幅 > 5%
- 杀跌阈值：跌幅 > 3% 且亏损

**适用场景：** 市场强势上涨，波动较大的行情

### 稳健型策略

**特点：**
- 中等仓位（最高 7 成）
- 趋势跟踪，波段操作
- 持有周期：数天至数周
- 严格止盈止损

**适用场景：** 趋势明确的市场，适合大多数投资者

### 保守型策略

**特点：**
- 低仓位（最高 5 成）
- 价值投资，长期持有
- 持有周期：数月至数年
- 极低换手率

**适用场景：** 震荡市或熊市，风险厌恶型投资者

## 数据库表结构

### 策略账户表 (`strategy_accounts`)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| strategy_name | String | 策略名称 |
| initial_cash | DECIMAL | 初始资金 |
| current_cash | DECIMAL | 当前现金 |
| total_value | DECIMAL | 总资产 |
| total_profit | DECIMAL | 总收益 |
| total_profit_pct | DECIMAL | 收益率 |
| position_count | Integer | 持仓数量 |

### 交易记录表 (`strategy_trades`)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| strategy_name | String | 策略名称 |
| symbol | String | 股票代码 |
| transaction_type | String | 交易类型 (buy/sell) |
| quantity | Integer | 数量 |
| price | DECIMAL | 价格 |
| amount | DECIMAL | 金额 |
| fee | DECIMAL | 手续费 |
| reason | String | 交易理由 |
| transaction_date | DateTime | 交易时间 |

### 每日报告表 (`daily_reports`)

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | Integer | 主键 |
| strategy_name | String | 策略名称 |
| report_date | Date | 报告日期 |
| cash | DECIMAL | 现金 |
| stock_value | DECIMAL | 持仓市值 |
| total_assets | DECIMAL | 总资产 |
| profit | DECIMAL | 收益 |
| profit_pct | DECIMAL | 收益率 |
| position_count | Integer | 持仓数量 |
| winning_trades | Integer | 盈利交易次数 |
| losing_trades | Integer | 亏损交易次数 |

## 使用示例

### 启动策略并执行

```bash
# 1. 启动所有策略
python -m simulate_trading.cli start

# 2. 执行交易周期（可多次执行）
python -m simulate_trading.cli cycle

# 3. 查看状态
python -m simulate_trading.cli status

# 4. 生成每日报告（收盘后）
python -m simulate_trading.cli daily

# 5. 生成对比报告
python -m simulate_trading.cli report
```

### 输出示例

```
======================================================================
🚀 Alpha Quant Trader Pro - 模拟交易系统
======================================================================

🕐 2026-03-17 10:30:00

📊 策略状态:

----------------------------------------------------------------------
📈 策略: 激进型
----------------------------------------------------------------------
  初始资金: 80,000.00 元
  当前现金: 12,500.00 元
  总资产:   90,800.00 元
  总收益:   +10,800.00 元 (+13.50%)
  持仓数量: 5 只

----------------------------------------------------------------------
📈 策略: 稳健型
----------------------------------------------------------------------
  初始资金: 60,000.00 元
  当前现金: 18,200.00 元
  总资产:   63,800.00 元
  总收益:   +3,800.00 元 (+6.33%)
  持仓数量: 3 只

----------------------------------------------------------------------
📈 策略: 保守型
----------------------------------------------------------------------
  初始资金: 50,000.00 元
  当前现金: 32,500.00 元
  总资产:   52,300.00 元
  总收益:   +2,300.00 元 (+4.60%)
  持仓数量: 2 只

======================================================================
```

## 注意事项

1. **依赖模块**：需要 `data_sources` 模块提供实时行情数据
2. **数据库**：需要 PostgreSQL 数据库，表结构已通过 SQLAlchemy 定义
3. **策略实现**：当前策略为占位符实现，完整逻辑需要服务层支持
4. **进程管理**：实时监控功能需要实现进程管理器（待完成）

## 后续开发计划

- [ ] 实现服务层（数据服务、交易执行器、报告生成器）
- [ ] 完善策略逻辑（追涨杀跌、趋势跟踪、价值投资）
- [ ] 实现进程管理器和后台监控
- [ ] 添加技术分析指标支持
- [ ] 实现持仓管理（集成 portfolio_manager）
- [ ] 添加 Web 管理界面
- [ ] 实现完整的单元测试和集成测试

## 参考资料

- [设计文档](../docs/superpowers/specs/2026-03-17-simulate-trading-design.md)
- [实施计划](../docs/superpowers/plans/2026-03-17-simulate-trading-implementation.md)
- [data_sources 模块](../data_sources/)
- [portfolio_manager 模块](../portfolio_manager/)
