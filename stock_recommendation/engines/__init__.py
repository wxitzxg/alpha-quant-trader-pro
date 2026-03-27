"""
Stock Recommendation Engines

This package contains recommendation engines:
- BaseSelector: Abstract base class for all selectors
- ShortTermSelector: Short-term trading recommendations
- LongTermSelector: Long-term investment recommendations
"""

from stock_recommendation.engines.base_selector import BaseSelector

__all__ = [
    "BaseSelector",
]
