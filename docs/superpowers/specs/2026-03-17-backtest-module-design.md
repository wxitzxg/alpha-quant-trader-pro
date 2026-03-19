# 回测模块设计文档

**创建日期:** 2026-03-17
**版本:** 1.0.0
**作者:** Claude Code
**审核状态:** 待审核

---

## 📋 摘要

本文档描述了 `backtest` 模块的完整设计，该模块提供基于现有 `technical_analysis` 模块的量化策略回测功能。采用混合事件驱动架构，支持单股票和多股票组合回测，提供完整的绩效分析和报告生成。

---

## 🎯 需求概述

### 核心功能

1. **回测范围**
   - 单只股票回测
   - 多股票组合回测

2. **策略类型**
   - 集成现有技术分析模块 (五维共振、VCP、九转、背离)
   - 支持策略组合和条件判断
   - 提供自定义策略接口

3. **回测指标**
   - 基础指标: 年化收益率、最大回撤、夏普比率、索提诺比率
   - 交易统计: 胜率、盈亏比、交易次数、平均持仓天数
   - 详细报告: 权益曲线、交易明细、可视化图表

4. **数据粒度**
   - 日线回测

5. **资金管理**
   - 固定初始资金 (100,000元)
   - 可配置参数
   - 支持多资金规模测试

---

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (BacktestService)               │
│  - BacktestService (统一入口)                           │
│  - 配置管理 (BacktestConfig)                            │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                   核心引擎层 (Core Engine)                │
│  - BacktestEngine (事件驱动引擎)                        │
│  - PositionTracker (持仓跟踪)                           │
│  - BrokerSimulator (经纪商模拟)                         │
│  - PerformanceAnalyzer (绩效分析)                       │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                   策略层 (Strategies)                     │
│  - 预设策略 (Prebuilt Strategies):                      │
│    • FiveDimensionStrategy (五维共振)                   │
│    • VCPBreakoutStrategy (VCP突破)                      │
│    • TDGoldenPitStrategy (九转黄金坑)                   │
│    • TopDivergenceStrategy (顶部背离)                   │
│  - 策略组合器 (StrategyCombiner)                        │
│  - 自定义策略接口 (Custom Strategy Interface)          │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│              数据源层 (Data Sources)                     │
│  - StockMarket (股票市场模块) ← 复用                    │
│  - TechnicalAnalysis (技术分析模块) ← 复用              │
│  - PortfolioManager (持仓管理模块) ← 复用               │
└─────────────────────────────────────────────────────────┘
```

### 模块结构

```
backtest/
├── __init__.py
├── config.py                    # 回测配置
├── models.py                    # 回测数据模型
│
├── core/                        # 核心引擎层
│   ├── __init__.py
│   ├── backtest_engine.py       # 回测引擎 (事件驱动)
│   ├── position_tracker.py      # 持仓跟踪 (复用 PortfolioCommands 逻辑)
│   ├── broker_simulator.py      # 经纪商模拟 (滑点、成交)
│   ├── data_feed.py             # 数据源适配 (对接 stock_market)
│   └── performance_analyzer.py  # 绩效分析器
│
├── strategies/                  # 策略层
│   ├── __init__.py
│   ├── base_strategy.py         # 策略基类
│   ├── prebuilt/                # 预设策略
│   │   ├── __init__.py
│   │   ├── five_dimension.py    # 五维共振策略
│   │   ├── vcp_breakout.py      # VCP 突破策略
│   │   ├── td_golden_pit.py     # 九转黄金坑策略
│   │   └── top_divergence.py    # 顶部背离策略
│   ├── strategy_combiner.py     # 策略组合器
│   └── strategy_factory.py      # 策略工厂
│
├── analyzers/                   # 分析器层
│   ├── __init__.py
│   ├── metrics.py               # 绩效指标 (年化收益、回撤、夏普)
│   ├── trade_analyzer.py        # 交易统计 (胜率、盈亏比)
│   ├── equity_curve.py          # 权益曲线
│   └── report_generator.py      # 报告生成器
│
└── services/                    # 服务层
    ├── __init__.py
    └── backtest_service.py      # 回测服务 (统一接口)
