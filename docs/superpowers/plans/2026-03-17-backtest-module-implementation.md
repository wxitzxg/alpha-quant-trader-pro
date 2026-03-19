# 回测模块实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的回测模块，支持单股票和多股票组合回测，集成现有技术分析策略（五维共振、VCP、九转、背离）

**Architecture:** 事件驱动核心引擎 + 策略系统（预设策略 + 组合器）+ 绩效分析 + 报告生成，复用现有 stock_market、technical_analysis、portfolio_manager 模块

**Tech Stack:** Python 3.8+, SQLAlchemy, pandas, numpy, matplotlib, pytest

---

## 📁 文件结构规划

### 将创建的文件 (21 个)

```
backtest/
├── __init__.py                    # 模块入口
├── config.py                      # 配置管理
├── models.py                      # 6 个数据模型
├── exceptions.py                  # 自定义异常
│
├── core/                          # 核心引擎层 (5 个文件)
│   ├── __init__.py
│   ├── backtest_engine.py         # 回测引擎 (事件驱动)
│   ├── position_tracker.py        # 持仓跟踪 (复用 PortfolioCommands)
│   ├── broker_simulator.py        # 经纪商模拟 (滑点、手续费)
│   └── data_feed.py               # 数据源适配 (对接 stock_market)
│
├── strategies/                    # 策略层 (6 个文件)
│   ├── __init__.py
│   ├── base_strategy.py           # 策略基类
│   ├── strategy_combiner.py       # 策略组合器 (AND/OR/Weighted)
│   └── prebuilt/
│       ├── __init__.py
│       ├── five_dimension.py      # 五维共振策略
│       ├── vcp_breakout.py        # VCP 突破策略
│       ├── td_golden_pit.py       # 九转黄金坑策略
│       └── top_divergence.py      # 顶部背离策略
│
├── analyzers/                     # 分析器层 (4 个文件)
│   ├── __init__.py
│   ├── metrics.py                 # 绩效指标 (年化收益、回撤、夏普)
│   ├── trade_analyzer.py          # 交易统计 (胜率、盈亏比)
│   ├── equity_curve.py            # 权益曲线
│   └── report_generator.py        # 报告生成器 (文本 + HTML)
│
├── services/                      # 服务层 (1 个文件)
│   ├── __init__.py
│   └── backtest_service.py        # 统一服务接口
│
└── utils/                         # 工具层 (1 个文件)
    └── validators.py              # 输入验证
```

### 将修改的文件 (0 个)

**注意:** 本模块完全独立，不修改现有模块，仅通过适配器模式复用接口。

---

## 📋 任务分解

### 阶段 1: 基础框架 (任务 1-5) - 3-4 天

---

### 任务 1: 项目结构和基础文件

**Files:**
- Create: `backtest/__init__.py`
- Create: `backtest/exceptions.py`
- Create: `backtest/utils/validators.py`

#### 步骤 1: 创建模块入口

```python
# backtest/__init__.py
"""Backtest Module - 回测模块"""

__version__ = "1.0.0"

from .services import BacktestService
from .config import BacktestConfig
from .models import (
    Signal,
    Trade,
    Position,
    DailyMetrics,
    PerformanceMetrics,
    BacktestResult
)
from .strategies import BaseStrategy, StrategyCombiner
from .strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)

__all__ = [
    'BacktestService',
    'BacktestConfig',
    'Signal',
    'Trade',
    'Position',
    'DailyMetrics',
    'PerformanceMetrics',
    'BacktestResult',
    'BaseStrategy',
    'StrategyCombiner',
    'FiveDimensionStrategy',
    'VCPBreakoutStrategy',
    'TDGoldenPitStrategy',
    'TopDivergenceStrategy',
]
```

#### 步骤 2: 创建自定义异常

```python
# backtest/exceptions.py
"""Backtest Exceptions - 回测异常"""


class BacktestError(Exception):
    """回测基础异常"""
    pass


class InsufficientDataError(BacktestError):
    """数据不足异常"""
    pass


class InsufficientFundsError(BacktestError):
    """资金不足异常"""
    pass


class InsufficientSharesError(BacktestError):
    """持仓不足异常"""
    pass


class InvalidConfigError(BacktestError):
    """配置无效异常"""
    pass
```

#### 步骤 3: 创建工具验证器

