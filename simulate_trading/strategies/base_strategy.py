"""
策略基类 - 定义策略的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
import logging

from simulate_trading.exceptions import StrategyExecutionError


@dataclass
class StrategyConfig:
    """策略配置数据类"""
    name: str
    description: str
    initial_cash: float
    max_position: float  # 最大仓位比例
    min_position: float  # 最小仓位比例
    stop_loss: float     # 止损比例（负数）
    take_profit: float   # 止盈比例（正数）
    trade_ratio: float   # 每次交易仓位比例
    chase_threshold: Optional[float] = None  # 追涨阈值
    cut_loss_threshold: Optional[float] = None  # 杀跌阈值
    trend_follow_days: Optional[int] = None  # 趋势跟踪天数
    value_threshold: Optional[float] = None  # 价值投资阈值


@dataclass
class TradeSignal:
    """交易信号"""
    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: float
    reason: str
    confidence: float  # 置信度 0-1


@dataclass
class StrategyResult:
    """策略执行结果"""
    strategy_name: str
    executed_trades: List[TradeSignal] = field(default_factory=list)
    skipped_trades: List[TradeSignal] = field(default_factory=list)
    total_value: float = 0.0
    profit: float = 0.0
    profit_pct: float = 0.0
    position_count: int = 0
    execution_time: datetime = field(default_factory=datetime.utcnow)


class BaseStrategy(ABC):
    """
    策略基类 - 所有策略的抽象基类
    """

    def __init__(self, config: StrategyConfig, db_session):
        """
        初始化策略

        Args:
            config: 策略配置
            db_session: 数据库会话
        """
        self.config = config
        self.db = db_session
        self.logger = logging.getLogger(f"simulate_trading.strategy.{config.name}")

        # 延迟导入，避免循环依赖
        from simulate_trading.services import TradingDataService, TradeExecutor
        from simulate_trading.repositories import (
            StrategyAccountRepository,
            StrategyTradeRepository,
            DailyReportRepository
        )
        from simulate_trading.utils import PositionManager

        self.data_service = TradingDataService(db_session)
        self.trade_executor = TradeExecutor(db_session, config.name)
        self.account_repo = StrategyAccountRepository(db_session)
        self.trade_repo = StrategyTradeRepository(db_session)
        self.report_repo = DailyReportRepository(db_session)
        self.position_manager = PositionManager(config.name)

        self.logger.info(f"初始化策略: {config.name}")

    @abstractmethod
    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        分析交易机会 - 子类必须实现

        Returns:
            交易信号列表
        """
        pass

    @abstractmethod
    def execute(self) -> StrategyResult:
        """
        执行策略核心逻辑 - 子类必须实现

        Returns:
            策略执行结果
        """
        pass

    def get_account_summary(self) -> Dict:
        """获取账户汇总信息"""
        account = self.account_repo.get_by_name(self.config.name)

        if not account:
            from simulate_trading.models import StrategyAccount
            account = StrategyAccount(
                strategy_name=self.config.name,
                initial_cash=self.config.initial_cash,
                current_cash=self.config.initial_cash,
                total_value=self.config.initial_cash,
                total_profit=0.0,
                total_profit_pct=0.0,
                position_count=0
            )
            self.account_repo.create(account)
            self.db.commit()

        return {
            'strategy_name': account.strategy_name,
            'current_cash': float(account.current_cash),
            'total_value': float(account.total_value),
            'total_profit': float(account.total_profit),
            'total_profit_pct': float(account.total_profit_pct),
            'position_count': account.position_count
        }

    def calculate_position_ratio(self) -> float:
        """计算当前仓位比例"""
        summary = self.get_account_summary()
        if summary['total_value'] == 0:
            return 0.0
        stock_value = summary['total_value'] - summary['current_cash']
        return stock_value / summary['total_value']

    def validate_config(self):
        """验证配置参数的有效性"""
        errors = []

        if not (0 < self.config.max_position <= 1):
            errors.append("max_position 必须在 0-1 之间")
        if not (0 <= self.config.min_position < self.config.max_position):
            errors.append("min_position 必须小于 max_position 且 >= 0")
        if not (-1 < self.config.stop_loss < 0):
            errors.append("stop_loss 必须在 -1 到 0 之间")
        if not (0 < self.config.take_profit <= 1):
            errors.append("take_profit 必须在 0-1 之间")
        if not (0 < self.config.trade_ratio <= 1):
            errors.append("trade_ratio 必须在 0-1 之间")

        if errors:
            from simulate_trading.exceptions import InvalidStrategyConfigError
            raise InvalidStrategyConfigError("; ".join(errors))

    def _calculate_trade_quantity(self, available_cash: float, price: float) -> int:
        """
        计算交易数量（100股整数倍）

        Args:
            available_cash: 可用资金
            price: 股票价格

        Returns:
            交易数量
        """
        trade_amount = available_cash * self.config.trade_ratio
        quantity = int(trade_amount / price / 100) * 100
        return max(quantity, 100) if quantity >= 100 else 0
