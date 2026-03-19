# 回测模块 (Backtest Module)

**版本:** 1.0.0
**最后更新:** 2026-03-17

---

## 📋 概述

`backtest` 模块提供完整的量化策略回测功能，支持单股票和多股票组合回测。采用事件驱动架构，集成现有技术分析模块（五维共振、VCP、九转、背离），提供完整的绩效分析和报告生成。

---

## 🏗️ 架构设计

### 核心组件

```
backtest/
├── config.py              # 配置管理
├── models.py              # 6 个数据模型
├── core/                  # 核心引擎层
│   ├── position_tracker.py    # 持仓跟踪
│   ├── broker_simulator.py    # 经纪商模拟
│   ├── data_feed.py           # 数据源适配
│   └── backtest_engine.py     # 回测引擎
├── strategies/            # 策略层
│   ├── base_strategy.py       # 策略基类
│   ├── strategy_combiner.py   # 策略组合器
│   └── prebuilt/              # 预设策略
│       ├── five_dimension.py  # 五维共振
│       ├── vcp_breakout.py    # VCP 突破
│       ├── td_golden_pit.py   # 九转黄金坑
│       └── top_divergence.py  # 顶部背离
├── analyzers/             # 分析器层
│   ├── metrics.py             # 绩效指标
│   ├── trade_analyzer.py      # 交易统计
│   └── report_generator.py    # 报告生成
└── services/              # 服务层
    └── backtest_service.py    # 统一服务
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install matplotlib pandas numpy
```

### 2. 基本使用

```python
from backtest.services import BacktestService
from backtest.strategies.prebuilt import FiveDimensionStrategy
from backtest.config import BacktestConfig
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService

# 初始化
db = DatabaseManager("postgresql://...")
with db.get_session() as session:
    analysis_service = AnalysisService(session)
    backtest_service = BacktestService(session)

    # 创建策略
    strategy = FiveDimensionStrategy(analysis_service)

    # 运行回测
    result = backtest_service.run_single_stock_backtest(
        symbol="600519",
        strategy=strategy,
        config=BacktestConfig(
            initial_capital=100000,
            start_date="2023-01-01",
            end_date="2024-12-31",
            commission_rate=0.00025,
            position_size=0.1
        )
    )

    # 打印结果
    print(result.summary)

    # 生成报告
    report = backtest_service.generate_backtest_report(result, format="text")
    print(report)
```

---

## 📚 核心功能

### 1. 单股票回测

```python
# 使用五维共振策略
from backtest.strategies.prebuilt import FiveDimensionStrategy

strategy = FiveDimensionStrategy(analysis_service)
result = backtest_service.run_single_stock_backtest(
    symbol="600519",
    strategy=strategy,
    config=config
)

# 查看结果
print(f"总收益率: {result.performance.total_return:.2f}%")
print(f"年化收益率: {result.performance.annual_return:.2f}%")
print(f"最大回撤: {result.performance.max_drawdown:.2f}%")
print(f"夏普比率: {result.performance.sharpe_ratio:.2f}")
```

### 2. 多股票组合回测

```python
symbols = ["600519", "000001", "300750", "600036"]

results = backtest_service.run_multi_stock_backtest(
    symbols=symbols,
    strategy=strategy,
    config=config
)

# 比较不同股票的结果
for symbol, result in results.items():
    print(f"{symbol}: {result.performance.annual_return:.2f}%")
```

### 3. 策略组合

```python
from backtest.strategies import StrategyCombiner
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy
)

# 创建多个策略
vcp_strategy = VCPBreakoutStrategy()
five_dim_strategy = FiveDimensionStrategy(analysis_service)

# AND 规则: 两个策略都发出信号才交易
combiner = StrategyCombiner(
    strategies=[vcp_strategy, five_dim_strategy],
    combination_rule="and"
)

result = backtest_service.run_single_stock_backtest(
    symbol="600519",
    strategy=combiner,
    config=config
)
```

### 4. 策略比较

```python
strategies = [
    FiveDimensionStrategy(analysis_service),
    VCPBreakoutStrategy(),
    TDGoldenPitStrategy()
]

results = backtest_service.compare_strategies(
    symbol="600519",
    strategies=strategies,
    config=config
)

# 比较不同策略的绩效
for name, result in results.items():
    print(f"{name}: 年化 {result.performance.annual_return:.2f}%, 夏普 {result.performance.sharpe_ratio:.2f}")
```

---

## 📊 绩效指标

### 收益指标

- **总收益率:** 回测期间总收益
- **年化收益率:** 年化后的收益率

### 风险指标

- **最大回撤:** 最大资金回撤幅度
- **波动率:** 收益波动程度
- **夏普比率:** 风险调整后收益 (越高越好)
- **索提诺比率:** 下行风险调整后收益
- **卡尔玛比率:** 年化收益 / 最大回撤

### 交易统计

- **总交易次数:** 买入 + 卖出次数
- **胜率:** 盈利交易占比
- **盈亏比:** 平均盈利 / 平均亏损
- **平均持仓天数:** 平均持仓时间
- **最大连胜/连败:** 连续盈利/亏损次数

---

## 📖 预设策略说明

### 1. 五维共振策略 (FiveDimensionStrategy)

