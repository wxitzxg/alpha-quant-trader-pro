"""
回测模块使用示例
"""

from backtest.services import BacktestService
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)
from backtest.config import BacktestConfig
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService


def example_1_single_stock_backtest():
    """示例 1: 单股票五维共振回测"""
    print("=" * 80)
    print("示例 1: 单股票五维共振回测")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        # 创建策略
        strategy = FiveDimensionStrategy(analysis_service)

        # 运行回测
        result = backtest_service.run_single_stock_backtest(
            symbol="600519",
            strategy=strategy,
            config=BacktestConfig(
                initial_capital=100000,
                start_date="2023-01-01",
                end_date="2024-12-31",
                commission_rate=0.00025
            )
        )

        # 打印结果
        print(result.summary)

        # 生成报告
        report = backtest_service.generate_backtest_report(result, format="text")
        print(report)


def example_2_strategy_comparison():
    """示例 2: 策略比较"""
    print("=" * 80)
    print("示例 2: 策略比较")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        # 创建多个策略
        strategies = [
            FiveDimensionStrategy(analysis_service),
            VCPBreakoutStrategy(),
            TDGoldenPitStrategy()
        ]

        results = backtest_service.compare_strategies(
            symbol="600519",
            strategies=strategies,
            config=BacktestConfig(
                initial_capital=100000,
                start_date="2023-01-01",
                end_date="2024-12-31"
            )
        )

        # 打印比较结果
        print(f"{'策略':<25} {'年化收益':>12} {'夏普比率':>12} {'胜率':>10}")
        print("-" * 60)
        for name, result in results.items():
            print(f"{name:<25} "
                  f"{result.performance.annual_return:>11.2f}% "
                  f"{result.performance.sharpe_ratio:>12.2f} "
                  f"{result.performance.win_rate:>9.1f}%")


def example_3_strategy_combiner():
    """示例 3: 策略组合器 (AND 规则)"""
    print("=" * 80)
    print("示例 3: 策略组合器 (AND 规则)")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        from backtest.strategies import StrategyCombiner

        # 组合 VCP + 九转策略
        vcp_strategy = VCPBreakoutStrategy()
        td_strategy = TDGoldenPitStrategy()

        combiner = StrategyCombiner(
            strategies=[vcp_strategy, td_strategy],
            combination_rule="and"  # 两个策略都发出信号才交易
        )

        result = backtest_service.run_single_stock_backtest(
            symbol="600519",
            strategy=combiner,
            config=BacktestConfig(
                initial_capital=100000,
                start_date="2023-01-01",
                end_date="2024-12-31"
            )
        )

        print(f"策略组合回测结果:")
        print(f"  年化收益: {result.performance.annual_return:.2f}%")
        print(f"  夏普比率: {result.performance.sharpe_ratio:.2f}")
        print(f"  总交易次数: {result.performance.total_trades}")


def example_4_multi_stock_backtest():
    """示例 4: 多股票组合回测"""
    print("=" * 80)
    print("示例 4: 多股票组合回测")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        strategy = FiveDimensionStrategy(analysis_service)

        # 多股票回测
        symbols = ["600519", "000001", "300750", "600036"]

        results = backtest_service.run_multi_stock_backtest(
            symbols=symbols,
            strategy=strategy,
            config=BacktestConfig(
                initial_capital=500000,  # 50万资金
                start_date="2023-01-01",
                end_date="2024-12-31",
                max_positions=5,         # 最多持有5只股票
                position_size=0.1        # 单只股票仓位10%
            )
        )

        print(f"多股票组合回测:")
        print(f"{'股票代码':<10} {'年化收益':>12} {'最大回撤':>12}")
        print("-" * 40)
        for symbol, result in results.items():
            print(f"{symbol:<10} "
                  f"{result.performance.annual_return:>11.2f}% "
                  f"{result.performance.max_drawdown:>11.2f}%")


def example_5_html_report():
    """示例 5: 生成 HTML 报告"""
    print("=" * 80)
    print("示例 5: 生成 HTML 报告")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        strategy = FiveDimensionStrategy(analysis_service)

        result = backtest_service.run_single_stock_backtest(
            symbol="600519",
            strategy=strategy,
            config=BacktestConfig(
                initial_capital=100000,
                start_date="2023-01-01",
                end_date="2024-12-31"
            )
        )

        # 生成 HTML 报告
        html_report = backtest_service.generate_backtest_report(result, format="html")

        with open("backtest_report.html", "w", encoding="utf-8") as f:
            f.write(html_report)

        print(f"HTML 报告已保存到: backtest_report.html")


def example_6_custom_config():
    """示例 6: 自定义配置"""
    print("=" * 80)
    print("示例 6: 自定义配置")
    print("=" * 80)

    db = DatabaseManager("postgresql://user:password@localhost/stock_market")
    with db.get_session() as session:
        analysis_service = AnalysisService(session)
        backtest_service = BacktestService(session)

        strategy = FiveDimensionStrategy(analysis_service)

        # 自定义配置
        config = BacktestConfig(
            initial_capital=200000,        # 20万初始资金
            commission_rate=0.0003,         # 万分之3手续费
            slippage_rate=0.002,            # 千分之2滑点
            position_size=0.15,             # 15%单笔仓位
            start_date="2022-01-01",        # 更长回测期
            end_date="2024-12-31",
            max_positions=3                 # 最多3只股票
        )

        result = backtest_service.run_single_stock_backtest(
            symbol="600519",
            strategy=strategy,
            config=config
        )

        print(f"自定义配置回测:")
        print(f"  初始资金: {config.initial_capital:,.0f}")
        print(f"  手续费率: {config.commission_rate * 10000:.1f}‱")
        print(f"  滑点率: {config.slippage_rate * 1000:.1f}‰")
        print(f"  总收益率: {result.performance.total_return:.2f}%")
        print(f"  年化收益率: {result.performance.annual_return:.2f}%")


if __name__ == "__main__":
    # 运行示例 1
    example_1_single_stock_backtest()

    # 运行其他示例 (需要修改数据库连接)
    # example_2_strategy_comparison()
    # example_3_strategy_combiner()
    # example_4_multi_stock_backtest()
    # example_5_html_report()
    # example_6_custom_config()
