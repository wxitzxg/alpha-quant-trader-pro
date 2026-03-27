#!/usr/bin/env python3
"""
Stock Recommendation API Router

Provides endpoints for stock scanning, analysis, and strategy configuration.
"""

import os
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from api_server.models.common import APIResponse
from stock_recommendation.models import (
    ScanRequest,
    ScanResult,
    StockRecommendation,
    StrategyType,
    StockPoolType,
)
from stock_recommendation.services.recommendation_service import RecommendationService
from stock_recommendation.strategies.strategy_config import (
    get_short_term_config,
    get_long_term_config,
    get_rating_thresholds,
    ShortTermConfig,
    LongTermConfig,
    RatingThresholds,
)
from common.database import DatabaseManager

logger = logging.getLogger(__name__)

recommendation_router = APIRouter()

# Database URL from environment
DATABASE_URL = os.environ.get(
    "DATABASE__URL",
    "postgresql://alpha_quant_trader_pro:alpha_quant_trader_pro@alpha-quant-db:5432/alpha_quant_trader_pro"
)


def get_db_session() -> Session:
    """Get database session dependency."""
    db_manager = DatabaseManager(DATABASE_URL)
    with db_manager.get_session() as session:
        yield session


def get_recommendation_service(session: Session) -> RecommendationService:
    """Create recommendation service instance."""
    return RecommendationService(session=session)


# ========== Scan Endpoints ==========

