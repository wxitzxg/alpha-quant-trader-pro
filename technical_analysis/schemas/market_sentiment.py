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