**逻辑:**
- 集成 `AnalysisService.analyze_stock()` 的五维评分
- 评分分级:
  - S 级 (≥85): 买入 20% 仓位
  - A 级 (≥65): 买入 10% 仓位
  - B 级 (≥40): 持有 5% 仓位
  - C 级 (<40): 卖出或观望

**使用:**
```python
strategy = FiveDimensionStrategy(analysis_service)
```

### 2. VCP 突破策略 (VCPBreakoutStrategy)

**逻辑:**
1. 检测 VCP 形态 (波动收缩)
2. 等待突破枢轴点
3. 确认成交量 > 1.5 倍均量
4. 确认趋势向上 (EMA 多头)

**使用:**
```python
strategy = VCPBreakoutStrategy()
```

### 3. 九转黄金坑策略 (TDGoldenPitStrategy)

**逻辑:**
- 神奇九转低九 (buy_count == 9) → 买入 (12% 仓位)
- 神奇九转高九 (sell_count == 9) → 卖出

**使用:**
```python
strategy = TDGoldenPitStrategy()
```

### 4. 顶部背离策略 (TopDivergenceStrategy)

**逻辑:**
- 检测顶背离 (bearish divergence)
- 价格新高，指标未新高
- 生成卖出信号 (止盈)

**使用:**
```python
strategy = TopDivergenceStrategy()
```

---

## 🔧 配置参数

```python
from backtest.config import BacktestConfig

config = BacktestConfig(
    # ========== 基础配置 ==========
    initial_capital=100000.0,     # 初始资金
    commission_rate=0.00025,       # 手续费率 (万分之2.5)
    slippage_rate=0.001,           # 滑点率 (千分之1)
    stamp_duty_rate=0.001,         # 印花税率 (千分之1, 卖出)

    # ========== 回测参数 ==========
    start_date="2023-01-01",      # 回测开始日期
    end_date="2024-12-31",         # 回测结束日期
    interval="1d",                 # K线周期 (1d, 5d, 10d, 1m)

    # ========== 资金管理 ==========
    position_size=0.1,             # 单笔交易仓位 (10%)
    max_positions=5,               # 最大持仓股票数
    use_dynamic_position=True,     # 是否动态调整仓位

    # ========== 风控参数 ==========
    stop_loss_pct=0.08,            # 止损比例 (8%)
    take_profit_pct=0.20,          # 止盈比例 (20%)
    enable_trailing_stop=False,    # 启用移动止损
    enable_position_control=True   # 启用仓位控制
)
```

---

## 📝 生成报告

### 文本报告

```python
report = backtest_service.generate_backtest_report(result, format="text")
print(report)
```

### HTML 报告

```python
html_report = backtest_service.generate_backtest_report(result, format="html")
with open("backtest_report.html", "w", encoding="utf-8") as f:
    f.write(html_report)
```

### JSON 报告

```python
json_report = backtest_service.generate_backtest_report(result, format="json")
print(json_report)
```

---

## 🧪 运行测试

```bash
# 运行所有回测模块测试
pytest tests/backtest/ -v

# 运行单个测试文件
pytest tests/backtest/test_backtest_service.py -v
```

---

## 📚 完整示例

### 示例 1: 五维共振回测 + 报告生成

```python
from backtest.services import BacktestService
from backtest.strategies.prebuilt import FiveDimensionStrategy
from backtest.config import BacktestConfig
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService

# 初始化
db = DatabaseManager("postgresql://...")
with db.get_session() as session:
    analysis_service = AnalysisService(session)
    backtest_service = BacktestService(session)

    # 创建策略和配置
    strategy = FiveDimensionStrategy(analysis_service)
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2023-01-01",
        end_date="2024-12-31"
    )

    # 运行回测
    result = backtest_service.run_single_stock_backtest(
        symbol="600519",
        strategy=strategy,
        config=config
    )

    # 打印摘要
    print(result.summary)

    # 生成详细报告
    report = backtest_service.generate_backtest_report(result, format="text")
    print(report)

    # 保存到文件
    with open("backtest_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
```

### 示例 2: 策略比较

```python
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy
)

strategies = [
    FiveDimensionStrategy(analysis_service),
    VCPBreakoutStrategy(),
    TDGoldenPitStrategy()
]

results = backtest_service.compare_strategies(
    symbol="600519",
    strategies=strategies,
    config=config
)

# 打印比较结果
print(f"{'策略':<20} {'年化收益':>10} {'夏普比率':>10} {'胜率':>8}")
print("-" * 48)
for name, result in results.items():
    print(f"{name:<20} {result.performance.annual_return:>9.2f}% "
          f"{result.performance.sharpe_ratio:>10.2f} "
          f"{result.performance.win_rate:>7.1f}%")
```

---

## ⚠️ 注意事项

1. **数据要求:** 至少需要 30 条 K 线数据
2. **数据同步:** 回测前确保已通过 `stock_market` 模块同步数据
3. **策略集成:** 使用 `AnalysisService` 时确保已初始化数据库连接
4. **性能优化:** 大规模回测建议使用并行处理

---

## 📖 相关文档

- [技术分析模块文档](../technical_analysis/README.md)
- [股票市场模块文档](../stock_market/README.md)
- [回测模块设计文档](../docs/superpowers/specs/2026-03-17-backtest-module-design.md)
- [回测模块实施计划](../docs/superpowers/plans/2026-03-17-backtest-module-implementation.md)

---

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解贡献指南。

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。