```python
# backtest/utils/validators.py
"""Input Validators - 输入验证"""


def validate_date_format(date_str: str) -> bool:
    """验证日期格式 (YYYY-MM-DD)"""
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def validate_positive_number(value: float, name: str = "value") -> None:
    """验证正数"""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_percentage(value: float, name: str = "percentage") -> None:
    """验证百分比 (0-1)"""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    return bool(symbol and len(symbol) <= 10)
```

#### 步骤 4: 提交

```bash
git add backtest/__init__.py backtest/exceptions.py backtest/utils/validators.py
git commit -m "feat: add backtest module structure and base files"
```

---

### 任务 2: 配置管理

**Files:**
- Create: `backtest/config.py`

#### 步骤 1: 编写测试

```python
# tests/backtest/test_config.py
"""Test Backtest Config"""

import pytest
from backtest.config import BacktestConfig


def test_default_config():
    """测试默认配置"""
    config = BacktestConfig()
    assert config.initial_capital == 100000.0
    assert config.commission_rate == 0.00025
    assert config.start_date == "2023-01-01"


def test_custom_config():
    """测试自定义配置"""
    config = BacktestConfig(
        initial_capital=500000,
        commission_rate=0.0003,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    assert config.initial_capital == 500000
    assert config.commission_rate == 0.0003
    assert config.start_date == "2024-01-01"


def test_invalid_config():
    """测试无效配置"""
    with pytest.raises(ValueError):
        BacktestConfig(initial_capital=-10000)
```

#### 步骤 2: 运行测试 (应该失败)

```bash
pytest tests/backtest/test_config.py -v
# Expected: ERROR - ModuleNotFoundError: No module named 'backtest.config'
```

#### 步骤 3: 实现配置类

```python
# backtest/config.py
"""Backtest Configuration - 回测配置"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BacktestConfig:
    """回测配置"""

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

    def __post_init__(self):
        """验证配置"""
        from .utils.validators import validate_positive_number, validate_date_format

        # 验证初始资金
        validate_positive_number(self.initial_capital, "initial_capital")

        # 验证手续费率
        if not 0 <= self.commission_rate <= 0.01:
            raise ValueError(f"commission_rate must be between 0 and 0.01, got {self.commission_rate}")

        # 验证日期格式
        if not validate_date_format(self.start_date):
            raise ValueError(f"Invalid start_date format: {self.start_date}")
        if not validate_date_format(self.end_date):
            raise ValueError(f"Invalid end_date format: {self.end_date}")

        # 验证回测时间
        if self.start_date >= self.end_date:
            raise ValueError(f"start_date must be before end_date")

        # 验证仓位
        if not 0 < self.position_size <= 1:
            raise ValueError(f"position_size must be between 0 and 1, got {self.position_size}")

        # 验证最大持仓数
        if self.max_positions < 1:
            raise ValueError(f"max_positions must be >= 1, got {self.max_positions}")
```

#### 步骤 4: 运行测试 (应该通过)

```bash
pytest tests/backtest/test_config.py -v
# Expected: PASSED
```

#### 步骤 5: 提交

```bash
git add backtest/config.py tests/backtest/test_config.py
git commit -m "feat: add backtest configuration management"
```

---

### 任务 3: 数据模型定义

**Files:**
- Create: `backtest/models.py`

#### 步骤 1: 编写测试

```python
# tests/backtest/test_models.py
"""Test Data Models"""

import pytest
from datetime import datetime
from backtest.models import Signal, Trade, Position, DailyMetrics, PerformanceMetrics, BacktestResult


def test_signal_creation():
    """测试信号创建"""
    signal = Signal(
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0
    )
    assert signal.symbol == "600519"
    assert signal.action == "BUY"
    assert signal.position_size == 0.1  # 默认仓位


def test_trade_creation():
    """测试交易创建"""
    trade = Trade(
        trade_id=1,
        symbol="600519",
        date="2024-01-01",
        action="BUY",
        price=1500.0,
        quantity=100,
        amount=150000.0,
        commission=37.5,
        slippage=150.0,
        total_cost=150187.5
    )
    assert trade.pnl is None  # 买入时无盈亏


def test_position_creation():
    """测试持仓创建"""
    position = Position(
        symbol="600519",
        quantity=100,
        cost_price=1500.0,
        market_price=1600.0,
        market_value=160000.0,
        floating_pl=10000.0,
        entry_date="2024-01-01"
    )
    assert position.floating_pl == 10000.0
```

