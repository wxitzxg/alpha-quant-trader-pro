# Market Sentiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在技术分析模块实现 7 维度市场情绪评分功能，支持 API 接口调用。

**Architecture:** 采用 Repository-Service 架构，新增 `MarketSentimentService` 服务层和 `MarketSentimentCalculator` 评分计算器。数据源优先使用实时行情，失败时降级到 K 线数据。

**Tech Stack:** Python 3.9+, Pydantic, SQLAlchemy, FastAPI

**Out of Scope (Phase 1):**
- Selection Strategy Filter (`filter_by_sentiment`) - 需要选股引擎集成
- Alert System WebSocket 推送 - 需要告警系统基础设施

---

## File Structure

| File | Action | Description |
|------|--------|-------------|
| `technical_analysis/schemas/__init__.py` | Create | 新建目录，数据结构导出 |
| `technical_analysis/schemas/market_sentiment.py` | Create | 数据结构定义 |
| `technical_analysis/indicators/market_sentiment.py` | Create | 7 维度评分计算器 |
| `technical_analysis/services/market_sentiment_service.py` | Create | 服务层入口 |
| `stock_market/repositories/stock_repository.py` | Modify | 新增 `get_all_latest_klines` 方法 |
| `api_server/routers/market_sentiment.py` | Create | REST API 路由 |
| `technical_analysis/indicators/__init__.py` | Modify | 添加导出 |
| `technical_analysis/services/__init__.py` | Modify | 添加导出 |
| `technical_analysis/__init__.py` | Modify | 添加导出 |
| `api_server/routers/__init__.py` | Modify | 添加路由导出 |
| `api_server/main.py` | Modify | 注册路由 |
| `tests/technical_analysis/test_market_sentiment.py` | Create | 单元测试 |

---

### Task 1: Data Structures (Schemas)

**Files:**
- Create: `technical_analysis/schemas/__init__.py`
- Create: `technical_analysis/schemas/market_sentiment.py`
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Write the failing test for data structures**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'technical_analysis.schemas'"

- [ ] **Step 3: Create the schemas directory and __init__.py**

```python
# technical_analysis/schemas/__init__.py
"""Market Sentiment Schemas - 市场情绪数据结构"""

from .market_sentiment import (
    MarketStockData,
    MarketStats,
    MarketSentimentResult,
)

__all__ = [
    'MarketStockData',
    'MarketStats',
    'MarketSentimentResult',
]
```

- [ ] **Step 4: Create the market_sentiment.py schema file**

```python
# technical_analysis/schemas/market_sentiment.py
"""
市场情绪评分数据结构定义
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class MarketStockData:
    """单只股票的市场数据"""
    symbol: str
    name: str
    price: float
    change_pct: float         # 涨跌幅%
    turnover: float = 0.0     # 换手率% (默认 0)
    amplitude: float = 0.0    # 振幅% (默认 0)


@dataclass
class MarketStats:
    """市场统计数据"""
    total: int = 0              # 总股票数
    gainers: int = 0            # 上涨数
    losers: int = 0             # 下跌数
    neutral: int = 0            # 平盘数
    limit_up: int = 0           # 涨停数 (≥9.8%)
    limit_down: int = 0         # 跌停数 (≤-9.8%)
    strong_stocks: int = 0      # 强势股数 (涨>5%)
    weak_stocks: int = 0        # 弱势股数 (跌>5%)
    avg_change: float = 0.0     # 平均涨幅%
    avg_turnover: float = 0.0   # 平均换手率%
    avg_volatility: float = 0.0 # 平均振幅%


@dataclass
class MarketSentimentResult:
    """市场情绪评分结果"""
    score: float                              # 情绪评分 (0-100)
    level: str                                # 等级
    emoji: str                                # 表情符号
    description: str                          # 描述
    stats: MarketStats                        # 统计数据
    data_source: str                          # 数据来源: realtime/kline
    update_time: str = field(                 # 计算时间
        default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add technical_analysis/schemas/ tests/technical_analysis/test_market_sentiment.py
git commit -m "$(cat <<'EOF'
feat(technical_analysis): add market sentiment data structures

- Add MarketStockData for individual stock data
- Add MarketStats for market statistics
- Add MarketSentimentResult for scoring output

EOF
)"
```

---

### Task 2: Market Sentiment Calculator

**Files:**
- Create: `technical_analysis/indicators/market_sentiment.py`
- Modify: `technical_analysis/indicators/__init__.py`
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Write the failing test for calculator**

