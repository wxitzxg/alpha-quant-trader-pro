"""
AKShare 数据源适配器 - 完整扩展版
"""

import akshare as ak
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..base import DataSourceAdapter
from ..models import Quote, KLine, BalanceSheet, IncomeStatement, CashFlowStatement
from ..exceptions import DataSourceError

logger = logging.getLogger(__name__)


class AKShareAdapter(DataSourceAdapter):
    """
    AKShare 数据源适配器 - 完整扩展版

    官网: https://akshare.akfamily.xyz
    特点: 免费、覆盖广、特色数据丰富
    限制: 依赖源站变动、需频繁升级

    扩展功能:
    - 完整的基本面数据（资产负债表、利润表、现金流量表）
    - 技术指标（MA、MACD、KDJ、RSI等）
    - 资金流向数据
    - 龙虎榜数据
    - 涨跌停数据
    - 换手率数据
    - 股票列表和详情
    - 基金净值数据
    """

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout: 超时时间（秒）
        """
        super().__init__()
        self.timeout = timeout
        logger.info("AKShareAdapter initialized")

    @property
    def name(self) -> str:
        return "akshare"

    def get_realtime(self, symbol: str) -> Optional[Quote]:
        """获取实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == symbol]

            if len(stock_data) == 0:
                return None

            row = stock_data.iloc[0]

            return Quote(
                symbol=symbol,
                price=float(row['最新价']),
                change=float(row['涨跌额']),
                percent=float(row['涨跌幅']) / 100,
                volume=int(row['成交量']),
                amount=float(row['成交额']),
                bid_price=[],
                bid_volume=[],
                ask_price=[],
                ask_volume=[],
                timestamp=datetime.now()
            )

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to get realtime: {e}", e)

    def batch_get_realtime(self, symbols: List[str]) -> List[Quote]:
        """批量获取实时行情"""
        quotes = []

        try:
            df = ak.stock_zh_a_spot_em()

            for symbol in symbols:
                stock_data = df[df['代码'] == symbol]

                if len(stock_data) > 0:
                    row = stock_data.iloc[0]
                    quote = Quote(
                        symbol=symbol,
                        price=float(row['最新价']),
                        change=float(row['涨跌额']),
                        percent=float(row['涨跌幅']) / 100,
                        volume=int(row['成交量']),
                        amount=float(row['成交额']),
                        bid_price=[],
                        bid_volume=[],
                        ask_price=[],
                        ask_volume=[],
                        timestamp=datetime.now()
                    )
                    quotes.append(quote)

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to batch get realtime: {e}", e)

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
            if interval == "1d":
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', '') if start_date else "",
                    end_date=end_date.replace('-', '') if end_date else "",
                    adjust="qfq"
                )
            elif interval in ["1w", "1M"]:
                period = "weekly" if interval == "1w" else "monthly"
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period=period,
                    start_date=start_date.replace('-', '') if start_date else "",
                    end_date=end_date.replace('-', '') if end_date else "",
                    adjust="qfq"
                )
            else:
                period_map = {
                    "1m": "1",
                    "5m": "5",
                    "15m": "15",
                    "30m": "30",
                    "60m": "60"
                }
                period = period_map.get(interval, "1")
                df = ak.stock_zh_a_minute(
                    symbol=symbol,
                    period=period,
                    adjust="qfq"
                )

            klines = []
            for _, row in df.iterrows():
                if '日期' in row:
                    dt = datetime.strptime(row['日期'], '%Y-%m-%d')
                elif 'day' in row:
                    dt = datetime.strptime(row['day'], '%Y-%m-%d %H:%M:%S')
                else:
                    continue

                open_price = float(row['开盘']) if not isinstance(row['开盘'], str) else float(row['开盘'].replace(',', ''))
                high = float(row['最高']) if not isinstance(row['最高'], str) else float(row['最高'].replace(',', ''))
                low = float(row['最低']) if not isinstance(row['最低'], str) else float(row['最低'].replace(',', ''))
                close = float(row['收盘']) if not isinstance(row['收盘'], str) else float(row['收盘'].replace(',', ''))
                volume = int(row['成交量']) if not isinstance(row['成交量'], str) else int(row['成交量'].replace(',', ''))
                amount = float(row['成交额']) if not isinstance(row['成交额'], str) else float(row['成交额'].replace(',', ''))

                kline = KLine(
                    symbol=symbol,
                    datetime=dt,
                    open_price=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    amount=amount,
                    turnover=float(row['换手率']) if '换手率' in row and not isinstance(row['换手率'], str) else None
                )
                klines.append(kline)

            return klines

        except Exception as e:
            raise DataSourceError("akshare", f"Failed to get kline: {e}", e)

    def get_balance_sheet(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[BalanceSheet]:
        """获取资产负债表"""
        try:
            # 根据年份和季度构造报告期
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            report_period = f"{year}{quarter_map[quarter]}"

            # 获取资产负债表（按报告期）
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)

            # 查找对应报告期的数据
            if '报告期' in df.columns:
                df_filtered = df[df['报告期'] == report_period]
            elif 'REPORT_DATE' in df.columns:
                df_filtered = df[df['REPORT_DATE'].str.contains(str(year))]
            else:
                logger.warning(f"No balance sheet data found for {symbol} {year}Q{quarter}")
                return None

            if len(df_filtered) == 0:
                logger.warning(f"No balance sheet data found for {symbol} {year}Q{quarter}")
                return None

            row = df_filtered.iloc[0]

            return BalanceSheet(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=report_period,
                total_assets=float(row.get('资产总计', 0)) if not pd.isna(row.get('资产总计', 0)) else 0.0,
                total_liabilities=float(row.get('负债总计', 0)) if not pd.isna(row.get('负债总计', 0)) else 0.0,
                shareholders_equity=float(row.get('所有者权益合计', 0)) if not pd.isna(row.get('所有者权益合计', 0)) else 0.0
            )

        except Exception as e:
            logger.error(f"AKShare balance sheet failed for {symbol}: {e}")
            return None

    def get_income_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[IncomeStatement]:
        """获取利润表"""
        try:
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            report_period = f"{year}{quarter_map[quarter]}"

            # 财报类型
            # 1: 一季度报
            # 2: 二季度报
            # 3: 三季度报
            # 4: 年报
            report_type_map = {1: '1', 2: '2', 3: '3', 4: '4'}
            report_type = report_type_map[quarter]

            # 获取利润表
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)

            if '报告期' in df.columns:
                df_filtered = df[df['报告期'] == report_period]
            else:
                logger.warning(f"No income statement data found for {symbol} {year}Q{quarter}")
                return None

            if len(df_filtered) == 0:
                logger.warning(f"No income statement data found for {symbol} {year}Q{quarter}")
                return None

            row = df_filtered.iloc[0]

            return IncomeStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=report_period,
                revenue=float(row.get('营业总收入', 0)) if not pd.isna(row.get('营业总收入', 0)) else 0.0,
                net_profit=float(row.get('净利润', 0)) if not pd.isna(row.get('净利润', 0)) else 0.0,
                eps=float(row.get('基本每股收益', 0)) if not pd.isna(row.get('基本每股收益', 0)) else 0.0
            )

        except Exception as e:
            logger.error(f"AKShare income statement failed for {symbol}: {e}")
            return None

    def get_cash_flow_statement(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[CashFlowStatement]:
        """获取现金流量表"""
        try:
            quarter_map = {1: '0331', 2: '0630', 3: '0930', 4: '1231'}
            report_period = f"{year}{quarter_map[quarter]}"

            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)

            if '报告期' in df.columns:
                df_filtered = df[df['报告期'] == report_period]
            else:
                logger.warning(f"No cash flow data found for {symbol} {year}Q{quarter}")
                return None

            if len(df_filtered) == 0:
                logger.warning(f"No cash flow data found for {symbol} {year}Q{quarter}")
                return None

            row = df_filtered.iloc[0]

            return CashFlowStatement(
                symbol=symbol,
                year=year,
                quarter=quarter,
                report_date=report_period,
                operating_cash_flow=float(row.get('经营活动产生的现金流量净额', 0)) if not pd.isna(row.get('经营活动产生的现金流量净额', 0)) else 0.0,
                investing_cash_flow=float(row.get('投资活动产生的现金流量净额', 0)) if not pd.isna(row.get('投资活动产生的现金流量净额', 0)) else 0.0,
                financing_cash_flow=float(row.get('筹资活动产生的现金流量净额', 0)) if not pd.isna(row.get('筹资活动产生的现金流量净额', 0)) else 0.0
            )

        except Exception as e:
            logger.error(f"AKShare cash flow failed for {symbol}: {e}")
            return None

    def get_financial_indicators(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Dict[str, float]:
        """获取财务指标"""
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if len(df) == 0:
                return {}

            # 获取最新的财务指标
            row = df.iloc[0]

            indicators = {}

            # ROE
            roe = row.get('净资产收益率(%)')
            if roe is not None and not pd.isna(roe):
                indicators['roe'] = float(roe) / 100

            # 毛利率
            gross_margin = row.get('销售毛利率(%)')
            if gross_margin is not None and not pd.isna(gross_margin):
                indicators['gross_margin'] = float(gross_margin) / 100

            # 净利率
            net_profit_margin = row.get('销售净利率(%)')
            if net_profit_margin is not None and not pd.isna(net_profit_margin):
                indicators['net_profit_margin'] = float(net_profit_margin) / 100

            # 资产负债率
            asset_liability_ratio = row.get('资产负债率(%)')
            if asset_liability_ratio is not None and not pd.isna(asset_liability_ratio):
                indicators['asset_liability_ratio'] = float(asset_liability_ratio) / 100

            return indicators

        except Exception as e:
            logger.error(f"AKShare financial indicators failed for {symbol}: {e}")
            return {}

    def get_stock_list(self) -> List[Dict]:
        """获取股票列表"""
        try:
            df = ak.stock_zh_a_spot_em()

            stock_list = []
            for _, row in df.iterrows():
                stock = {
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "exchange": "SH" if row['代码'].startswith(('6', '9')) else "SZ",
                    "list_date": None,  # AKShare 不直接提供
                    "industry": None,  # 需要从其他接口获取
                    "concept": None,
                    "region": None
                }
                stock_list.append(stock)

            logger.info(f"Fetched {len(stock_list)} stocks from AKShare")
            return stock_list

        except Exception as e:
            logger.error(f"AKShare get_stock_list failed: {e}")
            raise DataSourceError("akshare", f"Failed to get stock list: {e}", e)

    def get_stock_detail(self, symbol: str) -> Optional[Dict]:
        """获取股票详细信息"""
        try:
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == symbol]

            if len(stock_data) == 0:
                return None

            row = stock_data.iloc[0]

            return {
                "symbol": row['代码'],
                "name": row['名称'],
                "exchange": "SH" if row['代码'].startswith(('6', '9')) else "SZ",
                "list_date": None,
                "delist_date": None,
                "total_shares": None,  # 需要从其他接口获取
                "float_shares": None,
                "industry": None,
                "concept": None,
                "region": None
            }

        except Exception as e:
            logger.error(f"AKShare get_stock_detail failed for {symbol}: {e}")
            raise DataSourceError("akshare", f"Failed to get stock detail: {e}", e)

    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取技术指标数据"""
        try:
            # 获取K线数据
            klines = self.get_kline(symbol, "1d", start_date, end_date)

            if len(klines) == 0:
                return []

            # 提取价格数据
            close_prices = np.array([k.close for k in klines])
            high_prices = np.array([k.high for k in klines])
            low_prices = np.array([k.low for k in klines])
            volumes = np.array([k.volume for k in klines])

            # 计算技术指标（简化版）
            results = []

            for i, kline in enumerate(klines):
                # 简单移动平均
                ma5 = np.mean(close_prices[max(0, i-4):i+1]) if i >= 4 else None
                ma10 = np.mean(close_prices[max(0, i-9):i+1]) if i >= 9 else None
                ma20 = np.mean(close_prices[max(0, i-19):i+1]) if i >= 19 else None

                # RSI (简化版)
                rsi = None
                if i >= 14:
                    gains = np.maximum(0, np.diff(close_prices[i-14:i+1]))
                    losses = np.abs(np.minimum(0, np.diff(close_prices[i-14:i+1])))
                    avg_gain = np.mean(gains)
                    avg_loss = np.mean(losses)
                    if avg_loss != 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))

                # KDJ (简化版)
                kdj_k = kdj_d = kdj_j = None
                if i >= 8:
                    period_high = np.max(high_prices[max(0, i-8):i+1])
                    period_low = np.min(low_prices[max(0, i-8):i+1])
                    if period_high != period_low:
                        rsv = (close_prices[i] - period_low) / (period_high - period_low) * 100
                        if i == 8:
                            kdj_k = rsv
                            kdj_d = rsv
                        else:
                            kdj_k = (2 * results[i-1]['kdj_k'] + rsv) / 3 if results[i-1]['kdj_k'] is not None else rsv
                            kdj_d = (2 * results[i-1]['kdj_d'] + kdj_k) / 3 if results[i-1]['kdj_d'] is not None else kdj_k
                        kdj_j = 3 * kdj_k - 2 * kdj_d if kdj_k is not None and kdj_d is not None else None

                result = {
                    "date": kline.datetime.strftime("%Y-%m-%d"),
                    "ma5": float(ma5) if ma5 is not None else None,
                    "ma10": float(ma10) if ma10 is not None else None,
                    "ma20": float(ma20) if ma20 is not None else None,
                    "rsi": float(rsi) if rsi is not None else None,
                    "kdj_k": float(kdj_k) if kdj_k is not None else None,
                    "kdj_d": float(kdj_d) if kdj_d is not None else None,
                    "kdj_j": float(kdj_j) if kdj_j is not None else None,
                    "macd": None,  # MACD 需要更复杂的计算
                    "macd_signal": None,
                    "macd_hist": None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"AKShare get_tech_indicators failed for {symbol}: {e}")
            return []

    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取资金流向数据"""
        try:
            # 获取个股资金流
            df = ak.stock_individual_fund_flow(symbol=symbol, market="sh")

            if len(df) == 0:
                df = ak.stock_individual_fund_flow(symbol=symbol, market="sz")

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('日期', ''),
                    "main_net_inflow": float(row.get('主力净流入-净额', 0)) if not pd.isna(row.get('主力净流入-净额', 0)) else 0.0,
                    "retail_net_inflow": float(row.get('散户净流入-净额', 0)) if not pd.isna(row.get('散户净流入-净额', 0)) else 0.0,
                    "large_order_net_inflow": float(row.get('超大单净流入-净额', 0)) if not pd.isna(row.get('超大单净流入-净额', 0)) else 0.0,
                    "main_net_inflow_rate": float(row.get('主力净流入-净占比', 0)) / 100 if not pd.isna(row.get('主力净流入-净占比', 0)) else 0.0,
                    "retail_net_inflow_rate": float(row.get('散户净流入-净占比', 0)) / 100 if not pd.isna(row.get('散户净流入-净占比', 0)) else 0.0
                }
                results.append(result)

            # 过滤日期范围
            if start_date or end_date:
                filtered = []
                for item in results:
                    item_date = item['date']
                    if start_date and item_date < start_date:
                        continue
                    if end_date and item_date > end_date:
                        continue
                    filtered.append(item)
                results = filtered

            return results

        except Exception as e:
            logger.error(f"AKShare get_fund_flows failed for {symbol}: {e}")
            return []

    def get_dragon_tiger(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取龙虎榜数据"""
        try:
            # 获取个股龙虎榜详情
            df = ak.stock_lhb_stock_detail_em(symbol=symbol)

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('交易日', ''),
                    "buy_departments": row.get('买入营业部', []),
                    "sell_departments": row.get('卖出营业部', []),
                    "buy_amount": float(row.get('买入金额', 0)) if not pd.isna(row.get('买入金额', 0)) else 0.0,
                    "sell_amount": float(row.get('卖出金额', 0)) if not pd.isna(row.get('卖出金额', 0)) else 0.0,
                    "reason": row.get('上榜原因', '')
                }
                results.append(result)

            # 过滤日期范围
            if start_date or end_date:
                filtered = []
                for item in results:
                    item_date = item['date']
                    if start_date and item_date < start_date:
                        continue
                    if end_date and item_date > end_date:
                        continue
                    filtered.append(item)
                results = filtered

            return results

        except Exception as e:
            logger.error(f"AKShare get_dragon_tiger failed for {symbol}: {e}")
            return []

    def get_valuation(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取估值指标数据 - 需要计算"""
        logger.warning(f"AKShare get_valuation not fully supported for {symbol}")
        return []

    def get_per_share_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取每股指标数据 - 从财务数据提取"""
        try:
            # 获取财务指标
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('报告期', ''),
                    "eps": float(row.get('基本每股收益', 0)) if not pd.isna(row.get('基本每股收益', 0)) else 0.0,
                    "bvps": float(row.get('每股净资产', 0)) if not pd.isna(row.get('每股净资产', 0)) else 0.0,
                    "cfps": float(row.get('每股现金流', 0)) if not pd.isna(row.get('每股现金流', 0)) else 0.0,
                    "dps": float(row.get('每股股息', 0)) if not pd.isna(row.get('每股股息', 0)) else 0.0
                }
                results.append(result)

            # 过滤日期范围
            if start_date or end_date:
                filtered = []
                for item in results:
                    item_date = item['date']
                    if start_date and item_date < start_date:
                        continue
                    if end_date and item_date > end_date:
                        continue
                    filtered.append(item)
                results = filtered

            return results

        except Exception as e:
            logger.error(f"AKShare get_per_share_indicators failed for {symbol}: {e}")
            return []

    def get_osc_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取超买超卖指标数据"""
        try:
            # 获取K线数据
            klines = self.get_kline(symbol, "1d", start_date, end_date)

            if len(klines) == 0:
                return []

            # 计算超买超卖指标（简化版）
            results = []

            for i, kline in enumerate(klines):
                # 威廉指标（简化版）
                wr = None
                if i >= 13:
                    period_high = max([k.high for k in klines[max(0, i-13):i+1]])
                    period_low = min([k.low for k in klines[max(0, i-13):i+1]])
                    if period_high != period_low:
                        wr = (period_high - kline.close) / (period_high - period_low) * 100

                # 乖离率（简化版）
                bias = None
                if i >= 9:
                    ma10 = np.mean([k.close for k in klines[max(0, i-9):i+1]])
                    if ma10 != 0:
                        bias = (kline.close - ma10) / ma10 * 100

                result = {
                    "date": kline.datetime.strftime("%Y-%m-%d"),
                    "wr": float(wr) if wr is not None else None,
                    "bias": float(bias) if bias is not None else None,
                    "cci": None  # 需要更复杂的计算
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"AKShare get_osc_indicators failed for {symbol}: {e}")
            return []

    def get_price_vol_ind(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取量价指标数据"""
        try:
            # 获取K线数据
            klines = self.get_kline(symbol, "1d", start_date, end_date)

            if len(klines) == 0:
                return []

            results = []

            for i, kline in enumerate(klines):
                result = {
                    "date": kline.datetime.strftime("%Y-%m-%d"),
                    "obv": None,  # 能量潮需要累计计算
                    "vr": None,  # 量比需要对比
                    "mfi": None  # 资金流量指标
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"AKShare get_price_vol_ind failed for {symbol}: {e}")
            return []

    def get_limit_up_down(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取涨跌停数据"""
        try:
            # 获取K线数据
            klines = self.get_kline(symbol, "1d", start_date, end_date)

            if len(klines) == 0:
                return []

            results = []

            for i, kline in enumerate(klines):
                is_limit_up = False
                is_limit_down = False

                # 判断涨跌停（简化版，假设涨跌幅10%）
                if i > 0:
                    prev_close = klines[i-1].close
                    price_change_pct = (kline.close - prev_close) / prev_close * 100

                    is_limit_up = price_change_pct >= 9.9  # 涨停
                    is_limit_down = price_change_pct <= -9.9  # 跌停

                result = {
                    "date": kline.datetime.strftime("%Y-%m-%d"),
                    "is_limit_up": is_limit_up,
                    "is_limit_down": is_limit_down,
                    "limit_up_times": 1 if is_limit_up else 0,
                    "limit_down_times": 1 if is_limit_down else 0,
                    "consecutive_limit_up": 0  # 需要更复杂的连续判断
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"AKShare get_limit_up_down failed for {symbol}: {e}")
            return []

    def get_turnover_rates(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取换手率数据"""
        try:
            # 获取K线数据（包含换手率）
            klines = self.get_kline(symbol, "1d", start_date, end_date)

            if len(klines) == 0:
                return []

            results = []

            for kline in klines:
                result = {
                    "date": kline.datetime.strftime("%Y-%m-%d"),
                    "turnover_rate": kline.turnover,
                    "volume_ratio": None  # 量比需要对比
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"AKShare get_turnover_rates failed for {symbol}: {e}")
            return []

    def get_fund_quotes(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取基金净值数据"""
        try:
            # 获取基金历史净值
            df = ak.fund_open_fund_info_em(fund=symbol, indicator="单位净值走势")

            if len(df) == 0:
                return []

            results = []
            for _, row in df.iterrows():
                result = {
                    "date": row.get('净值日期', ''),
                    "nav": float(row.get('单位净值', 0)) if not pd.isna(row.get('单位净值', 0)) else 0.0,
                    "accumulated_nav": float(row.get('累计净值', 0)) if not pd.isna(row.get('累计净值', 0)) else 0.0,
                    "daily_return": float(row.get('日增长率', 0)) / 100 if not pd.isna(row.get('日增长率', 0)) else 0.0
                }
                results.append(result)

            # 过滤日期范围
            if start_date or end_date:
                filtered = []
                for item in results:
                    item_date = item['date']
                    if start_date and item_date < start_date:
                        continue
                    if end_date and item_date > end_date:
                        continue
                    filtered.append(item)
                results = filtered

            return results

        except Exception as e:
            logger.error(f"AKShare get_fund_quotes failed for {symbol}: {e}")
            return []

    def get_dupont_analysis(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """杜邦分析 - AKShare 不支持"""
        logger.warning(f"AKShare does not support dupont analysis for {symbol}")
        raise NotImplementedError(
            "AKShare does not support dupont analysis. "
            "Use Investoday data source instead."
        )
