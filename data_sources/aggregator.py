"""
数据源聚合器模块

统一入口，对外提供数据访问接口
"""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from .base import DataSourceAdapter
from .registry import AdapterRegistry
from .executor import FallbackExecutor
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement

logger = logging.getLogger(__name__)


class DataSourceAggregator:
    """
    数据源聚合器

    单例模式，提供统一的数据访问接口
    自动处理数据源降级和优先级
    """

    _instance = None
    _initialized = False

    def __new__(cls, config_path: str = "config/sources.json"):
        """
        单例模式

        Args:
            config_path: 配置文件路径
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/sources.json"):
        """
        初始化聚合器

        Args:
            config_path: 配置文件路径
        """
        if self._initialized:
            return

        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.registry = AdapterRegistry()
        self.executor: Optional[FallbackExecutor] = None

        # 加载配置
        self._load_config()

        # 创建执行器
        self.executor = FallbackExecutor(self.config)

        # 自动发现并初始化适配器
        self._initialize_adapters()

        self._initialized = True
        logger.info("DataSourceAggregator initialized successfully")

    def _load_config(self):
        """加载配置文件"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}, using default config")
            self.config = self._get_default_config()
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "sources": {
                "realtime": [
                    {"name": "sina", "priority": 10, "enabled": True, "timeout": 3},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 5},
                    {"name": "tushare", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "kline": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 10},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 10},
                    {"name": "sina", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "fundamentals": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 15},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 15}
                ]
            },
            "fallback": {
                "max_retries": 2,
                "retry_delay": 0.5,
                "log_failures": True
            }
        }

    def _initialize_adapters(self):
        """初始化所有适配器"""
        # 自动发现适配器类
        self.registry.auto_discover()

        # 根据配置创建适配器实例
        for category, sources in self.config.get('sources', {}).items():
            for source_cfg in sources:
                if source_cfg.get('enabled', True):
                    source_name = source_cfg['name']

                    # 跳过尚未实现的适配器
                    if source_name not in self.registry.get_adapter_names():
                        logger.warning(f"Adapter {source_name} not implemented, skipping")
                        continue

                    try:
                        # 创建适配器实例
                        adapter = self.registry.create_adapter(
                            source_name,
                            timeout=source_cfg.get('timeout', 5)
                        )

                        # 设置优先级（如果适配器支持）
                        if hasattr(adapter, '_priority'):
                            adapter._priority = source_cfg.get('priority', 100)  # type: ignore

                        logger.info(f"Initialized adapter: {source_name}")

                    except Exception as e:
                        logger.error(f"Failed to initialize {source_name}: {e}", exc_info=True)

    def _get_sorted_adapters(self, category: str) -> List[DataSourceAdapter]:
        """
        获取按优先级排序的适配器列表

        Args:
            category: 数据类别 (realtime, kline, fundamentals)

        Returns:
            排序后的适配器列表
        """
        sources = self.config.get('sources', {}).get(category, [])

        # 获取所有已启用的适配器
        adapters = []
        for source_cfg in sources:
            if source_cfg.get('enabled', True):
                adapter = self.registry.get_adapter(source_cfg['name'])
                if adapter:
                    adapters.append(adapter)

        # 按优先级排序
        adapters.sort(key=lambda a: getattr(a, 'priority', 100))

        return adapters

    # ========== 对外统一接口 ==========

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """
        获取单个股票实时行情

        Args:
            symbol: 股票代码

        Returns:
            Quote 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('realtime')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_realtime(symbol),
            "get_realtime"
        )

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表
        """
        if not self.executor:
            return []

        adapters = self._get_sorted_adapters('realtime')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.batch_get_realtime(symbols),
            "batch_get_realtime"
        )

        return result if result is not None else []

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """
        获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            KLine 对象列表
        """
        if not self.executor:
            return []

        adapters = self._get_sorted_adapters('kline')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_kline(symbol, interval, start_date, end_date),
            "get_kline"
        )

        return result if result is not None else []

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """
        获取资产负债表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            BalanceSheet 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_balance_sheet(symbol, year, quarter),
            "get_balance_sheet"
        )

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """
        获取利润表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            IncomeStatement 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_income_statement(symbol, year, quarter),
            "get_income_statement"
        )

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """
        获取现金流量表

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            CashFlowStatement 对象，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('fundamentals')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_cash_flow_statement(symbol, year, quarter),
            "get_cash_flow_statement"
        )

    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """
        获取财务指标

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}
        """
        if not self.executor:
            return {}

        adapters = self._get_sorted_adapters('fundamentals')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_financial_indicators(symbol, year, quarter),
            "get_financial_indicators"
        )

        return result if result is not None else {}


# ========== 简化调用接口 ==========

class QuoteAPI:
    """实时行情 API"""

    @staticmethod
    def get_realtime(symbol: str) -> Optional[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.get_realtime(symbol)

    @staticmethod
    def batch_get_realtime(symbols: List[str]) -> List[Quote]:
        aggregator = DataSourceAggregator()
        return aggregator.batch_get_realtime(symbols)


class KLineAPI:
    """K线数据 API"""

    @staticmethod
    def get(symbol: str, interval: str = "1d",
            start_date: str = "", end_date: str = "") -> List[KLine]:
        aggregator = DataSourceAggregator()
        return aggregator.get_kline(symbol, interval, start_date, end_date)


class FundamentalsAPI:
    """基本面数据 API"""

    @staticmethod
    def get_balance_sheet(symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        aggregator = DataSourceAggregator()
        return aggregator.get_balance_sheet(symbol, year, quarter)

    @staticmethod
    def get_income_statement(symbol: str, year: int, quarter: int) -> Optional[IncomeStatement]:
        aggregator = DataSourceAggregator()
        return aggregator.get_income_statement(symbol, year, quarter)

    @staticmethod
    def get_cash_flow_statement(symbol: str, year: int, quarter: int) -> Optional[CashFlowStatement]:
        aggregator = DataSourceAggregator()
        return aggregator.get_cash_flow_statement(symbol, year, quarter)

    @staticmethod
    def get_indicators(symbol: str, year: int, quarter: int) -> Dict[str, float]:
        aggregator = DataSourceAggregator()
        return aggregator.get_financial_indicators(symbol, year, quarter)
