"""
Test fixtures for stock_recommendation module tests.

Provides mock data and fixtures for testing selection engines.
"""

import sys
from pathlib import Path

# Add project root to path for pytest to find modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List


def generate_kline_data(
    num_days: int = 100,
    start_price: float = 10.0,
    trend: str = "up",
    volatility: float = 0.02
) -> pd.DataFrame:
    """
    Generate mock K-line data for testing.

    Args:
        num_days: Number of trading days
        start_price: Starting price
        trend: Price trend direction ('up', 'down', 'sideways')
        volatility: Daily volatility percentage

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)  # Reproducible results

    dates = pd.date_range(
        start=datetime.now() - timedelta(days=num_days),
        periods=num_days,
        freq='D'
    )

    # Generate price series based on trend
    if trend == "up":
        daily_return = 0.002  # 0.2% daily increase
    elif trend == "down":
        daily_return = -0.002  # 0.2% daily decrease
    else:
        daily_return = 0

    # Generate close prices
    noise = np.random.normal(0, volatility, num_days)
    returns = daily_return + noise
    prices = start_price * np.exp(np.cumsum(returns))

    # Generate OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC
        high_mult = 1 + abs(np.random.normal(0.01, 0.005))
        low_mult = 1 - abs(np.random.normal(0.01, 0.005))
        open_mult = 1 + np.random.normal(0, 0.005)

        high = close * high_mult
        low = close * low_mult
        open_price = close * open_mult

        # Ensure high >= max(open, close) and low <= min(open, close)
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        # Generate volume with some randomness
        base_volume = 10000000  # 10M shares
        volume = base_volume * (1 + np.random.uniform(-0.3, 0.5))

        data.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': int(volume),
            'date': date
        })

    df = pd.DataFrame(data)
    return df


def generate_kline_with_specific_conditions(
    rsi_oversold: bool = False,
    rsi_overbought: bool = False,
    kdj_golden_cross: bool = False,
    kdj_death_cross: bool = False,
    macd_golden_cross: bool = False,
    macd_death_cross: bool = False,
    near_bb_lower: bool = False,
    near_bb_upper: bool = False,
    volume_surge: bool = False,
    volume_shrink: bool = False
) -> pd.DataFrame:
    """
    Generate K-line data with specific technical conditions.

    Returns:
        DataFrame with OHLCV data configured to match specified conditions
    """
    np.random.seed(123)

    num_days = 100
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=num_days),
        periods=num_days,
        freq='D'
    )

    # Base price series
    if rsi_oversold:
        # Create downward trend then small recovery (RSI will be low)
        prices = np.concatenate([
            np.linspace(15, 8, 70),  # Sharp decline
            np.linspace(8, 9, 30)    # Small recovery
        ])
    elif rsi_overbought:
        # Create strong upward trend (RSI will be high)
        prices = np.concatenate([
            np.linspace(10, 20, 70),  # Strong rise
            np.linspace(20, 21, 30)   # Continued
        ])
    else:
        prices = np.linspace(10, 12, num_days)

    # Adjust for Bollinger conditions
    if near_bb_lower:
        # Price near lower band - sharp recent decline
        prices = np.concatenate([
            np.linspace(12, 10, 50),
            np.linspace(10, 8, 50)  # Recent decline
        ])
    elif near_bb_upper:
        # Price near upper band - strong recent rise
        prices = np.concatenate([
            np.linspace(10, 12, 50),
            np.linspace(12, 15, 50)  # Recent rise
        ])

    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        high_mult = 1.02
        low_mult = 0.98
        open_mult = 1.0

        high = close * high_mult
        low = close * low_mult
        open_price = prices[max(0, i-1)] if i > 0 else close

        high = max(high, open_price, close)
        low = min(low, open_price, close)

        # Volume adjustments
        if volume_surge and i >= num_days - 2:
            volume = 50000000  # High volume
        elif volume_shrink and i >= num_days - 2:
            volume = 2000000   # Low volume
        else:
            volume = 10000000

        data.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': int(volume),
            'date': date
        })

    df = pd.DataFrame(data)
    return df


@pytest.fixture
def sample_kline_data() -> pd.DataFrame:
    """Provide sample K-line data for general testing."""
    return generate_kline_data(num_days=100)


@pytest.fixture
def bullish_kline_data() -> pd.DataFrame:
    """Provide bullish trend K-line data."""
    return generate_kline_data(num_days=100, trend="up")


@pytest.fixture
def bearish_kline_data() -> pd.DataFrame:
    """Provide bearish trend K-line data."""
    return generate_kline_data(num_days=100, trend="down")


@pytest.fixture
def sideways_kline_data() -> pd.DataFrame:
    """Provide sideways K-line data."""
    return generate_kline_data(num_days=100, trend="sideways")


@pytest.fixture
def rsi_oversold_kline() -> pd.DataFrame:
    """Provide K-line data with RSI oversold condition."""
    return generate_kline_with_specific_conditions(rsi_oversold=True)


@pytest.fixture
def rsi_overbought_kline() -> pd.DataFrame:
    """Provide K-line data with RSI overbought condition."""
    return generate_kline_with_specific_conditions(rsi_overbought=True)


@pytest.fixture
def volume_surge_kline() -> pd.DataFrame:
    """Provide K-line data with volume surge."""
    return generate_kline_with_specific_conditions(volume_surge=True)


@pytest.fixture
def sample_fund_flow() -> Dict[str, Any]:
    """Provide sample fund flow data."""
    return {
        "main_net_inflow": 8000000,  # 800万流入
        "mainNetInflow": 8000000,
        "large_net_inflow": 3000000,
        "small_net_inflow": 2000000
    }


@pytest.fixture
def strong_inflow_fund_flow() -> Dict[str, Any]:
    """Provide fund flow data with strong inflow."""
    return {
        "main_net_inflow": 10000000,  # 1000万流入
        "mainNetInflow": 10000000,
        "large_net_inflow": 6000000
    }


@pytest.fixture
def strong_outflow_fund_flow() -> Dict[str, Any]:
    """Provide fund flow data with strong outflow."""
    return {
        "main_net_inflow": -10000000,  # 1000万流出
        "mainNetInflow": -10000000,
        "large_net_inflow": -6000000
    }


@pytest.fixture
def sample_fundamentals() -> Dict[str, Any]:
    """Provide sample fundamental data."""
    return {
        "roe": 0.18,  # 18% ROE
        "net_profit_growth": 0.25,  # 25% profit growth
        "dividend_yield": 0.03,  # 3% dividend yield
        "pe_ratio": 15.0,
        "pb_ratio": 2.0
    }


@pytest.fixture
def strong_fundamentals() -> Dict[str, Any]:
    """Provide strong fundamental data."""
    return {
        "roe": 0.25,  # 25% ROE
        "net_profit_growth": 0.35,  # 35% profit growth
        "dividend_yield": 0.05,  # 5% dividend yield
        "pe_ratio": 12.0,
        "pb_ratio": 1.5
    }


@pytest.fixture
def weak_fundamentals() -> Dict[str, Any]:
    """Provide weak fundamental data."""
    return {
        "roe": 0.05,  # 5% ROE
        "net_profit_growth": -0.10,  # -10% profit growth
        "dividend_yield": 0.005,  # 0.5% dividend yield
        "pe_ratio": 60.0,
        "pb_ratio": 8.0
    }


@pytest.fixture
def sample_stock_codes() -> List[str]:
    """Provide sample stock codes for various exchanges."""
    return [
        "600000",  # Shanghai main board
        "000001",  # Shenzhen main board
        "300001",  # GEM (创业板)
        "688001",  # STAR (科创板)
        "000002",  # Shenzhen main board
        "601318",  # Shanghai main board
    ]


@pytest.fixture
def gem_stock_codes() -> List[str]:
    """Provide GEM board stock codes."""
    return ["300001", "300002", "300750"]


@pytest.fixture
def star_stock_codes() -> List[str]:
    """Provide STAR board stock codes."""
    return ["688001", "688002", "688981"]


@pytest.fixture
def main_board_codes() -> List[str]:
    """Provide main board stock codes."""
    return ["600000", "000001", "601318", "000002"]


# Filter rule fixtures
@pytest.fixture
def default_filter_rules():
    """Provide default filter rules."""
    from stock_recommendation.strategies.strategy_config import FilterRules
    return FilterRules()


@pytest.fixture
def relaxed_filter_rules():
    """Provide relaxed filter rules (no exclusions)."""
    from stock_recommendation.strategies.strategy_config import FilterRules
    return FilterRules(
        exclude_gem=False,
        exclude_star=False,
        exclude_bse=False,
        min_price=1.0,
        min_volume=100000
    )


# Config fixtures
@pytest.fixture
def default_short_term_config():
    """Provide default short-term strategy config."""
    from stock_recommendation.strategies.strategy_config import DEFAULT_SHORT_TERM_CONFIG
    return DEFAULT_SHORT_TERM_CONFIG


@pytest.fixture
def default_long_term_config():
    """Provide default long-term strategy config."""
    from stock_recommendation.strategies.strategy_config import DEFAULT_LONG_TERM_CONFIG
    return DEFAULT_LONG_TERM_CONFIG


@pytest.fixture
def default_rating_thresholds():
    """Provide default rating thresholds."""
    from stock_recommendation.strategies.strategy_config import DEFAULT_RATING_THRESHOLDS
    return DEFAULT_RATING_THRESHOLDS