```python
# tests/technical_analysis/test_market_sentiment.py (append to existing file)

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestMarketSentimentCalculator -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create the calculator implementation**

```python
# technical_analysis/indicators/market_sentiment.py
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

from datetime import datetime
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

        # 涨停 (≥9.8%)
        limit_up = sum(1 for s in stocks if s.change_pct >= 9.8)
        # 跌停 (≤-9.8%)
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
```

- [ ] **Step 4: Update indicators __init__.py**

```python
# technical_analysis/indicators/__init__.py
"""Technical Indicators - 技术指标计算模块"""

from .base_indicators import BaseIndicators
from .td_sequential import TDSequential
from .vcp_detector import VCPDetector
from .divergence_check import DivergenceCheck
from .zigzag import ZigZag
from .market_sentiment import MarketSentimentCalculator

__all__ = [
    'BaseIndicators',
    'TDSequential',
    'VCPDetector',
    'DivergenceCheck',
    'ZigZag',
    'MarketSentimentCalculator',
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add technical_analysis/indicators/market_sentiment.py technical_analysis/indicators/__init__.py tests/technical_analysis/test_market_sentiment.py
git commit -m "$(cat <<'EOF'
feat(technical_analysis): add market sentiment calculator

- 7-dimension scoring system
- Statistics calculation
- Rating level mapping

EOF
)"
```

---

### Task 3: Repository Method for K-line Fallback

**Files:**
- Modify: `stock_market/repositories/stock_repository.py`
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Write the failing test for repository method**

```python
# tests/technical_analysis/test_market_sentiment.py (append)

class TestKLineRepositoryExtension:
    """测试 KLineRepository 扩展方法"""

    def test_get_all_latest_klines_method_exists(self):
        """测试 get_all_latest_klines 方法存在"""
        from stock_market.repositories.stock_repository import KLineRepository

        # 验证方法存在
        assert hasattr(KLineRepository, 'get_all_latest_klines')

    def test_get_all_latest_klines_with_mock_session(self):
        """测试使用 mock session 的 get_all_latest_klines"""
        from unittest.mock import MagicMock, patch
        from stock_market.models import KLine

        # 创建 mock session 和返回值
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        from stock_market.repositories.stock_repository import KLineRepository
        repo = KLineRepository(mock_session)
        result = repo.get_all_latest_klines(interval="1d")

        # 验证返回空列表
        assert result == []
        # 验证 execute 被调用
        assert mock_session.execute.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestKLineRepositoryExtension -v`
Expected: FAIL with "AttributeError: type object 'KLineRepository' has no attribute 'get_all_latest_klines'"

- [ ] **Step 3: Add repository method**

```python
# stock_market/repositories/stock_repository.py
# 在 KLineRepository 类中添加方法 (在 query_klines 方法后)

    def get_all_latest_klines(
        self,
        interval: str = "1d",
        limit: int = 5000
    ) -> List[KLine]:
        """
        获取所有股票的最新 K 线数据

        使用子查询获取每只股票的最新日期，然后关联获取完整 K 线

        Args:
            interval: K 线周期
            limit: 最大返回数量

        Returns:
            每只股票最新一天 K 线数据的列表
        """
        from sqlalchemy import func, and_

        # 子查询：获取每只股票的最新日期
        subquery = self.session.query(
            KLine.symbol,
            func.max(KLine.date).label('max_date')
        ).filter(
            KLine.interval == interval
        ).group_by(
            KLine.symbol
        ).subquery()

        # 主查询：关联获取完整 K 线数据
        stmt = select(KLine).join(
            subquery,
            and_(
                KLine.symbol == subquery.c.symbol,
                KLine.date == subquery.c.max_date,
                KLine.interval == interval
            )
        ).limit(limit)

        result = self.session.execute(stmt).scalars().all()
        return list(result)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestKLineRepositoryExtension -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add stock_market/repositories/stock_repository.py tests/technical_analysis/test_market_sentiment.py
git commit -m "$(cat <<'EOF'
feat(stock_market): add get_all_latest_klines method

For market sentiment calculation fallback

EOF
)"
```

---

### Task 4: Market Sentiment Service

**Files:**
- Create: `technical_analysis/services/market_sentiment_service.py`
- Modify: `technical_analysis/services/__init__.py`
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Write the failing test for service**

```python
# tests/technical_analysis/test_market_sentiment.py (append)

