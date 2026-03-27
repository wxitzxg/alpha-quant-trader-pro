"""
Unit tests for ShortTermSelector.

Tests scoring logic for:
- RSI indicator
- KDJ indicator
- MACD indicator
- Bollinger bands
- Volume-price anomaly
- Fund flow
- Comprehensive scoring and signal generation
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from stock_recommendation.engines.short_term_selector import ShortTermSelector
from stock_recommendation.strategies.strategy_config import (
    ShortTermConfig,
    ShortTermWeights,
    RatingThresholds,
    DEFAULT_SHORT_TERM_CONFIG,
    DEFAULT_RATING_THRESHOLDS,
)


class TestShortTermSelectorInit:
    """Test ShortTermSelector initialization."""

    def test_default_initialization(self):
        """Test default configuration initialization."""
        selector = ShortTermSelector()
        assert selector.config is not None
        assert selector.weights is not None
        assert selector.thresholds is not None

    def test_custom_config_initialization(self):
        """Test custom configuration initialization."""
        custom_config = ShortTermConfig(
            score_threshold=70,
            min_buy_signals=3
        )
        selector = ShortTermSelector(config=custom_config)
        assert selector.config.score_threshold == 70
        assert selector.config.min_buy_signals == 3

    def test_custom_rating_thresholds(self):
        """Test custom rating thresholds."""
        custom_thresholds = RatingThresholds(a_plus=90, a=80)
        selector = ShortTermSelector(rating_thresholds=custom_thresholds)
        assert selector.rating_thresholds.a_plus == 90
        assert selector.rating_thresholds.a == 80


class TestStockCodeValidation:
    """Test stock code validation and normalization."""

    def test_validate_valid_code(self):
        """Test validation of valid stock codes."""
        selector = ShortTermSelector()
        assert selector._validate_stock_code("000001") is True
        assert selector._validate_stock_code("600000") is True
        assert selector._validate_stock_code("688001") is True

    def test_validate_invalid_code(self):
        """Test validation of invalid stock codes."""
        selector = ShortTermSelector()
        assert selector._validate_stock_code("") is False
        assert selector._validate_stock_code("12345") is False  # 5 digits
        assert selector._validate_stock_code("1234567") is False  # 7 digits
        assert selector._validate_stock_code("abcdef") is False  # Letters
        assert selector._validate_stock_code(None) is False

    def test_normalize_code_with_prefix(self):
        """Test code normalization with prefixes."""
        selector = ShortTermSelector()
        assert selector._normalize_code("sh600000") == "600000"
        assert selector._normalize_code("sz000001") == "000001"
        assert selector._normalize_code("SH600000") == "600000"
        assert selector._normalize_code("bj430001") == "430001"

    def test_normalize_code_padding(self):
        """Test code padding with zeros."""
        selector = ShortTermSelector()
        assert selector._normalize_code("1") == "000001"
        assert selector._normalize_code("123") == "000123"


class TestRSIScoring:
    """Test RSI scoring logic."""

    def test_rsi_oversold_score(self):
        """Test RSI oversold condition scoring (RSI < 30)."""
        selector = ShortTermSelector()

        # Create mock latest data with RSI < 30
        latest = pd.Series({
            'rsi': 25.0
        })

        result = selector._score_rsi(latest)

        assert result['score'] == 20
        assert result['signal'] == 'oversold'
        assert result['is_buy_signal'] is True
        assert '超卖' in result['description']

    def test_rsi_near_oversold_score(self):
        """Test RSI near oversold condition (30 <= RSI < 40)."""
        selector = ShortTermSelector()

        latest = pd.Series({'rsi': 35.0})
        result = selector._score_rsi(latest)

        assert result['score'] == 12
        assert result['signal'] == 'near_oversold'
        assert result['is_buy_signal'] is True

    def test_rsi_neutral_score(self):
        """Test RSI neutral condition (40 <= RSI <= 60)."""
        selector = ShortTermSelector()

        latest = pd.Series({'rsi': 50.0})
        result = selector._score_rsi(latest)

        assert result['score'] == 5
        assert result['signal'] == 'neutral'
        assert result['is_buy_signal'] is False

    def test_rsi_near_overbought_score(self):
        """Test RSI near overbought condition (60 < RSI <= 70)."""
        selector = ShortTermSelector()

        latest = pd.Series({'rsi': 65.0})
        result = selector._score_rsi(latest)

        assert result['score'] == 3
        assert result['signal'] == 'near_overbought'
        assert result['is_buy_signal'] is False

    def test_rsi_overbought_score(self):
        """Test RSI overbought condition (RSI > 70)."""
        selector = ShortTermSelector()

        latest = pd.Series({'rsi': 75.0})
        result = selector._score_rsi(latest)

        assert result['score'] == 0
        assert result['signal'] == 'overbought'
        assert result['is_buy_signal'] is False
        assert '超买' in result['description']


class TestKDJScoring:
    """Test KDJ scoring logic."""

    def test_kdj_golden_cross_oversold(self):
        """Test KDJ golden cross with low J value."""
        selector = ShortTermSelector()

        # Create mock DataFrame with golden cross and low J
        df = pd.DataFrame({
            'high': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19] * 10,
            'low': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18] * 10,
            'close': [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5] * 10
        })

        # Mock KDJ calculation to return golden cross with low J
        latest = pd.Series({
            'stoch_k': 35.0,
            'stoch_d': 30.0
        })
        prev = pd.Series({
            'stoch_k': 28.0,
            'stoch_d': 32.0
        })

        # Patch _calculate_kdj to return controlled values
        with patch.object(selector, '_calculate_kdj', return_value={
            'k': 35.0, 'd': 30.0, 'j': 45.0,
            'prev_k': 28.0, 'prev_d': 32.0
        }):
            result = selector._score_kdj(df, latest, prev)

        assert result['score'] == 20
        assert 'golden_cross' in result['signal']
        assert result['is_buy_signal'] is True

    def test_kdj_oversold_j_value(self):
        """Test KDJ with J value oversold."""
        selector = ShortTermSelector()

        df = pd.DataFrame({'high': [10]*20, 'low': [9]*20, 'close': [9.5]*20})
        latest = pd.Series({'stoch_k': 25.0, 'stoch_d': 30.0})
        prev = pd.Series({'stoch_k': 27.0, 'stoch_d': 29.0})

        with patch.object(selector, '_calculate_kdj', return_value={
            'k': 25.0, 'd': 30.0, 'j': 15.0,  # J < 20
            'prev_k': 27.0, 'prev_d': 29.0
        }):
            result = selector._score_kdj(df, latest, prev)

        assert result['score'] == 15
        assert result['signal'] == 'oversold'
        assert result['is_buy_signal'] is True

    def test_kdj_death_cross_overbought(self):
        """Test KDJ death cross with high J value."""
        selector = ShortTermSelector()

        df = pd.DataFrame({'high': [10]*20, 'low': [9]*20, 'close': [9.5]*20})
        latest = pd.Series({'stoch_k': 75.0, 'stoch_d': 80.0})
        prev = pd.Series({'stoch_k': 82.0, 'stoch_d': 78.0})

        # J value = 3*K - 2*D = 3*75 - 2*80 = 225 - 160 = 65
        # For death cross with J > 70, we need higher J
        with patch.object(selector, '_calculate_kdj', return_value={
            'k': 75.0, 'd': 80.0, 'j': 75.0,  # J > 70 now
            'prev_k': 82.0, 'prev_d': 78.0
        }):
            result = selector._score_kdj(df, latest, prev)

        # Death cross + J > 70 should give -10
        assert result['score'] == -10
        assert 'death_cross' in result['signal']
        assert result['is_buy_signal'] is False


class TestMACDScoring:
    """Test MACD scoring logic."""

    def test_macd_golden_cross(self):
        """Test MACD golden cross scoring."""
        selector = ShortTermSelector()

        # Previous: MACD below signal, Current: MACD above signal
        latest = pd.Series({
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_histogram': 0.2
        })
        prev = pd.Series({
            'macd': 0.2,
            'macd_signal': 0.3,
            'macd_histogram': -0.1
        })

        result = selector._score_macd(latest, prev)

        assert result['score'] == 15
        assert result['signal'] == 'golden_cross'
        assert result['is_buy_signal'] is True

    def test_macd_turning_red(self):
        """Test MACD histogram turning red (positive)."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'macd': 0.1,
            'macd_signal': 0.2,
            'macd_histogram': 0.05  # Just turned positive
        })
        prev = pd.Series({
            'macd': 0.05,
            'macd_signal': 0.1,
            'macd_histogram': -0.02  # Was negative
        })

        result = selector._score_macd(latest, prev)

        assert result['score'] == 10
        assert result['signal'] == 'turning_red'
        assert result['is_buy_signal'] is True

    def test_macd_bullish(self):
        """Test MACD bullish histogram."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_histogram': 0.2  # Positive
        })
        prev = pd.Series({
            'macd': 0.4,
            'macd_signal': 0.25,
            'macd_histogram': 0.15  # Also positive
        })

        result = selector._score_macd(latest, prev)

        assert result['score'] == 8
        assert result['signal'] == 'bullish'
        assert result['is_buy_signal'] is True

    def test_macd_death_cross(self):
        """Test MACD death cross scoring."""
        selector = ShortTermSelector()

        # Previous: MACD above signal, Current: MACD below signal
        latest = pd.Series({
            'macd': 0.1,
            'macd_signal': 0.3,
            'macd_histogram': -0.2
        })
        prev = pd.Series({
            'macd': 0.4,
            'macd_signal': 0.3,
            'macd_histogram': 0.1
        })

        result = selector._score_macd(latest, prev)

        assert result['score'] == -10
        assert result['signal'] == 'death_cross'
        assert result['is_buy_signal'] is False


class TestBollingerScoring:
    """Test Bollinger band scoring logic."""

    def test_lower_band_bounce(self):
        """Test price bounce from lower band."""
        selector = ShortTermSelector()

        close = 10.5
        bb_lower = 10.0
        prev_close = 9.8  # Was at or below lower band
        prev_bb_lower = 9.9

        latest = pd.Series({
            'close': close,
            'bb_upper': 12.0,
            'bb_middle': 11.0,
            'bb_lower': bb_lower
        })
        prev = pd.Series({
            'close': prev_close,
            'bb_lower': prev_bb_lower
        })

        result = selector._score_bollinger(latest, prev)

        assert result['score'] == 15
        assert result['signal'] == 'lower_bounce'
        assert result['is_buy_signal'] is True

    def test_near_lower_band(self):
        """Test price near lower band."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 10.05,  # Very close to lower band
            'bb_upper': 12.0,
            'bb_middle': 11.0,
            'bb_lower': 10.0
        })
        prev = pd.Series({
            'close': 10.5,
            'bb_lower': 10.0
        })

        result = selector._score_bollinger(latest, prev)

        assert result['score'] == 12
        assert result['signal'] == 'near_lower'
        assert result['is_buy_signal'] is True

    def test_middle_support(self):
        """Test price above middle band with proper positioning."""
        selector = ShortTermSelector()

        # Set up price above middle band but not near upper
        # BB position = (close - bb_lower) / (bb_upper - bb_lower)
        # For middle_support: close >= bb_middle AND bb_position <= 0.6
        bb_upper = 12.0
        bb_middle = 11.0
        bb_lower = 10.0
        close = 11.3  # Above middle

        # bb_position = (11.3 - 10) / (12 - 10) = 1.3 / 2 = 0.65
        # This is > 0.6, so it doesn't trigger middle_support
        # Let's adjust to get position <= 0.6:
        # (close - 10) / 2 <= 0.6 => close - 10 <= 1.2 => close <= 11.2
        close = 11.1  # Now position = 1.1 / 2 = 0.55

        latest = pd.Series({
            'close': close,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower
        })
        prev = pd.Series({
            'close': 10.5,
            'bb_lower': bb_lower
        })

        result = selector._score_bollinger(latest, prev)

        assert result['score'] == 10
        assert result['signal'] == 'middle_support'
        assert result['is_buy_signal'] is True

    def test_near_upper_band(self):
        """Test price near upper band (risk signal)."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 11.95,  # Near upper band
            'bb_upper': 12.0,
            'bb_middle': 11.0,
            'bb_lower': 10.0
        })
        prev = pd.Series({
            'close': 11.5,
            'bb_lower': 10.0
        })

        result = selector._score_bollinger(latest, prev)

        assert result['score'] == -5
        assert result['signal'] == 'near_upper'


class TestVolumePriceScoring:
    """Test volume-price anomaly scoring logic."""

    def test_volume_surge_up(self):
        """Test volume surge with price increase."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 11.0,
            'volume': 30000000,  # High volume
            'volume_ma5': 10000000
        })
        prev = pd.Series({
            'close': 10.0,
            'volume': 12000000
        })

        result = selector._score_volume_price(latest, prev)

        # Volume ratio = 3.0 (> 2.0), Price change = 10% (> 3%)
        assert result['score'] == 15
        assert result['signal'] == 'volume_surge_up'
        assert result['is_buy_signal'] is True

    def test_moderate_volume_up(self):
        """Test moderate volume increase with price rise."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 10.5,
            'volume': 18000000,  # 1.8x average
            'volume_ma5': 10000000
        })
        prev = pd.Series({
            'close': 10.0,
            'volume': 11000000
        })

        result = selector._score_volume_price(latest, prev)

        # Volume ratio = 1.8 (> 1.5), Price change = 5% (> 2%)
        assert result['score'] == 12
        assert result['signal'] == 'moderate_volume_up'
        assert result['is_buy_signal'] is True

    def test_volume_surge_down(self):
        """Test volume surge with price decrease."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 9.0,
            'volume': 25000000,
            'volume_ma5': 10000000
        })
        prev = pd.Series({
            'close': 10.0,
            'volume': 11000000
        })

        result = selector._score_volume_price(latest, prev)

        # Volume ratio = 2.5 (> 2.0), Price change = -10% (< -3%)
        assert result['score'] == -10
        assert result['signal'] == 'volume_surge_down'
        assert result['is_buy_signal'] is False

    def test_shrink_volume_up(self):
        """Test shrinking volume with price increase."""
        selector = ShortTermSelector()

        latest = pd.Series({
            'close': 10.5,
            'volume': 7000000,  # Less than average
            'volume_ma5': 10000000
        })
        prev = pd.Series({
            'close': 10.0,
            'volume': 11000000
        })

        result = selector._score_volume_price(latest, prev)

        # Volume ratio = 0.7 (< 0.8), Price change = +5%
        assert result['score'] == 5
        assert result['signal'] == 'shrink_volume_up'


