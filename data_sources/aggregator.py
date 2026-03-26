"""
数据源聚合器模块

统一入口，对外提供数据访问接口
"""

import logging
import threading
from typing import List, Optional, Dict, Any, Tuple
from .base import DataSourceAdapter
from .registry import AdapterRegistry
from .executor import FallbackExecutor
from .exceptions import DataSourceError
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from common.config import get_config

logger = logging.getLogger(__name__)


class DataSourceAggregator:
    """
    数据源聚合器

    单例模式，提供统一的数据访问接口
    自动处理数据源降级和优先级
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()  # 线程锁，用于线程安全的单例模式

    def __new__(cls):
        """
        线程安全的单例模式 (Double-Checked Locking)

        Returns:
            DataSourceAggregator 实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化聚合器

        """
        if self._initialized:
            return

        self.config: Dict[str, Any] = {}
        self.registry = AdapterRegistry()
        self.executor: Optional[FallbackExecutor] = None

        # 加载配置
        self._load_config_from_config_system()

        # 创建执行器
        self.executor = FallbackExecutor(self.config)

        # 自动发现并初始化适配器
        self._initialize_adapters()

        self._initialized = True
        logger.info("DataSourceAggregator initialized successfully")

    def _load_config_from_config_system(self):
        """从统一配置系统加载配置"""
        config = get_config()

        # 从 Config.py 获取数据源配置
        data_sources_config = config.data_sources

        # 转换为 aggregator 需要的格式
        self.config = {
            "version": "2.0",
            "sources": {},
            "fallback": {
                "max_retries": data_sources_config.max_retries,
                "retry_delay": data_sources_config.retry_delay,
                "log_failures": data_sources_config.log_failures
            }
        }

        # 转换所有数据源类别
        for category_name in [
            'realtime', 'kline', 'fundamentals', 'tech_indicators',
            'fund_flows', 'dragon_tiger', 'valuation', 'per_share_indicators',
            'osc_indicators', 'price_vol_ind', 'limit_up_down', 'turnover_rates',
            'fund_quotes', 'dupont_analysis'
        ]:
            category_items = getattr(data_sources_config.sources, category_name, [])
            if category_items:
                self.config['sources'][category_name] = [
                    item.model_dump() for item in category_items
                ]

        logger.info("Loaded data sources configuration from unified config system")

    def _initialize_adapters(self):
        """初始化所有适配器"""
        import os

        # 自动发现适配器类
        self.registry.auto_discover()

        # 从环境变量读取 API tokens
        tushare_token = os.getenv('TUSHARE_TOKEN', '')

        # 收集所有需要初始化的适配器（去重）
        adapters_to_init = set()
        for category, sources in self.config.get('sources', {}).items():
            for source_cfg in sources:
                if source_cfg.get('enabled', True):
                    adapters_to_init.add(source_cfg['name'])

        # 创建适配器实例（每个适配器只创建一次）
        for source_name in adapters_to_init:
            # 跳过尚未实现的适配器
            if source_name not in self.registry.get_adapter_names():
                logger.warning(f"Adapter {source_name} not implemented, skipping")
                continue

            try:
                # 检查是否已存在
                if self.registry.get_adapter(source_name):
                    continue

                # 准备适配器参数
                adapter_kwargs = {
                    'timeout': 5  # 默认超时
                }

                # 根据适配器类型添加特定参数
                if source_name == 'tushare' and tushare_token:
                    adapter_kwargs['token'] = tushare_token

                # 创建适配器实例
                adapter = self.registry.create_adapter(source_name, **adapter_kwargs)
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

        # 获取所有已启用的适配器，并附带优先级
        adapter_with_priority = []
        for source_cfg in sources:
            if source_cfg.get('enabled', True):
                adapter = self.registry.get_adapter(source_cfg['name'])
                if adapter:
                    # 从配置读取优先级，而不是从 adapter 实例读取
                    priority = source_cfg.get('priority', 100)
                    adapter_with_priority.append((adapter, priority))

        # 按优先级排序（数字越小越优先）
        adapter_with_priority.sort(key=lambda x: x[1])

        # 返回排序后的 adapter 列表
        return [a for a, p in adapter_with_priority]

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

    def get_stock_list(self, exchange: Optional[str] = None) -> List[Dict]:
        """
        获取股票列表

        Args:
            exchange: 交易所筛选 (SH/SZ)，None 表示全部

        Returns:
            股票列表，每个元素包含 symbol, name, exchange 等字段
        """
        if not self.executor:
            return []

        adapters = self._get_sorted_adapters('realtime')

        result = self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_stock_list(),
            "get_stock_list"
        )

        if result is None:
            return []

        if exchange:
            result = [s for s in result if s.get('exchange') == exchange]

        return result

    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """
        获取股票详情

        Args:
            symbol: 股票代码

        Returns:
            股票详情字典，失败返回 None
        """
        if not self.executor:
            return None

        adapters = self._get_sorted_adapters('realtime')

        return self.executor.execute_with_fallback(
            adapters,
            lambda adapter: adapter.get_stock_detail(symbol),
            "get_stock_detail"
        )


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


class TopListAPI:
    """涨跌排行 API - 带内存缓存"""

    _cache: Dict[str, Tuple[List[Dict], float]] = {}
    _cache_ttl: int = 60  # 缓存60秒
    _cache_lock = threading.Lock()  # 线程锁，保护缓存访问

    @staticmethod
    def get(type: str, date: Optional[str] = None) -> List[Dict]:
        import time
        cache_key = f"toplist_{type}_{date}"
        now = time.time()

        # 检查缓存（加锁）
        with TopListAPI._cache_lock:
            if cache_key in TopListAPI._cache:
                data, timestamp = TopListAPI._cache[cache_key]
                if now - timestamp < TopListAPI._cache_ttl:
                    return data

        # 获取所有股票行情（不加锁，避免阻塞）
        aggregator = DataSourceAggregator()
        stocks = aggregator.get_stock_list()
        symbols = [s.get('symbol') for s in stocks[:500] if s.get('symbol')]  # 安全访问

        quotes = aggregator.batch_get_realtime(symbols)

        # 转换并排序（映射到 TopListEntry 模型）
        # TopListEntry 需要: ts_code, symbol, name, change_pct, current_price, change, volume
        items = []
        for q in quotes:
            items.append({
                "ts_code": f"{q.symbol}.SH",  # 根据代码推导交易所
                "symbol": q.symbol,
                "name": getattr(q, 'name', ''),
                "current_price": q.price,       # Quote.price -> TopListEntry.current_price
                "change": q.change,
                "change_pct": q.percent * 100,
                "volume": q.volume
            })

        # 按涨跌幅排序
        reverse = (type == "gain")  # 涨幅榜降序，跌幅榜升序
        items.sort(key=lambda x: x["change_pct"], reverse=reverse)

        # 更新缓存（加锁）
        with TopListAPI._cache_lock:
            TopListAPI._cache[cache_key] = (items[:100], now)

        return items[:100]


class KLineStatsAPI:
    """K线统计 API"""

    @staticmethod
    def get(symbol: str, period: str = "1y") -> Dict:
        from datetime import datetime, timedelta

        # 计算日期范围
        end_date = datetime.now().strftime("%Y-%m-%d")
        days_map = {"1y": 365, "6m": 180, "3m": 90, "1m": 30}
        days = days_map.get(period, 365)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 获取K线数据
        aggregator = DataSourceAggregator()
        klines = aggregator.get_kline(symbol, "1d", start_date, end_date)

        if not klines:
            return {
                "symbol": symbol,
                "period": period,
                "total_trading_days": 0,
                "price_range": {"min": 0, "max": 0, "avg": 0},
                "volume_stats": {"min": 0, "max": 0, "avg": 0, "total": 0},
                "volatility": 0.0,
                "highest_price": {"price": 0, "date": ""},
                "lowest_price": {"price": 0, "date": ""}
            }

        # 计算统计（KLine 模型属性: close, datetime, open_price）
        prices = [k.close for k in klines]  # 使用 close 而非 price
        volumes = [k.volume for k in klines]

        max_price_idx = prices.index(max(prices))
        min_price_idx = prices.index(min(prices))

        # 计算波动率（标准差）
        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price * 100 if avg_price > 0 else 0

        return {
            "symbol": symbol,
            "name": getattr(klines[0], 'name', ''),
            "period": period,
            "total_trading_days": len(klines),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "avg": round(avg_price, 2)
            },
            "volume_stats": {
                "min": min(volumes),
                "max": max(volumes),
                "avg": int(sum(volumes) / len(volumes)),
                "total": sum(volumes)
            },
            "volatility": round(volatility, 2),
            "highest_price": {
                "price": max(prices),
                "date": str(klines[max_price_idx].datetime.date())  # 使用 datetime
            },
            "lowest_price": {
                "price": min(prices),
                "date": str(klines[min_price_idx].datetime.date())  # 使用 datetime
            }
        }


class StockListAPI:
    """股票列表 API"""

    @staticmethod
    def get(exchange: Optional[str] = None) -> List[Dict]:
        aggregator = DataSourceAggregator()
        return aggregator.get_stock_list(exchange=exchange)
