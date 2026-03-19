"""Test Backtest Module Structure"""

import pytest


def test_module_imports():
    """测试模块导入"""
    from backtest import (
        BacktestService,
        BacktestConfig,
        Signal,
        Trade,
        Position,
        DailyMetrics,
        PerformanceMetrics,
        BacktestResult,
        BaseStrategy,
        StrategyCombiner,
        FiveDimensionStrategy,
        VCPBreakoutStrategy,
        TDGoldenPitStrategy,
        TopDivergenceStrategy
    )

    # 验证导入成功
    assert BacktestService is not None
    assert BacktestConfig is not None
