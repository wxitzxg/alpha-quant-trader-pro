"""Report Generator - 报告生成器"""

import os
from typing import List, Optional
import matplotlib.pyplot as plt
from backtest.models import BacktestResult


class ReportGenerator:
    """
    回测报告生成器

    生成以下报告:
    - 文本报告 (控制台输出)
    - HTML 可视化报告
    - 权益曲线图
    - 回撤曲线图
    """

    def generate_text_report(self, result: BacktestResult) -> str:
        """
        生成文本报告

        Args:
            result: 回测结果

        Returns:
            格式化的文本报告
        """
        report = f"""
{'='*80}
{' '*25}回测报告
{'='*80}

【策略信息】
  策略名称: {result.strategy_name}
  回测期间: {result.config.start_date} ~ {result.config.end_date}
  回测天数: {len(result.dates)} 天
  K线周期: {result.config.interval}

【资金信息】
  初始资金: {result.config.initial_capital:,.0f} 元
  期末资金: {result.equity_curve[-1]:,.0f} 元
  总收益率: {result.performance.total_return:.2f}%
  年化收益率: {result.performance.annual_return:.2f}%
  总盈利: {result.equity_curve[-1] - result.config.initial_capital:,.0f} 元

【风险指标】
  最大回撤: {result.performance.max_drawdown:.2f}%
  波动率: {result.performance.volatility:.2f}%
  夏普比率: {result.performance.sharpe_ratio:.2f}
  索提诺比率: {result.performance.sortino_ratio:.2f}
  卡尔玛比率: {result.performance.calmar_ratio:.2f}

【交易统计】
  总交易次数: {result.performance.total_trades}
  盈利次数: {result.performance.winning_trades}
  亏损次数: {result.performance.losing_trades}
  胜率: {result.performance.win_rate:.1f}%
  盈亏比: {result.performance.profit_factor:.2f}
  平均持仓天数: {result.performance.avg_holding_days:.1f} 天
  最大连胜次数: {result.performance.max_consecutive_wins}
  最大连败次数: {result.performance.max_consecutive_losses}

【权益曲线】
  初始: {result.equity_curve[0]:,.0f} 元
  最高: {max(result.equity_curve):,.0f} 元
  最低: {min(result.equity_curve):,.0f} 元
  期末: {result.equity_curve[-1]:,.0f} 元

{'='*80}
"""
        return report

    def generate_html_report(
        self,
        result: BacktestResult,
        output_path: str = "backtest_report.html"
    ):
        """
        生成 HTML 可视化报告

        Args:
            result: 回测结果
            output_path: 输出路径
        """
        # Create equity curve plot
        equity_plot_path = output_path.replace('.html', '_equity.png')
        self.generate_equity_curve_plot(
            result.equity_curve,
            result.dates,
            equity_plot_path
        )

        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>回测报告 - {result.strategy_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .section {{ margin: 30px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>📊 回测报告</h1>

    <div class="section">
        <h2>📈 策略信息</h2>
        <div class="metric">策略名称: {result.strategy_name}</div>
        <div class="metric">回测期间: {result.config.start_date} ~ {result.config.end_date}</div>
        <div class="metric">回测天数: {len(result.dates)} 天</div>
    </div>

    <div class="section">
        <h2>💰 资金信息</h2>
        <div class="metric">初始资金: {result.config.initial_capital:,.0f} 元</div>
        <div class="metric">期末资金: {result.equity_curve[-1]:,.0f} 元</div>
        <div class="metric {'positive' if result.performance.total_return > 0 else 'negative'}">
            总收益率: {result.performance.total_return:.2f}%
        </div>
        <div class="metric {'positive' if result.performance.annual_return > 0 else 'negative'}">
            年化收益率: {result.performance.annual_return:.2f}%
        </div>
    </div>

    <div class="section">
        <h2>⚠️ 风险指标</h2>
        <div class="metric">最大回撤: {result.performance.max_drawdown:.2f}%</div>
        <div class="metric">波动率: {result.performance.volatility:.2f}%</div>
        <div class="metric">夏普比率: {result.performance.sharpe_ratio:.2f}</div>
    </div>

    <div class="section">
        <h2>📈 交易统计</h2>
        <div class="metric">总交易次数: {result.performance.total_trades}</div>
        <div class="metric">胜率: {result.performance.win_rate:.1f}%</div>
        <div class="metric">盈亏比: {result.performance.profit_factor:.2f}</div>
    </div>

    <div class="section">
        <h2>📊 权益曲线</h2>
        <img src="{os.path.basename(equity_plot_path)}" alt="Equity Curve">
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def generate_equity_curve_plot(
        self,
        equity_curve: List[float],
        dates: List[str],
        output_path: str
    ):
        """
        生成权益曲线图

        Args:
            equity_curve: 权益曲线
            dates: 日期列表
            output_path: 输出路径
        """
        plt.figure(figsize=(12, 6))
        plt.plot(dates, equity_curve, linewidth=2, color='#1f77b4')
        plt.title('权益曲线', fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('资产 (元)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def generate_drawdown_plot(
        self,
        equity_curve: List[float],
        dates: List[str],
        output_path: str
    ):
        """
        生成回撤曲线图

        Args:
            equity_curve: 权益曲线
            dates: 日期列表
            output_path: 输出路径
        """
        # Calculate drawdown
        peak = equity_curve[0]
        drawdowns = []

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            drawdowns.append(drawdown)

        plt.figure(figsize=(12, 6))
        plt.plot(dates, drawdowns, linewidth=2, color='#d62728')
        plt.title('回撤曲线', fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('回撤 (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
