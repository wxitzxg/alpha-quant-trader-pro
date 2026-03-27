"""
Unit tests for stock filtering rules.

Tests filter logic for:
- GEM board exclusion (创业板 300xxx)
- STAR board exclusion (科创板 688xxx)
- Beijing Stock Exchange exclusion (北交所 8xxxxx, 4xxxxx)
- ST stocks exclusion
- Price filters
- Volume filters
- Combined filtering
"""

import pytest
import pandas as pd
from typing import List

from stock_recommendation.strategies.strategy_config import FilterRules
from stock_recommendation.models import ScanRequest, StockPoolType


class TestFilterRulesDefaults:
    """Test default filter rule configuration."""

    def test_default_filter_rules(self):
        """Test default filter rules values."""
        rules = FilterRules()

        assert rules.exclude_gem is True
        assert rules.exclude_star is True
        assert rules.exclude_bse is True
        assert rules.exclude_st is True
        assert rules.exclude_suspended is True

        assert rules.min_price == 2.0
        assert rules.max_price is None

        assert rules.min_volume == 1000000
        assert rules.min_turnover == 10000000

        assert rules.min_listing_days == 60

    def test_custom_filter_rules(self):
        """Test custom filter rules configuration."""
        rules = FilterRules(
            exclude_gem=False,
            exclude_star=False,
            min_price=5.0,
            min_volume=5000000
        )

        assert rules.exclude_gem is False
        assert rules.exclude_star is False
        assert rules.min_price == 5.0
        assert rules.min_volume == 5000000


class TestStockCodeFilters:
    """Test stock code filtering based on exchange/board."""

    @pytest.fixture
    def default_rules(self):
        return FilterRules()

    def is_gem_stock(self, code: str) -> bool:
        """Check if stock is GEM board (300xxx)."""
        return code.startswith('300')

    def is_star_stock(self, code: str) -> bool:
        """Check if stock is STAR board (688xxx)."""
        return code.startswith('688')

    def is_bse_stock(self, code: str) -> bool:
        """Check if stock is Beijing Stock Exchange (8xxxxx, 4xxxxx)."""
        return code.startswith('8') or code.startswith('4')

    def is_shanghai_main(self, code: str) -> bool:
        """Check if stock is Shanghai main board (60xxxx)."""
        return code.startswith('60') or code.startswith('688') is False

    def test_gem_stock_identification(self):
        """Test GEM stock identification."""
        assert self.is_gem_stock('300001') is True
        assert self.is_gem_stock('300750') is True
        assert self.is_gem_stock('300999') is True
        assert self.is_gem_stock('600000') is False
        assert self.is_gem_stock('000001') is False

    def test_star_stock_identification(self):
        """Test STAR board stock identification."""
        assert self.is_star_stock('688001') is True
        assert self.is_star_stock('688981') is True
        assert self.is_star_stock('600000') is False
        assert self.is_star_stock('300001') is False

    def test_bse_stock_identification(self):
        """Test Beijing Stock Exchange stock identification."""
        assert self.is_bse_stock('830001') is True
        assert self.is_bse_stock('430001') is True
        assert self.is_bse_stock('600000') is False
        assert self.is_bse_stock('000001') is False


class TestGemExclusion:
    """Test GEM (创业板) board exclusion."""

    def filter_gem_stocks(
        self,
        codes: List[str],
        exclude_gem: bool = True
    ) -> List[str]:
        """
        Filter out GEM board stocks if exclude_gem is True.

        Args:
            codes: List of stock codes
            exclude_gem: Whether to exclude GEM stocks

        Returns:
            Filtered list of stock codes
        """
        if not exclude_gem:
            return codes
        return [c for c in codes if not c.startswith('300')]

    def test_exclude_gem_stocks(self, gem_stock_codes):
        """Test exclusion of GEM stocks."""
        all_codes = ['600000', '000001', '300001', '300002', '601318']

        filtered = self.filter_gem_stocks(all_codes, exclude_gem=True)

        assert '300001' not in filtered
        assert '300002' not in filtered
        assert '600000' in filtered
        assert '000001' in filtered

    def test_include_gem_stocks(self, gem_stock_codes):
        """Test inclusion of GEM stocks when exclusion is disabled."""
        all_codes = ['600000', '000001', '300001', '300002', '601318']

        filtered = self.filter_gem_stocks(all_codes, exclude_gem=False)

        assert '300001' in filtered
        assert '300002' in filtered
        assert len(filtered) == 5

    def test_all_gem_stocks_excluded(self, gem_stock_codes):
        """Test filtering when all stocks are GEM."""
        filtered = self.filter_gem_stocks(gem_stock_codes, exclude_gem=True)

        assert len(filtered) == 0


