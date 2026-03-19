"""
股票市场管理模块 - 使用示例

演示如何使用股票市场管理模块进行：
1. 股票列表同步
2. 股票详情查询
3. K线数据同步
4. 并发同步
5. 增量同步
"""
from stock_market.database import DatabaseManager
from stock_market.managers.stock_manager import StockDataManager
from stock_market.managers.kline_manager import KLineDataManager
from stock_market.sync.concurrent_sync import ConcurrentSyncManager
from stock_market.sync.incremental_sync import IncrementalSyncStrategy


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("【示例 1】基本使用 - 股票列表和K线同步")
    print("=" * 60)

    # 初始化数据库
    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
    stock_manager = StockDataManager(db)
    kline_manager = KLineDataManager(db)

    # 1. 同步股票列表
    print("\n1. 同步股票列表...")
    count = stock_manager.sync_all_stocks()
    print(f"   ✓ 同步了 {count} 只股票")

    # 2. 获取股票列表
    print("\n2. 获取上市股票列表...")
    stocks = stock_manager.get_active_stocks()
    print(f"   ✓ 查询到 {len(stocks)} 只上市股票")
    print(f"   前3只: {', '.join([f'{s.symbol}({s.name})' for s in stocks[:3]])}")

    # 3. 同步单只股票K线
    if stocks:
        symbol = stocks[0].symbol
        print(f"\n3. 同步 {symbol} 的K线数据...")
        count = kline_manager.sync_single_kline(
            symbol=symbol,
            interval="1d",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        print(f"   ✓ 同步了 {count} 条K线数据")

    # 4. 查询K线数据
    print("\n4. 查询K线数据...")
    klines = kline_manager.query_klines(
        symbol=symbol,
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-01-10",
        order_by="desc"
    )
    print(f"   ✓ 查询到 {len(klines)} 条K线")
    if klines:
        print(f"   首条数据: {klines[0].date} 收盘价: {klines[0].close}")

    # 5. 获取最新K线
    print("\n5. 获取最新K线...")
    latest = kline_manager.get_latest_kline(symbol, "1d")
    if latest:
        print(f"   ✓ {latest.date} 开:{latest.open} 高:{latest.high} 低:{latest.low} 收:{latest.close} 量:{latest.volume}")


def example_query_features():
    """查询功能示例"""
    print("\n" + "=" * 60)
    print("【示例 2】高级查询功能")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
    stock_manager = StockDataManager(db)

    # 同步股票列表（如果还未同步）
    stock_manager.sync_all_stocks()

    # 1. 按行业查询
    print("\n1. 按行业查询（银行）...")
    bank_stocks = stock_manager.get_stocks_by_industry("银行")
    print(f"   ✓ 找到 {len(bank_stocks)} 只银行股")
    if bank_stocks:
        print(f"   前3只: {', '.join([f'{s.symbol}({s.name})' for s in bank_stocks[:3]])}")

    # 2. 按概念查询
    print("\n2. 按概念查询（白酒）...")
    white_wine_stocks = stock_manager.get_stocks_by_concept("白酒")
    print(f"   ✓ 找到 {len(white_wine_stocks)} 只白酒股")
    if white_wine_stocks:
        print(f"   前3只: {', '.join([f'{s.symbol}({s.name})' for s in white_wine_stocks[:3]])}")

    # 3. 获取单只股票详情
    print("\n3. 获取单只股票详情...")
    stock = stock_manager.get_stock("600000")
    if stock:
        print(f"   ✓ {stock.symbol} - {stock.name}")
        print(f"     行业: {stock.industry}")
        print(f"     概念: {stock.concept}")
        print(f"     总股本: {stock.shares} 万股")


def example_concurrent_sync():
    """并发同步示例"""
    print("\n" + "=" * 60)
    print("【示例 3】并发同步多只股票")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
    stock_manager = StockDataManager(db)

    # 获取股票列表
    stocks = stock_manager.get_active_stocks()
    if not stocks:
        stock_manager.sync_all_stocks()
        stocks = stock_manager.get_active_stocks()

    # 选择前10只股票进行并发同步
    symbols = [s.symbol for s in stocks[:10]]
    print(f"\n并发同步前 {len(symbols)} 只股票的K线数据...")
    print(f"股票: {', '.join(symbols[:5])} ...")

    # 并发同步
    concurrent_manager = ConcurrentSyncManager(db, max_workers=5)
    results = concurrent_manager.sync_klines_concurrently(
        symbols=symbols,
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-12-31",
        max_workers=3  # 使用3个线程
    )

    # 统计结果
    success = [s for s, r in results.items() if r.get("status") == "success"]
    failed = [s for s, r in results.items() if r.get("status") == "failed"]

    print(f"\n同步完成:")
    print(f"  ✓ 成功: {len(success)}/{len(symbols)}")
    print(f"  ✗ 失败: {len(failed)}")
    if failed:
        print(f"  失败列表: {', '.join(failed)}")


def example_incremental_sync():
    """增量同步示例"""
    print("\n" + "=" * 60)
    print("【示例 4】增量同步和数据完整性检查")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
    kline_manager = KLineDataManager(db)

    # 获取股票
    from stock_market.managers.stock_manager import StockDataManager
    stock_manager = StockDataManager(db)
    stocks = stock_manager.get_active_stocks()

    if not stocks:
        print("请先同步股票列表")
        return

    symbol = stocks[0].symbol

    # 1. 首次同步
    print(f"\n1. 首次同步 {symbol} 的K线（2023年1月）...")
    count1 = kline_manager.sync_single_kline(
        symbol=symbol,
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    print(f"   ✓ 同步了 {count1} 条")

    # 2. 增量同步（会自动从上次同步的下一天开始）
    print(f"\n2. 增量同步（自动检测时间范围）...")
    count2 = kline_manager.sync_single_kline(symbol=symbol, interval="1d")
    print(f"   ✓ 增量同步了 {count2} 条")

    # 3. 数据完整性检查
    print(f"\n3. 检查数据完整性...")
    strategy = IncrementalSyncStrategy(db)

    missing_dates = strategy.get_missing_dates(
        symbol=symbol,
        interval="1d",
        start_date="2023-01-01",
        end_date="2023-01-31"
    )

    print(f"   检测到 {len(missing_dates)} 个缺失日期")
    if missing_dates:
        print(f"   前3个缺失日期: {missing_dates[:3]}")

    # 4. 获取同步缺口
    print(f"\n4. 获取同步缺口（连续的缺失日期段）...")
    gaps = strategy.get_sync_gaps(symbol, "1d")
    print(f"   找到 {len(gaps)} 个同步缺口")
    if gaps:
        for i, gap in enumerate(gaps[:3], 1):
            print(f"     缺口{i}: {gap['start']} ~ {gap['end']}")


def example_multiple_intervals():
    """多周期同步示例"""
    print("\n" + "=" * 60)
    print("【示例 5】同步多周期K线")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")
    kline_manager = KLineDataManager(db)

    from stock_market.managers.stock_manager import StockDataManager
    stock_manager = StockDataManager(db)
    stocks = stock_manager.get_active_stocks()

    if not stocks:
        print("请先同步股票列表")
        return

    symbol = stocks[0].symbol

    intervals = ["1d", "5d", "10d", "1M"]
    interval_names = {
        "1d": "日线",
        "5d": "5日线",
        "10d": "10日线",
        "1M": "月线"
    }

    print(f"\n同步 {symbol} 的多种周期K线...")

    for interval in intervals:
        name = interval_names[interval]
        print(f"\n  {name}...")
        count = kline_manager.sync_single_kline(
            symbol=symbol,
            interval=interval,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        print(f"    ✓ 同步了 {count} 条")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "股票市场管理模块使用示例" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    # 运行各个示例
    try:
        example_basic_usage()
        example_query_features()
        example_concurrent_sync()
        example_incremental_sync()
        example_multiple_intervals()

        print("\n" + "=" * 60)
        print("✓ 所有示例运行完成")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()
