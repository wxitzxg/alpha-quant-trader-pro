"""
Stock Recommendation Strategies

This package contains strategy implementations:
- Technical analysis strategies
- Fundamental analysis strategies
- Combined strategies
"""

from stock_recommendation.strategies.strategy_config import (
    # Enums
    RatingLevel,
    # Data classes
    ShortTermWeights,
    LongTermWeights,
    FundamentalsWeights,
    IndicatorThresholds,
    FundamentalThresholds,
    FilterRules,
    ShortTermConfig,
    LongTermConfig,
    RatingThresholds,
    ScanConfig,
    # Default instances
    DEFAULT_SHORT_TERM_CONFIG,
    DEFAULT_LONG_TERM_CONFIG,
    DEFAULT_RATING_THRESHOLDS,
    DEFAULT_SCAN_CONFIG,
    # Functions
    get_short_term_config,
    get_long_term_config,
    get_rating_thresholds,
    get_scan_config,
    get_rating_from_score,
    calculate_normalized_long_term_score,
)

__all__ = [
    # Enums
    "RatingLevel",
    # Data classes
    "ShortTermWeights",
    "LongTermWeights",
    "FundamentalsWeights",
    "IndicatorThresholds",
    "FundamentalThresholds",
    "FilterRules",
    "ShortTermConfig",
    "LongTermConfig",
    "RatingThresholds",
    "ScanConfig",
    # Default instances
    "DEFAULT_SHORT_TERM_CONFIG",
    "DEFAULT_LONG_TERM_CONFIG",
    "DEFAULT_RATING_THRESHOLDS",
    "DEFAULT_SCAN_CONFIG",
    # Functions
    "get_short_term_config",
    "get_long_term_config",
    "get_rating_thresholds",
    "get_scan_config",
    "get_rating_from_score",
    "calculate_normalized_long_term_score",
]