class TestStarExclusion:
    """Test STAR (科创板) board exclusion."""

    def filter_star_stocks(
        self,
        codes: List[str],
        exclude_star: bool = True
    ) -> List[str]:
        """
        Filter out STAR board stocks if exclude_star is True.

        Args:
            codes: List of stock codes
            exclude_star: Whether to exclude STAR stocks

        Returns:
            Filtered list of stock codes
        """
        if not exclude_star:
            return codes
        return [c for c in codes if not c.startswith('688')]

    def test_exclude_star_stocks(self, star_stock_codes):
        """Test exclusion of STAR stocks."""
        all_codes = ['600000', '000001', '688001', '688002', '601318']

        filtered = self.filter_star_stocks(all_codes, exclude_star=True)

        assert '688001' not in filtered
        assert '688002' not in filtered
        assert '600000' in filtered
        assert '000001' in filtered

    def test_include_star_stocks(self, star_stock_codes):
        """Test inclusion of STAR stocks when exclusion is disabled."""
        all_codes = ['600000', '000001', '688001', '688002', '601318']

        filtered = self.filter_star_stocks(all_codes, exclude_star=False)

        assert '688001' in filtered
        assert '688002' in filtered
        assert len(filtered) == 5

    def test_all_star_stocks_excluded(self, star_stock_codes):
        """Test filtering when all stocks are STAR."""
        filtered = self.filter_star_stocks(star_stock_codes, exclude_star=True)

        assert len(filtered) == 0


class TestBSEExclusion:
    """Test Beijing Stock Exchange (北交所) exclusion."""

    def filter_bse_stocks(
        self,
        codes: List[str],
        exclude_bse: bool = True
    ) -> List[str]:
        """
        Filter out BSE stocks if exclude_bse is True.

        Args:
            codes: List of stock codes
            exclude_bse: Whether to exclude BSE stocks

        Returns:
            Filtered list of stock codes
        """
        if not exclude_bse:
            return codes
        return [c for c in codes if not (c.startswith('8') or c.startswith('4'))]

    def test_exclude_bse_stocks(self):
        """Test exclusion of BSE stocks."""
        all_codes = ['600000', '830001', '430001', '000001', '601318']

        filtered = self.filter_bse_stocks(all_codes, exclude_bse=True)

        assert '830001' not in filtered
        assert '430001' not in filtered
        assert '600000' in filtered
        assert '000001' in filtered

    def test_include_bse_stocks(self):
        """Test inclusion of BSE stocks when exclusion is disabled."""
        all_codes = ['600000', '830001', '430001', '000001']

        filtered = self.filter_bse_stocks(all_codes, exclude_bse=False)

        assert '830001' in filtered
        assert '430001' in filtered


class TestCombinedFilters:
    """Test combined filtering with multiple rules."""

    def apply_all_filters(
        self,
        codes: List[str],
        rules: FilterRules
    ) -> List[str]:
        """
        Apply all exclusion filters based on rules.

        Args:
            codes: List of stock codes
            rules: Filter rules configuration

        Returns:
            Filtered list of stock codes
        """
        filtered = codes.copy()

        if rules.exclude_gem:
            filtered = [c for c in filtered if not c.startswith('300')]

        if rules.exclude_star:
            filtered = [c for c in filtered if not c.startswith('688')]

        if rules.exclude_bse:
            filtered = [c for c in filtered if not (c.startswith('8') or c.startswith('4'))]

        return filtered

    def test_default_filters_exclude_all_boards(self, default_filter_rules):
        """Test default filters exclude GEM, STAR, and BSE."""
        all_codes = [
            '600000',  # Shanghai main
            '000001',  # Shenzhen main
            '300001',  # GEM
            '688001',  # STAR
            '830001',  # BSE
            '601318',  # Shanghai main
        ]

        filtered = self.apply_all_filters(all_codes, default_filter_rules)

        assert '300001' not in filtered
        assert '688001' not in filtered
        assert '830001' not in filtered
        assert '600000' in filtered
        assert '000001' in filtered
        assert '601318' in filtered

    def test_relaxed_filters_include_all(self, relaxed_filter_rules):
        """Test relaxed filters include all exchanges."""
        all_codes = [
            '600000',
            '000001',
            '300001',
            '688001',
            '830001',
        ]

        filtered = self.apply_all_filters(all_codes, relaxed_filter_rules)

        assert len(filtered) == 5  # All included

    def test_partial_exclusion_gem_only(self):
        """Test excluding only GEM board."""
        rules = FilterRules(
            exclude_gem=True,
            exclude_star=False,
            exclude_bse=False
        )

        all_codes = ['600000', '300001', '688001', '830001']

        filtered = self.apply_all_filters(all_codes, rules)

        assert '300001' not in filtered
        assert '688001' in filtered
        assert '830001' in filtered

    def test_partial_exclusion_star_only(self):
        """Test excluding only STAR board."""
        rules = FilterRules(
            exclude_gem=False,
            exclude_star=True,
            exclude_bse=False
        )

        all_codes = ['600000', '300001', '688001', '830001']

        filtered = self.apply_all_filters(all_codes, rules)

        assert '300001' in filtered
        assert '688001' not in filtered
        assert '830001' in filtered


