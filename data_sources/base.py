"""
抽象接口模块

定义所有数据源适配器必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from .models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from .exceptions import DataSourceError


class DataSourceAdapter(ABC):
    """
    数据源适配器抽象基类

    所有具体的数据源适配器都必须继承此类并实现所有抽象方法
    """

    def __init__(self, priority: int = 100, timeout: int = 5):
        """
        初始化数据源适配器

        Args:
            priority: 优先级,数值越小越优先 (默认 100)
            timeout: 超时时间(秒) (默认 5)
        """
        self._priority = priority
        self._timeout = timeout

    @property
    def priority(self) -> int:
        """
        数据源优先级

        Returns:
            优先级数值,越小越优先,默认 100 (低优先级)
        """
        return self._priority

    @property
    def timeout(self) -> int:
        """
        数据源超时时间

        Returns:
            超时时间(秒)
        """
        return self._timeout

    @abstractmethod
    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """
        获取单个股票实时行情

        Args:
            symbol: 股票代码 (如 "600519")

        Returns:
            Quote 对象，失败返回 None

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表 (可能为空)

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_kline(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> List[KLine]:
        """
        获取K线数据

        Args:
            symbol: 股票代码
            interval: 周期 ("1m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            KLine 对象列表 (可能为空)

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
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

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
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

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
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

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
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

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_stock_list(self) -> List[Dict]:
        """
        获取股票列表

        Returns:
            股票列表，每个股票为字典，包含:
            - symbol: 股票代码 (如 "600519")
            - name: 股票名称 (如 "贵州茅台")
            - exchange: 交易所 (如 "SH", "SZ")
            - list_date: 上市日期 (如 "2001-08-27")
            - industry: 所属行业 (可选)
            - concept: 概念板块 (可选)
            - region: 所属地区 (可选)

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """
        获取股票详细信息

        Args:
            symbol: 股票代码

        Returns:
            股票详细信息字典，包含:
            - symbol: 股票代码
            - name: 股票名称
            - exchange: 交易所
            - list_date: 上市日期
            - delist_date: 退市日期 (可选)
            - total_shares: 总股本 (可选)
            - float_shares: 流通股本 (可选)
            - industry: 所属行业 (可选)
            - concept: 概念板块 (可选)
            - region: 所属地区 (可选)
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取技术指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            技术指标数据列表，每个元素包含:
            - date: 日期
            - ma5: 5日均线
            - ma10: 10日均线
            - ma20: 20日均线
            - macd: MACD 值
            - macd_signal: MACD 信号线
            - macd_hist: MACD 柱状图
            - kdj_k: KDJ K 值
            - kdj_d: KDJ D 值
            - kdj_j: KDJ J 值
            - rsi: RSI 值
            - 更多指标...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取资金流向数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            资金流向数据列表，每个元素包含:
            - date: 日期
            - main_net_inflow: 主力净流入
            - retail_net_inflow: 散户净流入
            - large_order_net_inflow: 大单净流入
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取龙虎榜数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            龙虎榜数据列表，每个元素包含:
            - date: 日期
            - buy_departments: 买入营业部列表
            - sell_departments: 卖出营业部列表
            - buy_amount: 买入金额
            - sell_amount: 卖出金额
            - reason: 上榜原因
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_valuation(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取估值指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            估值指标数据列表，每个元素包含:
            - date: 日期
            - pe_ttm: 市盈率 (TTM)
            - pe_lyr: 市盈率 (LYR)
            - pb: 市净率
            - ps: 市销率
            - 更多指标...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取每股指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            每股指标数据列表，每个元素包含:
            - date: 日期
            - eps: 每股收益
            - bvps: 每股净资产
            - cfps: 每股现金流
            - dps: 每股股息
            - 更多指标...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_osc_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取超买超卖指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            超买超卖指标数据列表，每个元素包含:
            - date: 日期
            - wr: 威廉指标
            - bias: 乖离率
            - cci: 顺势指标
            - 更多指标...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取量价指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            量价指标数据列表，每个元素包含:
            - date: 日期
            - obv: 能量潮
            - vr: 量比
            - mfi: 资金流量指标
            - 更多指标...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_limit_up_down(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取涨跌停数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            涨跌停数据列表，每个元素包含:
            - date: 日期
            - is_limit_up: 是否涨停
            - is_limit_down: 是否跌停
            - limit_up_times: 涨停次数
            - limit_down_times: 跌停次数
            - consecutive_limit_up: 连板天数
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_turnover_rates(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取换手率数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            换手率数据列表，每个元素包含:
            - date: 日期
            - turnover_rate: 换手率
            - volume_ratio: 量比
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_fund_quotes(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取基金净值数据

        Args:
            symbol: 基金代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            基金净值数据列表，每个元素包含:
            - date: 日期
            - nav: 单位净值
            - accumulated_nav: 累计净值
            - daily_return: 日收益率
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """
        获取杜邦分析数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            杜邦分析数据列表，每个元素包含:
            - date: 日期
            - roe: 净资产收益率
            - net_profit_margin: 净利率
            - asset_turnover: 资产周转率
            - equity_multiplier: 权益乘数
            - 更多字段...

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        数据源名称

        Returns:
            数据源唯一标识 (如 "tushare", "akshare")
        """
        pass

    @property
    def priority(self) -> int:
        """
        数据源优先级

        Returns:
            优先级数值，越小越优先，默认 100 (低优先级)
        """
        return 100

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        子类可以重写此方法实现健康检查

        Returns:
            True 表示可用
        """
        return True
