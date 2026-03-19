"""
模拟交易模块 - 三种策略并行模拟交易系统

功能：
- 激进型策略：高仓位追涨杀跌
- 稳健型策略：中等仓位趋势跟踪
- 保守型策略：低仓位价值投资
- 实时行情监控
- 交易日报生成
- 策略对比分析
"""

from .controller import TradingController
from .strategies import (
    BaseStrategy,
    AggressiveStrategy,
    ModerateStrategy,
    ConservativeStrategy,
    StrategyConfig,
    TradeSignal,
    StrategyResult
)

__all__ = [
    'TradingController',
    'BaseStrategy',
    'AggressiveStrategy',
    'ModerateStrategy',
    'ConservativeStrategy',
    'StrategyConfig',
    'TradeSignal',
    'StrategyResult'
]
