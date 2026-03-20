"""
Tushare Pro 数据源适配器
"""

import tushare as ts
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError
import pandas as pd

logger = logging.getLogger(__name__)


class TushareAdapter(DataSourceAdapter):
    """
    Tushare Pro 数据源适配器

    官网: https://tushare.pro
    特点: 数据规范、稳定、基本面数据强
    限制: 需要 Token，高频受限
    """

    def __init__(self, token: str, timeout: int = 10):
        """
        Args:
            token: Tushare API Token
            timeout: 超时时间（秒）
        """
        super().__init__()
        self.token = token
        self.timeout = timeout
        self.pro = ts.pro_api(token)
        logger.info("TushareAdapter initialized")

    @property
    def name(self) -> str:
        return "tushare"

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            # Tushare 的 daily_basic 提供当日行情
            ts_code = self._format_symbol(symbol)
            today = datetime.now().strftime('%Y%m%d')

            df = self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=today
            )

            if len(df) == 0:
                logger.warning(f"No realtime data found for {symbol}")
                return None

            row = df.iloc[0]

            return Quote(
                symbol=symbol,
                price=float(row['close']),
                change=float(row['close']) - float(row['pre_close']),
                percent=(float(row['close']) - float(row['pre_close'])) / float(row['pre_close']),
                volume=int(row['volume']) * 100,  # 手 -> 股
                amount=float(row['amount']) * 1000,  # 千元 -> 元
                bid_price=[],
                bid_volume=[],
                ask_price=[],
                ask_volume=[],
                timestamp=datetime.now()
            )

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get realtime: {e}", e)

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        quotes = []

        try:
            # Tushare 支持批量查询
            ts_codes = [self._format_symbol(s) for s in symbols]
            ts_codes_str = ','.join(ts_codes)
            today = datetime.now().strftime('%Y%m%d')

            df = self.pro.daily_basic(
                ts_code=ts_codes_str,
                trade_date=today
            )

            for _, row in df.iterrows():
                symbol = self._parse_symbol(row['ts_code'])
                quote = Quote(
                    symbol=symbol,
                    price=float(row['close']),
                    change=float(row['close']) - float(row['pre_close']),
                    percent=(float(row['close']) - float(row['pre_close'])) / float(row['pre_close']),
                    volume=int(row['volume']) * 100,
                    amount=float(row['amount']) * 1000,
                    bid_price=[],
                    bid_volume=[],
                    ask_price=[],
                    ask_volume=[],
                    timestamp=datetime.now()
                )
                quotes.append(quote)

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to batch get realtime: {e}", e)

        return quotes

    def get_kline(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = "",
        end_date: str = ""
    ) -> List[KLine]:
        """获取K线数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 转换日期格式 YYYYMMDD
            start_date_fmt = start_date.replace('-', '') if start_date else ''
            end_date_fmt = end_date.replace('-', '') if end_date else ''

            # Tushare 支持不同周期
            if interval == "1d":
                # 日线
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date_fmt,
                    end_date=end_date_fmt
                )
            elif interval in ["1w", "1M"]:
                # 周线/月线
                freq = "W" if interval == "1w" else "M"
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date_fmt,
                    end_date=end_date_fmt
                )
                # 需要自己按周/月聚合
            else:
                # 分钟线需要使用其他接口
                logger.warning(f"Minute interval {interval} not fully supported by Tushare")
                return []

            klines = []
            for _, row in df.iterrows():
                # 日期格式 "20230101" -> datetime
                try:
                    dt = datetime.strptime(row['trade_date'], '%Y%m%d')
                except:
                    dt = datetime.now()

                kline = KLine(
                    symbol=symbol,
                    datetime=dt,
                    open_price=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['vol']) * 100,  # 手 -> 股
                    amount=float(row['amount']) * 1000,  # 千元 -> 元
                    turnover=None
                )
                klines.append(kline)

            return klines

        except Exception as e:
            raise DataSourceError("tushare", f"Failed to get kline: {e}", e)

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        try:
            ts_code = self._format_symbol(symbol)

            # Tushare 的 period 格式: YYYYMMDD (如 20230331 表示 2023年一季度)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.balancesheet_vip(
                ts_code=ts_code,
                period=period,
                fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_assets,total_liab,total_hldr_eqy_inc_min_int'
            )

            if len(df) == 0:
                logger.warning(f"No balance sheet found for {symbol} {year}Q{quarter}")
                return None

            row = df.iloc[0]

            return BalanceSheet(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                total_assets=float(row['total_assets']) if row['total_assets'] else 0.0,
                total_liabilities=float(row['total_liab']) if row['total_liab'] else 0.0,
                shareholders_equity=float(row['total_hldr_eqy_inc_min_int']) if row['total_hldr_eqy_inc_min_int'] else 0.0
            )

        except Exception as e:
            logger.warning(f"Tushare balance sheet not available (need VIP): {e}")
            return None

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """获取利润表"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.income_vip(
                ts_code=ts_code,
                period=period,
                fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,revenue,n_income,basic_eps'
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]

            return IncomeStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                revenue=float(row['revenue']) if row['revenue'] else 0.0,
                net_profit=float(row['n_income']) if row['n_income'] else 0.0,
                eps=float(row['basic_eps']) if row['basic_eps'] else 0.0
            )

        except Exception as e:
            logger.warning(f"Tushare income statement not available (need VIP): {e}")
            return None

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """获取现金流量表"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.cashflow_vip(
                ts_code=ts_code,
                period=period,
                fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,net_cashflow_oper_act,net_cashflow_inv_act,net_cashflow_fnc_act'
            )

            if len(df) == 0:
                return None

            row = df.iloc[0]

            return CashFlowStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=row['end_date'],
                operating_cash_flow=float(row['net_cashflow_oper_act']) if row['net_cashflow_oper_act'] else 0.0,
                investing_cash_flow=float(row['net_cashflow_inv_act']) if row['net_cashflow_inv_act'] else 0.0,
                financing_cash_flow=float(row['net_cashflow_fnc_act']) if row['net_cashflow_fnc_act'] else 0.0
            )

        except Exception as e:
            logger.warning(f"Tushare cash flow not available (need VIP): {e}")
            return None

    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """获取财务指标"""
        try:
            ts_code = self._format_symbol(symbol)
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            period = f"{year}{quarter_map[quarter]}"

            df = self.pro.fina_indicator(
                ts_code=ts_code,
                period=period
            )

            if len(df) == 0:
                return {}

            row = df.iloc[0]

            return {
                "roe": float(row['roe']) if row.get('roe') and not row['roe'] is None else 0.0,
                "gross_margin": float(row['grossprofit_margin']) if row.get('grossprofit_margin') else 0.0,
                "net_profit_margin": float(row['netprofit_margin']) if row.get('netprofit_margin') else 0.0,
                "asset_liability_ratio": float(row['asset_liab_ratio']) if row.get('asset_liab_ratio') else 0.0
            }

        except Exception as e:
            logger.warning(f"Tushare financial indicators not available: {e}")
            return {}

    def get_stock_list(self) -> List[Dict]:
        """
        获取股票列表

        使用 Tushare 的 stock_basic 接口
        """
        try:
            # 获取基础股票列表
            df = self.pro.stock_basic(
                fields='ts_code,symbol,name,area,industry,list_date,market'
            )

            stock_list = []
            for _, row in df.iterrows():
                # 转换 Tushare 格式到标准格式
                ts_code = row['ts_code']  # 如: 600519.SH
                symbol = row['symbol']     # 如: 600519

                stock = {
                    "symbol": symbol,
                    "name": row['name'],
                    "exchange": "SH" if ts_code.endswith(".SH") else "SZ",
                    "list_date": row['list_date'],  # YYYYMMDD 格式
                    "industry": row['industry'] if row['industry'] else None,
                    "region": row['area'] if row['area'] else None,
                    "market": row['market']  # 主板/创业板/科创板等
                }
                stock_list.append(stock)

            logger.info(f"Fetched {len(stock_list)} stocks from Tushare")
            return stock_list

        except Exception as e:
            logger.error(f"Failed to get stock list from Tushare: {e}")
            raise DataSourceError("tushare", f"Failed to get stock list: {e}", e)

    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """
        获取股票详细信息

        使用 Tushare 的 stock_basic 接口
        """
        try:
            ts_code = self._format_symbol(symbol)

            df = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,list_date,total_share,float_share'
            )

            if len(df) == 0:
                logger.warning(f"No stock detail found for {symbol}")
                return None

            row = df.iloc[0]

            return {
                "symbol": row['symbol'],
                "name": row['name'],
                "exchange": "SH" if ts_code.endswith(".SH") else "SZ",
                "list_date": row['list_date'],
                "delist_date": None,  # Tushare 不直接提供退市日期
                "total_shares": int(row['total_share'] * 10000) if row['total_share'] else None,  # 万股 -> 股
                "float_shares": int(row['float_share'] * 10000) if row['float_share'] else None,  # 万股 -> 股
                "industry": row['industry'] if row['industry'] else None,
                "concept": None,  # Tushare 不直接提供概念
                "region": row['area'] if row['area'] else None
            }

        except Exception as e:
            logger.error(f"Failed to get stock detail for {symbol}: {e}")
            raise DataSourceError("tushare", f"Failed to get stock detail: {e}", e)

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为 Tushare 格式

        Tushare 格式: 600519.SH (沪市) 或 000001.SZ (深市)
        """
        if symbol.startswith(('6', '9', '7')):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"

    def _parse_symbol(self, ts_code: str) -> str:
        """
        从 Tushare 代码解析股票代码

        Tushare 格式: 600519.SH -> 600519
        """
        return ts_code.split('.')[0]

    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取技术指标数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取量价因子数据（包含部分技术指标）
            df = self.pro.stk_factor(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "ma5": float(row.get('ma5', 0)) if not pd.isna(row.get('ma5', 0)) else None,
                    "ma10": float(row.get('ma10', 0)) if not pd.isna(row.get('ma10', 0)) else None,
                    "ma20": float(row.get('ma20', 0)) if not pd.isna(row.get('ma20', 0)) else None,
                    "macd": float(row.get('macd_dif', 0)) if not pd.isna(row.get('macd_dif', 0)) else None,
                    "macd_signal": float(row.get('macd_dea', 0)) if not pd.isna(row.get('macd_dea', 0)) else None,
                    "macd_hist": float(row.get('macd', 0)) if not pd.isna(row.get('macd', 0)) else None,
                    "rsi": None,  # Tushare stk_factor 可能不包含 RSI
                    "kdj_k": None,
                    "kdj_d": None,
                    "kdj_j": None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_tech_indicators failed for {symbol}: {e}")
            return []

    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取资金流向数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取个股资金流向
            df = self.pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "main_net_inflow": float(row.get('buy_elg_amount', 0) - row.get('sell_elg_amount', 0)) if not pd.isna(row.get('buy_elg_amount', 0)) else 0.0,
                    "retail_net_inflow": float(row.get('buy_sm_amount', 0) - row.get('sell_sm_amount', 0)) if not pd.isna(row.get('buy_sm_amount', 0)) else 0.0,
                    "large_order_net_inflow": float(row.get('buy_lg_amount', 0) - row.get('sell_lg_amount', 0)) if not pd.isna(row.get('buy_lg_amount', 0)) else 0.0,
                    "main_net_inflow_rate": None,
                    "retail_net_inflow_rate": None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_fund_flows failed for {symbol}: {e}")
            return []

    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取龙虎榜数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取龙虎榜每日明细
            df = self.pro.top_list(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "buy_departments": [],
                    "sell_departments": [],
                    "buy_amount": float(row.get('buy', 0)) if not pd.isna(row.get('buy', 0)) else 0.0,
                    "sell_amount": float(row.get('sell', 0)) if not pd.isna(row.get('sell', 0)) else 0.0,
                    "reason": row.get('reason', '')
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_dragon_tiger failed for {symbol}: {e}")
            return []

    def get_valuation(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取估值指标数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取每日指标（包含估值数据）
            df = self.pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "pe_ttm": float(row.get('pe_ttm', 0)) if not pd.isna(row.get('pe_ttm', 0)) else None,
                    "pe_lyr": float(row.get('pe', 0)) if not pd.isna(row.get('pe', 0)) else None,
                    "pb": float(row.get('pb', 0)) if not pd.isna(row.get('pb', 0)) else None,
                    "ps": float(row.get('ps_ttm', 0)) if not pd.isna(row.get('ps_ttm', 0)) else None,
                    "total_mv": float(row.get('total_mv', 0)) if not pd.isna(row.get('total_mv', 0)) else None  # 总市值（万元）
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_valuation failed for {symbol}: {e}")
            return []

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取每股指标数据"""
        try:
            # 从财务指标中提取每股数据
            ts_code = self._format_symbol(symbol)

            df = self.pro.fina_indicator(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('end_date', ''),
                    "eps": float(row.get('eps', 0)) if not pd.isna(row.get('eps', 0)) else 0.0,
                    "bvps": float(row.get('bps', 0)) if not pd.isna(row.get('bps', 0)) else 0.0,
                    "cfps": float(row.get('cfps', 0)) if not pd.isna(row.get('cfps', 0)) else 0.0,
                    "dps": float(row.get('diluted_eps', 0)) if not pd.isna(row.get('diluted_eps', 0)) else 0.0
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_per_share_indicators failed for {symbol}: {e}")
            return []

    def get_osc_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取超买超卖指标数据 - 部分支持"""
        logger.warning(f"Tushare get_osc_indicators has limited support for {symbol}")
        return []

    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取量价指标数据 - 部分支持"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取量价因子
            df = self.pro.stk_factor(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "obv": None,  # Tushare 可能不直接提供
                    "vr": float(row.get('volume_ratio', 0)) if not pd.isna(row.get('volume_ratio', 0)) else None,
                    "mfi": None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_price_vol_ind failed for {symbol}: {e}")
            return []

    def get_limit_up_down(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取涨跌停数据"""
        try:
            # 获取涨跌停列表
            df = self.pro.limit_list_d(
                trade_date=start_date.replace('-', '') if start_date else None,
                ts_code=self._format_symbol(symbol) if symbol else None,
                limit_type=None  # U: 涨停, D: 跌停, Z: 涨跌停
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "is_limit_up": row.get('limit_type') == 'U',
                    "is_limit_down": row.get('limit_type') == 'D',
                    "limit_up_times": 1 if row.get('limit_type') == 'U' else 0,
                    "limit_down_times": 1 if row.get('limit_type') == 'D' else 0,
                    "consecutive_limit_up": int(row.get('up_stat', '0').split('/')[0]) if row.get('up_stat') else 0
                }
                results.append(result)

            # 过滤结束日期
            if end_date:
                filtered = []
                for item in results:
                    if item['date'] <= end_date.replace('-', ''):
                        filtered.append(item)
                results = filtered

            return results

        except Exception as e:
            logger.error(f"Tushare get_limit_up_down failed for {symbol}: {e}")
            return []

    def get_turnover_rates(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取换手率数据"""
        try:
            ts_code = self._format_symbol(symbol)

            # 获取每日指标（包含换手率）
            df = self.pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('trade_date', ''),
                    "turnover_rate": float(row.get('turnover_rate', 0)) if not pd.isna(row.get('turnover_rate', 0)) else None,
                    "volume_ratio": float(row.get('volume_ratio', 0)) if not pd.isna(row.get('volume_ratio', 0)) else None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_turnover_rates failed for {symbol}: {e}")
            return []

    def get_fund_quotes(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取基金净值数据 - 有限支持"""
        try:
            # 获取基金净值
            df = self.pro.fund_nav(
                ts_code=symbol,
                start_date=start_date.replace('-', '') if start_date else None,
                end_date=end_date.replace('-', '') if end_date else None
            )

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('nav_date', ''),
                    "nav": float(row.get('unit_nav', 0)) if not pd.isna(row.get('unit_nav', 0)) else 0.0,
                    "accumulated_nav": float(row.get('accum_nav', 0)) if not pd.isna(row.get('accum_nav', 0)) else 0.0,
                    "daily_return": float(row.get('daily_return', 0)) / 100 if not pd.isna(row.get('daily_return', 0)) else 0.0
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Tushare get_fund_quotes failed for {symbol}: {e}")
            return []

    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """杜邦分析 - Tushare 不支持"""
        logger.warning(f"Tushare does not support dupont analysis for {symbol}")
        raise NotImplementedError(
            "Tushare does not support dupont analysis. "
            "Use Investoday data source instead."
        )
