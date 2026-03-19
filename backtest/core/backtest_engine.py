"""Backtest Engine - 回测引擎"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from backtest.config import BacktestConfig
from backtest.core.position_tracker import PositionTracker
from backtest.core.broker_simulator import BrokerSimulator
from backtest.core.data_feed import DataFeed
from backtest.strategies.base_strategy import BaseStrategy, Signal
from backtest.models import (
    Trade,
    DailyMetrics,
    BacktestResult,
    PerformanceMetrics
)
from backtest.analyzers.metrics import MetricsCalculator
from backtest.analyzers.trade_analyzer import TradeAnalyzer


class BacktestEngine:
    """
    回测引擎 - 事件驱动核心

    核心流程:
    1. 初始化数据
    2. 逐日推进
    3. 每日执行:
       - 获取当日数据
       - 调用策略生成信号
       - 执行交易 (买入/卖出)
       - 更新持仓
       - 记录绩效指标
    4. 生成最终报告
    """

    def __init__(
        self,
        config: BacktestConfig,
        data_feed: DataFeed,
        strategy: BaseStrategy,
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
            slippage_rate=config.slippage_rate,
            stamp_duty_rate=config.stamp_duty_rate
        )
        self.metrics_calculator = MetricsCalculator()
        self.trade_analyzer = TradeAnalyzer()

        # 运行状态
        self.current_date = None
        self.trades: List[Trade] = []
        self.daily_metrics: List[DailyMetrics] = []
        self.equity_curve: List[float] = []
        self.dates: List[str] = []
        self.trade_id_counter = 1

    def run(self, symbol: str, start_date: str, end_date: str) -> BacktestResult:
        """
        运行回测

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            BacktestResult: 回测结果
        """
        # 获取数据
        df = self.data_feed.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=self.config.interval
        )

        if len(df) < 30:
            raise ValueError(
                f"数据不足，需要至少 30 条 K 线，当前只有 {len(df)} 条"
            )

        # 初始化权益曲线
        self.equity_curve = [self.initial_capital]
        self.dates = [start_date]

        # 逐日推进
        prev_close = None
        for date, row in df.iterrows():
            self.current_date = str(date)
            self.dates.append(self.current_date)

            # 转换为 dict 格式供策略使用
            data_dict = {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }

            # 更新持仓市值
            if prev_close is not None:
                self.position_tracker.update_market_value(symbol, prev_close)

            # 调用策略生成信号
            signal = self.strategy.on_data(symbol, data_dict, self.current_date)

            # 执行交易
            self._execute_trade(signal, row['close'])

            # 记录当日指标
            self._record_daily_metrics()

            # 更新前收盘价
            prev_close = row['close']

        # 生成最终结果
        result = self._generate_result(symbol, start_date, end_date)

        return result

    def _execute_trade(self, signal: Signal, current_price: float):
        """
        执行交易

        Args:
            signal: 交易信号
            current_price: 当前价格
        """
        if signal.action == "BUY":
            self._execute_buy(signal, current_price)
        elif signal.action == "SELL":
            self._execute_sell(signal, current_price)
        # HOLD or other actions: do nothing

    def _execute_buy(self, signal: Signal, current_price: float):
        """
        执行买入

        Args:
            signal: 买入信号
            current_price: 当前价格
        """
        # 计算买入金额
        buy_amount = self.position_tracker.get_total_value() * signal.position_size
        quantity = int(buy_amount / current_price)

        if quantity <= 0:
            return  # Quantity too small

        # 执行订单
        execution = self.broker.execute_order(
            symbol=signal.symbol,
            quantity=quantity,
            price=current_price,
            direction="buy"
        )

        # 买入股票
        success = self.position_tracker.buy(
            symbol=signal.symbol,
            quantity=quantity,
            price=execution.actual_price
        )

        if success:
            # 记录交易
            trade = Trade(
                trade_id=self.trade_id_counter,
                symbol=signal.symbol,
                date=signal.date,
                action="BUY",
                price=execution.actual_price,
                quantity=quantity,
                amount=execution.actual_price * quantity,
                commission=execution.commission,
                slippage=execution.slippage,
                total_cost=execution.total_cost
            )
            self.trades.append(trade)
            self.trade_id_counter += 1

    def _execute_sell(self, signal: Signal, current_price: float):
        """
        执行卖出

        Args:
            signal: 卖出信号
            current_price: 当前价格
        """
        # 获取当前持仓
        position = self.position_tracker.get_position(signal.symbol)

        if not position or position.quantity <= 0:
            return  # No position to sell

        # 执行订单
        execution = self.broker.execute_order(
            symbol=signal.symbol,
            quantity=position.quantity,
            price=current_price,
            direction="sell"
        )

        # 卖出股票
        success = self.position_tracker.sell(
            symbol=signal.symbol,
            quantity=position.quantity,
            price=execution.actual_price
        )

        if success:
            # 计算盈亏 (简化版)
            pnl = (execution.actual_price - position.cost_price) * position.quantity - execution.total_cost

            # 记录交易
            trade = Trade(
                trade_id=self.trade_id_counter,
                symbol=signal.symbol,
                date=signal.date,
                action="SELL",
                price=execution.actual_price,
                quantity=position.quantity,
                amount=execution.actual_price * position.quantity,
                commission=execution.commission,
                slippage=execution.slippage,
                total_cost=execution.total_cost,
                pnl=pnl
            )
            self.trades.append(trade)
            self.trade_id_counter += 1

    def _record_daily_metrics(self):
        """
        记录当日指标
        """
        total_value = self.position_tracker.get_total_value()

        # 计算日收益率
        if len(self.equity_curve) > 0:
            prev_value = self.equity_curve[-1]
            daily_return = ((total_value / prev_value) - 1) * 100 if prev_value > 0 else 0
        else:
            daily_return = 0

        # 计算累计收益率
        cumulative_return = ((total_value / self.initial_capital) - 1) * 100

        metrics = DailyMetrics(
            date=self.current_date,
            total_value=total_value,
            cash=self.position_tracker.cash,
            stock_value=total_value - self.position_tracker.cash,
            positions_count=len(self.position_tracker.positions),
            daily_return=daily_return,
            cumulative_return=cumulative_return
        )

        self.daily_metrics.append(metrics)
        self.equity_curve.append(total_value)

    def _generate_result(self, symbol: str, start_date: str, end_date: str) -> BacktestResult:
        """
        生成回测结果

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            BacktestResult
        """
        # 计算绩效指标
        total_return = self.metrics_calculator.calculate_total_return(self.equity_curve)
        annual_return = self.metrics_calculator.calculate_annual_return(
            total_return,
            (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        )
        max_drawdown = self.metrics_calculator.calculate_max_drawdown(self.equity_curve)
        volatility = self.metrics_calculator.calculate_volatility(
            [m.daily_return / 100 for m in self.daily_metrics]
        )
        sharpe_ratio = self.metrics_calculator.calculate_sharpe_ratio(
            [m.daily_return / 100 for m in self.daily_metrics]
        )
        sortino_ratio = self.metrics_calculator.calculate_sortino_ratio(
            [m.daily_return / 100 for m in self.daily_metrics]
        )
        calmar_ratio = self.metrics_calculator.calculate_calmar_ratio(
            annual_return,
            max_drawdown
        )

        # 交易统计
        trade_stats = self.trade_analyzer.analyze_trades(self.trades)

        performance = PerformanceMetrics(
            total_return=total_return,
            annual_return=annual_return,
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=trade_stats['total_trades'],
            winning_trades=trade_stats['winning_trades'],
            losing_trades=trade_stats['losing_trades'],
            win_rate=trade_stats['win_rate'],
            profit_factor=trade_stats['profit_factor'],
            avg_holding_days=trade_stats['avg_holding_days'],
            max_consecutive_wins=trade_stats['max_consecutive_wins'],
            max_consecutive_losses=trade_stats['max_consecutive_losses']
        )

        return BacktestResult(
            config=self.config,
            strategy_name=self.strategy.get_name(),
            trades=self.trades,
            daily_metrics=self.daily_metrics,
            positions_history=[],  # TODO: Implement position history tracking
            performance=performance,
            equity_curve=self.equity_curve,
            dates=self.dates
        )