```

---

## 📦 核心组件详细设计

### 1. 核心引擎层 (Core Engine)

#### 1.1 回测引擎 (BacktestEngine)

**职责:** 事件驱动核心，逐日推进回测流程

**接口设计:**

```python
class BacktestEngine:
    """
    回测引擎 - 事件驱动核心
    """

    def __init__(
        self,
        config: BacktestConfig,
        data_feed: DataFeed,
        strategy: Strategy,
        initial_capital: float = 100000.0
    ):
        """
        初始化回测引擎

        Args:
            config: 回测配置
            data_feed: 数据源适配器
            strategy: 交易策略
            initial_capital: 初始资金
        """
        self.config = config
        self.data_feed = data_feed
        self.strategy = strategy
        self.initial_capital = initial_capital

        # 核心组件
        self.position_tracker = PositionTracker(initial_capital)
        self.broker = BrokerSimulator(
            commission_rate=config.commission_rate,
            slippage_rate=config.slippage_rate
        )
        self.performance_analyzer = PerformanceAnalyzer()

        # 运行状态
        self.current_date = None
        self.trades = []
        self.daily_metrics = []

    def run(self, start_date: str, end_date: str) -> BacktestResult:
        """
        运行回测

        流程:
        1. 初始化数据
        2. 逐日推进
        3. 每日执行:
           - 获取当日数据
           - 调用策略生成信号
           - 执行交易 (买入/卖出)
           - 更新持仓
           - 记录绩效指标
        4. 生成最终报告

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            BacktestResult: 回测结果
        """
        pass

    def _on_bar(self, date: str, data: Dict):
        """
        处理单日数据

        1. 更新持仓市值
        2. 调用策略获取信号
        3. 执行交易
        4. 记录当日指标
        """
        pass

    def _execute_trade(self, signal: Signal):
        """
        执行交易

        1. 检查资金/持仓是否充足
        2. 计算交易金额和手续费
        3. 更新持仓
        4. 记录交易明细
        """
        pass
```

**关键特性:**
- ✅ 事件驱动架构，逐日推进
- ✅ 支持动态调仓和止损止盈
- ✅ 完整的状态跟踪 (持仓、现金、交易记录)
- ✅ 每日绩效指标记录

---

#### 1.2 持仓跟踪器 (PositionTracker)

**职责:** 管理持仓状态，复用 `PortfolioCommands` 的核心逻辑

**接口设计:**

```python
class PositionTracker:
    """
    持仓跟踪器 - 复用 PortfolioCommands 逻辑
    """

    def __init__(self, initial_capital: float):
        """
        初始化持仓跟踪器

        Args:
            initial_capital: 初始资金
        """
        self.cash = initial_capital
        self.positions = {}  # {symbol: Position}

    def buy(self, symbol: str, quantity: int, price: float) -> bool:
        """
        买入股票

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格

        Returns:
            bool: 是否成功
        """
        pass

    def sell(self, symbol: str, quantity: int, price: float) -> bool:
        """
        卖出股票

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            bool: 是否成功
        """
        pass

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            Position or None
        """
        pass

    def update_market_value(self, symbol: str, current_price: float):
        """
        更新持仓市值

        Args:
            symbol: 股票代码
            current_price: 当前价格
        """
        pass

    def get_total_value(self) -> float:
        """
        获取总资产 (现金 + 股票市值)

        Returns:
            总资产
        """
        pass

    def get_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓

        Returns:
            持仓字典
        """
        pass
```

**复用逻辑:**
- 复用 `PortfolioCommands.buy()` 和 `sell()` 的核心逻辑
- 复用 `PositionModel` 和 `TransactionModel` 数据模型
- 简化版，仅保留回测所需功能

---

#### 1.3 经纪商模拟器 (BrokerSimulator)

**职责:** 模拟真实交易环境，处理成交、滑点、手续费

**接口设计:**

```python
class BrokerSimulator:
    """
    经纪商模拟器
    """

    def __init__(
        self,
        commission_rate: float = 0.00025,  # 万分之2.5
        slippage_rate: float = 0.001,       # 千分之1滑点
        stamp_duty_rate: float = 0.001      # 千分之1印花税 (卖出)
    ):
        """
        初始化经纪商模拟器

        Args:
            commission_rate: 手续费率
            slippage_rate: 滑点率
            stamp_duty_rate: 印花税率
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.stamp_duty_rate = stamp_duty_rate

    def calculate_commission(self, amount: float) -> float:
        """
        计算手续费

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        return amount * self.commission_rate

    def apply_slippage(self, price: float, direction: str) -> float:
        """
        应用滑点

        Args:
            price: 原始价格
            direction: 交易方向 ('buy' or 'sell')

        Returns:
            调整后的价格
        """
        if direction == 'buy':
            return price * (1 + self.slippage_rate)
        else:
            return price * (1 - self.slippage_rate)

    def execute_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        direction: str  # 'buy' or 'sell'
    ) -> ExecutionResult:
        """
        执行订单

        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            direction: 交易方向

        Returns:
            ExecutionResult: 执行结果 (包含实际成交价、手续费等)
        """
        pass
