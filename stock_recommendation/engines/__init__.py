"""
Stock Recommendation Engines

This package contains recommendation engines:
- BaseSelector: Abstract base class for all selectors
- ShortTermSelector: Short-term trading recommendations
- LongTermSelector: Long-term investment recommendations
"""

from stock_recommendation.engines.base_selector import BaseSelector
from stock_recommendation.engines.short_term_selector import ShortTermSelector
from stock_recommendation.engines.long_term_selector import LongTermSelector

__all__ = [
    "BaseSelector",
    "ShortTermSelector",
    "LongTermSelector",
]
