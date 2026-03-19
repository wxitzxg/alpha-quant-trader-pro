"""Five Dimension Strategy - 五维共振策略"""

from typing import Dict, Optional
from backtest.strategies.base_strategy import BaseStrategy, Signal
from technical_analysis.services import AnalysisService


class FiveDimensionStrategy(BaseStrategy):
    """
    五维共振策略 - 调用 AnalysisService.analyze_stock()

    策略逻辑:
    - 五维共振总分 >= 85: STRONG_BUY (S级, 20% 仓位)
    - 五维共振总分 >= 65: BUY (A级, 10% 仓位)
    - 五维共振总分 >= 40: HOLD (B级, 5% 仓位)
    - 五维共振总分 < 40: SELL (C级, 卖出或观望)
    """

    def __init__(self, analysis_service: AnalysisService):
        """
        初始化五维共振策略

        Args:
            analysis_service: 技术分析服务
        """
        self.analysis_service = analysis_service

    def on_data(self, symbol: str, data: Dict, date: str) -> Signal:
        """
        五维共振评分决策

        Args:
            symbol: 股票代码
            data: K线数据 (包含 open, high, low, close, volume 等)
            date: 日期

        Returns:
            Signal: 交易信号
        """
        # 获取当日收盘价 (用于信号价格)
        current_price = data.get('close', 0) if isinstance(data.get('close'), (int, float)) else \
            data['close'].iloc[-1] if hasattr(data['close'], 'iloc') else data.get('close', [0])[-1]

        # 调用技术分析模块
        result = self.analysis_service.analyze_stock(
            symbol=symbol,
            interval="1d",
            end_date=date,
            days=120
        )

        # 提取评分
        score = result.get('total_score', 0)

        # 根据评分生成信号
        if score >= 85:
            return Signal(
                symbol=symbol,
                date=date,
                action="BUY",
                price=current_price,
                position_size=0.2,
                reason=f"五维共振 S 级信号 (总分: {score})"
            )
        elif score >= 65:
            return Signal(
                symbol=symbol,
                date=date,
                action="BUY",
                price=current_price,
                position_size=0.1,
                reason=f"五维共振 A 级信号 (总分: {score})"
            )
        elif score >= 40:
            return Signal(
                symbol=symbol,
                date=date,
                action="HOLD",
                price=current_price,
                position_size=0.05,
                reason=f"五维共振 B 级信号 (总分: {score})"
            )
        else:
            return Signal(
                symbol=symbol,
                date=date,
                action="SELL",
                price=current_price,
                reason=f"五维共振 C 级信号 (总分: {score}, 观望)"
            )

    def get_name(self) -> str:
        """获取策略名称"""
        return "FiveDimensionStrategy"
