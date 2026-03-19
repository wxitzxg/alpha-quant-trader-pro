"""Backtest Module - 回测模块"""

__version__ = "1.0.0"

from .services import BacktestService
from .config import BacktestConfig
from .models import (
    Signal,
    Trade,
    Position,
    DailyMetrics,
    PerformanceMetrics,
    BacktestResult
)
from .strategies import BaseStrategy, StrategyCombiner
from .strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)

__all__ = [
    'BacktestService',
    'BacktestConfig',
    'Signal',
    'Trade',
    'Position',
    'DailyMetrics',
    'PerformanceMetrics',
    'BacktestResult',
    'BaseStrategy',
    'StrategyCombiner',
    'FiveDimensionStrategy',
    'VCPBreakoutStrategy',
    'TDGoldenPitStrategy',
    'TopDivergenceStrategy',
]