class TestFundFlowScoring:
    """Test fund flow scoring logic."""

    def test_strong_inflow(self):
        """Test strong main net inflow."""
        selector = ShortTermSelector()

        result = selector._score_fund_flow(6000000)  # 600万流入

        assert result['score'] == 15
        assert result['signal'] == 'strong_inflow'
        assert result['is_buy_signal'] is True

    def test_moderate_inflow(self):
        """Test moderate main net inflow."""
        selector = ShortTermSelector()

        result = selector._score_fund_flow(3000000)  # 300万流入

        assert result['score'] == 12
        assert result['signal'] == 'moderate_inflow'
        assert result['is_buy_signal'] is True

    def test_slight_inflow(self):
        """Test slight main net inflow."""
        selector = ShortTermSelector()

        result = selector._score_fund_flow(500000)  # 50万流入

        assert result['score'] == 8
        assert result['signal'] == 'slight_inflow'
        assert result['is_buy_signal'] is True

    def test_slight_outflow(self):
        """Test slight main net outflow."""
        selector = ShortTermSelector()

        result = selector._score_fund_flow(-500000)  # 50万流出

        assert result['score'] == 5
        assert result['signal'] == 'slight_outflow'
        assert result['is_buy_signal'] is False

    def test_strong_outflow(self):
        """Test strong main net outflow."""
        selector = ShortTermSelector()

        result = selector._score_fund_flow(-6000000)  # 600万流出

        assert result['score'] == 0
        assert result['signal'] == 'strong_outflow'
        assert result['is_buy_signal'] is False


