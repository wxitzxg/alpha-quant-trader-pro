"""Data Feed - 数据源适配器"""

import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from stock_market.repositories import KLineRepository
from api_server.models.kline import KLineQueryParams


class DataFeed:
    """
    数据源适配器 - 对接 stock_market 模块
    """

    def __init__(self, session: Session):
        """
        初始化数据源适配器

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.kline_repo = KLineRepository(session)

    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期

        Returns:
            DataFrame with columns: [open, high, low, close, volume, timestamp]
        """
        params = KLineQueryParams(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        klines = self.kline_repo.query_klines(params)

        if not klines:
            raise ValueError(f"No data found for {symbol} from {start_date} to {end_date}")

        # 转换为 DataFrame
        data = []
        for kline in klines:
            data.append({
                'open': kline.open_price,
                'high': kline.high_price,
                'low': kline.low_price,
                'close': kline.close_price,
                'volume': kline.volume,
                'timestamp': kline.timestamp
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def get_multi_stock_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据 (用于组合回测)

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期

        Returns:
            {symbol: DataFrame}
        """
        return {symbol: self.get_stock_data(symbol, start_date, end_date, interval)
                for symbol in symbols}