class TestMarketSentimentService:
    """测试市场情绪服务"""

    def test_service_with_mock_data(self):
        """测试服务层使用 mock 数据"""
        from unittest.mock import MagicMock, patch
        from technical_analysis.schemas.market_sentiment import MarketStockData

        # Mock dependencies
        mock_session = MagicMock()
        mock_stock_repo = MagicMock()
        mock_stock_repo.get_active.return_value = []  # 无股票数据

        with patch('technical_analysis.services.market_sentiment_service.StockRepository', return_value=mock_stock_repo):
            from technical_analysis.services.market_sentiment_service import MarketSentimentService

            service = MarketSentimentService(mock_session)
            result = service.get_market_sentiment(use_realtime=False)

            assert result.score == 50.0  # 无数据返回中性

    def test_service_fallback_to_kline(self):
        """测试实时数据失败时降级到 K 线"""
        from unittest.mock import MagicMock, patch

        mock_session = MagicMock()

        # Mock StockRepository
        mock_stock_repo = MagicMock()
        mock_stock_repo.get_active.return_value = []

        with patch('technical_analysis.services.market_sentiment_service.StockRepository', return_value=mock_stock_repo):
            from technical_analysis.services.market_sentiment_service import MarketSentimentService

            service = MarketSentimentService(mock_session)
            result = service.get_market_sentiment(use_realtime=True)

            # 无股票数据，返回中性评分
            assert result.score == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestMarketSentimentService -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create the service implementation**