class TestComprehensiveScoring:
    """Test comprehensive analysis and signal generation."""

    def test_analyze_invalid_code(self):
        """Test analysis with invalid stock code."""
        selector = ShortTermSelector()

        result = selector.analyze_single_stock(code="invalid")

        assert result['error'] is not None
        assert result['score'] == 0
        assert result['rating'] == 'D'
        assert result['recommendation'] is False

    def test_analyze_insufficient_data(self):
        """Test analysis with insufficient K-line data."""
        selector = ShortTermSelector()

        # Create small DataFrame (< 50 rows)
        small_df = pd.DataFrame({
            'open': [10, 10.5, 11],
            'high': [10.5, 11, 11.5],
            'low': [9.5, 10, 10.5],
            'close': [10.2, 10.8, 11.2],
            'volume': [1000000, 1100000, 1200000]
        })

        result = selector.analyze_single_stock(code="000001", kline_data=small_df)

        assert result['error'] is not None
        assert '数据不足' in result['error']

    def test_analyze_single_stock_success(self, sample_kline_data, sample_fund_flow):
        """Test successful single stock analysis."""
        selector = ShortTermSelector()

        result = selector.analyze_single_stock(
            code="000001",
            kline_data=sample_kline_data,
            fund_flow=sample_fund_flow
        )

        assert result['code'] == '000001'
        assert 'score' in result
        assert 'rating' in result
        assert 'recommendation' in result
        assert 'details' in result
        assert 'stop_loss' in result
        assert 'take_profit' in result

    def test_buy_signal_count(self):
        """Test buy signal counting."""
        selector = ShortTermSelector()

        score_details = {
            'rsi': {'is_buy_signal': True},
            'kdj': {'is_buy_signal': True},
            'macd': {'is_buy_signal': False},
            'bollinger': {'is_buy_signal': True},
            'volume_price': {'is_buy_signal': False},
            'fund_flow': {'is_buy_signal': True}
        }

        count = selector._count_buy_signals(score_details)
        assert count == 4

    def test_recommendation_threshold(self, bullish_kline_data, strong_inflow_fund_flow):
        """Test recommendation based on score threshold."""
        selector = ShortTermSelector()

        result = selector.analyze_single_stock(
            code="000001",
            kline_data=bullish_kline_data,
            fund_flow=strong_inflow_fund_flow
        )

        # Check if score meets threshold
        if result['score'] >= selector.config.score_threshold:
            assert result['recommendation'] is True


