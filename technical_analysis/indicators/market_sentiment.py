"""
市场情绪评分计算器

7 维度评分体系 (基准分 50):
1. 涨跌家数比 (20%) -> ±10分
2. 平均涨幅 (20%) -> ±10分
3. 涨跌停比 (15%) -> ±8分
4. 强势股占比 (15%) -> ±8分
5. 成交活跃度 (10%) -> ±5分
6. 波动率 (10%) -> ±5分
7. 趋势强度 (10%) -> 暂不实现，固定 0 分
"""

from typing import List, Tuple

from technical_analysis.schemas.market_sentiment import (
    MarketStockData,
    MarketStats,
    MarketSentimentResult,
)


class MarketSentimentCalculator:
    """市场情绪评分计算器"""

    def calculate(self, stocks: List[MarketStockData]) -> MarketSentimentResult:
        """
        计算市场情绪评分

        Args:
            stocks: 股票市场数据列表

        Returns:
            市场情绪评分结果
        """
        # 空数据处理
        if not stocks:
            return MarketSentimentResult(
                score=50.0,
                level="中性",
                emoji="😐",
                description="暂无数据",
                stats=MarketStats(),
                data_source="unknown"
            )

        # 计算统计数据
        stats = self._calculate_stats(stocks)

        # 计算各维度得分
        sentiment_score = 50  # 基准分

        # 1. 涨跌家数比 (±10分)
        gain_ratio = stats.gainers / stats.total if stats.total > 0 else 0.5
        sentiment_score += self._score_gain_ratio(gain_ratio)

        # 2. 平均涨幅 (±10分)
        sentiment_score += self._score_avg_change(stats.avg_change)

        # 3. 涨跌停比 (±8分)
        limit_diff = stats.limit_up - stats.limit_down
        sentiment_score += self._score_limit_ratio(limit_diff)

        # 4. 强势股占比 (±8分)
        sentiment_score += self._score_strong_ratio(
            stats.strong_stocks, stats.weak_stocks, stats.total
        )

        # 5. 成交活跃度 (±5分)
        sentiment_score += self._score_turnover(stats.avg_turnover)

        # 6. 波动率 (±5分)
        sentiment_score += self._score_volatility(stats.avg_volatility)

        # 7. 趋势强度 - 暂不实现 (0分)
        # 需要 MA20 数据支持

        # 限制在 0-100 范围
        sentiment_score = max(0, min(100, sentiment_score))

        # 获取等级
        level, emoji = self._get_rating(sentiment_score)
        description = self._get_description(level)

        return MarketSentimentResult(
            score=round(sentiment_score, 1),
            level=level,
            emoji=emoji,
            description=description,
            stats=stats,
            data_source="calculator"
        )

    def _calculate_stats(self, stocks: List[MarketStockData]) -> MarketStats:
        """计算市场统计数据"""
        total = len(stocks)
        gainers = sum(1 for s in stocks if s.change_pct > 0)
        losers = sum(1 for s in stocks if s.change_pct < 0)
        neutral = total - gainers - losers

        # 涨停 (>=9.8%)
        limit_up = sum(1 for s in stocks if s.change_pct >= 9.8)
        # 跌停 (<=-9.8%)
        limit_down = sum(1 for s in stocks if s.change_pct <= -9.8)

        # 强势股 (涨>5%)
        strong_stocks = sum(1 for s in stocks if s.change_pct > 5)
        # 弱势股 (跌>5%)
        weak_stocks = sum(1 for s in stocks if s.change_pct < -5)

        # 平均涨幅
        avg_change = sum(s.change_pct for s in stocks) / total if total > 0 else 0

        # 平均换手率
        avg_turnover = sum(s.turnover for s in stocks) / total if total > 0 else 0

        # 平均振幅
        avg_volatility = sum(s.amplitude for s in stocks) / total if total > 0 else 0

        return MarketStats(
            total=total,
            gainers=gainers,
            losers=losers,
            neutral=neutral,
            limit_up=limit_up,
            limit_down=limit_down,
            strong_stocks=strong_stocks,
            weak_stocks=weak_stocks,
            avg_change=round(avg_change, 2),
            avg_turnover=round(avg_turnover, 2),
            avg_volatility=round(avg_volatility, 2)
        )

    def _score_gain_ratio(self, ratio: float) -> int:
        """涨跌家数比评分"""
        if ratio > 0.7:
            return 10
        elif ratio > 0.6:
            return 7
        elif ratio > 0.5:
            return 4
        elif ratio > 0.4:
            return 0
        elif ratio > 0.3:
            return -4
        else:
            return -10

    def _score_avg_change(self, avg_change: float) -> int:
        """平均涨幅评分"""
        if avg_change > 3:
            return 10
        elif avg_change > 1.5:
            return 7
        elif avg_change > 0.5:
            return 4
        elif avg_change > -0.5:
            return 0
        elif avg_change > -1.5:
            return -4
        elif avg_change > -3:
            return -7
        else:
            return -10

    def _score_limit_ratio(self, limit_diff: int) -> int:
        """涨跌停比评分"""
        if limit_diff >= 10:
            return 8
        elif limit_diff >= 5:
            return 5
        elif limit_diff >= 1:
            return 2
        elif limit_diff >= -1:
            return 0
        elif limit_diff >= -5:
            return -2
        elif limit_diff >= -10:
            return -5
        else:
            return -8

    def _score_strong_ratio(
        self,
        strong_stocks: int,
        weak_stocks: int,
        total: int
    ) -> int:
        """强势股占比评分"""
        if total == 0:
            return 0

        strong_ratio = strong_stocks / total
        weak_ratio = weak_stocks / total

        if strong_ratio > 0.3:
            return 8
        elif strong_ratio > 0.2:
            return 5
        elif strong_ratio > 0.1:
            return 2
        elif weak_ratio > 0.3:
            return -8
        elif weak_ratio > 0.2:
            return -5
        elif weak_ratio > 0.1:
            return -2
        return 0

    def _score_turnover(self, avg_turnover: float) -> int:
        """成交活跃度评分"""
        if avg_turnover > 5:
            return 5
        elif avg_turnover > 3:
            return 3
        elif avg_turnover > 2:
            return 1
        elif avg_turnover > 1:
            return 0
        else:
            return -5

    def _score_volatility(self, avg_volatility: float) -> int:
        """波动率评分"""
        if avg_volatility > 8:
            return -3
        elif avg_volatility > 5:
            return 2
        elif avg_volatility > 3:
            return 5
        elif avg_volatility > 2:
            return 2
        else:
            return -3

    def _get_rating(self, score: float) -> Tuple[str, str]:
        """获取评级和表情"""
        if score >= 80:
            return ("极度乐观", "🔥")
        elif score >= 65:
            return ("乐观", "📈")
        elif score >= 55:
            return ("偏乐观", "🟢")
        elif score >= 45:
            return ("中性", "😐")
        elif score >= 35:
            return ("偏悲观", "🔻")
        elif score >= 20:
            return ("悲观", "📉")
        else:
            return ("极度悲观", "❄️")

    def _get_description(self, level: str) -> str:
        """获取描述"""
        descriptions = {
            "极度乐观": "市场情绪极度亢奋，注意追高风险",
            "乐观": "市场情绪积极，趋势向上",
            "偏乐观": "市场偏强，情绪稳定",
            "中性": "市场平稳，多空平衡",
            "偏悲观": "市场偏弱，观望为主",
            "悲观": "市场情绪低迷，谨慎操作",
            "极度悲观": "市场情绪极度低迷，恐慌情绪蔓延"
        }
        return descriptions.get(level, "市场状态未知")
