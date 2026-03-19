"""Backtest Service - 回测服务"""

from typing import List, Dict
from sqlalchemy.orm import Session
from backtest.config import BacktestConfig
from backtest.strategies.base_strategy import BaseStrategy
from backtest.models import BacktestResult
from backtest.core.data_feed import DataFeed
from backtest.core.backtest_engine import BacktestEngine
from backtest.analyzers.report_generator import ReportGenerator


class BacktestService:
    """
    回测服务 - 统一接口

    使用示例:
    >>> from backtest.services import BacktestService
    >>> from backtest.strategies.prebuilt import FiveDimensionStrategy
    >>> from common.database import DatabaseManager
    >>> from technical_analysis.services import AnalysisService
    >>>
    >>> db = DatabaseManager("postgresql://...")
    >>> with db.get_session() as session:
    ...     analysis_service = AnalysisService(session)
    ...     backtest_service = BacktestService(session)
    ...     strategy = FiveDimensionStrategy(analysis_service)
    ...     result = backtest_service.run_single_stock_backtest(
    ...         symbol="600519",
    ...         strategy=strategy,
    ...         config=BacktestConfig(
    ...             initial_capital=100000,
    ...             start_date="2023-01-01",
    ...             end_date="2024-12-31"
    ...         )
    ...     )
    ...     print(result.summary)
    """

    def __init__(self, session: Session):
        """
        初始化回测服务

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.data_feed = DataFeed(session)

    def run_single_stock_backtest(
        self,
        symbol: str,
        strategy: BaseStrategy,
        config: BacktestConfig
    ) -> BacktestResult:
        """
        单只股票回测

        Args:
            symbol: 股票代码
            strategy: 交易策略
            config: 回测配置

        Returns:
            BacktestResult: 回测结果

        Raises:
            ValueError: 数据不足或配置无效
        """
        # 1. 获取数据
        data = self.data_feed.get_stock_data(
            symbol=symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            interval=config.interval
        )

        if len(data) < 30:
            raise ValueError(f"数据不足，需要至少 30 条 K 线，当前只有 {len(data)} 条")

        # 2. 创建回测引擎
        engine = BacktestEngine(
            config=config,
            data_feed=self.data_feed,
            strategy=strategy,
            initial_capital=config.initial_capital
        )

        # 3. 运行回测
        result = engine.run(
            symbol=symbol,
            start_date=config.start_date,
            end_date=config.end_date
        )

        return result

    def run_multi_stock_backtest(
        self,
        symbols: List[str],
        strategy: BaseStrategy,
        config: BacktestConfig
    ) -> Dict[str, BacktestResult]:
        """
        多股票组合回测

        支持:
        - 等权重配置
        - 动态调仓
        - 最大持仓数限制

        Args:
            symbols: 股票代码列表
            strategy: 交易策略
            config: 回测配置

        Returns:
            {symbol: BacktestResult}
        """
        results = {}

        for symbol in symbols:
            try:
                result = self.run_single_stock_backtest(symbol, strategy, config)
                results[symbol] = result
            except Exception as e:
                # Log error and continue with other symbols
                print(f"Error backtesting {symbol}: {e}")
                continue

        return results

    def run_portfolio_backtest(
        self,
        portfolio_config: Dict
    ) -> BacktestResult:
        """
        投资组合回测

        支持:
        - 不同股票使用不同策略
        - 不同仓位配置
        - 多资金规模测试

        Args:
            portfolio_config: 投资组合配置

        Returns:
            BacktestResult: 回测结果
        """
        # TODO: Implement portfolio-level backtest
        # This would require a portfolio-level engine that can handle
        # multiple symbols simultaneously with capital allocation
        raise NotImplementedError("Portfolio backtest not yet implemented")

    def generate_backtest_report(
        self,
        result: BacktestResult,
        format: str = "text"  # "text", "html", "json"
    ) -> str:
        """
        生成回测报告

        Args:
            result: 回测结果
            format: 报告格式

        Returns:
            报告内容
        """
        generator = ReportGenerator()

        if format == "text":
            return generator.generate_text_report(result)
        elif format == "html":
            # Generate HTML report with visualization
            import tempfile
            import os
            with tempfile.TemporaryDirectory() as tmpdir:
                html_path = os.path.join(tmpdir, "report.html")
                generator.generate_html_report(result, html_path)
                with open(html_path, 'r', encoding='utf-8') as f:
                    return f.read()
        elif format == "json":
            return result.to_json()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def compare_strategies(
        self,
        symbol: str,
        strategies: List[BaseStrategy],
        config: BacktestConfig
    ) -> Dict[str, BacktestResult]:
        """
        比较多个策略

        Args:
            symbol: 股票代码
            strategies: 策略列表
            config: 回测配置

        Returns:
            {strategy_name: BacktestResult}
        """
        results = {}

        for strategy in strategies:
            try:
                result = self.run_single_stock_backtest(symbol, strategy, config)
                results[strategy.get_name()] = result
            except Exception as e:
                print(f"Error backtesting strategy {strategy.get_name()}: {e}")
                continue

        return results
