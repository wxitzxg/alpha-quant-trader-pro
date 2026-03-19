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
    "financial_router"
]
