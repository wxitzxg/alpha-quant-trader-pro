"""
交易执行器 - 执行买入/卖出操作并更新账户
"""

import logging
from typing import Optional
from decimal import Decimal

from simulate_trading.exceptions import InsufficientCashError
from simulate_trading.models import StrategyTrade, StrategyAccount


logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    交易执行器 - 执行买入/卖出操作

    职责：
    1. 执行买入/卖出交易
    2. 计算手续费
    3. 更新策略账户
    4. 记录交易历史
    """

    # 手续费配置（模拟）
    STAMP_DUTY = Decimal('0.001')      # 印花税 0.1%（卖出收取）
    EXCHANGE_FEE = Decimal('0.00002')  # 交易所费用 0.002%
    BROKER_COMMISSION = Decimal('0.0003')  # 券商佣金 0.03%
    MIN_COMMISSION = Decimal('5.0')    # 最低佣金 5元

    def __init__(self, db_session, strategy_name: str):
        self.db = db_session
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"simulate_trading.services.trade_executor.{strategy_name}")

    def execute_buy(self, symbol: str, quantity: int, price: float, reason: str):
        """
        执行买入交易

        流程：
        1. 计算交易金额和手续费
        2. 检查现金是否足够
        3. 创建交易记录
        4. 更新策略账户
        5. 更新持仓信息（待实现）

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格
            reason: 交易理由
        """
        self.logger.info(f"执行买入: {symbol} {quantity} 股 @ {price}")

        # 计算交易金额
        amount = Decimal(str(price)) * Decimal(str(quantity))

        # 计算手续费（买入不收印花税）
        fee = self._calculate_buy_fee(amount)

        # 总支出 = 金额 + 手续费
        total_cost = amount + fee

        # 检查现金是否足够
        account = self._get_or_create_account()
        if Decimal(str(account.current_cash)) < total_cost:
            raise InsufficientCashError(
                required=float(total_cost),
                available=float(account.current_cash)
            )

        # 创建交易记录
        trade = StrategyTrade(
            strategy_name=self.strategy_name,
            symbol=symbol,
            transaction_type='buy',
            quantity=quantity,
            price=Decimal(str(price)),
            amount=amount,
            fee=fee,
            reason=reason
        )

        from simulate_trading.repositories import StrategyTradeRepository
        trade_repo = StrategyTradeRepository(self.db)
        trade_repo.create(trade)

        # 更新账户（扣减现金，增加持仓市值）
        account.current_cash = Decimal(str(account.current_cash)) - total_cost
        account.total_value = Decimal(str(account.total_value))  # 待更新持仓市值
        account.total_profit = account.total_value - account.initial_cash
        account.total_profit_pct = (account.total_profit / account.initial_cash) * Decimal('100')

        from simulate_trading.repositories import StrategyAccountRepository
        account_repo = StrategyAccountRepository(self.db)
        account_repo.update(account)

        self.db.commit()

        self.logger.info(f"买入成功: {symbol} {quantity} 股, 金额={amount}, 手续费={fee}")

    def execute_sell(self, symbol: str, quantity: int, price: float, reason: str):
        """
        执行卖出交易

        流程：
        1. 计算交易金额和手续费
        2. 创建交易记录
        3. 更新策略账户
        4. 更新持仓信息（待实现）

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格
            reason: 交易理由
        """
        self.logger.info(f"执行卖出: {symbol} {quantity} 股 @ {price}")

        # 计算交易金额
        amount = Decimal(str(price)) * Decimal(str(quantity))

        # 计算手续费（卖出收取印花税）
        fee = self._calculate_sell_fee(amount)

        # 到账金额 = 金额 - 手续费
        net_amount = amount - fee

        # 创建交易记录
        trade = StrategyTrade(
            strategy_name=self.strategy_name,
            symbol=symbol,
            transaction_type='sell',
            quantity=quantity,
            price=Decimal(str(price)),
            amount=net_amount,  # 实际到账金额
            fee=fee,
            reason=reason
        )

        from simulate_trading.repositories import StrategyTradeRepository
        trade_repo = StrategyTradeRepository(self.db)
        trade_repo.create(trade)

        # 更新账户（增加现金）
        account = self._get_or_create_account()
        account.current_cash = Decimal(str(account.current_cash)) + net_amount
        account.total_value = Decimal(str(account.total_value))  # 待更新持仓市值
        account.total_profit = account.total_value - account.initial_cash
        account.total_profit_pct = (account.total_profit / account.initial_cash) * Decimal('100')

        from simulate_trading.repositories import StrategyAccountRepository
        account_repo = StrategyAccountRepository(self.db)
        account_repo.update(account)

        self.db.commit()

        self.logger.info(f"卖出成功: {symbol} {quantity} 股, 到账={net_amount}, 手续费={fee}")

    def _calculate_buy_fee(self, amount: Decimal) -> Decimal:
        """
        计算买入手续费

        买入手续费 = 交易所费用 + 券商佣金
        不收印花税

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        exchange_fee = amount * self.EXCHANGE_FEE
        broker_commission = amount * self.BROKER_COMMISSION

        total_fee = exchange_fee + broker_commission

        # 最低佣金限制
        if total_fee < self.MIN_COMMISSION:
            total_fee = self.MIN_COMMISSION

        return total_fee

    def _calculate_sell_fee(self, amount: Decimal) -> Decimal:
        """
        计算卖出手续费

        卖出手续费 = 印花税 + 交易所费用 + 券商佣金

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        stamp_duty = amount * self.STAMP_DUTY
        exchange_fee = amount * self.EXCHANGE_FEE
        broker_commission = amount * self.BROKER_COMMISSION

        total_fee = stamp_duty + exchange_fee + broker_commission

        # 最低佣金限制
        if total_fee < self.MIN_COMMISSION:
            total_fee = self.MIN_COMMISSION

        return total_fee

    def _get_or_create_account(self) -> StrategyAccount:
        """
        获取或创建策略账户

        Returns:
            策略账户
        """
        from simulate_trading.repositories import StrategyAccountRepository
        account_repo = StrategyAccountRepository(self.db)

        account = account_repo.get_by_name(self.strategy_name)

        if not account:
            # 创建新账户
            from simulate_trading.models import StrategyAccount
            from simulate_trading.strategies import StrategyConfig

            # 从配置文件读取初始资金
            import yaml
            import os
            config_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'strategies.yaml'
            )

            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    strategy_config = config['strategies'].get(self.strategy_name, {})
                    initial_cash = Decimal(str(strategy_config.get('initial_cash', 100000)))
            else:
                initial_cash = Decimal('100000')

            account = StrategyAccount(
                strategy_name=self.strategy_name,
                initial_cash=initial_cash,
                current_cash=initial_cash,
                total_value=initial_cash,
                total_profit=Decimal('0'),
                total_profit_pct=Decimal('0'),
                position_count=0
            )

            account_repo.create(account)
            self.db.commit()
            self.logger.info(f"创建新账户: {self.strategy_name}, 初始资金={initial_cash}")

        return account
