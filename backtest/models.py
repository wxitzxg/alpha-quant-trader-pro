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
            self.position_size = 0.1  # Default position size 10%


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