@recommendation_router.post("/scan", response_model=APIResponse[ScanResult])
async def scan_stocks(request: ScanRequest = Body(...)):
    """
    Scan stock pool for recommendations.

    Analyzes stocks based on specified strategy type and returns top recommendations.

    Args:
        request: Scan parameters including:
            - strategy_type: short | long | both
            - top_n: Number of stocks to return (1-100)
            - stock_pool: all | watchlist | custom
            - custom_codes: Custom stock codes (optional)
            - exclude_gem: Exclude GEM board stocks
            - exclude_star: Exclude STAR board stocks
            - min_score: Minimum score filter (0-100)

    Returns:
        ScanResult with recommendations
    """
    try:
        logger.info(
            f"Scanning stocks - strategy: {request.strategy_type}, "
            f"pool: {request.stock_pool}, top_n: {request.top_n}"
        )

        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            service = get_recommendation_service(session)
            result = service.scan_stocks(request)

            return APIResponse(
                data=result,
                message=f"Scan completed. Found {len(result.recommendations)} recommendations."
            )
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@recommendation_router.get("/analyze/{stock_code}", response_model=APIResponse)
async def analyze_stock(
    stock_code: str = Path(..., description="Stock code", example="600519"),
    strategy_type: str = Query("both", description="Strategy type: short | long | both"),
):
    """
    Analyze a single stock.

    Returns detailed analysis results for the specified stock using the selected strategy.

    Args:
        stock_code: 6-digit stock code
        strategy_type: Strategy to use for analysis (short/long/both)

    Returns:
        Detailed analysis with scores, signals, and recommendations
    """
    try:
        logger.info(f"Analyzing stock: {stock_code}, strategy: {strategy_type}")

        # Validate strategy type
        if strategy_type not in ["short", "long", "both"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy_type: {strategy_type}. Must be 'short', 'long', or 'both'"
            )

        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            service = get_recommendation_service(session)
            result = service.analyze_stock(stock_code, strategy_type)

            if result.get("error"):
                raise HTTPException(
                    status_code=400,
                    detail=result["error"]
                )

            return APIResponse(
                data=result,
                message=f"Analysis completed for {stock_code}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ========== Strategy Endpoints ==========

@recommendation_router.get("/strategies", response_model=APIResponse)
async def get_strategies():
    """
    Get available strategy list and their descriptions.

    Returns information about short-term and long-term strategies,
    including their scoring weights and thresholds.

    Returns:
        List of available strategies with configuration details
    """
    try:
        short_config = get_short_term_config()
        long_config = get_long_term_config()

        strategies = [
            {
                "name": "short",
                "display_name": "Short-term Strategy",
                "description": "Technical analysis based strategy for short-term trading",
                "scoring_weights": short_config.weights.to_dict(),
                "score_threshold": short_config.score_threshold,
                "min_buy_signals": short_config.min_buy_signals,
                "max_hold_days": short_config.max_hold_days,
                "indicators": ["RSI", "KDJ", "MACD", "Bollinger", "Volume", "Fund Flow"],
            },
            {
                "name": "long",
                "display_name": "Long-term Strategy",
                "description": "Combined fundamental and technical analysis for long-term investment",
                "scoring_weights": long_config.weights.to_dict(),
                "score_threshold": long_config.score_threshold,
                "min_hold_days": long_config.min_hold_days,
                "max_hold_days": long_config.max_hold_days,
                "indicators": ["Trend", "Fundamentals", "Valuation", "Momentum", "Volume Energy", "DMI", "Fund Flow"],
            },
        ]

        return APIResponse(
            data={
                "strategies": strategies,
                "rating_levels": {
                    "A+": "Strong Buy (>=85)",
                    "A": "Buy (70-84)",
                    "B+": "Actionable (60-69)",
                    "B": "Watch (50-59)",
                    "C": "Hold (40-49)",
                    "D": "Not Recommended (<40)",
                },
            },
            message="Strategy list retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")


# ========== Configuration Endpoints ==========

@recommendation_router.get("/config", response_model=APIResponse)
async def get_config():
    """
    Get current recommendation configuration.

    Returns all configuration parameters for short-term and long-term strategies.

    Returns:
        Complete configuration including weights, thresholds, and filter rules
    """
    try:
        short_config = get_short_term_config()
        long_config = get_long_term_config()
        rating_thresholds = get_rating_thresholds()

        config = {
            "short_term": {
                "weights": short_config.weights.to_dict(),
                "score_threshold": short_config.score_threshold,
                "min_buy_signals": short_config.min_buy_signals,
                "atr_stop_multiplier": short_config.atr_stop_multiplier,
                "atr_profit_multiplier": short_config.atr_profit_multiplier,
                "max_hold_days": short_config.max_hold_days,
                "filters": {
                    "exclude_gem": short_config.filters.exclude_gem,
                    "exclude_star": short_config.filters.exclude_star,
                    "exclude_bse": short_config.filters.exclude_bse,
                    "min_price": short_config.filters.min_price,
                    "min_volume": short_config.filters.min_volume,
                },
            },
            "long_term": {
                "weights": long_config.weights.to_dict(),
                "score_threshold": long_config.score_threshold,
                "min_roe": long_config.min_roe,
                "min_profit_growth": long_config.min_profit_growth,
                "atr_stop_multiplier": long_config.atr_stop_multiplier,
                "atr_profit_multiplier": long_config.atr_profit_multiplier,
                "min_hold_days": long_config.min_hold_days,
                "max_hold_days": long_config.max_hold_days,
            },
            "rating_thresholds": {
                "a_plus": rating_thresholds.a_plus,
                "a": rating_thresholds.a,
                "b_plus": rating_thresholds.b_plus,
                "b": rating_thresholds.b,
                "c": rating_thresholds.c,
            },
        }

        return APIResponse(
            data=config,
            message="Configuration retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@recommendation_router.put("/config", response_model=APIResponse)
async def update_config(
    short_term_weights: Optional[Dict[str, int]] = Body(None, description="Short-term weights"),
    long_term_weights: Optional[Dict[str, int]] = Body(None, description="Long-term weights"),
    score_threshold: Optional[Dict[str, int]] = Body(None, description="Score thresholds"),
):
    """
    Update recommendation configuration.

    Note: This endpoint currently returns the proposed configuration.
    Persistent configuration updates would require additional implementation.

    Args:
        short_term_weights: New weights for short-term strategy
        long_term_weights: New weights for long-term strategy
        score_threshold: New score thresholds

    Returns:
        Updated configuration preview
    """
    try:
        # Get current config
        short_config = get_short_term_config()
        long_config = get_long_term_config()
        rating_thresholds = get_rating_thresholds()

        # Build updated config (note: this doesn't persist changes)
        updated_config = {
            "message": "Configuration update received (not persisted in current implementation)",
            "requested_changes": {},
            "current_config": {
                "short_term_weights": short_config.weights.to_dict(),
                "long_term_weights": long_config.weights.to_dict(),
            },
        }

        if short_term_weights:
            updated_config["requested_changes"]["short_term_weights"] = short_term_weights

        if long_term_weights:
            updated_config["requested_changes"]["long_term_weights"] = long_term_weights

        if score_threshold:
            updated_config["requested_changes"]["score_threshold"] = score_threshold

        return APIResponse(
            data=updated_config,
            message="Configuration update request received"
        )
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


# ========== Batch Scan Endpoint ==========

@recommendation_router.post("/batch-scan", response_model=APIResponse)
async def batch_scan_stocks(
    strategies: list[StrategyType] = Body(..., description="Strategy types to run"),
    top_n_per_strategy: int = Body(5, ge=1, le=50, description="Top N per strategy"),
    stock_pool: StockPoolType = Body(StockPoolType.ALL, description="Stock pool type"),
    custom_codes: Optional[list[str]] = Body(None, description="Custom stock codes"),
    min_score: int = Body(60, ge=0, le=100, description="Minimum score filter"),
):
    """
    Batch scan with multiple strategies.

    Runs multiple strategy scans in parallel and aggregates results.

    Args:
        strategies: List of strategies to run
        top_n_per_strategy: Number of stocks per strategy
        stock_pool: Stock pool type
        custom_codes: Custom stock codes for custom pool
        min_score: Minimum score filter

    Returns:
        Combined results from all strategies
    """
    try:
        logger.info(f"Batch scan - strategies: {strategies}, top_n: {top_n_per_strategy}")

        db_manager = DatabaseManager(DATABASE_URL)
        with db_manager.get_session() as session:
            service = get_recommendation_service(session)

            results = {}
            for strategy in strategies:
                request = ScanRequest(
                    strategy_type=strategy,
                    top_n=top_n_per_strategy,
                    stock_pool=stock_pool,
                    custom_codes=custom_codes,
                    min_score=min_score,
                )
                result = service.scan_stocks(request)
                results[strategy.value] = result

            return APIResponse(
                data={
                    "batch_results": results,
                    "strategies_run": [s.value for s in strategies],
                },
                message=f"Batch scan completed for {len(strategies)} strategies"
            )
    except Exception as e:
        logger.error(f"Batch scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch scan failed: {str(e)}")