class TestPriceFilters:
    """Test price-based filtering."""

    def filter_by_price(
        self,
        stocks: List[dict],
        min_price: float,
        max_price: float = None
    ) -> List[dict]:
        """
        Filter stocks by price range.

        Args:
            stocks: List of stock dicts with 'code' and 'price' keys
            min_price: Minimum price
            max_price: Maximum price (optional)

        Returns:
            Filtered list of stocks
        """
        filtered = [s for s in stocks if s['price'] >= min_price]

        if max_price is not None:
            filtered = [s for s in filtered if s['price'] <= max_price]

        return filtered

    def test_min_price_filter(self):
        """Test minimum price filter."""
        stocks = [
            {'code': '000001', 'price': 10.0},
            {'code': '000002', 'price': 1.5},  # Below min
            {'code': '000003', 'price': 5.0},
        ]

        filtered = self.filter_by_price(stocks, min_price=2.0)

        assert len(filtered) == 2
        assert '000002' not in [s['code'] for s in filtered]

    def test_max_price_filter(self):
        """Test maximum price filter."""
        stocks = [
            {'code': '000001', 'price': 500.0},  # Above max
            {'code': '000002', 'price': 50.0},
            {'code': '000003', 'price': 100.0},
        ]

        filtered = self.filter_by_price(stocks, min_price=0, max_price=200.0)

        assert len(filtered) == 2
        assert '000001' not in [s['code'] for s in filtered]

    def test_price_range_filter(self):
        """Test price range filter."""
        stocks = [
            {'code': '000001', 'price': 10.0},
            {'code': '000002', 'price': 1.0},   # Below range
            {'code': '000003', 'price': 100.0}, # Above range
            {'code': '000004', 'price': 50.0},
        ]

        filtered = self.filter_by_price(stocks, min_price=5.0, max_price=80.0)

        assert len(filtered) == 2
        assert set(s['code'] for s in filtered) == {'000001', '000004'}


class TestVolumeFilters:
    """Test volume-based filtering."""

    def filter_by_volume(
        self,
        stocks: List[dict],
        min_volume: int,
        min_turnover: float = None
    ) -> List[dict]:
        """
        Filter stocks by volume.

        Args:
            stocks: List of stock dicts with 'volume' and optionally 'turnover'
            min_volume: Minimum daily volume
            min_turnover: Minimum daily turnover (optional)

        Returns:
            Filtered list of stocks
        """
        filtered = [s for s in stocks if s['volume'] >= min_volume]

        if min_turnover is not None:
            filtered = [s for s in filtered if s.get('turnover', 0) >= min_turnover]

        return filtered

    def test_min_volume_filter(self):
        """Test minimum volume filter."""
        stocks = [
            {'code': '000001', 'volume': 5000000},
            {'code': '000002', 'volume': 500000},  # Below min
            {'code': '000003', 'volume': 2000000},
        ]

        filtered = self.filter_by_volume(stocks, min_volume=1000000)

        assert len(filtered) == 2
        assert '000002' not in [s['code'] for s in filtered]

    def test_min_turnover_filter(self):
        """Test minimum turnover filter."""
        stocks = [
            {'code': '000001', 'volume': 5000000, 'turnover': 50000000},
            {'code': '000002', 'volume': 5000000, 'turnover': 5000000},  # Below min
            {'code': '000003', 'volume': 5000000, 'turnover': 15000000},
        ]

        filtered = self.filter_by_volume(
            stocks,
            min_volume=0,
            min_turnover=10000000
        )

        assert len(filtered) == 2
        assert '000002' not in [s['code'] for s in filtered]


