"""
稳健型策略 - 中等仓位趋势跟踪，波段操作
"""

from typing import List
from datetime import datetime

from .base_strategy import BaseStrategy, StrategyConfig, TradeSignal, StrategyResult


class ModerateStrategy(BaseStrategy):
    """
    稳健型策略：中等仓位趋势跟踪，波段操作

    特点：
    - 中等仓位（最高7成）
    - 趋势跟踪：选择走势稳定的股票
    - 波段操作：持有数天至数周
    - 严格止盈止损
    """

    def __init__(self, config: StrategyConfig, db_session):
        super().__init__(config, db_session)
        self.logger.info("初始化稳健型策略")

    def analyze_opportunities(self) -> List[TradeSignal]:
        """稳健型机会分析"""
        signals = []

        try:
            summary = self.get_account_summary()
            current_cash = summary['current_cash']
            position_ratio = self.calculate_position_ratio()

            self.logger.info(f"当前仓位: {position_ratio:.1%}, 现金: {current_cash:,.2f}")

            # 买入机会：仓位未满且有合适机会
            if position_ratio < self.config.max_position:
                signals.extend(self._find_trend_opportunities(current_cash))

            # 卖出机会
            signals.extend(self._find_exit_opportunities())

        except Exception as e:
            self.logger.error(f"分析机会失败: {e}", exc_info=True)

        return signals

    def _find_trend_opportunities(self, current_cash: float) -> List[TradeSignal]:
        """寻找趋势机会"""
        signals = []
        hot_stocks = self.data_service.get_hot_stocks()

        for symbol, name in hot_stocks[:8]:
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                change_pct = price_data.get('change_percent', 0)
                current_price = price_data.get('price', 0)

                # 趋势确认：温和上涨
                if 1 <= change_pct <= 5:
                    position = self.position_manager.get_position(symbol)
                    if not position:
                        quantity = self._calculate_trade_quantity(current_cash, current_price)
                        if quantity >= 100:
                            signals.append(TradeSignal(
                                symbol=symbol,
                                action='buy',
                                quantity=quantity,
                                price=current_price,
                                reason=f'趋势: {name} 涨幅{change_pct:.2f}%',
                                confidence=0.6
                            ))

            except Exception as e:
                self.logger.warning(f"分析股票 {symbol} 失败: {e}")

        return signals

    def _find_exit_opportunities(self) -> List[TradeSignal]:
        """寻找卖出机会"""
        signals = []
        positions = self.position_manager.get_all_positions()

        for symbol, position in positions.items():
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                current_price = price_data.get('price', 0)
                profit_pct = (current_price - position.cost_price) / position.cost_price

                # 止盈
                if profit_pct >= self.config.take_profit:
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'止盈: 盈利{profit_pct:.2%}',
                        confidence=0.8
                    ))

                # 止损
                elif profit_pct <= self.config.stop_loss:
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'止损: 亏损{profit_pct:.2%}',
                        confidence=0.8
                    ))

            except Exception as e:
                self.logger.warning(f"分析持仓 {symbol} 失败: {e}")

        return signals

    def execute(self) -> StrategyResult:
        """执行稳健型策略"""
        self.logger.info("=== 开始执行稳健型策略 ===")

        start_time = datetime.utcnow()
        executed_trades = []
        skipped_trades = []

        try:
            self.validate_config()
            signals = self.analyze_opportunities()

            for signal in signals:
                try:
                    if signal.action == 'buy':
                        self.trade_executor.execute_buy(
                            signal.symbol,
                            signal.quantity,
                            signal.price,
                            signal.reason
                        )
                        self.position_manager.add_position(
                            signal.symbol,
                            signal.quantity,
                            signal.price
                        )
                    else:
                        self.trade_executor.execute_sell(
                            signal.symbol,
                            signal.quantity,
                            signal.price,
                            signal.reason
                        )
                        self.position_manager.reduce_position(
                            signal.symbol,
                            signal.quantity
                        )

                    executed_trades.append(signal)

                except Exception as e:
                    skipped_trades.append(signal)
                    self.logger.warning(f"跳过交易 {signal.symbol}: {e}")

            summary = self.get_account_summary()

            result = StrategyResult(
                strategy_name=self.config.name,
                executed_trades=executed_trades,
                skipped_trades=skipped_trades,
                total_value=summary['total_value'],
                profit=summary['total_profit'],
                profit_pct=summary['total_profit_pct'],
                position_count=summary['position_count'],
                execution_time=start_time
            )

            self.logger.info(f"=== 策略执行完成 === 总资产: {result.total_value:,.2f}, 收益: {result.profit:+,.2f}")

            return result

        except Exception as e:
            self.logger.error(f"策略执行失败: {e}", exc_info=True)
            raise
