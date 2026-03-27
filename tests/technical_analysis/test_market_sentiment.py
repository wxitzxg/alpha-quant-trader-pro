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


class TestMarketSentimentCalculator:
    """测试评分计算器"""

    def test_calculate_with_normal_data(self):
        """测试正常数据计算"""
        from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator
        from technical_analysis.schemas.market_sentiment import MarketStockData

        calculator = MarketSentimentCalculator()

        # 模拟上涨市场数据
        stocks = [
            MarketStockData("600000", "浦发银行", 10.0, 2.5, 1.5, 3.0),
            MarketStockData("600001", "邯郸钢铁", 5.0, 1.2, 2.0, 2.5),
            MarketStockData("600002", "齐鲁石化", 8.0, -0.5, 1.0, 2.0),
            MarketStockData("600003", "ST东北高", 3.0, 5.5, 3.0, 6.0),  # 强势股
            MarketStockData("600004", "白云机场", 15.0, 10.2, 4.0, 12.0),  # 涨停
        ]

        result = calculator.calculate(stocks)

        assert 0 <= result.score <= 100
        assert result.stats.total == 5
        assert result.stats.gainers == 4
        assert result.stats.losers == 1
        assert result.stats.limit_up == 1  # 10.2% >= 9.8%
        assert result.stats.strong_stocks == 2  # > 5%

    def test_calculate_with_empty_data(self):
        """测试空数据返回中性评分"""
        from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator

        calculator = MarketSentimentCalculator()
        result = calculator.calculate([])

        assert result.score == 50.0
        assert result.level == "中性"
        assert result.description == "暂无数据"
        assert result.stats.total == 0

    def test_rating_level_mapping(self):
        """测试评分等级映射"""
        from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator

        calculator = MarketSentimentCalculator()

        # 测试各等级映射
        assert calculator._get_rating(85) == ("极度乐观", "🔥")
        assert calculator._get_rating(70) == ("乐观", "📈")
        assert calculator._get_rating(60) == ("偏乐观", "🟢")
        assert calculator._get_rating(50) == ("中性", "😐")
        assert calculator._get_rating(40) == ("偏悲观", "🔻")
        assert calculator._get_rating(30) == ("悲观", "📉")
        assert calculator._get_rating(15) == ("极度悲观", "❄️")

    def test_dimension_score_boundaries(self):
        """测试各维度边界值"""
        from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator

        calculator = MarketSentimentCalculator()

        # 1. 测试涨跌家数比评分
        assert calculator._score_gain_ratio(0.75) == 10  # > 70%
        assert calculator._score_gain_ratio(0.65) == 7   # > 60%
        assert calculator._score_gain_ratio(0.55) == 4   # > 50%
        assert calculator._score_gain_ratio(0.45) == 0   # > 40%
        assert calculator._score_gain_ratio(0.35) == -4  # > 30%
        assert calculator._score_gain_ratio(0.25) == -10 # <= 30%

        # 2. 测试平均涨幅评分
        assert calculator._score_avg_change(4.0) == 10   # > 3%
        assert calculator._score_avg_change(2.0) == 7    # > 1.5%
        assert calculator._score_avg_change(0.8) == 4    # > 0.5%
        assert calculator._score_avg_change(0.0) == 0    # > -0.5%
        assert calculator._score_avg_change(-1.0) == -4  # > -1.5%
        assert calculator._score_avg_change(-2.5) == -7  # > -3%
        assert calculator._score_avg_change(-5.0) == -10 # <= -3%

        # 3. 测试涨跌停比评分
        assert calculator._score_limit_ratio(15) == 8    # >= 10
        assert calculator._score_limit_ratio(6) == 5     # >= 5
        assert calculator._score_limit_ratio(2) == 2     # >= 1
        assert calculator._score_limit_ratio(0) == 0     # >= -1
        assert calculator._score_limit_ratio(-3) == -2   # >= -5
        assert calculator._score_limit_ratio(-8) == -5   # >= -10
        assert calculator._score_limit_ratio(-15) == -8  # < -10

        # 4. 测试强势股占比评分
        assert calculator._score_strong_ratio(35, 5, 100) == 8   # strong > 30%
        assert calculator._score_strong_ratio(25, 5, 100) == 5   # strong > 20%
        assert calculator._score_strong_ratio(15, 5, 100) == 2   # strong > 10%
        assert calculator._score_strong_ratio(5, 35, 100) == -8  # weak > 30%
        assert calculator._score_strong_ratio(5, 25, 100) == -5  # weak > 20%
        assert calculator._score_strong_ratio(5, 15, 100) == -2  # weak > 10%

        # 5. 测试成交活跃度评分
        assert calculator._score_turnover(6.0) == 5   # > 5%
        assert calculator._score_turnover(4.0) == 3   # > 3%
        assert calculator._score_turnover(2.5) == 1   # > 2%
        assert calculator._score_turnover(1.5) == 0   # > 1%
        assert calculator._score_turnover(0.5) == -5  # <= 1%

        # 6. 测试波动率评分
        assert calculator._score_volatility(10.0) == -3  # > 8%
        assert calculator._score_volatility(6.0) == 2    # > 5%
        assert calculator._score_volatility(4.0) == 5    # 3-5%
        assert calculator._score_volatility(2.5) == 2    # > 2%
        assert calculator._score_volatility(1.5) == -3   # <= 2%


class TestKLineRepositoryExtension:
    """测试 KLineRepository 扩展方法"""

    def test_get_all_latest_klines_method_exists(self):
        """测试 get_all_latest_klines 方法存在"""
        from stock_market.repositories.stock_repository import KLineRepository

        # 验证方法存在
        assert hasattr(KLineRepository, 'get_all_latest_klines')

    def test_get_all_latest_klines_with_mock_session(self):
        """测试使用内存 SQLite 数据库的 get_all_latest_klines"""
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from common.database import Base
        from stock_market.models import KLine, Stock
        from datetime import date

        # 创建内存数据库 (禁用 RETURNING 以兼容 SQLite)
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 使用 raw SQL 插入测试数据以避免 RETURNING 兼容性问题
        session.execute(text("""
            INSERT INTO stocks (id, symbol, name, exchange, list_date, is_active)
            VALUES
                (1, '600000', '浦发银行', 'SH', '2020-01-01', 1),
                (2, '600001', '邯郸钢铁', 'SH', '2020-01-01', 1)
        """))

        session.execute(text("""
            INSERT INTO klines (id, stock_id, symbol, date, interval, open, high, low, close, volume, amount, sync_time)
            VALUES
                (1, 1, '600000', '2026-03-26', '1d', 10.0, 10.5, 9.8, 10.2, 1000000, 10200000.0, datetime('now')),
                (2, 1, '600000', '2026-03-27', '1d', 10.2, 10.8, 10.0, 10.6, 1200000, 12720000.0, datetime('now')),
                (3, 2, '600001', '2026-03-26', '1d', 5.0, 5.2, 4.9, 5.1, 500000, 2550000.0, datetime('now')),
                (4, 2, '600001', '2026-03-27', '1d', 5.1, 5.3, 5.0, 5.2, 600000, 3120000.0, datetime('now'))
        """))
        session.commit()

        from stock_market.repositories.stock_repository import KLineRepository
        repo = KLineRepository(session)
        result = repo.get_all_latest_klines(interval="1d")

        # 验证返回结果 - 应该返回两只股票的最新 K 线
        assert len(result) == 2
        symbols = [k.symbol for k in result]
        assert "600000" in symbols
        assert "600001" in symbols
        # 验证都是最新日期
        for k in result:
            assert k.date == date(2026, 3, 27)
