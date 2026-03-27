"""
Strategy Configuration for Stock Recommendation

Defines scoring weights, thresholds, and filter rules for:
- Short-term strategies (technical analysis based)
- Long-term strategies (fundamental + technical combined)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RatingLevel(str, Enum):
    """Rating levels for stock recommendations"""
    A_PLUS = "A+"      # Strong recommendation (>=85)
    A = "A"            # Recommended (70-84)
    B_PLUS = "B+"      # Actionable (60-69)
    B = "B"            # Watch (50-59)
    C = "C"            # Hold (40-49)
    D = "D"            # Not recommended (<40)


@dataclass
class ShortTermWeights:
    """
    Short-term strategy scoring weights (total: 100 points)

    Based on technical indicators for short-term trading signals.
    """
    rsi: int = 20          # RSI signal weight
    kdj: int = 20          # KDJ signal weight
    macd: int = 15         # MACD signal weight
    bollinger: int = 15    # Bollinger band signal weight
    volume_price: int = 15 # Volume-price anomaly weight
    fund_flow: int = 15    # Fund flow weight

    def to_dict(self) -> Dict[str, int]:
        return {
            "rsi": self.rsi,
            "kdj": self.kdj,
            "macd": self.macd,
            "bollinger": self.bollinger,
            "volume_price": self.volume_price,
            "fund_flow": self.fund_flow,
        }

    @property
    def total(self) -> int:
        """Total weight points"""
        return self.rsi + self.kdj + self.macd + self.bollinger + self.volume_price + self.fund_flow


@dataclass
class LongTermWeights:
    """
    Long-term strategy scoring weights (raw total: 130 points, normalized to 100)

    Combines trend, fundamentals, valuation, and momentum analysis.
    """
    trend: int = 30            # Trend score weight
    fundamentals: int = 30     # Fundamentals score weight (ROE + profit growth + dividend yield)
    valuation: int = 15        # Valuation score weight
    momentum: int = 15         # Momentum score weight
    volume_energy: int = 15    # Volume energy score weight
    dmi: int = 15              # DMI indicator weight
    fund_flow: int = 10        # Fund flow score weight

    def to_dict(self) -> Dict[str, int]:
        return {
            "trend": self.trend,
            "fundamentals": self.fundamentals,
            "valuation": self.valuation,
            "momentum": self.momentum,
            "volume_energy": self.volume_energy,
            "dmi": self.dmi,
            "fund_flow": self.fund_flow,
        }

    @property
    def total(self) -> int:
        """Raw total weight points"""
        return (
            self.trend + self.fundamentals + self.valuation +
            self.momentum + self.volume_energy + self.dmi + self.fund_flow
        )

    @property
    def normalization_factor(self) -> float:
        """Factor to normalize score to 100 points"""
        return 100.0 / self.total


@dataclass
class FundamentalsWeights:
    """
    Sub-weights for fundamental analysis (within long-term fundamentals score)

    Total should match the fundamentals weight in LongTermWeights.
    """
    roe: int = 10             # ROE weight
    profit_growth: int = 10   # Profit growth weight
    dividend_yield: int = 10  # Dividend yield weight

    def to_dict(self) -> Dict[str, int]:
        return {
            "roe": self.roe,
            "profit_growth": self.profit_growth,
            "dividend_yield": self.dividend_yield,
        }

    @property
    def total(self) -> int:
        return self.roe + self.profit_growth + self.dividend_yield


@dataclass
class IndicatorThresholds:
    """Threshold values for technical indicators"""
    # RSI thresholds
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    rsi_period: int = 14

    # KDJ thresholds
    kdj_oversold: int = 20
    kdj_overbought: int = 80
    kdj_golden_cross_threshold: float = 5.0  # K-D difference for golden cross
    kdj_fast_k: int = 9
    kdj_slow_k: int = 3
    kdj_slow_d: int = 3

    # MACD thresholds
    macd_golden_cross_above_zero: bool = True  # Golden cross above zero line is stronger
    macd_histogram_threshold: float = 0.0

    # Bollinger band thresholds
    bollinger_period: int = 20
    bollinger_std_dev: float = 2.0
    bollinger_breakout_threshold: float = 0.02  # 2% above upper band

    # MA thresholds
    ma_short_period: int = 5
    ma_medium_period: int = 10
    ma_long_period: int = 20
    ma_convergence_threshold: float = 0.01  # 1% difference for MA convergence

    # Volume thresholds
    volume_surge_ratio: float = 2.0  # Volume surge compared to average
    volume_avg_period: int = 5


@dataclass
class FundamentalThresholds:
    """Threshold values for fundamental analysis"""
    # ROE thresholds (%)
    roe_excellent: float = 15.0
    roe_good: float = 10.0
    roe_acceptable: float = 5.0

    # Profit growth thresholds (%)
    profit_growth_excellent: float = 30.0
    profit_growth_good: float = 15.0
    profit_growth_acceptable: float = 0.0

    # Dividend yield thresholds (%)
    dividend_yield_excellent: float = 4.0
    dividend_yield_good: float = 2.0
    dividend_yield_acceptable: float = 1.0

    # PE ratio thresholds
    pe_low: float = 15.0
    pe_medium: float = 30.0
    pe_high: float = 50.0

    # PB ratio thresholds
    pb_low: float = 1.0
    pb_medium: float = 3.0
    pb_high: float = 5.0


@dataclass
class FilterRules:
    """Filter rules for stock selection"""
    # Exchange filters
    exclude_gem: bool = True      # Exclude GEM board (300xxx)
    exclude_star: bool = True     # Exclude STAR board (688xxx)
    exclude_bse: bool = True      # Exclude Beijing Stock Exchange (8xxxxx, 4xxxxx)
    exclude_st: bool = True       # Exclude ST and *ST stocks
    exclude_suspended: bool = True  # Exclude suspended stocks

    # Price filters
    min_price: float = 2.0        # Minimum stock price (CNY)
    max_price: Optional[float] = None  # Maximum stock price (optional)

    # Volume filters
    min_volume: int = 1000000     # Minimum daily volume (shares)
    min_turnover: float = 10000000  # Minimum daily turnover (CNY)
    min_turnover_rate: float = 1.0  # Minimum turnover rate (%)

    # Market cap filters
    min_market_cap: Optional[float] = None  # Minimum market cap (CNY)
    max_market_cap: Optional[float] = None  # Maximum market cap (CNY)

    # Listing time filter
    min_listing_days: int = 60    # Minimum days since listing

    # Additional filters
    require_positive_earnings: bool = True  # Require positive earnings
    require_profit_growth: bool = False     # Require positive profit growth


@dataclass
class ShortTermConfig:
    """Short-term strategy configuration"""
    weights: ShortTermWeights = field(default_factory=ShortTermWeights)
    thresholds: IndicatorThresholds = field(default_factory=IndicatorThresholds)
    filters: FilterRules = field(default_factory=FilterRules)

    # Score thresholds
    score_threshold: int = 60     # Minimum score for recommendation
    min_buy_signals: int = 2      # Minimum number of buy signals required

    # Risk management
    atr_stop_multiplier: float = 2.0    # ATR-based stop loss multiplier
    atr_profit_multiplier: float = 3.0  # ATR-based take profit multiplier
    max_hold_days: int = 10             # Maximum holding days


@dataclass
class LongTermConfig:
    """Long-term strategy configuration"""
    weights: LongTermWeights = field(default_factory=LongTermWeights)
    fundamentals_weights: FundamentalsWeights = field(default_factory=FundamentalsWeights)
    thresholds: FundamentalThresholds = field(default_factory=FundamentalThresholds)
    filters: FilterRules = field(default_factory=FilterRules)

    # Score thresholds
    score_threshold: int = 65     # Minimum score for recommendation

    # Fundamental requirements
    min_roe: float = 10.0         # Minimum ROE (%)
    min_profit_growth: float = 10.0  # Minimum profit growth (%)

    # Risk management
    atr_stop_multiplier: float = 2.5
    atr_profit_multiplier: float = 4.0
    min_hold_days: int = 30       # Minimum holding days
    max_hold_days: int = 180      # Maximum holding days


@dataclass
class RatingThresholds:
    """Score thresholds for rating levels"""
    a_plus: int = 85    # Strong recommendation
    a: int = 70         # Recommended
    b_plus: int = 60    # Actionable
    b: int = 50         # Watch
    c: int = 40         # Hold

    def get_rating(self, score: float) -> RatingLevel:
        """
        Get rating level based on score.

        Args:
            score: The calculated score (0-100)

        Returns:
            RatingLevel enum value
        """
        if score >= self.a_plus:
            return RatingLevel.A_PLUS
        elif score >= self.a:
            return RatingLevel.A
        elif score >= self.b_plus:
            return RatingLevel.B_PLUS
        elif score >= self.b:
            return RatingLevel.B
        elif score >= self.c:
            return RatingLevel.C
        else:
            return RatingLevel.D


@dataclass
class ScanConfig:
    """Configuration for stock scanning"""
    default_top_n: int = 10       # Default number of stocks to return
    max_workers: int = 10         # Parallel analysis threads
    cache_ttl: int = 300          # Cache TTL in seconds (5 minutes)
    batch_size: int = 50          # Batch size for processing
    timeout: int = 30             # Timeout for individual stock analysis (seconds)


# ========== Default Configuration Instances ==========

DEFAULT_SHORT_TERM_CONFIG = ShortTermConfig()
DEFAULT_LONG_TERM_CONFIG = LongTermConfig()
DEFAULT_RATING_THRESHOLDS = RatingThresholds()
DEFAULT_SCAN_CONFIG = ScanConfig()


# ========== Configuration Access Functions ==========

def get_short_term_config() -> ShortTermConfig:
    """
    Get short-term strategy configuration.

    Returns:
        ShortTermConfig instance with default values
    """
    return DEFAULT_SHORT_TERM_CONFIG


def get_long_term_config() -> LongTermConfig:
    """
    Get long-term strategy configuration.

    Returns:
        LongTermConfig instance with default values
    """
    return DEFAULT_LONG_TERM_CONFIG


def get_rating_thresholds() -> RatingThresholds:
    """
    Get rating thresholds configuration.

    Returns:
        RatingThresholds instance with default values
    """
    return DEFAULT_RATING_THRESHOLDS


def get_scan_config() -> ScanConfig:
    """
    Get scan configuration.

    Returns:
        ScanConfig instance with default values
    """
    return DEFAULT_SCAN_CONFIG


def get_rating_from_score(score: float) -> RatingLevel:
    """
    Convert numerical score to rating level.

    Args:
        score: Calculated score (0-100)

    Returns:
        RatingLevel enum value
    """
    return DEFAULT_RATING_THRESHOLDS.get_rating(score)


def calculate_normalized_long_term_score(raw_score: float) -> float:
    """
    Normalize long-term raw score to 100-point scale.

    Args:
        raw_score: Raw score based on LongTermWeights

    Returns:
        Normalized score (0-100)
    """
    return raw_score * DEFAULT_LONG_TERM_CONFIG.weights.normalization_factor
