"""Backtest Configuration - 回测配置

兼容层：从统一配置系统读取配置
Compatibility layer: reads from unified config system
"""

from dataclasses import dataclass, field
from typing import Optional
from common.config import get_config


@dataclass
class BacktestConfig:
    """回测配置"""

    # ========== 兼容层：从统一配置读取 ==========
    # Backward compatibility: read from unified config

    def __init__(self, **kwargs):
        """初始化配置"""
        # 从统一配置加载默认值
        unified_config = get_config()
        bt_config = unified_config.backtest

        # 基础配置
        self.initial_capital: float = kwargs.get('initial_capital', bt_config.initial_capital)
        self.commission_rate: float = kwargs.get('commission_rate', bt_config.commission_rate)
        self.slippage_rate: float = kwargs.get('slippage_rate', bt_config.slippage_rate)
        self.stamp_duty_rate: float = kwargs.get('stamp_duty_rate', bt_config.stamp_duty_rate)

        # 回测参数
        self.start_date: str = kwargs.get('start_date', bt_config.start_date)
        self.end_date: str = kwargs.get('end_date', bt_config.end_date)
        self.interval: str = kwargs.get('interval', bt_config.interval)

        # 资金管理
        self.position_size: float = kwargs.get('position_size', bt_config.position_size)
        self.max_positions: int = kwargs.get('max_positions', bt_config.max_positions)
        self.use_dynamic_position: bool = kwargs.get('use_dynamic_position', bt_config.use_dynamic_position)

        # 风控参数
        self.stop_loss_pct: float = kwargs.get('stop_loss_pct', bt_config.stop_loss_pct)
        self.take_profit_pct: float = kwargs.get('take_profit_pct', bt_config.take_profit_pct)
        self.enable_trailing_stop: bool = kwargs.get('enable_trailing_stop', bt_config.enable_trailing_stop)
        self.enable_position_control: bool = kwargs.get('enable_position_control', bt_config.enable_position_control)

        # 验证配置
        self.__post_init__()

    # ========== 基础配置 ==========
    initial_capital: float  # 初始资金
    commission_rate: float  # 手续费率 (万分之2.5)
    slippage_rate: float  # 滑点率 (千分之1)
    stamp_duty_rate: float  # 印花税率 (千分之1, 卖出)

    # ========== 回测参数 ==========
    start_date: str  # 回测开始日期
    end_date: str  # 回测结束日期
    interval: str  # K线周期 (1d, 5d, 10d, 1m)

    # ========== 资金管理 ==========
    position_size: float  # 单笔交易仓位 (10%)
    max_positions: int  # 最大持仓股票数
    use_dynamic_position: bool  # 是否动态调整仓位

    # ========== 风控参数 ==========
    stop_loss_pct: float  # 止损比例 (8%)
    take_profit_pct: float  # 止盈比例 (20%)
    enable_trailing_stop: bool  # 启用移动止损
    enable_position_control: bool  # 启用仓位控制

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
