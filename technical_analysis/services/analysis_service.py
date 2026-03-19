#!/usr/bin/env python3
"""
Analysis Service - 技术分析服务层

提供统一的技术分析接口，适配现有的 Repository-Service 架构
"""

import pandas as pd
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from stock_market.repositories import KLineRepository
from stock_market.schemas import KLineQuerySchema
from ..engines import UltimateEngine
from ..strategies import VCPBreakoutStrategy, TDGoldenPitStrategy, TopDivergenceStrategy


class AnalysisService:
    """技术分析服务"""

    def __init__(self, session: Session):
        """
        初始化技术分析服务

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.kline_repo = KLineRepository(session)

    def analyze_stock(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 120
    ) -> Dict:
        """
        完整技术分析 (五维共振)

        Args:
            symbol: 股票代码
            interval: K线周期 (1d, 5d, 10d, 1m)
            start_date: 开始日期
            end_date: 结束日期
            days: 回溯天数 (默认 120 天)

        Returns:
            五维共振分析结果
        """
        # 获取 K 线数据
        klines = self._get_klines(symbol, interval, start_date, end_date, days)

        if len(klines) < 30:
            return {
                'error': '数据不足',
                'message': f'需要至少 30 条 K 线数据，当前只有 {len(klines)} 条',
                'symbol': symbol
            }

        # 转换为 DataFrame
        df = self._klines_to_dataframe(klines)

        # 执行五维共振分析
        engine = UltimateEngine(df)
        result = engine.evaluate_all()

        # 添加股票信息
        result['symbol'] = symbol
        result['interval'] = interval
        result['data_points'] = len(klines)
        result['analysis_date'] = df.index[-1].strftime('%Y-%m-%d') if hasattr(df.index[-1], 'strftime') else str(df.index[-1])

        return result

    def analyze_with_strategies(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 120
    ) -> Dict:
        """
        使用三大策略进行分析

        Args:
            symbol: 股票代码
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
            days: 回溯天数

        Returns:
            三大策略分析结果
        """
        # 获取 K 线数据
        klines = self._get_klines(symbol, interval, start_date, end_date, days)

        if len(klines) < 30:
            return {
                'error': '数据不足',
                'message': f'需要至少 30 条 K 线数据，当前只有 {len(klines)} 条',
                'symbol': symbol
            }

        # 转换为 DataFrame
        df = self._klines_to_dataframe(klines)

        # VCP 策略
        vcp_strategy = VCPBreakoutStrategy(df)
        vcp_result = vcp_strategy.analyze()

        # 九转黄金坑策略
        td_strategy = TDGoldenPitStrategy(df)
        td_result = td_strategy.analyze()

        # 顶部背离策略
        div_strategy = TopDivergenceStrategy(df)
        div_result = div_strategy.analyze()

        return {
            'symbol': symbol,
            'interval': interval,
            'data_points': len(klines),
            'strategies': {
                'vcp_breakout': vcp_result,
                'td_golden_pit': td_result,
                'top_divergence': div_result
            }
        }

    def generate_analysis_report(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 120
    ) -> str:
        """
        生成完整分析报告

        Args:
            symbol: 股票代码
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
            days: 回溯天数

        Returns:
            格式化的分析报告
        """
        # 获取 K 线数据
        klines = self._get_klines(symbol, interval, start_date, end_date, days)

        if len(klines) < 30:
            return f"错误：数据不足，需要至少 30 条 K 线，当前只有 {len(klines)} 条"

        # 转换为 DataFrame
        df = self._klines_to_dataframe(klines)

        # 生成五维共振报告
        engine = UltimateEngine(df)
        report = engine.generate_report()

        # 添加策略概要
        report += "\n【策略信号概要】\n"

        vcp_strategy = VCPBreakoutStrategy(df)
        vcp_result = vcp_strategy.analyze()
        report += f"VCP 突破: {vcp_result['signal']} (得分: {vcp_result['score']})\n"

        td_strategy = TDGoldenPitStrategy(df)
        td_result = td_strategy.analyze()
        report += f"九转黄金坑: {td_result['signal']} (得分: {td_result['score']})\n"

        div_strategy = TopDivergenceStrategy(df)
        div_result = div_strategy.analyze()
        report += f"顶部背离: {div_result['signal']} (得分: {div_result['score']})\n"

        return report

    def get_technical_indicators(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 60
    ) -> Dict:
        """
        获取技术指标数据

        Args:
            symbol: 股票代码
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
            days: 回溯天数

        Returns:
            技术指标数据
        """
        # 获取 K 线数据
        klines = self._get_klines(symbol, interval, start_date, end_date, days)

        if len(klines) < 20:
            return {
                'error': '数据不足',
                'message': f'需要至少 20 条 K 线数据，当前只有 {len(klines)} 条',
                'symbol': symbol
            }

        # 转换为 DataFrame
        df = self._klines_to_dataframe(klines)

        # 计算所有指标
        from ..indicators import BaseIndicators
        indicators = BaseIndicators(df)
        df_with_indicators = indicators.calculate_all_indicators()

        # 获取最新信号
        latest_signals = indicators.get_latest_signals()

        return {
            'symbol': symbol,
            'interval': interval,
            'current_price': df['close'].iloc[-1],
            'latest_signals': latest_signals,
            'data_points': len(klines)
        }

    def _get_klines(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[str],
        end_date: Optional[str],
        days: int
    ) -> List:
        """
        获取 K 线数据

        Args:
            symbol: 股票代码
            interval: K线周期
            start_date: 开始日期
            end_date: 结束日期
            days: 回溯天数

        Returns:
            K 线数据列表
        """
        params = KLineQuerySchema(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            limit=200
        )
        return self.kline_repo.query_klines(params)

    def _klines_to_dataframe(self, klines: List) -> pd.DataFrame:
        """
        将 K 线数据转换为 DataFrame

        Args:
            klines: K 线数据列表

        Returns:
            pandas DataFrame
        """
        data = []
        for kline in klines:
            data.append({
                'open': kline.open_price,
                'high': kline.high_price,
                'low': kline.low_price,
                'close': kline.close_price,
                'volume': kline.volume,
                'timestamp': kline.timestamp
            })

        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)

        return df