#### 步骤 2: 运行测试 (应该失败)

```bash
pytest tests/backtest/test_models.py -v
# Expected: ERROR - ModuleNotFoundError: No module named 'backtest.models'
```

#### 步骤 3: 实现数据模型

```python
# backtest/models.py
"""Data Models - 数据模型"""

from dataclasses import dataclass, field
from typing import List, Optional
from backtest.config import BacktestConfig


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

    def __post_init__(self):
        """设置默认值"""
        if self.position_size is None:
            self.position_size = 0.1  # 默认仓位 10%


@dataclass
class Trade:
    """交易记录"""
    trade_id: int
    symbol: str
    date: str
    action: str  # "BUY" or "SELL"
    price: float
    quantity: int
    amount: float  # price * quantity
    commission: float
    slippage: float
    total_cost: float  # amount + commission + slippage
    pnl: Optional[float] = None  # 盈亏 (卖出时计算)


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float
    market_value: float  # market_price * quantity
    floating_pl: float  # (market_price - cost_price) * quantity
    entry_date: str


@dataclass
class DailyMetrics:
    """每日指标"""
    date: str
    total_value: float
    cash: float
    stock_value: float
    positions_count: int
    daily_return: float  # 当日收益率 (%)
    cumulative_return: float  # 累计收益率 (%)


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

#### 步骤 4: 运行测试 (应该通过)

```bash
pytest tests/backtest/test_models.py -v
# Expected: PASSED
```

#### 步骤 5: 提交

```bash
git add backtest/models.py tests/backtest/test_models.py
git commit -m "feat: add backtest data models (Signal, Trade, Position, Metrics, Result)"
```

---

### 任务 4: 数据源适配器

**Files:**
- Create: `backtest/core/data_feed.py`

#### 步骤 1: 编写测试

```python
# tests/backtest/test_data_feed.py
"""Test Data Feed"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from backtest.core.data_feed import DataFeed


def test_data_feed_initialization():
    """测试数据源适配器初始化"""
    mock_session = Mock(spec=Session)
    data_feed = DataFeed(mock_session)
    assert data_feed.session is not None


@patch('backtest.core.data_feed.KLineRepository')
def test_get_stock_data(mock_kline_repo):
    """测试获取股票数据"""
    from backtest.core.data_feed import DataFeed

    mock_session = Mock(spec=Session)
    data_feed = DataFeed(mock_session)

    # Mock KLine data
    mock_kline = Mock()
    mock_kline.open_price = 1500.0
    mock_kline.high_price = 1520.0
    mock_kline.low_price = 1490.0
    mock_kline.close_price = 1510.0
    mock_kline.volume = 1000000
    mock_kline.timestamp = "2024-01-01"

    mock_kline_repo.return_value.query_klines.return_value = [mock_kline]

    df = data_feed.get_stock_data("600519", "2024-01-01", "2024-01-31")

    assert len(df) == 1
    assert df['open'].iloc[0] == 1500.0
    assert df['close'].iloc[0] == 1510.0
```

#### 步骤 2: 运行测试 (应该失败)

```bash
pytest tests/backtest/test_data_feed.py -v
# Expected: ERROR - ModuleNotFoundError: No module named 'backtest.core.data_feed'
```

#### 步骤 3: 实现数据源适配器

```python
# backtest/core/data_feed.py
"""Data Feed - 数据源适配器"""

import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from stock_market.repositories import KLineRepository
from stock_market.schemas import KLineQueryParams


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

        if not klines:
            raise ValueError(f"No data found for {symbol} from {start_date} to {end_date}")

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

#### 步骤 4: 运行测试 (应该通过)

```bash
pytest tests/backtest/test_data_feed.py -v
# Expected: PASSED
```

#### 步骤 5: 提交

```bash
git add backtest/core/data_feed.py tests/backtest/test_data_feed.py
git commit -m "feat: add data feed adapter for stock_market integration"
```

---

### 任务 5: 持仓跟踪器和经纪商模拟器

**Files:**
- Create: `backtest/core/position_tracker.py`
- Create: `backtest/core/broker_simulator.py`

#### 步骤 1: 编写持仓跟踪器测试

```python
# tests/backtest/test_position_tracker.py
"""Test Position Tracker"""

import pytest
from backtest.core.position_tracker import PositionTracker


def test_position_tracker_initialization():
    """测试持仓跟踪器初始化"""
    tracker = PositionTracker(initial_capital=100000)
    assert tracker.cash == 100000
    assert len(tracker.positions) == 0


def test_buy_stock():
    """测试买入股票"""
    tracker = PositionTracker(initial_capital=100000)
    success = tracker.buy(symbol="600519", quantity=100, price=1500.0)

    assert success is True
    assert tracker.cash == 100000 - 150000  # 100 * 1500
    assert tracker.positions["600519"].quantity == 100


def test_sell_stock():
    """测试卖出股票"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    success = tracker.sell(symbol="600519", quantity=50, price=1600.0)

    assert success is True
    assert tracker.cash == -50000 + 50 * 1600  # 买入后现金 + 卖出收入


