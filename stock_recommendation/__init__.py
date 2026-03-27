"""
Stock Recommendation Module

This module provides stock recommendation functionality with:
- Short-term trading strategies
- Long-term investment strategies
- Multi-factor filtering and scoring
"""

from .models import (
    StrategyType,
    StockPoolType,
    Rating,
    ScanRequest,
    ScanResult,
    StockRecommendation,
    AnalysisDetail,
    DimensionScore,
    RecommendationHistory,
    BatchScanRequest,
)

__version__ = "0.1.0"

__all__ = [
    "StrategyType",
    "StockPoolType",
    "Rating",
    "ScanRequest",
    "ScanResult",
    "StockRecommendation",
    "AnalysisDetail",
    "DimensionScore",
    "RecommendationHistory",
    "BatchScanRequest",
]