```

**关键特性:**
- ✅ 支持手续费计算 (佣金 + 印花税)
- ✅ 支持滑点模拟
- ✅ 返回完整的执行结果

---

#### 1.4 数据源适配器 (DataFeed)

**职责:** 统一数据接口，对接现有的 `stock_market` 模块

**接口设计:**

```python
class DataFeed:
    """
    数据源适配器 - 对接 stock_market 模块
    """

    def __init__(self, session: Session):
        """
        初始化数据源适配器

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.kline_repo = KLineRepository(session)

    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期

        Returns:
            DataFrame with columns: [open, high, low, close, volume, timestamp]
        """
        params = KLineQueryParams(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        klines = self.kline_repo.query_klines(params)

        # 转换为 DataFrame
        data = []
        for kline in klines:
            data.append({
                'open': kline.open_price,
                'high': kline.high_price,
                'low': kline.low_price,
                'close': kline.close_price,
                'volume': kline.volume,
                'timestamp': kline.timestamp
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def get_multi_stock_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据 (用于组合回测)

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期

        Returns:
            {symbol: DataFrame}
        """
        return {symbol: self.get_stock_data(symbol, start_date, end_date, interval)
                for symbol in symbols}
```

**复用逻辑:**
- 复用 `KLineRepository.query_klines()`
- 复用 `KLineQueryParams` 数据模型
- 转换为 pandas DataFrame 供策略使用

---

### 2. 策略层 (Strategies)

#### 2.1 策略基类 (BaseStrategy)

**职责:** 定义策略统一接口，所有策略继承此基类

**接口设计:**

```python
class BaseStrategy(ABC):
    """
    策略基类
    """

    @abstractmethod
    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        处理当日数据，生成交易信号

        Args:
            symbol: 股票代码
            data: {open, high, low, close, volume, ...}
            date: 日期

        Returns:
            Signal: 交易信号 (BUY/SELL/HOLD/COVER)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取策略名称

        Returns:
            策略名称
        """
        pass

    def get_position_size(self, total_capital: float) -> float:
        """
        计算建议仓位 (0-1)

        Args:
            total_capital: 总资金

        Returns:
            仓位比例
        """
        pass
```

**关键特性:**
- ✅ 统一的策略接口
- ✅ 支持仓位管理
- ✅ 易于扩展和测试

---

#### 2.2 预设策略

##### 五维共振策略 (FiveDimensionStrategy)

```python
class FiveDimensionStrategy(BaseStrategy):
    """
    五维共振策略 - 调用 AnalysisService.analyze_stock()
    """

    def __init__(self, analysis_service: AnalysisService):
        """
        初始化五维共振策略

        Args:
            analysis_service: 技术分析服务
        """
        self.analysis_service = analysis_service

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        五维共振评分决策:
        - ≥85分: STRONG_BUY (满仓 20%)
        - ≥65分: BUY (半仓 10%)
        - ≥40分: HOLD (轻仓 5%)
        - <40分: SELL (卖出)

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        # 调用技术分析模块
        result = self.analysis_service.analyze_stock(
            symbol=symbol,
            interval="1d",
            end_date=date,
            days=120
        )

        score = result.get('total_score', 0)

        if score >= 85:
            return Signal(symbol=symbol, date=date, action="BUY",
                         position_size=0.2, reason="五维共振 S 级信号")
        elif score >= 65:
            return Signal(symbol=symbol, date=date, action="BUY",
                         position_size=0.1, reason="五维共振 A 级信号")
        elif score >= 40:
            return Signal(symbol=symbol, date=date, action="HOLD",
                         position_size=0.05, reason="五维共振 B 级信号")
        else:
            return Signal(symbol=symbol, date=date, action="SELL",
                         reason="五维共振 C 级信号")

    def get_name(self) -> str:
        """获取策略名称"""
        return "FiveDimensionStrategy"
```

##### VCP 突破策略 (VCPBreakoutStrategy)

```python
class VCPBreakoutStrategy(BaseStrategy):
    """
    VCP 突破策略
    """

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        VCP 突破策略:
        1. 检测 VCP 形态 (波动收缩)
        2. 等待突破枢轴点
        3. 确认成交量 > 1.5 倍均量
        4. 结合趋势和位置确认

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        # 1. 检测 VCP 形态
        from technical_analysis.indicators import VCPDetector
        vcp = VCPDetector(data)
        vcp_result = vcp.detect_vcp()

        if not vcp_result['breakout_detected']:
            return Signal(symbol=symbol, date=date, action="HOLD")

        # 2. 确认成交量
        volume_ratio = data['volume'] / data['volume'].rolling(5).mean()
        if volume_ratio.iloc[-1] < 1.5:
            return Signal(symbol=symbol, date=date, action="HOLD")

        # 3. 确认趋势
        from technical_analysis.indicators import BaseIndicators
        indicators = BaseIndicators(data)
        ma_trend = indicators.get_latest_signals()['ma_trend']

        if ma_trend not in ['strong_uptrend', 'uptrend']:
            return Signal(symbol=symbol, date=date, action="HOLD")

        # 4. VCP 突破确认
        return Signal(
            symbol=symbol,
            date=date,
            action="BUY",
            position_size=0.15,
            reason="VCP 突破 + 成交量确认 + 趋势向上"
        )

    def get_name(self) -> str:
        """获取策略名称"""
        return "VCPBreakoutStrategy"
```

##### 九转黄金坑策略 (TDGoldenPitStrategy)

```python
class TDGoldenPitStrategy(BaseStrategy):
    """
    九转黄金坑策略
    """

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        九转黄金坑策略:
        1. 等待神奇九转低九信号
        2. 确认趋势向上 (EMA 多头排列)
        3. 确认位置超卖 (RSI < 30)
        4. 有效低九买入

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        pass

    def get_name(self) -> str:
        """获取策略名称"""
        return "TDGoldenPitStrategy"
```

##### 顶部背离策略 (TopDivergenceStrategy)

```python
class TopDivergenceStrategy(BaseStrategy):
    """
    顶部背离策略 - 止盈策略
    """

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        顶部背离策略:
        1. 检测顶背离信号 (价格新高，指标未新高)
        2. 确认超买状态 (RSI > 70)
        3. 提供止盈建议

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        pass

    def get_name(self) -> str:
        """获取策略名称"""
        return "TopDivergenceStrategy"
```

---

#### 2.3 策略组合器 (StrategyCombiner)

**职责:** 组合多个策略信号，支持 AND/OR/权重规则

**接口设计:**

```python
class StrategyCombiner(BaseStrategy):
    """
    策略组合器
    """

    def __init__(
        self,
        strategies: List[BaseStrategy],
        combination_rule: str = "and",  # "and", "or", "weighted"
        weights: Optional[List[float]] = None
    ):
        """
        初始化策略组合器

        Args:
            strategies: 策略列表
            combination_rule: 组合规则 ('and', 'or', 'weighted')
            weights: 权重列表 (仅 weighted 模式使用)
        """
        self.strategies = strategies
        self.combination_rule = combination_rule
        self.weights = weights if weights else [1.0 / len(strategies)] * len(strategies)

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        组合多个策略信号:
        - AND: 所有策略都发出买入信号才买入
        - OR: 任一策略发出买入信号就买入
        - Weighted: 加权评分 (例如: 五维共振*0.6 + VCP*0.4)

        Args:
            symbol: 股票代码
            data: K线数据
            date: 日期

        Returns:
            Signal: 交易信号
        """
        signals = [s.on_data(symbol, data, date) for s in self.strategies]

        if self.combination_rule == "and":
            return self._combine_and(signals)
        elif self.combination_rule == "or":
            return self._combine_or(signals)
        elif self.combination_rule == "weighted":
            return self._combine_weighted(signals, self.weights)

    def _combine_and(self, signals: List[Signal]) -> Signal:
        """AND 规则: 所有策略都买入才买入"""
        if all(s.action == "BUY" for s in signals):
            # 取最小仓位
            min_position = min(s.position_size for s in signals if s.position_size)
            return Signal(action="BUY", position_size=min_position)
        else:
            return Signal(action="HOLD")

    def _combine_or(self, signals: List[Signal]) -> Signal:
        """OR 规则: 任一策略买入就买入"""
        buy_signals = [s for s in signals if s.action == "BUY"]
        if buy_signals:
            # 取最大仓位
            max_position = max(s.position_size for s in buy_signals if s.position_size)
            return Signal(action="BUY", position_size=max_position)
        else:
            return Signal(action="HOLD")

    def _combine_weighted(self, signals: List[Signal], weights: List[float]) -> Signal:
        """加权规则: 按权重计算综合评分"""
        buy_score = sum(
            (s.position_size or 0) * w
            for s, w in zip(signals, weights)
            if s.action == "BUY"
        )

        if buy_score >= 0.1:  # 阈值
            return Signal(action="BUY", position_size=min(buy_score, 0.3))
        else:
            return Signal(action="HOLD")

    def get_name(self) -> str:
        """获取策略名称"""
        strategy_names = [s.get_name() for s in self.strategies]
        return f"Combiner({','.join(strategy_names)})"
```

**关键特性:**
- ✅ 支持多种组合规则
- ✅ 灵活的权重配置
- ✅ 易于扩展新的组合逻辑

---

### 3. 配置管理 (BacktestConfig)

**职责:** 管理回测参数

**接口设计:**

```python
@dataclass
class BacktestConfig:
    """
    回测配置
    """

    # ========== 基础配置 ==========
    initial_capital: float = 100000.0  # 初始资金
    commission_rate: float = 0.00025    # 手续费率 (万分之2.5)
    slippage_rate: float = 0.001        # 滑点率 (千分之1)
    stamp_duty_rate: float = 0.001      # 印花税率 (千分之1, 卖出)

    # ========== 回测参数 ==========
    start_date: str = "2023-01-01"     # 回测开始日期
    end_date: str = "2024-12-31"       # 回测结束日期
    interval: str = "1d"               # K线周期 (1d, 5d, 10d, 1m)

    # ========== 资金管理 ==========
    position_size: float = 0.1          # 单笔交易仓位 (10%)
    max_positions: int = 5              # 最大持仓股票数
    use_dynamic_position: bool = True   # 是否动态调整仓位

    # ========== 风控参数 ==========
    stop_loss_pct: float = 0.08         # 止损比例 (8%)
    take_profit_pct: float = 0.20       # 止盈比例 (20%)
    enable_trailing_stop: bool = False  # 启用移动止损
    enable_position_control: bool = True  # 启用仓位控制
```

---

### 4. 分析器层 (Analyzers)

#### 4.1 绩效指标计算 (MetricsCalculator)

```python
class MetricsCalculator:
    """
    绩效指标计算
    """

    def calculate_total_return(self, equity_curve: List[float]) -> float:
        """
        总收益率

        Args:
            equity_curve: 权益曲线

        Returns:
            总收益率 (%)
        """
        return (equity_curve[-1] / equity_curve[0] - 1) * 100

    def calculate_annual_return(
        self,
        total_return: float,
        days: int
    ) -> float:
        """
        年化收益率

        Args:
            total_return: 总收益率 (%)
            days: 回测天数

        Returns:
            年化收益率 (%)
        """
        years = days / 365.0
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        最大回撤

        Args:
            equity_curve: 权益曲线

        Returns:
            最大回撤 (%)
        """
        peak = equity_curve[0]
        max_dd = 0

        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            max_dd = max(max_dd, dd)

        return max_dd

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        夏普比率

        Args:
            returns: 日收益率列表
            risk_free_rate: 无风险利率 (年化)

        Returns:
            夏普比率
        """
        excess_returns = [r - risk_free_rate/252 for r in returns]
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        索提诺比率 (只惩罚下行风险)

        Args:
            returns: 日收益率列表
            risk_free_rate: 无风险利率 (年化)

        Returns:
            索提诺比率
        """
        excess_returns = [r - risk_free_rate/252 for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]

        if len(downside_returns) == 0:
            return 0

        downside_std = np.std(downside_returns)
        return np.mean(excess_returns) / downside_std * np.sqrt(252)

    def calculate_volatility(self, returns: List[float]) -> float:
        """
        波动率

        Args:
            returns: 日收益率列表

        Returns:
            年化波动率 (%)
        """
        return np.std(returns) * np.sqrt(252) * 100

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> float:
        """
        卡尔玛比率 (年化收益 / 最大回撤)

        Args:
            annual_return: 年化收益率 (%)
            max_drawdown: 最大回撤 (%)

        Returns:
            卡尔玛比率
        """
        if max_drawdown == 0:
            return 0
        return annual_return / abs(max_drawdown)
```

---

#### 4.2 交易统计分析 (TradeAnalyzer)

```python
class TradeAnalyzer:
    """
    交易统计分析
    """

    def analyze_trades(self, trades: List[Trade]) -> Dict:
        """
        分析交易统计

        Args:
            trades: 交易列表

        Returns:
            统计结果字典
        """
        # 过滤出完整的交易对 (买入+卖出)
        completed_trades = self._pair_trades(trades)

        winning_trades = [t for t in completed_trades if t.pnl > 0]
        losing_trades = [t for t in completed_trades if t.pnl <= 0]

        total_profit = sum(t.pnl for t in winning_trades)
        total_loss = abs(sum(t.pnl for t in losing_trades))

        return {
            'total_trades': len(completed_trades),           # 总交易次数
            'winning_trades': len(winning_trades),           # 盈利次数
            'losing_trades': len(losing_trades),             # 亏损次数
            'win_rate': len(winning_trades) / len(completed_trades) if completed_trades else 0,  # 胜率
            'avg_profit': total_profit / len(winning_trades) if winning_trades else 0,  # 平均盈利
            'avg_loss': total_loss / len(losing_trades) if losing_trades else 0,        # 平均亏损
            'profit_factor': total_profit / total_loss if total_loss > 0 else 0,        # 盈亏比
            'avg_holding_days': self._calculate_avg_holding_days(completed_trades),     # 平均持仓天数
            'max_consecutive_wins': self._calculate_max_consecutive_wins(completed_trades),  # 最大连胜
            'max_consecutive_losses': self._calculate_max_consecutive_losses(completed_trades)  # 最大连败
        }

    def calculate_profit_factor(self, trades: List[Trade]) -> float:
        """
        计算盈亏比 = 总盈利 / 总亏损

        Args:
            trades: 交易列表

        Returns:
            盈亏比
        """
        stats = self.analyze_trades(trades)
        return stats['profit_factor']
```

---

#### 4.3 报告生成器 (ReportGenerator)

```python
class ReportGenerator:
    """
    回测报告生成器
    """

    def generate_text_report(self, result: BacktestResult) -> str:
        """
        生成文本报告

        Args:
            result: 回测结果

        Returns:
            格式化的文本报告
        """
        report = f"""
{'='*80}
{' '*25}回测报告
{'='*80}

【策略信息】
  策略名称: {result.strategy_name}
  回测期间: {result.config.start_date} ~ {result.config.end_date}
  回测天数: {len(result.dates)} 天
  K线周期: {result.config.interval}

【资金信息】
  初始资金: {result.config.initial_capital:,.0f} 元
  期末资金: {result.equity_curve[-1]:,.0f} 元
  总收益率: {result.performance.total_return:.2f}%
  年化收益率: {result.performance.annual_return:.2f}%
  总盈利: {result.equity_curve[-1] - result.config.initial_capital:,.0f} 元

【风险指标】
  最大回撤: {result.performance.max_drawdown:.2f}%
  波动率: {result.performance.volatility:.2f}%
  夏普比率: {result.performance.sharpe_ratio:.2f}
  索提诺比率: {result.performance.sortino_ratio:.2f}
  卡尔玛比率: {result.performance.calmar_ratio:.2f}

【交易统计】
  总交易次数: {result.performance.total_trades}
  盈利次数: {result.performance.winning_trades}
  亏损次数: {result.performance.losing_trades}
  胜率: {result.performance.win_rate:.1f}%
  盈亏比: {result.performance.profit_factor:.2f}
  平均持仓天数: {result.performance.avg_holding_days:.1f}

【每日指标】
  最佳单日收益: {max(result.daily_metrics, key=lambda x: x.daily_return).daily_return:.2f}%
  最差单日收益: {min(result.daily_metrics, key=lambda x: x.daily_return).daily_return:.2f}%

{'='*80}
"""
        return report

    def generate_html_report(self, result: BacktestResult, output_path: str):
        """
        生成 HTML 可视化报告

        Args:
            result: 回测结果
            output_path: 输出路径
        """
        # 使用 plotly/matplotlib 生成图表
        # 1. 权益曲线图
        # 2. 回撤曲线图
        # 3. 交易分布图
        # 4. 持仓变化图
        # 5. 月度收益图
        pass

    def generate_equity_curve_plot(
        self,
        equity_curve: List[float],
        dates: List[str],
        output_path: str
    ):
        """
        生成权益曲线图

        Args:
            equity_curve: 权益曲线
            dates: 日期列表
            output_path: 输出路径
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.plot(dates, equity_curve, linewidth=2)
        plt.title('权益曲线')
        plt.xlabel('日期')
        plt.ylabel('资产 (元)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
```

---

### 5. 服务层 (BacktestService)

**职责:** 统一的回测服务接口，类似 `AnalysisService`

**接口设计:**

```python
class BacktestService:
    """
    回测服务 - 统一接口
    """

    def __init__(self, session: Session):
        """
        初始化回测服务

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.data_feed = DataFeed(session)

    def run_single_stock_backtest(
        self,
        symbol: str,
        strategy: BaseStrategy,
        config: BacktestConfig
    ) -> BacktestResult:
        """
        单只股票回测

        使用示例:
        >>> from backtest.services import BacktestService
        >>> from backtest.strategies.prebuilt import FiveDimensionStrategy
        >>> from common.database import DatabaseManager
        >>>
        >>> db = DatabaseManager("postgresql://...")
        >>> with db.get_session() as session:
        ...     backtest_service = BacktestService(session)
        ...     strategy = FiveDimensionStrategy(analysis_service)
        ...     result = backtest_service.run_single_stock_backtest(
        ...         symbol="600519",
        ...         strategy=strategy,
        ...         config=BacktestConfig(
        ...             initial_capital=100000,
        ...             start_date="2023-01-01",
        ...             end_date="2024-12-31"
        ...         )
        ...     )
        ...     print(result.summary)

        Args:
            symbol: 股票代码
            strategy: 交易策略
            config: 回测配置

        Returns:
            BacktestResult: 回测结果
        """
        # 1. 获取数据
        data = self.data_feed.get_stock_data(
            symbol=symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            interval=config.interval
        )

        if len(data) < 30:
            raise ValueError(f"数据不足，需要至少 30 条 K 线，当前只有 {len(data)} 条")

        # 2. 创建回测引擎
        engine = BacktestEngine(
            config=config,
            data_feed=self.data_feed,
            strategy=strategy,
            initial_capital=config.initial_capital
        )

        # 3. 运行回测
        result = engine.run(config.start_date, config.end_date)

        return result

    def run_multi_stock_backtest(
        self,
        symbols: List[str],
        strategy: BaseStrategy,
        config: BacktestConfig
    ) -> BacktestResult:
        """
        多股票组合回测

        支持:
        - 等权重配置
        - 动态调仓
        - 最大持仓数限制

        Args:
            symbols: 股票代码列表
            strategy: 交易策略
            config: 回测配置

        Returns:
            BacktestResult: 回测结果
        """
        # 1. 获取多股票数据
        multi_data = self.data_feed.get_multi_stock_data(
            symbols=symbols,
            start_date=config.start_date,
            end_date=config.end_date,
            interval=config.interval
        )

        # 2. 创建回测引擎
        engine = BacktestEngine(
            config=config,
            data_feed=self.data_feed,
            strategy=strategy,
            initial_capital=config.initial_capital
        )

        # 3. 运行回测 (引擎内部处理多股票逻辑)
        result = engine.run_multi_stock(multi_data, config.start_date, config.end_date)

        return result

    def run_portfolio_backtest(
        self,
        portfolio_config: PortfolioBacktestConfig
    ) -> BacktestResult:
        """
        投资组合回测

        支持:
        - 不同股票使用不同策略
        - 不同仓位配置
        - 多资金规模测试

        Args:
            portfolio_config: 投资组合配置

        Returns:
            BacktestResult: 回测结果
        """
        pass

    def generate_backtest_report(
        self,
        result: BacktestResult,
        format: str = "text"  # "text", "html", "json"
    ) -> str:
        """
        生成回测报告

        Args:
            result: 回测结果
            format: 报告格式

        Returns:
            报告内容
        """
        generator = ReportGenerator()

        if format == "text":
            return generator.generate_text_report(result)
        elif format == "html":
            return generator.generate_html_report(result)
        elif format == "json":
            return result.to_json()
```

---

### 6. 数据模型 (Models)

#### 6.1 信号模型 (Signal)

```python
@dataclass
class Signal:
    """交易信号"""
    symbol: str
    date: str
    action: str  # "BUY", "SELL", "HOLD", "COVER"
    price: float
    quantity: Optional[int] = None
    position_size: Optional[float] = None  # 仓位比例 (0-1)
    reason: Optional[str] = None  # 信号原因
```

#### 6.2 交易模型 (Trade)

```python
@dataclass
class Trade:
    """交易记录"""
    trade_id: int
    symbol: str
    date: str
    action: str  # "BUY" or "SELL"
    price: float
    quantity: int
    amount: float
    commission: float
    slippage: float
    total_cost: float
    pnl: Optional[float] = None  # 盈亏 (卖出时计算)
```

#### 6.3 持仓模型 (Position)

```python
@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float
    market_value: float
    floating_pl: float  # 浮动盈亏
    entry_date: str
```

#### 6.4 每日指标模型 (DailyMetrics)

```python
@dataclass
class DailyMetrics:
    """每日指标"""
    date: str
    total_value: float
    cash: float
    stock_value: float
    positions_count: int
    daily_return: float
    cumulative_return: float
```

#### 6.5 绩效指标模型 (PerformanceMetrics)

```python
@dataclass
class PerformanceMetrics:
    """绩效指标汇总"""
    # 收益指标
    total_return: float          # 总收益率 (%)
    annual_return: float         # 年化收益率 (%)
    volatility: float            # 波动率 (%)

    # 风险指标
    max_drawdown: float          # 最大回撤 (%)
    sharpe_ratio: float          # 夏普比率
    sortino_ratio: float         # 索提诺比率
    calmar_ratio: float          # 卡尔玛比率

    # 交易统计
    total_trades: int            # 总交易次数
    winning_trades: int          # 盈利次数
    losing_trades: int           # 亏损次数
    win_rate: float              # 胜率 (%)
    profit_factor: float         # 盈亏比
    avg_holding_days: float      # 平均持仓天数
```

#### 6.6 回测结果模型 (BacktestResult)

```python
@dataclass
class BacktestResult:
    """回测结果"""
    config: BacktestConfig
    strategy_name: str
    trades: List[Trade]
    daily_metrics: List[DailyMetrics]
    positions_history: List[Position]
    performance: PerformanceMetrics
    equity_curve: List[float]
    dates: List[str]

    @property
    def summary(self) -> str:
        """简要摘要"""
        return f"""
        策略: {self.strategy_name}
        回测期间: {self.config.start_date} ~ {self.config.end_date}
        初始资金: {self.config.initial_capital:,.0f}
        总收益率: {self.performance.total_return:.2f}%
        年化收益率: {self.performance.annual_return:.2f}%
        最大回撤: {self.performance.max_drawdown:.2f}%
        夏普比率: {self.performance.sharpe_ratio:.2f}
        总交易次数: {self.performance.total_trades}
        胜率: {self.performance.win_rate:.1f}%
        盈亏比: {self.performance.profit_factor:.2f}
        """

    def to_json(self) -> str:
        """转换为 JSON"""
        import json
        from dataclasses import asdict

        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
```

---

## 💡 使用示例

### 示例 1: 单股票五维共振回测

```python
from backtest.services import BacktestService
from backtest.strategies.prebuilt import FiveDimensionStrategy
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

### 示例 2: 策略组合回测

```python
from backtest.strategies import StrategyCombiner
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy
)

# 组合多个策略 (VCP + 九转)
vcp_strategy = VCPBreakoutStrategy()
td_strategy = TDGoldenPitStrategy()

combiner = StrategyCombiner(
    strategies=[vcp_strategy, td_strategy],
    combination_rule="and"  # 两个策略都发出信号才交易
)

# 运行回测
result = backtest_service.run_single_stock_backtest(
    symbol="600519",
    strategy=combiner,
    config=BacktestConfig(
        initial_capital=100000,
        start_date="2023-01-01",
        end_date="2024-12-31"
    )
)

print(f"策略组合回测结果:")
print(f"  年化收益: {result.performance.annual_return:.2f}%")
print(f"  夏普比率: {result.performance.sharpe_ratio:.2f}")
```

### 示例 3: 多股票组合回测

```python
# 多股票回测
symbols = ["600519", "000001", "300750", "600036"]

result = backtest_service.run_multi_stock_backtest(
    symbols=symbols,
    strategy=FiveDimensionStrategy(analysis_service),
    config=BacktestConfig(
        initial_capital=500000,  # 50万资金
        start_date="2023-01-01",
        end_date="2024-12-31",
        max_positions=5,         # 最多持有5只股票
        position_size=0.1,       # 单只股票仓位10%
        enable_position_control=True
    )
)

print(f"多股票组合回测:")
print(f"  总收益率: {result.performance.total_return:.2f}%")
print(f"  最大回撤: {result.performance.max_drawdown:.2f}%")
print(f"  交易次数: {result.performance.total_trades}")
```

### 示例 4: 多资金规模测试

```python
# 测试不同资金规模
capital_levels = [100000, 500000, 1000000]

for capital in capital_levels:
    result = backtest_service.run_single_stock_backtest(
        symbol="600519",
        strategy=FiveDimensionStrategy(analysis_service),
        config=BacktestConfig(
            initial_capital=capital,
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
    )

    print(f"资金 {capital:,.0f}: 年化收益 {result.performance.annual_return:.2f}%, "
          f"夏普比率 {result.performance.sharpe_ratio:.2f}")
```

---

## 🔧 关键设计决策

### 1. 架构选择: 混合事件驱动

**决策理由:**
- ✅ 支持逐日推进，逻辑清晰准确
- ✅ 支持复杂的持仓管理 (动态调仓、止损止盈)
- ✅ 易于扩展新的策略和分析器
- ✅ 符合现有项目的 Repository-Service 架构

**替代方案:**
- 向量化模式: 性能快但不支持复杂逻辑
- 纯事件驱动: 过于复杂，开发成本高

---

### 2. 模块复用策略

**复用现有模块:**
- `stock_market`: K线数据获取 (`KLineRepository`)
- `technical_analysis`: 策略信号生成 (`AnalysisService`)
- `portfolio_manager`: 持仓管理逻辑 (`PortfolioCommands`)

**优势:**
- ✅ 减少重复代码
- ✅ 保持架构一致性
- ✅ 利用已有的测试和验证

**风险控制:**
- 通过适配器模式封装，降低耦合
- 添加回测专用逻辑，不破坏现有模块

---

### 3. 策略系统设计

**混合策略支持:**
- 预设策略: 开箱即用，基于技术分析模块
- 策略组合器: 灵活组合，支持 AND/OR/权重
- 自定义接口: 扩展性强，满足特殊需求

**优势:**
- ✅ 降低使用门槛 (预设策略)
- ✅ 提供灵活性 (组合器)
- ✅ 支持高级用法 (自定义)

---

### 4. 绩效指标选择

**核心指标:**
- 收益指标: 总收益率、年化收益率
- 风险指标: 最大回撤、波动率、夏普比率、索提诺比率
- 交易统计: 胜率、盈亏比、平均持仓天数

**选择理由:**
- 覆盖收益、风险、交易三个维度
- 业界标准指标，易于理解和对比
- 支持策略优化和对比

---

## ⚠️ 潜在风险和挑战

### 1. 数据质量

**风险:**
- K线数据缺失或异常
- 数据不同步导致信号失效

**缓解措施:**
- 添加数据验证和清洗逻辑
- 提供数据质量检查工具
- 支持数据源切换和对比

---

### 2. 策略过拟合

**风险:**
- 回测结果过于乐观
- 实盘表现不佳

**缓解措施:**
- 支持滚动回测 (Walk-forward)
- 提供样本外测试功能
- 添加过拟合检测指标

---

### 3. 性能瓶颈

**风险:**
- 多股票回测速度慢
- 大规模参数优化耗时

**缓解措施:**
- 优化数据加载和处理
- 支持并行回测
- 提供缓存机制

---

## 📅 下一步计划

### 阶段 1: 基础框架 (1-2 周)

1. 创建模块结构
2. 实现核心引擎 (`BacktestEngine`)
3. 实现数据适配器 (`DataFeed`)
4. 实现基础策略 (五维共振)
5. 实现基本绩效指标

### 阶段 2: 策略系统 (1 周)

1. 实现其他预设策略 (VCP、九转、背离)
2. 实现策略组合器
3. 实现自定义策略接口

### 阶段 3: 高级功能 (1 周)

1. 实现多股票组合回测
2. 实现完整的绩效分析
3. 实现报告生成器 (文本 + HTML)

### 阶段 4: 测试和优化 (1 周)

1. 编写单元测试
2. 编写集成测试
3. 性能优化
4. 文档完善

---

## 📚 参考资料

1. **现有项目模块:**
   - `stock_market`: 股票市场管理模块
   - `technical_analysis`: 技术分析模块
   - `portfolio_manager`: 持仓管理模块

2. **设计参考:**
   - Zipline (事件驱动回测框架)
   - Backtrader (Python 回测框架)
   - VectorBT (向量化回测框架)

3. **绩效指标:**
   - 《主动投资组合管理》
   - Sharpe Ratio, Sortino Ratio, Calmar Ratio

---

## ✅ 审核清单

- [ ] 架构设计是否清晰合理？
- [ ] 接口设计是否易用？
- [ ] 是否充分利用现有模块？
- [ ] 是否支持所有需求场景？
- [ ] 数据模型是否完整？
- [ ] 使用示例是否清晰？
- [ ] 潜在风险是否已识别？

---

**文档版本:** 1.0.0
**最后更新:** 2026-03-17
**下一步:** 运行 spec review 循环，然后实施