class TestTradePointsCalculation:
    """Test stop-loss and take-profit calculation."""

    def test_calc_trade_points_basic(self):
        """Test basic trade points calculation."""
        selector = ShortTermSelector()

        result = selector._calc_trade_points(
            current_price=100.0,
            atr=5.0,
            stop_multiplier=2.0,
            profit_multiplier=3.0
        )

        assert result['stop_loss'] == 90.0  # 100 - 5*2
        assert result['take_profit'] == 115.0  # 100 + 5*3
        assert result['stop_loss_pct'] == -10.0
        assert result['take_profit_pct'] == 15.0
        assert result['risk_reward_ratio'] == 1.5

    def test_calc_trade_points_invalid_price(self):
        """Test trade points with invalid price."""
        selector = ShortTermSelector()

        with pytest.raises(ValueError, match="价格必须大于0"):
            selector._calc_trade_points(current_price=0, atr=5.0)

    def test_calc_trade_points_invalid_atr(self):
        """Test trade points with invalid ATR."""
        selector = ShortTermSelector()

        with pytest.raises(ValueError, match="ATR必须大于0"):
            selector._calc_trade_points(current_price=100, atr=0)


class TestBatchAnalysis:
    """Test batch analysis functionality."""

    def test_analyze_batch(self, sample_kline_data, sample_fund_flow):
        """Test batch analysis of multiple stocks."""
        selector = ShortTermSelector()

        stocks_data = [
            {'code': '000001', 'kline_data': sample_kline_data, 'fund_flow': sample_fund_flow},
            {'code': '600000', 'kline_data': sample_kline_data, 'fund_flow': sample_fund_flow},
        ]

        results = selector.analyze_batch(stocks_data)

        assert len(results) == 2
        # Results should be sorted by score (descending)
        if len(results) > 1:
            assert results[0]['score'] >= results[1]['score']

    def test_filter_recommended(self):
        """Test filtering recommended stocks."""
        selector = ShortTermSelector()

        results = [
            {'code': '000001', 'score': 75, 'recommendation': True},
            {'code': '600000', 'score': 55, 'recommendation': False},
            {'code': '000002', 'score': 80, 'recommendation': True},
        ]

        recommended = selector.filter_recommended(results)

        assert len(recommended) == 2
        assert all(r['recommendation'] for r in recommended)
