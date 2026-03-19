"""Test Report Generator"""

import pytest
from datetime import datetime
from backtest.analyzers.report_generator import ReportGenerator
from backtest.models import (
    BacktestResult,
    PerformanceMetrics,
    DailyMetrics,
    Trade,
    Position
)
from backtest.config import BacktestConfig


def create_test_result():
    """创建测试回测结果"""
    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    performance = PerformanceMetrics(
        total_return=35.5,
        annual_return=18.2,
        volatility=25.0,
        max_drawdown=15.3,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        calmar_ratio=1.19,
        total_trades=45,
        winning_trades=28,
        losing_trades=17,
        win_rate=62.2,
        profit_factor=1.8,
        avg_holding_days=5.3
    )

    result = BacktestResult(
        config=config,
        strategy_name="FiveDimensionStrategy",
        trades=[],
        daily_metrics=[
            DailyMetrics(
                date="2024-01-01",
                total_value=100000,
                cash=100000,
                stock_value=0,
                positions_count=0,
                daily_return=0,
                cumulative_return=0
            ),
            DailyMetrics(
                date="2024-01-02",
                total_value=101000,
                cash=99000,
                stock_value=2000,
                positions_count=1,
                daily_return=1.0,
                cumulative_return=1.0
            )
        ],
        positions_history=[],
        performance=performance,
        equity_curve=[100000.0, 101000.0, 102500.0, 105000.0],
        dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    )

    return result


def test_generate_text_report():
    """测试生成文本报告"""
    generator = ReportGenerator()
    result = create_test_result()

    report = generator.generate_text_report(result)

    # Check key sections
    assert "回测报告" in report
    assert "FiveDimensionStrategy" in report
    assert "2024-01-01" in report
    assert "35.50%" in report  # total_return
    assert "18.20%" in report  # annual_return
    assert "15.30%" in report  # max_drawdown
    assert "1.20" in report  # sharpe_ratio
    assert "45" in report  # total_trades
    assert "62.2" in report  # win_rate


def test_generate_text_report_empty_result():
    """测试空结果的文本报告"""
    generator = ReportGenerator()

    config = BacktestConfig(
        initial_capital=100000,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    performance = PerformanceMetrics(
        total_return=0.0,
        annual_return=0.0,
        volatility=0.0,
        max_drawdown=0.0,
        sharpe_ratio=0.0,
        sortino_ratio=0.0,
        calmar_ratio=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        win_rate=0.0,
        profit_factor=0.0,
        avg_holding_days=0.0
    )

    result = BacktestResult(
        config=config,
        strategy_name="TestStrategy",
        trades=[],
        daily_metrics=[],
        positions_history=[],
        performance=performance,
        equity_curve=[100000.0],
        dates=["2024-01-01"]
    )

    report = generator.generate_text_report(result)

    assert "TestStrategy" in report
    assert "0.00%" in report


def test_summary_property():
    """测试摘要属性"""
    result = create_test_result()

    summary = result.summary

    assert "FiveDimensionStrategy" in summary
    assert "35.50%" in summary
    assert "18.20%" in summary


def test_to_json():
    """测试转换为 JSON"""
    result = create_test_result()

    json_str = result.to_json()

    assert isinstance(json_str, str)
    assert "FiveDimensionStrategy" in json_str
    assert "total_return" in json_str
    assert "35.5" in json_str
