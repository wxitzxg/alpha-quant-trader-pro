"""
市场情绪 API 路由
"""

import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from common.database import DatabaseManager
from technical_analysis.services import MarketSentimentService

# Database URL from environment
DATABASE_URL = os.environ.get(
    "DATABASE__URL",
    "postgresql://alpha_quant_trader_pro:alpha_quant_trader_pro@alpha-quant-db:5432/alpha_quant_trader_pro"
)


def get_db_session() -> Session:
    """获取数据库 session 依赖"""
    db_manager = DatabaseManager(DATABASE_URL)
    with db_manager.get_session() as session:
        yield session


router = APIRouter(prefix="/market", tags=["市场情绪"])


@router.get("/sentiment")
async def get_market_sentiment(
    use_realtime: bool = Query(True, description="是否使用实时数据"),
    exclude_gem: bool = Query(False, description="排除创业板"),
    exclude_star: bool = Query(False, description="排除科创板"),
    session: Session = Depends(get_db_session)
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
    session: Session = Depends(get_db_session)
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
