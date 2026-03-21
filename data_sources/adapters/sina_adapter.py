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
        logger.info("SinaAdapter initialized")

    @property
    def name(self) -> str:
        return "sina"

    @property
    def priority(self) -> int:
        return self._priority

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            sina_symbol = self._format_symbol(symbol)
            url = f"{self.base_url}{sina_symbol}"

            response = requests.get(url, timeout=self.timeout)
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
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []

            if len(values) >= 22:
                # 五档买价和买量
                for i in range(5):
                    idx = 10 + i * 2
                    if idx < len(values) and values[idx]:
                        bid_prices.append(float(values[idx]))
                    if idx + 1 < len(values) and values[idx + 1]:
                        bid_volumes.append(int(values[idx + 1]))

                # 五档卖价和卖量
                for i in range(5):
                    idx = 20 + i * 2
                    if idx < len(values) and values[idx]:
                        ask_prices.append(float(values[idx]))
                    if idx + 1 < len(values) and values[idx + 1]:
                        ask_volumes.append(int(values[idx + 1]))

            return Quote(
                symbol=symbol,
                price=current,
                change=change,
                percent=percent,
                volume=volume,
                amount=0.0,  # 新浪不直接提供成交额
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

            response = requests.get(url, timeout=self.timeout * 2)  # 批量查询增加超时
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

                current = float(values[3]) if values[3] else 0.0
                pre_close = float(values[2]) if values[2] else 0.0
                change = current - pre_close
                percent = change / pre_close if pre_close != 0 else 0.0

                quote = Quote(
                    symbol=symbol,
                    price=current,
                    change=change,
                    percent=percent,
                    volume=int(values[8]) if values[8] else 0,
                    amount=0.0,
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

                response = requests.get(url, params=params, timeout=self.timeout)
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
                logger.warning(f"SinaFinance minute KLine not fully supported for {interval}")
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

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为新浪格式

        新浪格式: sh600519 (沪市) 或 sz000001 (深市)
        """
        if symbol.startswith(('6', '9', '7')):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"

    def _parse_symbol(self, sina_code: str) -> str:
        """
        从新浪代码解析股票代码

        新浪格式: sh600519 -> 600519
        """
        if sina_code.startswith(('sh', 'sz')):
            return sina_code[2:]
        return sina_code

    def _format_symbol_kline(self, symbol: str) -> str:
        """
        格式化股票代码为K线接口格式

        K线格式: sh0000001 或 sz0000001
        """
        if symbol.startswith(('6', '9', '7')):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"
