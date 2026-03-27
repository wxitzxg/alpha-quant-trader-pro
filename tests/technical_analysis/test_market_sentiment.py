# tests/technical_analysis/test_market_sentiment.py
"""市场情绪评分测试"""

import pytest
from datetime import datetime


class TestMarketSentimentSchemas:
    """测试数据结构"""

    def test_market_stock_data_creation(self):
        """测试 MarketStockData 创建"""
        from technical_analysis.schemas.market_sentiment import MarketStockData

        data = MarketStockData(
            symbol="600519",
            name="贵州茅台",
            price=1800.0,
            change_pct=2.5,
            turnover=0.5,
            amplitude=3.2
        )

        assert data.symbol == "600519"
        assert data.name == "贵州茅台"
        assert data.price == 1800.0
        assert data.change_pct == 2.5
        assert data.turnover == 0.5
        assert data.amplitude == 3.2

    def test_market_stats_creation(self):
        """测试 MarketStats 创建"""
        from technical_analysis.schemas.market_sentiment import MarketStats

        stats = MarketStats(
            total=100,
            gainers=60,
            losers=35,
            neutral=5,
            limit_up=3,
            limit_down=1,
            strong_stocks=10,
            weak_stocks=5,
            avg_change=0.8,
            avg_turnover=2.5,
            avg_volatility=3.1
        )

        assert stats.total == 100
        assert stats.gainers == 60
        assert stats.limit_up == 3

    def test_market_sentiment_result_creation(self):
        """测试 MarketSentimentResult 创建"""
        from technical_analysis.schemas.market_sentiment import (
            MarketSentimentResult,
            MarketStats
        )

        stats = MarketStats(
            total=100, gainers=60, losers=35, neutral=5,
            limit_up=3, limit_down=1, strong_stocks=10, weak_stocks=5,
            avg_change=0.8, avg_turnover=2.5, avg_volatility=3.1
        )

        result = MarketSentimentResult(
            score=57.0,
            level="偏乐观",
            emoji="🟢",
            description="市场偏强，情绪稳定",
            stats=stats,
            data_source="realtime",
            update_time="2026-03-27 14:30:00"
        )

        assert result.score == 57.0
        assert result.level == "偏乐观"
        assert result.data_source == "realtime"