class TestSTExclusion:
    """Test ST stock exclusion."""

    def filter_st_stocks(
        self,
        stocks: List[dict],
        exclude_st: bool = True
    ) -> List[dict]:
        """
        Filter out ST and *ST stocks.

        Args:
            stocks: List of stock dicts with 'name' key
            exclude_st: Whether to exclude ST stocks

        Returns:
            Filtered list of stocks
        """
        if not exclude_st:
            return stocks

        return [
            s for s in stocks
            if not (s.get('name', '').startswith('ST') or
                    s.get('name', '').startswith('*ST'))
        ]

    def test_exclude_st_stocks(self):
        """Test exclusion of ST stocks."""
        stocks = [
            {'code': '000001', 'name': '平安银行'},
            {'code': '000002', 'name': 'ST某某'},  # ST
            {'code': '000003', 'name': '*ST某某'},  # *ST
            {'code': '000004', 'name': '万科A'},
        ]

        filtered = self.filter_st_stocks(stocks, exclude_st=True)

        assert len(filtered) == 2
        assert '000002' not in [s['code'] for s in filtered]
        assert '000003' not in [s['code'] for s in filtered]

    def test_include_st_stocks(self):
        """Test inclusion of ST stocks when exclusion is disabled."""
        stocks = [
            {'code': '000001', 'name': '平安银行'},
            {'code': '000002', 'name': 'ST某某'},
        ]

        filtered = self.filter_st_stocks(stocks, exclude_st=False)

        assert len(filtered) == 2


class TestScanRequest:
    """Test ScanRequest model with filter options."""

    def test_default_scan_request(self):
        """Test default scan request values."""
        from stock_recommendation.models import ScanRequest, StrategyType, StockPoolType

        request = ScanRequest()

        assert request.strategy_type == StrategyType.BOTH
        assert request.top_n == 10
        assert request.stock_pool == StockPoolType.ALL
        assert request.exclude_gem is True
        assert request.exclude_star is True
        assert request.min_score == 60

    def test_custom_scan_request(self):
        """Test custom scan request values."""
        from stock_recommendation.models import ScanRequest, StrategyType

        request = ScanRequest(
            strategy_type=StrategyType.SHORT,
            top_n=20,
            exclude_gem=False,
            exclude_star=False,
            min_score=70
        )

        assert request.strategy_type == StrategyType.SHORT
        assert request.top_n == 20
        assert request.exclude_gem is False
        assert request.exclude_star is False
        assert request.min_score == 70

    def test_custom_stock_pool(self):
        """Test custom stock pool."""
        from stock_recommendation.models import ScanRequest, StockPoolType

        request = ScanRequest(
            stock_pool=StockPoolType.CUSTOM,
            custom_codes=['000001', '600000']
        )

        assert request.stock_pool == StockPoolType.CUSTOM
        assert request.custom_codes == ['000001', '600000']

    def test_min_score_validation(self):
        """Test min_score validation."""
        from stock_recommendation.models import ScanRequest
        from pydantic import ValidationError

        # Valid range
        request = ScanRequest(min_score=50)
        assert request.min_score == 50

        # Invalid - below range
        with pytest.raises(ValidationError):
            ScanRequest(min_score=-1)

        # Invalid - above range
        with pytest.raises(ValidationError):
            ScanRequest(min_score=101)


class TestFilterIntegration:
    """Integration tests for filtering functionality."""

    def test_complete_filter_workflow(self):
        """Test complete filter workflow with multiple criteria."""
        # Sample stock data
        stocks = [
            {'code': '600000', 'name': '浦发银行', 'price': 10.0, 'volume': 50000000},
            {'code': '300001', 'name': '特锐德', 'price': 25.0, 'volume': 10000000},  # GEM
            {'code': '688001', 'name': '华兴源创', 'price': 50.0, 'volume': 5000000},  # STAR
            {'code': '000001', 'name': '平安银行', 'price': 15.0, 'volume': 80000000},
            {'code': '000002', 'name': 'ST某某', 'price': 3.0, 'volume': 2000000},  # ST
            {'code': '000003', 'name': '低股价', 'price': 1.5, 'volume': 1000000},  # Low price
        ]

        # Apply all filters
        rules = FilterRules(
            exclude_gem=True,
            exclude_star=True,
            exclude_st=True,
            min_price=2.0,
            min_volume=1000000
        )

        filtered = stocks.copy()

        # Apply exchange filters
        if rules.exclude_gem:
            filtered = [s for s in filtered if not s['code'].startswith('300')]
        if rules.exclude_star:
            filtered = [s for s in filtered if not s['code'].startswith('688')]

        # Apply ST filter
        if rules.exclude_st:
            filtered = [s for s in filtered
                        if not (s['name'].startswith('ST') or s['name'].startswith('*ST'))]

        # Apply price filter
        filtered = [s for s in filtered if s['price'] >= rules.min_price]

        # Apply volume filter
        filtered = [s for s in filtered if s['volume'] >= rules.min_volume]

        # Verify results
        assert len(filtered) == 2
        codes = [s['code'] for s in filtered]
        assert '600000' in codes
        assert '000001' in codes
        assert '300001' not in codes  # GEM excluded
        assert '688001' not in codes  # STAR excluded
        assert '000002' not in codes  # ST excluded
        assert '000003' not in codes  # Low price excluded
