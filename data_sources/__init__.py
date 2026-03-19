"""股票数据源聚合模块"""

__version__ = "0.1.0"

from .models import (
    Quote,
    KLine,
    FinancialStatement,
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement
)
from .exceptions import (
    DataSourceError,
    DataSourceTimeoutError,
    DataSourceNotFoundError,
    DataSourceConfigError
)
from .base import DataSourceAdapter
from .registry import AdapterRegistry
from .executor import FallbackExecutor
from .aggregator import (
    DataSourceAggregator,
    QuoteAPI,
    KLineAPI,
    FundamentalsAPI
)

__all__ = [
    "Quote",
    "KLine",
    "FinancialStatement",
    "BalanceSheet",
    "IncomeStatement",
    "CashFlowStatement",
    "DataSourceError",
    "DataSourceTimeoutError",
    "DataSourceNotFoundError",
    "DataSourceConfigError",
    "DataSourceAdapter",
    "AdapterRegistry",
    "FallbackExecutor",
    "DataSourceAggregator",
    "QuoteAPI",
    "KLineAPI",
    "FundamentalsAPI"
]
