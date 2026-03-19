"""
性能优化示例
"""

import time
from typing import List
from common.database import DatabaseManager
from common.config import get_config
from common.performance import BatchProcessor, SimpleCache, cached
from stock_market.models import Stock


def example_batch_insert():
    """示例：批量插入股票数据"""
    print("=" * 60)
    print("批量插入示例")
    print("=" * 60)

    # 准备测试数据
    stock_data = [
        {"symbol": f"600{i:03d}", "name": f"Stock{i}", "industry": "测试"}
        for i in range(1000)
    ]

    # 初始化数据库
    config = get_config()
    db_manager = DatabaseManager(config.database.url)

    with db_manager.get_session() as session:
        # 测量时间
        start = time.time()

        # 批量插入（batch_size=100）
        count = BatchProcessor.batch_insert(
            session=session,
            model_class=Stock,
            data_list=stock_data,
            batch_size=100
        )
        session.commit()

        elapsed = time.time() - start

        print(f"✓ 批量插入 {count} 条记录")
        print(f"✓ 耗时: {elapsed:.2f} 秒")
        print(f"✓ 平均: {count/elapsed:.0f} 条/秒")


def example_cache_usage():
    """示例：使用缓存"""
    print("\n" + "=" * 60)
    print("缓存使用示例")
    print("=" * 60)

    # 创建缓存
    stock_cache = SimpleCache(ttl=300)  # 5 分钟过期

    # 初始化数据库
    config = get_config()
    db_manager = DatabaseManager(config.database.url)

    with db_manager.get_session() as session:
        # 定义带缓存的函数
        @cached(stock_cache, key_prefix="stock")
        def get_stock_cached(symbol: str):
            print(f"  [DB Query] 查询 {symbol}")
            return session.query(Stock).filter_by(symbol=symbol).first()

        # 第一次调用 - 查询数据库
        print("第一次调用（查询数据库）:")
        stock1 = get_stock_cached("600000")

        # 第二次调用 - 从缓存读取
        print("\n第二次调用（从缓存读取）:")
        stock2 = get_stock_cached("600000")

        print(f"\n✓ 缓存命中: {stock1 is stock2}")


def example_batch_update():
    """示例：批量更新"""
    print("\n" + "=" * 60)
    print("批量更新示例")
    print("=" * 60)

    # 准备更新数据
    update_data = [
        {"symbol": f"600{i:03d}", "name": f"Updated{i}"}
        for i in range(100)
    ]

    # 初始化数据库
    config = get_config()
    db_manager = DatabaseManager(config.database.url)

    with db_manager.get_session() as session:
        start = time.time()

        # 批量更新
        count = BatchProcessor.batch_update(
            session=session,
            model_class=Stock,
            data_list=update_data,
            key_field="symbol",
            batch_size=50
        )
        session.commit()

        elapsed = time.time() - start

        print(f"✓ 批量更新 {count} 条记录")
        print(f"✓ 耗时: {elapsed:.2f} 秒")


def example_cache_invalidation():
    """示例：缓存失效"""
    print("\n" + "=" * 60)
    print("缓存失效示例")
    print("=" * 60)

    cache = SimpleCache(ttl=10)  # 10 秒过期

    # 缓存数据
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    print(f"缓存大小: {len(cache)}")

    # 删除单个键
    cache.delete("key1")
    print(f"删除 key1 后，缓存大小: {len(cache)}")

    # 等待过期
    time.sleep(11)
    print(f"11 秒后，缓存大小: {len(cache)}")  # 应该为 0


def example_performance_comparison():
    """示例：性能对比"""
    print("\n" + "=" * 60)
    print("性能对比示例")
    print("=" * 60)

    config = get_config()
    db_manager = DatabaseManager(config.database.url)

    with db_manager.get_session() as session:
        # 方式 1：逐条插入
        print("\n方式 1：逐条插入")
        data1 = [{"symbol": f"100{i:03d}", "name": f"Stock{i}"} for i in range(100)]

        start = time.time()
        for item in data1:
            session.add(Stock(**item))
        session.commit()
        elapsed1 = time.time() - start

        print(f"  耗时: {elapsed1:.2f} 秒")

        # 方式 2：批量插入
        print("\n方式 2：批量插入")
        data2 = [{"symbol": f"200{i:03d}", "name": f"Stock{i}"} for i in range(100)]

        session.rollback()  # 回滚上一次提交
        start = time.time()
        BatchProcessor.batch_insert(session, Stock, data2, batch_size=50)
        session.commit()
        elapsed2 = time.time() - start

        print(f"  耗时: {elapsed2:.2f} 秒")

        # 对比
        if elapsed1 > 0 and elapsed2 > 0:
            improvement = (elapsed1 - elapsed2) / elapsed1 * 100
            print(f"\n✓ 性能提升: {improvement:.1f}%")


if __name__ == "__main__":
    example_batch_insert()
    example_batch_update()
    example_cache_usage()
    example_cache_invalidation()
    example_performance_comparison()

    print("\n" + "=" * 60)
    print("✓ 所有性能优化示例执行完成")
    print("=" * 60)
