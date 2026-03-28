"""
Stock Recommendation API Routers

This package contains FastAPI routers:
- Recommendation endpoints
- Scan endpoints
- Configuration endpoints
"""

from .recommendation import recommendation_router

__all__ = ["recommendation_router"]
