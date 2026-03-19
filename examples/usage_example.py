"""
数据源聚合模块使用示例

演示如何使用统一的 API 获取股票数据
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources import QuoteAPI, KLineAPI, FundamentalsAPI


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_get_realtime():
    """示例：获取实时行情"""
    print("\n=== 获取实时行情 ===")

    # 单个股票
    quote = QuoteAPI.get_realtime("600519")  # 贵州茅台
    if quote:
        print(f"贵州茅台 ({quote.symbol}):")
        print(f"  价格: {quote.price:.2f} 元")
        print(f"  涨跌: {quote.change:+.2f} ({quote.percent:+.2%})")
        print(f"  成交量: {quote.volume:,} 股")
        print(f"  成交额: {quote.amount:,.2f} 元")
    else:
        print("无法获取贵州茅台行情数据")


def example_batch_get_realtime():
    """示例：批量获取实时行情"""
    print("\n=== 批量获取实时行情 ===")

    symbols = ["600519", "000001", "601318"]  # 贵州茅台、平安银行、中国平安
    quotes = QuoteAPI.batch_get_realtime(symbols)

    print(f"获取到 {len(quotes)} 条行情数据:")
    for quote in quotes:
        print(f"  {quote.symbol}: {quote.price:.2f} 元 ({quote.percent:+.2%})")


def example_get_kline():
    """示例：获取历史K线"""
    print("\n=== 获取历史K线 ===")

    # 获取贵州茅台上个月的日线数据
    klines = KLineAPI.get(
        symbol="600519",
        interval="1d",
        start_date="2023-12-01",
        end_date="2023-12-31"
    )

    print(f"获取到 {len(klines)} 条K线数据:")
    if klines:
        for kline in klines[:5]:  # 只显示前5条
            print(f"  {kline.datetime.date()}: "
                  f"开 {kline.open_price:.2f}, "
                  f"高 {kline.high:.2f}, "
                  f"低 {kline.low:.2f}, "
                  f"收 {kline.close:.2f}, "
                  f"量 {kline.volume:,}")


def example_get_fundamentals():
    """示例：获取基本面数据"""
    print("\n=== 获取基本面数据 ===")

    # 获取资产负债表（示例，实际需要 Tushare VIP 权限）
    # balance = FundamentalsAPI.get_balance_sheet("600519", year=2023, quarter=3)
    # if balance:
    #     print(f"总资产: {balance.total_assets:,.2f}")
    #     print(f"总负债: {balance.total_liabilities:,.2f}")
    #     print(f"股东权益: {balance.shareholders_equity:,.2f}")

    # 获取财务指标
    indicators = FundamentalsAPI.get_indicators("600519", year=2023, quarter=3)
    if indicators:
        print(f"ROE: {indicators.get('roe', 0):.2%}")
        print(f"毛利率: {indicators.get('gross_margin', 0):.2%}")
        print(f"净利率: {indicators.get('net_profit_margin', 0):.2%}")


def main():
    """主函数"""
    setup_logging()

    print("=" * 60)
    print("股票数据源聚合模块使用示例")
    print("=" * 60)

    # 运行各个示例
    example_get_realtime()
    example_batch_get_realtime()
    example_get_kline()
    example_get_fundamentals()

    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
