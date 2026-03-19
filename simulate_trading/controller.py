"""
模拟交易主控制器 - 统一管理入口
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import yaml
import os

from simulate_trading.strategies import (
    AggressiveStrategy,
    ModerateStrategy,
    ConservativeStrategy,
    StrategyConfig
)
from simulate_trading.repositories import (
    StrategyAccountRepository,
    StrategyTradeRepository,
    DailyReportRepository
)


class TradingController:
    """
    模拟交易主控制器

    功能：
    - 管理三种策略的启动和停止
    - 获取实时状态
    - 生成报告
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化控制器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.logger = logging.getLogger("simulate_trading.controller")

        # 加载配置
        self.config = self._load_config(config_path)

        # 策略容器
        self.strategies = {}

        # 数据库会话
        self.db = None

        self.logger.info("TradingController 初始化完成")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        if config_path:
            config_file = config_path
        else:
            config_file = os.path.join(
                os.path.dirname(__file__),
                'config',
                'strategies.yaml'
            )

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            self.logger.warning(f"配置文件不存在: {config_file}")
            return {}

    def initialize_db(self, db_session):
        """初始化数据库会话"""
        self.db = db_session

    def start_all_strategies(self):
        """启动所有启用的策略"""
        self.logger.info("开始启动所有策略")

        strategies_config = self.config.get('strategies', {})

        for strategy_name, strategy_config in strategies_config.items():
            if not strategy_config.get('enabled', True):
                self.logger.info(f"策略 {strategy_name} 已禁用，跳过")
                continue

            try:
                # 创建策略配置对象
                config = StrategyConfig(
                    name=strategy_config['name'],
                    description=strategy_config['description'],
                    initial_cash=strategy_config['initial_cash'],
                    max_position=strategy_config['max_position'],
                    min_position=strategy_config['min_position'],
                    stop_loss=strategy_config['stop_loss'],
                    take_profit=strategy_config['take_profit'],
                    trade_ratio=strategy_config['trade_ratio'],
                    chase_threshold=strategy_config.get('chase_threshold'),
                    cut_loss_threshold=strategy_config.get('cut_loss_threshold'),
                    trend_follow_days=strategy_config.get('trend_follow_days'),
                    value_threshold=strategy_config.get('value_threshold')
                )

                # 创建策略实例
                if strategy_name == 'aggressive':
                    strategy = AggressiveStrategy(config, self.db)
                elif strategy_name == 'moderate':
                    strategy = ModerateStrategy(config, self.db)
                elif strategy_name == 'conservative':
                    strategy = ConservativeStrategy(config, self.db)
                else:
                    self.logger.warning(f"未知的策略: {strategy_name}")
                    continue

                self.strategies[strategy_name] = strategy
                self.logger.info(f"策略 {strategy_name} 初始化成功")

            except Exception as e:
                self.logger.error(f"初始化策略 {strategy_name} 失败: {e}")

        self.logger.info(f"所有策略启动完成，共 {len(self.strategies)} 个策略")

    def stop_all_strategies(self):
        """停止所有策略"""
        self.logger.info("停止所有策略")
        self.strategies.clear()

    def status(self) -> Dict:
        """获取当前状态"""
        accounts_repo = StrategyAccountRepository(self.db)
        accounts = accounts_repo.get_all()

        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'strategies': {}
        }

        for account in accounts:
            status['strategies'][account.strategy_name] = {
                'initial_cash': float(account.initial_cash),
                'current_cash': float(account.current_cash),
                'total_value': float(account.total_value),
                'total_profit': float(account.total_profit),
                'total_profit_pct': float(account.total_profit_pct),
                'position_count': account.position_count
            }

        return status

    def execute_single_cycle(self):
        """执行单次交易周期（所有策略各执行一次）"""
        self.logger.info("开始执行交易周期")

        results = {}

        for strategy_name, strategy in self.strategies.items():
            try:
                result = strategy.execute()
                results[strategy_name] = result
                self.logger.info(
                    f"策略 {strategy_name} 执行完成: "
                    f"总资产={result.total_value:.2f}, "
                    f"收益={result.profit:.2f}({result.profit_pct:.2%})"
                )
            except Exception as e:
                self.logger.error(f"策略 {strategy_name} 执行失败: {e}")

        self.logger.info("交易周期执行完成")
        return results

    def generate_daily_report(self):
        """生成每日报告"""
        self.logger.info("生成每日报告")

        report_repo = DailyReportRepository(self.db)
        today = datetime.now().date()

        for strategy_name in self.strategies.keys():
            try:
                # 检查是否已生成今日报告
                existing = report_repo.get_by_strategy_and_date(strategy_name, today)
                if existing:
                    self.logger.info(f"策略 {strategy_name} 今日报告已存在，跳过")
                    continue

                # 获取账户信息
                accounts_repo = StrategyAccountRepository(self.db)
                account = accounts_repo.get_by_name(strategy_name)

                if not account:
                    self.logger.warning(f"策略 {strategy_name} 账户不存在")
                    continue

                # 获取今日交易
                trade_repo = StrategyTradeRepository(self.db)
                trades = trade_repo.get_daily_trades(strategy_name, datetime.now())

                # 创建日报
                from simulate_trading.models import DailyReport
                report = DailyReport(
                    strategy_name=strategy_name,
                    report_date=today,
                    cash=float(account.current_cash),
                    stock_value=float(account.total_value - account.current_cash),
                    total_assets=float(account.total_value),
                    profit=float(account.total_profit),
                    profit_pct=float(account.total_profit_pct),
                    position_count=account.position_count,
                    total_trades=len(trades),
                    winning_trades=0,  # 需要实际计算
                    losing_trades=0    # 需要实际计算
                )

                report_repo.create(report)
                self.db.commit()

                self.logger.info(f"策略 {strategy_name} 日报生成成功")

            except Exception as e:
                self.logger.error(f"生成策略 {strategy_name} 日报失败: {e}")

        self.logger.info("每日报告生成完成")

    def generate_comparison_report(self) -> Dict:
        """生成策略对比报告"""
        self.logger.info("生成策略对比报告")

        report_repo = DailyReportRepository(self.db)
        reports = report_repo.get_all_latest()

        comparison = {
            'timestamp': datetime.utcnow().isoformat(),
            'strategies': {}
        }

        for report in reports:
            comparison['strategies'][report.strategy_name] = {
                'report_date': report.report_date.isoformat(),
                'cash': float(report.cash),
                'stock_value': float(report.stock_value),
                'total_assets': float(report.total_assets),
                'profit': float(report.profit),
                'profit_pct': float(report.profit_pct),
                'position_count': report.position_count,
                'total_trades': report.total_trades,
                'winning_trades': report.winning_trades,
                'losing_trades': report.losing_trades
            }

        # 计算排名
        sorted_strategies = sorted(
            comparison['strategies'].items(),
            key=lambda x: x[1]['profit_pct'],
            reverse=True
        )

        comparison['rankings'] = [
            {'strategy': name, 'profit_pct': data['profit_pct'], 'rank': i + 1}
            for i, (name, data) in enumerate(sorted_strategies)
        ]

        return comparison
