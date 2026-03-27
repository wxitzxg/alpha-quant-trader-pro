"""
Stock Recommendation Services

This package contains business services:
- RecommendationService: Main recommendation orchestration
- FilterService: Stock filtering logic
- ScoreService: Scoring calculations
"""

from stock_recommendation.services.recommendation_service import RecommendationService

__all__ = ["RecommendationService"]