def test_get_total_value():
    """测试获取总资产"""
    tracker = PositionTracker(initial_capital=100000)
    tracker.buy(symbol="600519", quantity=100, price=1500.0)
    tracker.update_market_value(symbol="600519", current_price=1600.0)

    total_value = tracker.get_total_value()
    assert total_value == -50000 + 100 * 1600  # 现金 + 股票市值
```

#### 步骤 2: 运行测试 (应该失败)

```bash
pytest tests/backtest/test_position_tracker.py -v
# Expected: ERROR - ModuleNotFoundError: No module named 'backtest.core.position_tracker'
```

#### 步骤 3: 实现持仓跟踪器

```python
# backtest/core/position_tracker.py
"""Position Tracker - 持仓跟踪器"""

from typing import Dict, Optional
from dataclasses import dataclass
from backtest.exceptions import InsufficientFundsError, InsufficientSharesError


@dataclass
class Position:
    """持仓信息 (内部使用)"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float = 0.0
    entry_date: Optional[str] = None


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
        self.positions: Dict[str, Position] = {}

    def buy(self, symbol: str, quantity: int, price: float) -> bool:
        """
        买入股票

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格

        Returns:
            bool: 是否成功

        Raises:
            InsufficientFundsError: 资金不足
        """
        total_cost = quantity * price

        if self.cash < total_cost:
            raise InsufficientFundsError(
                f"Insufficient funds: need {total_cost}, have {self.cash}"
            )

        if symbol in self.positions:
            # 加仓 - 更新成本价 (加权平均)
            existing = self.positions[symbol]
            new_cost_price = (
                existing.cost_price * existing.quantity + price * quantity
            ) / (existing.quantity + quantity)

            existing.quantity += quantity
            existing.cost_price = new_cost_price
        else:
            # 新建持仓
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=price
            )

        self.cash -= total_cost
        return True

    def sell(self, symbol: str, quantity: int, price: float) -> bool:
        """
        卖出股票

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格

        Returns:
            bool: 是否成功

        Raises:
            InsufficientSharesError: 持仓不足
        """
        if symbol not in self.positions:
            raise InsufficientSharesError(f"No position for {symbol}")

        position = self.positions[symbol]

        if position.quantity < quantity:
            raise InsufficientSharesError(
                f"Insufficient shares: need {quantity}, have {position.quantity}"
            )

        # 更新持仓
        position.quantity -= quantity
        if position.quantity == 0:
            del self.positions[symbol]

        # 增加现金
        self.cash += quantity * price
        return True

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            Position or None
        """
        return self.positions.get(symbol)

    def update_market_value(self, symbol: str, current_price: float):
        """
        更新持仓市值

        Args:
            symbol: 股票代码
            current_price: 当前价格
        """
        if symbol in self.positions:
            self.positions[symbol].market_price = current_price

    def get_total_value(self) -> float:
        """
        获取总资产 (现金 + 股票市值)

        Returns:
            总资产
        """
        stock_value = sum(
            p.market_price * p.quantity if p.market_price > 0 else p.cost_price * p.quantity
            for p in self.positions.values()
        )
        return self.cash + stock_value

    def get_positions(self) -> Dict[str, Position]:
        """
        获取所有持仓

        Returns:
            持仓字典
        """
        return self.positions.copy()
```

#### 步骤 4: 编写经纪商模拟器测试

```python
# tests/backtest/test_broker_simulator.py
"""Test Broker Simulator"""

import pytest
from backtest.core.broker_simulator import BrokerSimulator


def test_broker_initialization():
    """测试经纪商初始化"""
    broker = BrokerSimulator()
    assert broker.commission_rate == 0.00025
    assert broker.slippage_rate == 0.001


