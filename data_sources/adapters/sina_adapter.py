"""
新浪财经数据源适配器
"""

import requests
import logging
from typing import List, Optional, Dict
from datetime import datetime
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError

logger = logging.getLogger(__name__)


class SinaAdapter(DataSourceAdapter):
    """
    新浪财经数据源适配器

    官网: https://finance.sina.com.cn
    特点: 实时性强、免费、速度快
    限制: 无官方文档、历史数据少
    """

    def __init__(self, timeout: int = 5):
        """
        Args:
            timeout: 超时时间（秒）
        """
        super().__init__()  # 调用父类 __init__ 初始化 _priority
        self.timeout = timeout
        self.base_url = "http://hq.sinajs.cn/list="

        # 创建 HTTP Session 复用连接
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; StockDataBot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "keep-alive"
        })

        logger.info("SinaAdapter initialized")

    def __del__(self):
        """析构函数 - 清理连接"""
        if hasattr(self, '_session'):
            self._session.close()

    def is_available(self) -> bool:
        """
        Check if Sina Finance API is available

        Returns:
            True if service is reachable
        """
        try:
            # Test connectivity with a simple request
            test_symbol = self._format_symbol("600519")
            url = f"{self.base_url}{test_symbol}"
            # 必须添加 Referer 头才能访问
            headers = {"Referer": "https://finance.sina.com.cn"}
            response = self._session.get(url, timeout=3, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Sina health check failed: {e}")
            return False

    @property
    def name(self) -> str:
        return "sina"

    # priority 属性继承自基类，无需重写

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            sina_symbol = self._format_symbol(symbol)
            url = f"{self.base_url}{sina_symbol}"

            # 必须添加 Referer 头才能访问
            headers = {"Referer": "https://finance.sina.com.cn"}
            response = self._session.get(url, timeout=self.timeout, headers=headers)
            response.encoding = 'gbk'

            if response.status_code != 200:
                return None

            data = response.text.strip()
            if not data or '="' not in data:
                return None

            # 解析新浪返回的 CSV 格式
            # 格式: var hq_str_sh600519="名称,开盘,昨收,当前,最高,最低,..."
            parts = data.split('="')
            if len(parts) < 2:
                return None

            values = parts[1].strip('"').split(',')
            if len(values) < 9:
                return None

            name = values[0]
            open_price = float(values[1]) if values[1] else 0.0
            pre_close = float(values[2]) if values[2] else 0.0
            current = float(values[3]) if values[3] else 0.0
            high = float(values[4]) if values[4] else 0.0
            low = float(values[5]) if values[5] else 0.0
            bid_price_1 = float(values[6]) if values[6] else 0.0
            ask_price_1 = float(values[7]) if values[7] else 0.0
            volume = int(values[8]) if values[8] else 0

            # 计算涨跌
            change = current - pre_close
            percent = change / pre_close if pre_close != 0 else 0.0

            # 解析五档数据
            # Sina 格式: [10]=买一量, [11]=买一价, [12]=买二量, [13]=买二价, ...
            #           [20]=卖一量, [21]=卖一价, [22]=卖二量, [23]=卖二价, ...
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []

            if len(values) >= 22:
                # 五档买量和买价 (量在前，价在后)
                for i in range(5):
                    idx = 10 + i * 2
                    if idx < len(values) and values[idx]:
                        bid_volumes.append(int(float(values[idx])))  # 量
                    if idx + 1 < len(values) and values[idx + 1]:
                        bid_prices.append(float(values[idx + 1]))     # 价

                # 五档卖量和卖价 (量在前，价在后)
                for i in range(5):
                    idx = 20 + i * 2
                    if idx < len(values) and values[idx]:
                        ask_volumes.append(int(float(values[idx])))   # 量
                    if idx + 1 < len(values) and values[idx + 1]:
                        ask_prices.append(float(values[idx + 1]))     # 价

            return Quote(
                symbol=symbol,
                name=name,
                price=current,
                open_price=open_price,
                high=high,
                low=low,
                pre_close=pre_close,
                change=change,
                percent=percent,
                volume=volume,
                amount=float(values[9]) if len(values) > 9 and values[9] else 0.0,  # 成交额
                bid_price=bid_prices,
                bid_volume=bid_volumes,
                ask_price=ask_prices,
                ask_volume=ask_volumes,
                timestamp=datetime.now()
            )

        except Exception as e:
            raise DataSourceError("sina", f"Failed to get realtime: {e}", e)

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        quotes = []

        try:
            sina_symbols = [self._format_symbol(s) for s in symbols]
            url = f"{self.base_url}{','.join(sina_symbols)}"

            # 必须添加 Referer 头才能访问
            headers = {"Referer": "https://finance.sina.com.cn"}
            response = self._session.get(url, timeout=self.timeout * 2, headers=headers)  # 批量查询增加超时
            response.encoding = 'gbk'

            if response.status_code != 200:
                return quotes

            lines = response.text.strip().split('\n')

            for line in lines:
                if not line or '="' not in line:
                    continue

                parts = line.split('="')
                if len(parts) < 2:
                    continue

                # 提取股票代码
                symbol_part = parts[0].replace('var hq_str_', '')
                symbol = self._parse_symbol(symbol_part)

                values = parts[1].strip('"').split(',')
                if len(values) < 9:
                    continue

                # 解析 OHLC
                name = values[0]
                open_price = float(values[1]) if values[1] else 0.0
                current = float(values[3]) if values[3] else 0.0
                high = float(values[4]) if values[4] else 0.0
                low = float(values[5]) if values[5] else 0.0
                pre_close = float(values[2]) if values[2] else 0.0
                volume = int(values[8]) if values[8] else 0
                amount = float(values[9]) if len(values) > 9 and values[9] else 0.0
                change = current - pre_close
                percent = change / pre_close if pre_close != 0 else 0.0

                quote = Quote(
                    symbol=symbol,
                    name=name,
                    price=current,
                    open_price=open_price,
                    high=high,
                    low=low,
                    pre_close=pre_close,
                    change=change,
                    percent=percent,
                    volume=volume,
                    amount=amount,
                    bid_price=[],
                    bid_volume=[],
                    ask_price=[],
                    ask_volume=[],
                    timestamp=datetime.now()
                )
                quotes.append(quote)

        except Exception as e:
            raise DataSourceError("sina", f"Failed to batch get realtime: {e}", e)

        return quotes

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """获取K线数据（新浪限制较多，仅支持近期数据）"""
        try:
            if interval == "1d":
                # 日线数据
                url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
                params = {
                    'symbol': self._format_symbol_kline(symbol),
                    'scale': '240',  # 日线
                    'ma': 'no',
                    'datalen': '1024'  # 最多1024条
                }

                response = self._session.get(url, params=params, timeout=self.timeout)
                if response.status_code != 200:
                    return []

                data = response.json()
                if not isinstance(data, list):
                    return []

                klines = []
                for item in data:
                    try:
                        dt = datetime.strptime(item['day'], '%Y-%m-%d')
                        kline = KLine(
                            symbol=symbol,
                            datetime=dt,
                            open_price=float(item['open']),
                            high=float(item['high']),
                            low=float(item['low']),
                            close=float(item['close']),
                            volume=int(item['vol']),
                            amount=float(item['amount']),
                            turnover=None
                        )
                        klines.append(kline)
                    except (KeyError, ValueError):
                        continue

                return klines

            else:
                logger.debug(f"SinaFinance minute KLine not fully supported for {interval}")
                return []

        except Exception as e:
            raise DataSourceError("sina", f"Failed to get kline: {e}", e)

    def get_balance_sheet(self, symbol: str, year: int, quarter: int) -> Optional[BalanceSheet]:
        logger.warning("SinaFinance balance sheet not supported")
        return None

    def get_income_statement(self, symbol: str, year: int, quarter: int) -> Optional[IncomeStatement]:
        logger.warning("SinaFinance income statement not supported")
        return None

    def get_cash_flow_statement(self, symbol: str, year: int, quarter: int) -> Optional[CashFlowStatement]:
        logger.warning("SinaFinance cash flow statement not supported")
        return None

    def get_financial_indicators(self, symbol: str, year: int, quarter: int) -> Dict[str, float]:
        """
        获取财务指标

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            指标字典 {"roe": 0.15, "gross_margin": 0.4, ...}
        """
        logger.warning("SinaFinance financial indicators not supported")
        return {}

    def get_stock_list(self) -> List[Dict]:
        """获取股票列表 - Sina 不支持"""
        logger.warning("SinaFinance stock list not supported")
        return []

    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """获取股票详情 - Sina 不支持"""
        logger.warning("SinaFinance stock detail not supported")
        return None

    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取技术指标 - Sina 不支持"""
        logger.warning("SinaFinance tech indicators not supported")
        return []

    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取资金流向 - Sina 不支持"""
        logger.warning("SinaFinance fund flows not supported")
        return []

    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取龙虎榜 - Sina 不支持"""
        logger.warning("SinaFinance dragon tiger not supported")
        return []

    def get_valuation(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取估值指标 - Sina 不支持"""
        logger.warning("SinaFinance valuation not supported")
        return []

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取每股指标 - Sina 不支持"""
        logger.warning("SinaFinance per share indicators not supported")
        return []

    def get_osc_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取超买超卖指标 - Sina 不支持"""
        logger.warning("SinaFinance osc indicators not supported")
        return []

    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取量价指标 - Sina 不支持"""
        logger.warning("SinaFinance price vol indicators not supported")
        return []

    def get_limit_up_down(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取涨跌停 - Sina 不支持"""
        logger.warning("SinaFinance limit up down not supported")
        return []

    def get_turnover_rates(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取换手率 - Sina 不支持"""
        logger.warning("SinaFinance turnover rates not supported")
        return []

    def get_fund_quotes(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取基金净值 - Sina 不支持"""
        logger.warning("SinaFinance fund quotes not supported")
        return []

    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取杜邦分析 - Sina 不支持"""
        logger.warning("SinaFinance dupont analysis not supported")
        return []

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为新浪格式

        新浪格式: sh600519 (沪市) 或 sz000001 (深市)

        Args:
            symbol: 标准股票代码 (如 "600519")

        Returns:
            新浪格式代码 (如 "sh600519" 或 "sz000001")

        Examples:
            >>> adapter._format_symbol("600519")
            'sh600519'
            >>> adapter._format_symbol("000001")
            'sz000001'
        """
        if symbol.startswith(('6', '9', '7')):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"

    def _parse_symbol(self, sina_code: str) -> str:
        """
        从新浪代码解析股票代码

        新浪格式: sh600519 -> 600519

        Args:
            sina_code: 新浪格式的股票代码 (如 "sh600519")

        Returns:
            标准股票代码 (如 "600519")

        Examples:
            >>> adapter._parse_symbol("sh600519")
            '600519'
            >>> adapter._parse_symbol("sz000001")
            '000001'
        """
        if sina_code.startswith(('sh', 'sz')):
            return sina_code[2:]
        return sina_code

    def _format_symbol_kline(self, symbol: str) -> str:
        """
        格式化股票代码为K线接口格式

        K线格式: sh0000001 或 sz0000001

        Args:
            symbol: 标准股票代码 (如 "600519")

        Returns:
            K线接口格式代码 (如 "sh600519" 或 "sz000001")

        Examples:
            >>> adapter._format_symbol_kline("600519")
            'sh600519'
            >>> adapter._format_symbol_kline("000001")
            'sz000001'
        """
        if symbol.startswith(('6', '9', '7')):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"
