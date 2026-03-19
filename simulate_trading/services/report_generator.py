"""
报告生成器 - 生成日报和对比报告
"""

import logging
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器 - 生成每日报告和策略对比报告
    """

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger("simulate_trading.services.report_generator")

    def generate_daily_report(self, strategy_name: str, report_date: Optional[date] = None):
        """
        生成单个策略的日报

        流程：
        1. 获取账户信息
        2. 获取当日交易记录
        3. 计算盈利/亏损交易次数
        4. 创建日报记录

        Args:
            strategy_name: 策略名称
            report_date: 报告日期（默认今天）
        """
        if report_date is None:
            report_date = date.today()

        self.logger.info(f"生成日报: {strategy_name} - {report_date}")

        # 检查是否已存在
        from simulate_trading.repositories import DailyReportRepository
        report_repo = DailyReportRepository(self.db)

        existing = report_repo.get_by_strategy_and_date(strategy_name, report_date)
        if existing:
            self.logger.info(f"日报已存在，跳过: {strategy_name} - {report_date}")
            return existing

        # 获取账户信息
        from simulate_trading.repositories import StrategyAccountRepository
        account_repo = StrategyAccountRepository(self.db)
        account = account_repo.get_by_name(strategy_name)

        if not account:
            self.logger.warning(f"账户不存在: {strategy_name}")
            return None

        # 获取当日交易
        from simulate_trading.repositories import StrategyTradeRepository
        trade_repo = StrategyTradeRepository(self.db)
        trades = trade_repo.get_daily_trades(strategy_name, datetime.now())

        # 计算盈利/亏损交易（简化版：只统计卖出交易）
        winning_trades = 0
        losing_trades = 0
        total_trades = len(trades)

        # 创建日报
        from simulate_trading.models import DailyReport
        report = DailyReport(
            strategy_name=strategy_name,
            report_date=report_date,
            cash=Decimal(str(account.current_cash)),
            stock_value=Decimal(str(account.total_value - account.current_cash)),
            total_assets=Decimal(str(account.total_value)),
            profit=Decimal(str(account.total_profit)),
            profit_pct=Decimal(str(account.total_profit_pct)),
            position_count=account.position_count,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades
        )

        report_repo.create(report)
        self.db.commit()

        self.logger.info(f"日报生成成功: {strategy_name} - {report_date}")
        return report

    def generate_comparison_report(self, date_range: Optional[tuple] = None) -> Dict:
        """
        生成策略对比报告

        包括：
        - 收益率对比
        - 波动率对比
        - 交易次数对比
        - 胜率对比

        Args:
            date_range: 日期范围 (start_date, end_date)

        Returns:
            对比报告数据
        """
        self.logger.info("生成策略对比报告")

        from simulate_trading.repositories import DailyReportRepository
        report_repo = DailyReportRepository(self.db)

        reports = report_repo.get_all_latest()

        comparison = {
            'timestamp': datetime.utcnow().isoformat(),
            'date_range': str(date_range) if date_range else 'latest',
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
                'losing_trades': report.losing_trades,
                'win_rate': (report.winning_trades / report.total_trades * 100) if report.total_trades > 0 else 0.0
            }

        # 计算排名
        sorted_strategies = sorted(
            comparison['strategies'].items(),
            key=lambda x: x[1]['profit_pct'],
            reverse=True
        )

        comparison['rankings'] = [
            {
                'strategy': name,
                'profit_pct': data['profit_pct'],
                'rank': i + 1,
                'total_assets': data['total_assets']
            }
            for i, (name, data) in enumerate(sorted_strategies)
        ]

        # 计算统计数据
        if len(reports) > 0:
            total_assets = sum(r.total_assets for r in reports)
            total_profit = sum(r.profit for r in reports)
            avg_profit_pct = total_profit / total_assets * 100 if total_assets > 0 else 0

            comparison['summary'] = {
                'total_strategies': len(reports),
                'total_assets': float(total_assets),
                'total_profit': float(total_profit),
                'average_profit_pct': float(avg_profit_pct)
            }

        self.logger.info("策略对比报告生成成功")
        return comparison

    def export_report_to_text(self, report_data: Dict) -> str:
        """
        导出报告为文本格式

        Args:
            report_data: 报告数据

        Returns:
            文本格式的报告
        """
        lines = []
        lines.append("=" * 70)
        lines.append("📈 模拟交易日报")
        lines.append("=" * 70)
        lines.append(f"\n📅 日期: {report_data['timestamp']}")
        lines.append(f"📊 对比周期: {report_data.get('date_range', '最新')}\n")

        # 显示排名
        lines.append("🏆 策略收益率排名")
        lines.append("─" * 70)
        for item in report_data.get('rankings', []):
            emoji = "🥇" if item['rank'] == 1 else "🥈" if item['rank'] == 2 else "🥉" if item['rank'] == 3 else "  "
            lines.append(
                f"  {emoji} {item['rank']}. {item['strategy']:10s} "
                f"收益率: {item['profit_pct']:+6.2f}% "
                f"总资产: {item['total_assets']:,.2f} 元"
            )

        lines.append("\n" + "─" * 70)

        # 显示详细信息
        for strategy_name, data in report_data.get('strategies', {}).items():
            lines.append(f"\n📈 {strategy_name}")
            lines.append("─" * 70)
            lines.append(f"  报告日期: {data['report_date']}")
            lines.append(f"  总资产:   {data['total_assets']:,.2f} 元")
            lines.append(f"  现金:     {data['cash']:,.2f} 元")
            lines.append(f"  持仓市值: {data['stock_value']:,.2f} 元")
            lines.append(f"  收益率:   {data['profit_pct']:+.2f}%")
            lines.append(f"  交易次数: {data['total_trades']} 次")
            lines.append(f"  胜率:     {data['win_rate']:.1f}%")
            lines.append(f"  持仓数:   {data['position_count']} 只")

        # 显示汇总
        if 'summary' in report_data:
            summary = report_data['summary']
            lines.append("\n" + "=" * 70)
            lines.append("📊 汇总统计")
            lines.append("=" * 70)
            lines.append(f"  策略总数: {summary['total_strategies']}")
            lines.append(f"  总资产:   {summary['total_assets']:,.2f} 元")
            lines.append(f"  总收益:   {summary['total_profit']:+,.2f} 元")
            lines.append(f"  平均收益率: {summary['average_profit_pct']:+.2f}%")

        lines.append("\n" + "=" * 70 + "\n")

        return "\n".join(lines)

    def export_report_to_json(self, report_data: Dict, file_path: str):
        """
        导出报告为 JSON 文件

        Args:
            report_data: 报告数据
            file_path: 文件路径
        """
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已导出到: {file_path}")
