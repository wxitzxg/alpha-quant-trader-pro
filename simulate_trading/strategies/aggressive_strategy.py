"""
激进型策略 - 高仓位追涨杀跌，短线为主
"""

from typing import List
from datetime import datetime

from .base_strategy import BaseStrategy, StrategyConfig, TradeSignal, StrategyResult


class AggressiveStrategy(BaseStrategy):
    """
    激进型策略：高仓位追涨杀跌，短线为主

    特点：
    - 高仓位（最高9成）
    - 追涨：涨幅>5%且未持仓，建议买入
    - 杀跌：跌幅>3%且持仓亏损，建议卖出
    - 快进快出，短线操作
    """

    def __init__(self, config: StrategyConfig, db_session):
        super().__init__(config, db_session)
        self.logger.info("初始化激进型策略")

    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        激进型机会分析：
        1. 追涨机会：热门股涨幅>5%且无持仓
        2. 杀跌机会：持仓股跌幅>3%且亏损
        3. 止盈机会：持仓股涨幅>15%
        4. 止损机会：持仓股跌幅>8%
        """
        signals = []

        try:
            # 获取账户信息
            summary = self.get_account_summary()
            current_cash = summary['current_cash']
            position_ratio = self.calculate_position_ratio()

            self.logger.info(f"当前仓位: {position_ratio:.1%}, 现金: {current_cash:,.2f}")

            # 追涨机会
            if position_ratio < self.config.max_position:
                signals.extend(self._find_chase_opportunities(current_cash))

            # 杀跌、止盈、止损机会
            signals.extend(self._find_exit_opportunities())

            self.logger.info(f"发现 {len(signals)} 个交易机会")

        except Exception as e:
            self.logger.error(f"分析机会失败: {e}", exc_info=True)

        return signals

    def _find_chase_opportunities(self, current_cash: float) -> List[TradeSignal]:
        """寻找追涨机会"""
        signals = []

        hot_stocks = self.data_service.get_hot_stocks()

        for symbol, name in hot_stocks[:10]:  # 分析前10只热门股
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                change_pct = price_data.get('change_percent', 0)
                current_price = price_data.get('price', 0)

                # 追涨条件：涨幅 > 追涨阈值 且 未持仓
                if change_pct > (self.config.chase_threshold or 0.05):
                    position = self.position_manager.get_position(symbol)
                    if not position:
                        quantity = self._calculate_trade_quantity(current_cash, current_price)
                        if quantity >= 100:
                            signals.append(TradeSignal(
                                symbol=symbol,
                                action='buy',
                                quantity=quantity,
                                price=current_price,
                                reason=f'追涨: {name} 涨幅{change_pct:.2f}%',
                                confidence=0.7 if change_pct > 8 else 0.5
                            ))
                            self.logger.info(f"追涨机会: {name} +{change_pct:.2f}%")

            except Exception as e:
                self.logger.warning(f"分析股票 {symbol} 失败: {e}")

        return signals

    def _find_exit_opportunities(self) -> List[TradeSignal]:
        """寻找卖出机会（杀跌、止盈、止损）"""
        signals = []

        positions = self.position_manager.get_all_positions()

        for symbol, position in positions.items():
            try:
                price_data = self.data_service.get_realtime_price(symbol)
                if not price_data:
                    continue

                current_price = price_data.get('price', 0)
                change_pct = price_data.get('change_percent', 0)

                # 计算盈亏
                profit_pct = (current_price - position.cost_price) / position.cost_price

                # 止盈
                if profit_pct >= self.config.take_profit:
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'止盈: 盈利{profit_pct:.2%} >= {self.config.take_profit:.0%}',
                        confidence=0.9
                    ))
                    self.logger.info(f"止盈信号: {symbol} 盈利{profit_pct:.2%}")

                # 止损
                elif profit_pct <= self.config.stop_loss:
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'止损: 亏损{profit_pct:.2%} <= {self.config.stop_loss:.0%}',
                        confidence=0.9
                    ))
                    self.logger.info(f"止损信号: {symbol} 亏损{profit_pct:.2%}")

                # 杀跌：小幅亏损且股价继续下跌
                elif (profit_pct < (self.config.cut_loss_threshold or -0.03) and
                      change_pct < -3):
                    signals.append(TradeSignal(
                        symbol=symbol,
                        action='sell',
                        quantity=position.quantity,
                        price=current_price,
                        reason=f'杀跌: 亏损{profit_pct:.2%} 且股价下跌{change_pct:.2f}%',
                        confidence=0.6
                    ))
                    self.logger.info(f"杀跌信号: {symbol} 亏损{profit_pct:.2%}, 股价-{change_pct:.2f}%")

            except Exception as e:
                self.logger.warning(f"分析持仓 {symbol} 失败: {e}")

        return signals

    def execute(self) -> StrategyResult:
        """执行激进型策略"""
        self.logger.info("=== 开始执行激进型策略 ===")

        start_time = datetime.utcnow()
        executed_trades = []
        skipped_trades = []

        try:
            # 验证配置
            self.validate_config()

            # 分析交易机会
            signals = self.analyze_opportunities()

            # 执行交易
            for signal in signals:
                try:
                    if signal.action == 'buy':
                        self.trade_executor.execute_buy(
                            signal.symbol,
                            signal.quantity,
                            signal.price,
                            signal.reason
                        )
                        # 更新虚拟持仓
                        self.position_manager.add_position(
                            signal.symbol,
                            signal.quantity,
                            signal.price
                        )
                    else:  # sell
                        self.trade_executor.execute_sell(
                            signal.symbol,
                            signal.quantity,
                            signal.price,
                            signal.reason
                        )
                        # 更新虚拟持仓
                        self.position_manager.reduce_position(
                            signal.symbol,
                            signal.quantity
                        )

                    executed_trades.append(signal)
                    self.logger.info(f"✓ 执行交易: {signal.action} {signal.symbol} {signal.quantity} 股 @ {signal.price}")

                except Exception as e:
                    skipped_trades.append(signal)
                    self.logger.warning(f"✗ 跳过交易 {signal.symbol}: {e}")

            # 更新账户摘要
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

            self.logger.info(
                f"=== 策略执行完成 ===\n"
                f"  总资产: {result.total_value:,.2f}\n"
                f"  收益: {result.profit:+,.2f} ({result.profit_pct:+.2f}%)\n"
                f"  执行: {len(executed_trades)} 笔 | 跳过: {len(skipped_trades)} 笔"
            )

            return result

        except Exception as e:
            self.logger.error(f"策略执行失败: {e}", exc_info=True)
            raise
