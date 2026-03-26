"""
Investoday 数据源适配器

今日投资 (Investoday) 是专业的金融数据平台，提供 186+ 个金融数据接口，
覆盖沪深京股票、基金、港股等数据，具有数据质量高、接口丰富等优势。

官网: https://data-api.investoday.net
特点: 专业金融数据、丰富的技术指标和资金流向数据、实体识别等 AI 友好功能
认证: 环境变量 INVESTODAY_API_KEY
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError, DataSourceConfigError


logger = logging.getLogger(__name__)


class InvestodayAdapter(DataSourceAdapter):
    """
    今日投资数据源适配器

    特性:
    - 环境变量认证 (INVESTODAY_API_KEY)
    - 20个核心+特色接口实现
    - 遵循 DataSourceAdapter 统一接口规范
    - 支持配置优先级和超时控制
    """

    def __init__(self, timeout: int = 10):
        """
        初始化 Investoday 适配器

        Args:
            timeout: 超时时间（秒），默认 10 秒

        Raises:
            DataSourceConfigError: 缺少 API Key 配置
        """
        super().__init__()
        self.base_url = "https://data-api.investoday.net/data"
        self.timeout = timeout

        # 获取 API Key
        self.api_key = os.environ.get("INVESTODAY_API_KEY")
        if not self.api_key:
            raise DataSourceConfigError(
                "investoday",
                "Missing INVESTODAY_API_KEY environment variable"
            )

        # 创建 HTTP 会话
        # Investoday 使用 apiKey header 认证，不是 Authorization Bearer
        self._session = requests.Session()
        self._session.headers.update({
            "apiKey": self.api_key,
            "Content-Type": "application/json"
        })

        logger.info("InvestodayAdapter initialized")

    def is_available(self) -> bool:
        """
        Check if Investoday API is available

        Returns:
            True if API key is valid and service is reachable
        """
        try:
            # Test API connectivity
            self._call_api(
                endpoint="stock-quote/realtime",
                method="GET",
                params={"stockCode": "600519"}
            )
            return True
        except Exception as e:
            logger.error(f"Investoday health check failed: {e}")
            return False

    @property
    def name(self) -> str:
        """数据源唯一标识"""
        return "investoday"

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        通用 API 调用方法

        Args:
            endpoint: 接口路径 (如 "stock-quote/realtime")
            method: HTTP 方法 ("GET" 或 "POST")
            params: GET 参数 (query string)
            json_data: POST 数据 (JSON body)

        Returns:
            API 返回的 data 字段

        Raises:
            DataSourceError: API 调用失败或返回错误
        """
        url = f"{self.base_url}/{endpoint}"

        # 确保 params 是字典
        if params is None:
            params = {}

        try:
            if method.upper() == "POST":
                response = self._session.post(
                    url,
                    params=params,
                    json=json_data,
                    timeout=self.timeout
                )
            else:
                response = self._session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

            # 检查 HTTP 状态码
            response.raise_for_status()

            # 解析 JSON 响应
            result = response.json()

            # 检查 API 响应状态
            # Investoday 返回 code: 0 表示成功，其他值表示失败
            code = result.get("code", -1)
            if code != 0:
                error_msg = result.get("message", "Unknown API error")
                raise DataSourceError(
                    "investoday",
                    f"API call failed: {error_msg}",
                    original_error=None
                )

            return result.get("data", {})

        except requests.exceptions.Timeout as e:
            raise DataSourceError(
                "investoday",
                f"Request timeout after {self.timeout} seconds",
                original_error=e
            )
        except requests.exceptions.RequestException as e:
            raise DataSourceError(
                "investoday",
                f"HTTP request failed: {e}",
                original_error=e
            )
        except ValueError as e:
            raise DataSourceError(
                "investoday",
                f"Invalid JSON response: {e}",
                original_error=e
            )
        except Exception as e:
            raise DataSourceError(
                "investoday",
                f"Unexpected error in API call: {e}",
                original_error=e
            )

    def _get_report_date(self, year: int, quarter: int) -> str:
        """
        根据年份和季度推导报告期日期

        Args:
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            报告期日期字符串 "YYYY-MM-DD"

        Raises:
            ValueError: 季度不在有效范围内
        """
        if quarter < 1 or quarter > 4:
            raise ValueError(f"Quarter must be between 1 and 4, got {quarter}")

        # 季度对应的报告期日期
        quarter_dates = {
            1: f"{year}-03-31",
            2: f"{year}-06-30",
            3: f"{year}-09-30",
            4: f"{year}-12-31"
        }

        return quarter_dates[quarter]

    def _parse_quote(self, data: Dict[str, Any]) -> Quote:
        """
        解析实时行情数据

        Args:
            data: Investoday API 返回的实时行情数据

        Returns:
            Quote 对象
        """
        symbol = data.get("stockCode", "")
        name = data.get("stockName", "")
        price = float(data.get("currentPrice", 0) or 0)
        open_price = float(data.get("openPrice", 0) or 0)
        high = float(data.get("highPrice", 0) or 0)
        low = float(data.get("lowPrice", 0) or 0)
        pre_close = float(data.get("closePriceYDay", 0) or 0)
        change_pct = float(data.get("changeRatio", 0) or 0)  # 涨跌幅（小数形式）
        change = price - pre_close if pre_close > 0 else 0  # 涨跌额
        volume = int(data.get("dealStockAmount", 0) or 0)  # 成交量（手）
        amount = float(data.get("dealMoney", 0) or 0)  # 成交额

        # Investoday 可能不提供买卖盘数据，使用空列表
        bid_price = []
        bid_volume = []
        ask_price = []
        ask_volume = []

        return Quote(
            symbol=symbol,
            name=name,
            price=price,
            open_price=open_price,
            high=high,
            low=low,
            pre_close=pre_close,
            change=change,
            percent=change_pct,
            volume=volume,
            amount=amount,
            bid_price=bid_price,
            bid_volume=bid_volume,
            ask_price=ask_price,
            ask_volume=ask_volume,
            timestamp=datetime.now()
        )

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
        try:
            data = self._call_api(
                endpoint="stock-quote/realtime",
                method="GET",
                params={"stockCode": symbol}
            )
            return self._parse_quote(data)
        except Exception as e:
            logger.error(f"Investoday get_realtime failed for {symbol}: {e}")
            return None

    def batch_get_realtime(self, symbols: list[str]) -> list[Quote]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            Quote 对象列表 (可能为空)
        """
        try:
            # Use Investoday's batch endpoint if available
            # Otherwise fall back to sequential calls
            results = []

            # Attempt batch API call
            try:
                data = self._call_api(
                    endpoint="stock-quote/realtime-batch",
                    method="POST",
                    json_data={"stockCodes": symbols}
                )

                items = data.get("items", [])
                for item in items:
                    quote = self._parse_quote(item)
                    results.append(quote)

                return results

            except DataSourceError:
                # Batch API not available, fall back to sequential
                logger.info("Batch API not available, falling back to sequential calls")
                for symbol in symbols:
                    quote = self.get_realtime(symbol)
                    if quote:
                        results.append(quote)
                return results

        except Exception as e:
            logger.error(f"Investoday batch_get_realtime failed: {e}")
            return []

    def _parse_kline(self, data: Dict[str, Any]) -> KLine:
        """
        解析K线数据

        Args:
            data: Investoday API 返回的K线数据项

        Returns:
            KLine 对象
        """
        symbol = data.get("stockCode", "")
        datetime_str = data.get("tradeDate", "")
        # Investoday 返回格式: "2025-03-25 00:00:00"，需要截取日期部分
        if " " in datetime_str:
            datetime_str = datetime_str.split(" ")[0]
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d")

        open_price = float(data.get("openPrice", 0) or 0)
        high = float(data.get("highPrice", 0) or 0)  # Investoday 用 highPrice，不是 highestPrice
        low = float(data.get("lowPrice", 0) or 0)    # Investoday 用 lowPrice，不是 lowestPrice
        close = float(data.get("closePrice", 0) or 0)
        volume = int(data.get("volume", 0) or 0)
        amount = float(data.get("amount", 0) or 0)
        turnover = float(data.get("turnover", 0)) if data.get("turnover") is not None else None

        return KLine(
            symbol=symbol,
            datetime=datetime_obj,
            open_price=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            amount=amount,
            turnover=turnover
        )

    def get_kline(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> list[KLine]:
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
        all_klines = []
        page_num = 1
        page_size = 500

        while True:
            try:
                data = self._call_api(
                    endpoint="stock/adjusted-quotes",
                    method="GET",
                    params={
                        "stockCode": symbol,
                        "beginDate": start_date,
                        "endDate": end_date,
                        "pageNum": page_num,
                        "pageSize": page_size
                    }
                )

                # Investoday 返回的 data 直接是列表，不是 {items: [...]}
                items = data if isinstance(data, list) else data.get("items", [])
                if not items:
                    break

                for item in items:
                    kline = self._parse_kline(item)
                    all_klines.append(kline)

                if len(items) < page_size:
                    break
                page_num += 1

            except Exception as e:
                logger.error(f"Investoday get_kline failed for {symbol}: {e}")
                break

        return all_klines

    def _parse_balance_sheet(self, data: Dict[str, Any]) -> BalanceSheet:
        """
        解析资产负债表

        Args:
            data: Investoday API 返回的资产负债表数据

        Returns:
            BalanceSheet 对象
        """
        symbol = data.get("stockCode", "")
        year = int(data.get("reportYear", 0))
        quarter = int(data.get("reportQuarter", 0))
        report_date = data.get("reportDate", "")

        total_assets = float(data.get("totalAssets", 0))
        total_liabilities = float(data.get("totalLiabilities", 0))
        shareholders_equity = float(data.get("shareholdersEquity", 0))

        return BalanceSheet(
            symbol=symbol,
            year=year,
            quarter=quarter,
            report_date=report_date,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            shareholders_equity=shareholders_equity
        )

    def _parse_income_statement(self, data: Dict[str, Any]) -> IncomeStatement:
        """
        解析利润表

        Args:
            data: Investoday API 返回的利润表数据

        Returns:
            IncomeStatement 对象
        """
        symbol = data.get("stockCode", "")
        year = int(data.get("reportYear", 0))
        quarter = int(data.get("reportQuarter", 0))
        report_date = data.get("reportDate", "")

        revenue = float(data.get("revenue", 0))
        net_profit = float(data.get("netProfit", 0))
        eps = float(data.get("eps", 0))

        return IncomeStatement(
            symbol=symbol,
            year=year,
            quarter=quarter,
            report_date=report_date,
            revenue=revenue,
            net_profit=net_profit,
            eps=eps
        )

    def _parse_cash_flow_statement(self, data: Dict[str, Any]) -> CashFlowStatement:
        """
        解析现金流量表

        Args:
            data: Investoday API 返回的现金流量表数据

        Returns:
            CashFlowStatement 对象
        """
        symbol = data.get("stockCode", "")
        year = int(data.get("reportYear", 0))
        quarter = int(data.get("reportQuarter", 0))
        report_date = data.get("reportDate", "")

        operating_cash_flow = float(data.get("operatingCashFlow", 0))
        investing_cash_flow = float(data.get("investingCashFlow", 0))
        financing_cash_flow = float(data.get("financingCashFlow", 0))

        return CashFlowStatement(
            symbol=symbol,
            year=year,
            quarter=quarter,
            report_date=report_date,
            operating_cash_flow=operating_cash_flow,
            investing_cash_flow=investing_cash_flow,
            financing_cash_flow=financing_cash_flow
        )

    def _date_to_quarter(self, date_str: str) -> tuple[int, int]:
        """
        从日期字符串推导年份和季度

        Args:
            date_str: 日期字符串 "YYYY-MM-DD"

        Returns:
            (year, quarter) 元组
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year = dt.year
        month = dt.month

        if month in [1, 2, 3]:
            quarter = 1
        elif month in [4, 5, 6]:
            quarter = 2
        elif month in [7, 8, 9]:
            quarter = 3
        else:
            quarter = 4

        return year, quarter

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
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/balance-sheets",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_balance_sheet(items[0])
            return None
        except Exception as e:
            logger.error(f"Investoday get_balance_sheet failed for {symbol}: {e}")
            return None

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
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/income-statements",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_income_statement(items[0])
            return None
        except Exception as e:
            logger.error(f"Investoday get_income_statement failed for {symbol}: {e}")
            return None

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
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/cash-flows",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if items:
                return self._parse_cash_flow_statement(items[0])
            return None
        except Exception as e:
            logger.error(f"Investoday get_cash_flow_statement failed for {symbol}: {e}")
            return None

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
        try:
            report_date = self._get_report_date(year, quarter)

            data = self._call_api(
                endpoint="stock/financial-indicators",
                method="GET",
                params={
                    "stockCode": symbol,
                    "beginDate": report_date,
                    "endDate": report_date
                }
            )

            items = data.get("items", [])
            if not items:
                return {}

            # 提取常见财务指标
            item = items[0]
            indicators = {}

            # ROE (净资产收益率)
            if item.get("roe") is not None:
                indicators["roe"] = float(item["roe"])

            # 毛利率
            if item.get("grossMargin") is not None:
                indicators["gross_margin"] = float(item["grossMargin"])

            # 净利率
            if item.get("netProfitMargin") is not None:
                indicators["net_profit_margin"] = float(item["netProfitMargin"])

            # 资产负债率
            if item.get("assetLiabilityRatio") is not None:
                indicators["asset_liability_ratio"] = float(item["assetLiabilityRatio"])

            # EPS (每股收益)
            if item.get("eps") is not None:
                indicators["eps"] = float(item["eps"])

            return indicators

        except Exception as e:
            logger.error(f"Investoday get_financial_indicators failed for {symbol}: {e}")
            return {}

    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取技术指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            技术指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/tech-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_tech_indicators failed for {symbol}: {e}")
            return []

    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取资金流向数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            资金流向数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/fund-flows",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_fund_flows failed for {symbol}: {e}")
            return []

    def get_valuation(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取估值指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            估值指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/valuation",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_valuation failed for {symbol}: {e}")
            return []

    def get_financial_indicators_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取财务指标历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            财务指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/financial-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_financial_indicators_history failed for {symbol}: {e}")
            return []

    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取龙虎榜数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            龙虎榜数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/dragon-tiger",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_dragon_tiger failed for {symbol}: {e}")
            return []

    def entity_recognition(
        self,
        text: str
    ) -> dict:
        """
        实体识别 - 独家功能

        Args:
            text: 输入文本

        Returns:
            实体识别结果字典，失败返回空字典
        """
        try:
            data = self._call_api(
                endpoint="ai/entity-recognition",
                method="POST",
                json_data={"text": text}
            )
            return data
        except Exception as e:
            logger.error(f"Investoday entity_recognition failed: {e}")
            return {}

    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取杜邦分析数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            杜邦分析数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/dupont-analysis",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_dupont_analysis failed for {symbol}: {e}")
            return []

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取每股指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            每股指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/per-share-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_per_share_indicators failed for {symbol}: {e}")
            return []

    def get_osc_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取超买超卖指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            超买超卖指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/osc-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_osc_indicators failed for {symbol}: {e}")
            return []

    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取量价指标数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            量价指标数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/price-vol-indicators",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_price_vol_ind failed for {symbol}: {e}")
            return []

    def get_limit_up_down(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取涨跌停数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            涨跌停数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/limit-up-down",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_limit_up_down failed for {symbol}: {e}")
            return []

    def get_turnover_rates(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取换手率数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            换手率数据列表，失败返回空列表
        """
        try:
            params = {"stockCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="stock/turnover-rates",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_turnover_rates failed for {symbol}: {e}")
            return []

    def get_fund_quotes(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取基金净值数据

        Args:
            symbol: 基金代码
            start_date: 开始日期 "YYYY-MM-DD" (可选)
            end_date: 结束日期 "YYYY-MM-DD" (可选)

        Returns:
            基金净值数据列表，失败返回空列表
        """
        try:
            params = {"fundCode": symbol}
            if start_date:
                params["beginDate"] = start_date
            if end_date:
                params["endDate"] = end_date

            data = self._call_api(
                endpoint="fund/quotes",
                method="GET",
                params=params
            )
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Investoday get_fund_quotes failed for {symbol}: {e}")
            return []

    def search(
        self,
        query: str,
        page_num: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        综合搜索

        Args:
            query: 搜索关键词
            page_num: 页码，默认 1
            page_size: 每页数量，默认 20

        Returns:
            搜索结果字典，失败返回空字典
        """
        try:
            data = self._call_api(
                endpoint="search",
                method="GET",
                params={
                    "query": query,
                    "pageNum": page_num,
                    "pageSize": page_size
                }
            )
            return data
        except Exception as e:
            logger.error(f"Investoday search failed: {e}")
            return {}

    def get_stock_list(self) -> List[Dict]:
        """
        获取股票列表

        Returns:
            股票列表，每个元素包含股票代码、名称等信息
        """
        logger.warning("get_stock_list not implemented for Investoday")
        return []

    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """
        获取股票详细信息

        Args:
            symbol: 股票代码

        Returns:
            股票详细信息字典或 None
        """
        logger.warning(f"get_stock_detail not implemented for {symbol}")
        return None