```python
# technical_analysis/services/market_sentiment_service.py
"""
Market Sentiment Service - 市场情绪服务层

提供市场情绪评分功能，支持实时数据优先和 K 线数据降级
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session

from stock_market.repositories import StockRepository, KLineRepository
from data_sources.aggregator import DataSourceAggregator
from technical_analysis.schemas.market_sentiment import (
    MarketStockData,
    MarketSentimentResult,
)
from technical_analysis.indicators.market_sentiment import MarketSentimentCalculator

logger = logging.getLogger(__name__)


class MarketSentimentService:
    """市场情绪评分服务"""

    def __init__(self, session: Session):
        """
        初始化市场情绪服务

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.stock_repo = StockRepository(session)
        self.kline_repo = KLineRepository(session)
        self.calculator = MarketSentimentCalculator()
        self.data_aggregator = DataSourceAggregator()

    def get_market_sentiment(
        self,
        use_realtime: bool = True,
        stock_filter: Optional[Dict] = None
    ) -> MarketSentimentResult:
        """
        获取市场情绪评分

        Args:
            use_realtime: 是否优先使用实时数据
            stock_filter: 可选的股票过滤条件

        Returns:
            市场情绪评分结果
        """
        stocks_data: List[MarketStockData] = []
        data_source = "unknown"

        # 尝试获取实时数据
        if use_realtime:
            try:
                stocks_data = self._get_realtime_data(stock_filter)
                if stocks_data:
                    data_source = "realtime"
                    logger.info(f"获取实时行情数据: {len(stocks_data)} 只股票")
            except Exception as e:
                logger.warning(f"实时数据获取失败: {e}，尝试 K 线数据")

        # 降级到 K 线数据
        if not stocks_data:
            try:
                stocks_data = self._get_kline_data(stock_filter)
                if stocks_data:
                    data_source = "kline"
                    logger.info(f"获取 K 线数据: {len(stocks_data)} 只股票")
            except Exception as e:
                logger.error(f"K 线数据获取失败: {e}")

        # 计算评分
        result = self.calculator.calculate(stocks_data)
        result.data_source = data_source

        return result

    def get_sentiment_for_stocks(
        self,
        symbols: List[str],
        use_realtime: bool = True
    ) -> MarketSentimentResult:
        """
        计算指定股票池的市场情绪

        Args:
            symbols: 股票代码列表
            use_realtime: 是否使用实时数据

        Returns:
            市场情绪评分结果
        """
        stocks_data: List[MarketStockData] = []
        data_source = "unknown"

        if use_realtime:
            try:
                quotes = self.data_aggregator.batch_get_realtime(symbols)
                stocks_data = self._quotes_to_stock_data(quotes)
                if stocks_data:
                    data_source = "realtime"
            except Exception as e:
                logger.warning(f"实时数据获取失败: {e}")

        if not stocks_data:
            try:
                klines = self.kline_repo.get_all_latest_klines()
                # 过滤指定股票
                klines = [k for k in klines if k.symbol in symbols]
                stocks_data = self._klines_to_stock_data(klines)
                if stocks_data:
                    data_source = "kline"
            except Exception as e:
                logger.error(f"K 线数据获取失败: {e}")

        result = self.calculator.calculate(stocks_data)
        result.data_source = data_source

        return result

    def _get_realtime_data(
        self,
        stock_filter: Optional[Dict] = None
    ) -> List[MarketStockData]:
        """获取实时行情数据"""
        # 获取所有上市股票代码
        stocks = self.stock_repo.get_active()
        symbols = [s.symbol for s in stocks]

        # 应用过滤条件
        if stock_filter:
            exclude_gem = stock_filter.get('exclude_gem', False)
            exclude_star = stock_filter.get('exclude_star', False)

            if exclude_gem:
                symbols = [s for s in symbols if not s.startswith('3')]
            if exclude_star:
                symbols = [s for s in symbols if not s.startswith('688')]

        # 分批获取实时数据 (每批 500 只)
        all_quotes = []
        batch_size = 500

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            try:
                quotes = self.data_aggregator.batch_get_realtime(batch)
                all_quotes.extend(quotes)
            except Exception as e:
                logger.warning(f"批量获取实时数据失败 (batch {i}): {e}")

        return self._quotes_to_stock_data(all_quotes)

    def _get_kline_data(
        self,
        stock_filter: Optional[Dict] = None
    ) -> List[MarketStockData]:
        """获取 K 线数据"""
        klines = self.kline_repo.get_all_latest_klines()

        # 应用过滤条件
        if stock_filter:
            exclude_gem = stock_filter.get('exclude_gem', False)
            exclude_star = stock_filter.get('exclude_star', False)

            if exclude_gem:
                klines = [k for k in klines if not k.symbol.startswith('3')]
            if exclude_star:
                klines = [k for k in klines if not k.symbol.startswith('688')]

        return self._klines_to_stock_data(klines)

    def _quotes_to_stock_data(self, quotes: List) -> List[MarketStockData]:
        """将 Quote 对象转换为 MarketStockData"""
        result = []

        for quote in quotes:
            if not quote:
                continue

            # 计算涨跌幅 (Quote.percent 是小数，需乘 100)
            change_pct = quote.percent * 100 if quote.percent else 0

            # 计算振幅
            amplitude = 0.0
            if quote.high and quote.low and quote.pre_close and quote.pre_close > 0:
                amplitude = ((quote.high - quote.low) / quote.pre_close) * 100

            result.append(MarketStockData(
                symbol=quote.symbol,
                name=quote.name or "",
                price=quote.price,
                change_pct=round(change_pct, 2),
                turnover=0.0,  # 实时数据通常无换手率
                amplitude=round(amplitude, 2)
            ))

        return result

    def _klines_to_stock_data(self, klines: List) -> List[MarketStockData]:
        """将 KLine 对象转换为 MarketStockData"""
        result = []

        for kline in klines:
            if not kline:
                continue

            # 计算涨跌幅
            change_pct = 0.0
            if kline.open and kline.open > 0:
                change_pct = ((kline.close - kline.open) / kline.open) * 100

            # 计算振幅
            amplitude = 0.0
            if kline.open and kline.open > 0:
                amplitude = ((kline.high - kline.low) / kline.open) * 100

            result.append(MarketStockData(
                symbol=kline.symbol,
                name="",  # K 线数据通常无名称
                price=float(kline.close),
                change_pct=round(change_pct, 2),
                turnover=float(kline.turnover) if kline.turnover else 0.0,
                amplitude=round(amplitude, 2)
            ))

        return result
```

- [ ] **Step 4: Update services __init__.py**

```python
# technical_analysis/services/__init__.py
"""Analysis Services - 技术分析服务层"""

from .analysis_service import AnalysisService
from .market_sentiment_service import MarketSentimentService

__all__ = [
    'AnalysisService',
    'MarketSentimentService',
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add technical_analysis/services/market_sentiment_service.py technical_analysis/services/__init__.py tests/technical_analysis/test_market_sentiment.py
git commit -m "$(cat <<'EOF'
feat(technical_analysis): add market sentiment service

- Realtime data with fallback to kline
- Batch processing (500 per batch)
- Stock filtering support

EOF
)"
```

---

### Task 5: API Router

