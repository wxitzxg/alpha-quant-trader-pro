"""
保守型策略 - 低仓位价值投资，长期持有
"""

from typing import List
from datetime import datetime

from .base_strategy import BaseStrategy, StrategyConfig, TradeSignal, StrategyResult


class ConservativeStrategy(BaseStrategy):
    """
    保守型策略：低仓位价值投资，长期持有

    特点：
    - 低仓位（最高5成）
    - 价值投资：选择优质股票
    - 长期持有：数月至数年
    - 极低换手率
    """

    def __init__(self, config: StrategyConfig, db_session):
        super().__init__(config, db_session)
        self.logger.info("初始化保守型策略")

    def analyze_opportunities(self) -> List[TradeSignal]:
        """保守型机会分析"""
        signals = []

        try:
            summary = self.get_account_summary()
            current_cash = summary['current_cash']
            position_ratio = self.calculate_position_ratio()

            self.logger.info(f"当前仓位: {position_ratio:.1%}, 现金: {current_cash:,.2f}")

            # 买入机会：只在仓位很低时买入
            if position_ratio < self.config.min_position:
                signals.extend(self._find_value_opportunities(current_cash))

            # 卖出机会：只在极端情况卖出
            signals.extend(self._find_exit_opportunities())

        except Exception as e:
            self.logger.error(f"分析机会失败: {e}", exc_info=True)

        return signals

    def _find_value_opportunities(self, current_cash: float) -> List[TradeSignal]:
        """寻找价值投资机会"""
        signals = []
        hot_stocks = self.data_service.get_hot_stocks()

        for symbol, name in hot_stocks[:5]:  # 只选最优质的5只
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                current_price = price_data.get('price', 0)
                position = self.position_manager.get_position(symbol)

                if not position:
                    quantity = self._calculate_trade_quantity(current_cash, current_price)
                    if quantity >= 100:
                        signals.append(TradeSignal(
                            symbol=symbol,
                            action='buy',
                            quantity=quantity,
                            price=current_price,
                            reason=f'价值投资: {name}',
                            confidence=0.5
                        ))

            except Exception as e:
                self.logger.warning(f"分析股票 {symbol} 失败: {e}")

        return signals

    def _find_exit_opportunities(self) -> List[TradeSignal]:
        """寻找卖出机会（保守型很少卖出）"""
        signals = []
        positions = self.position_manager.get_all_positions()

        for symbol, position in positions.items():
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                current_price = price_data.get('price', 0)
                profit_pct = (current_price - position.cost_price) / position.cost_price

                # 只在极端亏损时止损
                if profit_pct <= self.config.stop_loss:
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'极端止损: 亏损{profit_pct:.2%}',
                        confidence=0.7
                    ))

            except Exception as e:
                self.logger.warning(f"分析持仓 {symbol} 失败: {e}")

        return signals

    def execute(self) -> StrategyResult:
        """执行保守型策略"""
        self.logger.info("=== 开始执行保守型策略 ===")

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

            self.logger.info(f"=== 策略执行完成 === 总资产: {result.total_value:,.2f}")

            return result

        except Exception as e:
            self.logger.error(f"策略执行失败: {e}", exc_info=True)
            raise