def test_calculate_commission():
    """测试手续费计算"""
    broker = BrokerSimulator(commission_rate=0.00025)
    commission = broker.calculate_commission(100000)
    assert commission == 25.0  # 100000 * 0.00025


def test_apply_slippage_buy():
    """测试买入滑点"""
    broker = BrokerSimulator(slippage_rate=0.001)
    adjusted_price = broker.apply_slippage(price=1500.0, direction='buy')
    assert adjusted_price == 1500.0 * 1.001


def test_apply_slippage_sell():
    """测试卖出滑点"""
    broker = BrokerSimulator(slippage_rate=0.001)
    adjusted_price = broker.apply_slippage(price=1500.0, direction='sell')
    assert adjusted_price == 1500.0 * 0.999


def test_execute_order_buy():
    """测试执行买入订单"""
    broker = BrokerSimulator()
    result = broker.execute_order(
        symbol="600519",
        quantity=100,
        price=1500.0,
        direction="buy"
    )

    assert result.symbol == "600519"
    assert result.direction == "buy"
    assert result.actual_price > 1500.0  # 滑点后价格更高
    assert result.commission == 1500.0 * 100 * 0.00025
```

#### 步骤 5: 运行测试 (应该失败)

```bash
pytest tests/backtest/test_broker_simulator.py -v
# Expected: ERROR - ModuleNotFoundError: No module named 'backtest.core.broker_simulator'
```

#### 步骤 6: 实现经纪商模拟器

```python
# backtest/core/broker_simulator.py
"""Broker Simulator - 经纪商模拟器"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """订单执行结果"""
    symbol: str
    direction: str  # 'buy' or 'sell'
    quantity: int
    requested_price: float
    actual_price: float
    slippage: float
    commission: float
    total_cost: float


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
        elif direction == 'sell':
            return price * (1 - self.slippage_rate)
        else:
            raise ValueError(f"Invalid direction: {direction}")

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
            ExecutionResult: 执行结果
        """
        # 应用滑点
        actual_price = self.apply_slippage(price, direction)
        slippage = abs(actual_price - price)

        # 计算手续费
        amount = actual_price * quantity
        commission = self.calculate_commission(amount)

        # 卖出时计算印花税
        stamp_duty = 0.0
        if direction == 'sell':
            stamp_duty = amount * self.stamp_duty_rate

        # 总成本
        total_cost = commission + stamp_duty

        return ExecutionResult(
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            requested_price=price,
            actual_price=actual_price,
            slippage=slippage,
            commission=commission,
            total_cost=total_cost
        )
```

#### 步骤 7: 运行所有测试

```bash
pytest tests/backtest/test_position_tracker.py tests/backtest/test_broker_simulator.py -v
# Expected: PASSED
```

#### 步骤 8: 提交

```bash
git add backtest/core/position_tracker.py backtest/core/broker_simulator.py
git add tests/backtest/test_position_tracker.py tests/backtest/test_broker_simulator.py
git commit -m "feat: add position tracker and broker simulator"
```

---

### 阶段 2: 策略系统 (任务 6-11) - 4-5 天

**任务 6-11 将在后续提交中继续...**

---

## 📊 实施进度

| 阶段 | 任务数 | 状态 | 预计时间 |
|------|--------|------|----------|
| 阶段 1: 基础框架 | 5/17 | ✅ 进行中 | 3-4 天 |
| 阶段 2: 策略系统 | 6/17 | ⏳ 待开始 | 4-5 天 |
| 阶段 3: 核心引擎 | 3/17 | ⏳ 待开始 | 3-4 天 |
| 阶段 4: 服务层和集成 | 3/17 | ⏳ 待开始 | 2-3 天 |

**总任务数:** 17 个任务
**预计总时间:** 3-4 周
**当前进度:** 5/17 (29%)

---

## ⚠️ 关键注意事项

1. **模块复用:** 复用 `stock_market` 的 `KLineRepository`，复用 `technical_analysis` 的策略信号
2. **测试优先:** 每个任务都遵循 TDD 流程
3. **小步提交:** 每个步骤完成后立即提交
4. **代码质量:** 保持文件在 200-400 行，函数在 50 行以内
5. **类型注解:** 所有公共接口必须有类型注解
6. **错误处理:** 显式处理所有可能的错误

---

**计划保存位置:** `docs/superpowers/plans/2026-03-17-backtest-module-implementation.md`