**Files:**
- Create: `api_server/routers/market_sentiment.py`
- Modify: `api_server/routers/__init__.py`
- Modify: `api_server/main.py`
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Write the failing test for API endpoint**

```python
# tests/technical_analysis/test_market_sentiment.py (append)

class TestMarketSentimentAPI:
    """测试 API 端点"""

    def test_api_endpoint_exists(self):
        """测试 API 端点路由存在"""
        from api_server.routers import market_sentiment_router

        # 验证路由器存在
        assert market_sentiment_router is not None

        # 验证路由路径
        routes = [route.path for route in market_sentiment_router.routes]
        assert "/sentiment" in routes
        assert "/sentiment/stats" in routes

    def test_api_response_format(self):
        """测试 API 响应格式"""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, MagicMock

        # 创建测试应用
        from fastapi import FastAPI
        from api_server.routers.market_sentiment import router

        app = FastAPI()
        app.include_router(router)

        # Mock 服务层
        with patch('api_server.routers.market_sentiment.MarketSentimentService') as MockService:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.score = 50.0
            mock_result.level = "中性"
            mock_result.emoji = "😐"
            mock_result.description = "暂无数据"
            mock_result.data_source = "unknown"
            mock_result.update_time = "2026-03-27 14:30:00"
            mock_result.stats.total = 0
            mock_result.stats.gainers = 0
            mock_result.stats.losers = 0
            mock_result.stats.neutral = 0
            mock_result.stats.limit_up = 0
            mock_result.stats.limit_down = 0
            mock_result.stats.strong_stocks = 0
            mock_result.stats.weak_stocks = 0
            mock_result.stats.avg_change = 0.0
            mock_result.stats.avg_turnover = 0.0
            mock_result.stats.avg_volatility = 0.0
            mock_instance.get_market_sentiment.return_value = mock_result
            MockService.return_value = mock_instance

            client = TestClient(app)
            response = client.get("/sentiment?use_realtime=false")

            assert response.status_code == 200
            data = response.json()
            assert "score" in data
            assert "level" in data
            assert "stats" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestMarketSentimentAPI -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create the API router**

```python
# api_server/routers/market_sentiment.py
"""
市场情绪 API 路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from common.database import get_session
from technical_analysis.services import MarketSentimentService

router = APIRouter(prefix="/market", tags=["市场情绪"])


@router.get("/sentiment")
async def get_market_sentiment(
    use_realtime: bool = Query(True, description="是否使用实时数据"),
    exclude_gem: bool = Query(False, description="排除创业板"),
    exclude_star: bool = Query(False, description="排除科创板"),
    session: Session = Depends(get_session)
):
    """
    获取市场情绪评分

    返回 7 维度市场情绪评分，包括:
    - 涨跌家数比
    - 平均涨幅
    - 涨跌停比
    - 强势股占比
    - 成交活跃度
    - 波动率
    """
    service = MarketSentimentService(session)

    stock_filter = {
        'exclude_gem': exclude_gem,
        'exclude_star': exclude_star
    }

    result = service.get_market_sentiment(
        use_realtime=use_realtime,
        stock_filter=stock_filter
    )

    return {
        "score": result.score,
        "level": result.level,
        "emoji": result.emoji,
        "description": result.description,
        "stats": {
            "total": result.stats.total,
            "gainers": result.stats.gainers,
            "losers": result.stats.losers,
            "neutral": result.stats.neutral,
            "limit_up": result.stats.limit_up,
            "limit_down": result.stats.limit_down,
            "strong_stocks": result.stats.strong_stocks,
            "weak_stocks": result.stats.weak_stocks,
            "avg_change": result.stats.avg_change,
            "avg_turnover": result.stats.avg_turnover,
            "avg_volatility": result.stats.avg_volatility
        },
        "data_source": result.data_source,
        "update_time": result.update_time
    }


@router.get("/sentiment/stats")
async def get_market_stats(
    use_realtime: bool = Query(True, description="是否使用实时数据"),
    session: Session = Depends(get_session)
):
    """
    获取市场详细统计数据
    """
    service = MarketSentimentService(session)
    result = service.get_market_sentiment(use_realtime=use_realtime)

    return {
        "stats": {
            "total": result.stats.total,
            "gainers": result.stats.gainers,
            "losers": result.stats.losers,
            "neutral": result.stats.neutral,
            "limit_up": result.stats.limit_up,
            "limit_down": result.stats.limit_down,
            "strong_stocks": result.stats.strong_stocks,
            "weak_stocks": result.stats.weak_stocks,
            "avg_change": result.stats.avg_change,
            "avg_turnover": result.stats.avg_turnover,
            "avg_volatility": result.stats.avg_volatility
        },
        "data_source": result.data_source,
        "update_time": result.update_time
    }
```

- [ ] **Step 4: Update routers __init__.py**

```python
# api_server/routers/__init__.py
"""Routers 模块"""
from .health import health_router
from .data_source import data_source_router
from .stock_market import stock_market_router
from .portfolio import portfolio_router
from .analysis import analysis_router
from .risk_control import risk_control_router
from .performance import performance_router
from .alerts import alerts_router
from .backtest import backtest_router
from .simulation import simulation_router
from .base_indicators import base_indicators_router
from .divergence import divergence_router
from .td_sequential import td_sequential_router
from .vcp import vcp_router
from .zigzag import zigzag_router
from .fundflow import fundflow_router
from .news import news_router
from .financial import financial_router
from .market_sentiment import router as market_sentiment_router

__all__ = [
    "health_router",
    "data_source_router",
    "stock_market_router",
    "portfolio_router",
    "analysis_router",
    "risk_control_router",
    "performance_router",
    "alerts_router",
    "backtest_router",
    "simulation_router",
    "base_indicators_router",
    "divergence_router",
    "td_sequential_router",
    "vcp_router",
    "zigzag_router",
    "fundflow_router",
    "news_router",
    "financial_router",
    "market_sentiment_router",
]
```

- [ ] **Step 5: Update main.py to register router**

```python
# api_server/main.py
# 在导入部分添加 market_sentiment_router
from .routers import (
    # ... existing imports ...
    market_sentiment_router
)

# 在 app.include_router 部分添加 (使用 /api/v1 前缀保持一致)
app.include_router(market_sentiment_router, prefix="/api/v1", tags=["市场情绪"])
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py::TestMarketSentimentAPI -v`
Expected: PASS

- [ ] **Step 7: Update technical_analysis __init__.py**

```python
# technical_analysis/__init__.py
"""Technical Analysis Module - 股票技术分析模块"""

__version__ = "1.0.0"

from .services import AnalysisService, MarketSentimentService
from .indicators import MarketSentimentCalculator

__all__ = [
    'AnalysisService',
    'MarketSentimentService',
    'MarketSentimentCalculator',
]
```

- [ ] **Step 8: Commit**

```bash
git add api_server/routers/market_sentiment.py api_server/routers/__init__.py api_server/main.py technical_analysis/__init__.py tests/technical_analysis/test_market_sentiment.py
git commit -m "$(cat <<'EOF'
feat(api): add market sentiment API endpoints

- GET /api/v1/market/sentiment
- GET /api/v1/market/sentiment/stats

EOF
)"
```

---

### Task 6: Integration Test and Final Verification

**Files:**
- Test: `tests/technical_analysis/test_market_sentiment.py`

- [ ] **Step 1: Run all tests**

Run: `cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -m pytest tests/technical_analysis/test_market_sentiment.py -v`
Expected: PASS (all tests ~15+)

- [ ] **Step 2: Verify module imports work**

```bash
cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/recomment && python -c "
from technical_analysis import MarketSentimentService, MarketSentimentCalculator
from technical_analysis.schemas import MarketSentimentResult, MarketStats, MarketStockData
from api_server.routers import market_sentiment_router
print('All imports successful')
"
```
Expected: "All imports successful"

- [ ] **Step 3: Final commit (if any changes)**

```bash
git status
# If clean, no action needed
```

---

## Summary

**Total Tasks:** 6
**Estimated Time:** 2-3 hours

**Key Deliverables:**
1. Data structures for market sentiment
2. 7-dimension scoring calculator
3. Service layer with data source fallback
4. REST API endpoints (`/api/v1/market/sentiment`)
5. Comprehensive tests (~15+ test cases)

**Testing Commands:**
```bash
# Run all market sentiment tests
python -m pytest tests/technical_analysis/test_market_sentiment.py -v

# Run with coverage
python -m pytest tests/technical_analysis/test_market_sentiment.py --cov=technical_analysis --cov-report=term-missing
```

**API Endpoints:**
- `GET /api/v1/market/sentiment` - 获取市场情绪评分
- `GET /api/v1/market/sentiment/stats` - 获取市场统计数据
