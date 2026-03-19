# portfolio_manager/fee_calculator.py
"""
手续费计算器
"""

from decimal import Decimal
from typing import Optional
from common.config import get_config, Config


class FeeCalculator:
    """手续费计算器 - 使用统一配置系统"""

    def __init__(self, fee_config=None):
        """
        初始化手续费计算器

        Args:
            fee_config: FeeConfig 对象或 None（从统一配置加载）
        """
        if fee_config is None:
            # 从统一配置加载
            config: Config = get_config()
            self._config = config.get_fee_config()
        else:
            self._config = fee_config

    @property
    def stamp_duty(self) -> Decimal:
        """印花税率"""
        return Decimal(str(self._config.stamp_duty))

    @property
    def exchange_fee(self) -> Decimal:
        """交易所费用率"""
        return Decimal(str(self._config.exchange_fee))

    @property
    def broker_commission(self) -> Decimal:
        """券商佣金率"""
        return Decimal(str(self._config.broker_commission))

    @property
    def min_commission(self) -> Decimal:
        """最低佣金"""
        return Decimal(str(self._config.min_commission))

    def calculate_buy_fee(self, amount: float) -> float:
        """
        计算买入手续费

        买入费用 = 交易所费用 + 券商佣金
        注意：买入不收印花税

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        amount_d = Decimal(str(amount))

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee

        # 券商佣金
        broker_commission = amount_d * self.broker_commission
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        total_fee = exchange_fee + broker_commission
        return float(total_fee)

    def calculate_sell_fee(self, amount: float) -> float:
        """
        计算卖出手续费

        卖出费用 = 印花税 + 交易所费用 + 券商佣金

        Args:
            amount: 交易金额

        Returns:
            手续费
        """
        amount_d = Decimal(str(amount))

        # 印花税（仅卖出收取）
        stamp_duty = amount_d * self.stamp_duty

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee

        # 券商佣金
        broker_commission = amount_d * self.broker_commission
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        total_fee = stamp_duty + exchange_fee + broker_commission
        return float(total_fee)

    @property
    def config(self):
        """获取配置对象"""
        return self._config
