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
            raise ValueError(f"start_date must be before end_date, got {self.start_date} >= {self.end_date}")

        # 验证仓位
        if not 0 < self.position_size <= 1:
            raise ValueError(f"position_size must be between 0 and 1, got {self.position_size}")

        # 验证最大持仓数
        if self.max_positions < 1:
            raise ValueError(f"max_positions must be >= 1, got {self.max_positions}")
