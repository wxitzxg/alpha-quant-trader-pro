#!/usr/bin/env python3
"""测试数据源配置修改"""

import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent))

# 导入必要的模块
from common.config import get_config
from data_sources.aggregator import DataSourceAggregator
from data_sources import QuoteAPI, KLineAPI, FundamentalsAPI
from data_sources.base import DataSourceAdapter
from data_sources.registry import AdapterRegistry
from data_sources.executor import FallbackExecutor


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    try:
        config = get_config()
        data_sources_config = config.data_sources.model_dump()

        print("✓ 配置加载成功")
        print(f"  超时配置: {data_sources_config.get('fallback', {}).get('timeout', 'N/A')}")
        print(f"  重试次数: {data_sources_config.get('fallback', {}).get('max_retries', 'N/A')}")

        # 检查数据源配置
        sources = data_sources_config.get('sources', {})
        print(f"\n  数据源配置:")
        for category, configs in sources.items():
            print(f"    {category}:")
            for cfg in configs:
                print(f"      - {cfg['name']}: priority={cfg.get('priority')}, timeout={cfg.get('timeout')}")

        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregator_singleton():
    """测试单例模式"""
    print("\n=== 测试单例模式 ===")
    try:
        agg1 = DataSourceAggregator()
        agg2 = DataSourceAggregator()

        if agg1 is agg2:
            print("✓ 单例模式正常")
        else:
            print("✗ 单例模式失败")
            return False

        # 检查配置是否正确加载
        if hasattr(agg1, 'config') and agg1.config:
            print("✓ 聚合器配置加载成功")
            return True
        else:
            print("✗ 聚合器配置加载失败")
            return False
    except Exception as e:
        print(f"✗ 单例测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_methods():
    """测试简化API方法"""
    print("\n=== 测试简化API方法 ===")
    try:
        # 测试QuoteAPI
        print(f"  QuoteAPI.get 签名: {QuoteAPI.get}")
        print(f"  QuoteAPI.batch_get 签名: {QuoteAPI.batch_get}")

        # 测试KLineAPI
        print(f"  KLineAPI.get 签名: {KLineAPI.get}")

        # 测试FundamentalsAPI
        print(f"  FundamentalsAPI.get_balance_sheet 签名: {FundamentalsAPI.get_balance_sheet}")
        print(f"  FundamentalsAPI.get_income_statement 签名: {FundamentalsAPI.get_income_statement}")
        print(f"  FundamentalsAPI.get_cash_flow_statement 签名: {FundamentalsAPI.get_cash_flow_statement}")
        print(f"  FundamentalsAPI.get_indicators 签名: {FundamentalsAPI.get_indicators}")

        print("✓ 简化API方法签名正常")
        return True
    except Exception as e:
        print(f"✗ API方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_names():
    """测试方法名称一致性"""
    print("\n=== 测试方法名称一致性 ===")
    try:
        agg = DataSourceAggregator()

        # 检查旧方法名是否已被移除
        old_methods = ['get_realtime', 'batch_get_realtime', 'get_kline',
                      'get_balance_sheet', 'get_income_statement',
                      'get_cash_flow_statement', 'get_financial_indicators']

        print("  旧方法名检查:")
        for method_name in old_methods:
            if hasattr(agg, method_name):
                print(f"    ✗ {method_name} 仍然存在")
                return False
            else:
                print(f"    ✓ {method_name} 已移除")

        # 检查新方法名是否存在
        new_methods = ['realtime', 'batch_realtime', 'kline',
                      'fundamentals_balance_sheet', 'fundamentals_income_statement',
                      'fundamentals_cash_flow_statement', 'fundamentals_indicators']

        print("  新方法名检查:")
        for method_name in new_methods:
            if hasattr(agg, method_name):
                print(f"    ✓ {method_name} 存在")
            else:
                print(f"    ✗ {method_name} 不存在")
                return False

        print("✓ 方法名称一致性正常")
        return True
    except Exception as e:
        print(f"✗ 方法名测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_class_signature():
    """测试基类构造函数签名"""
    print("\n=== 测试基类构造函数签名 ===")
    try:
        print(f"  DataSourceAdapter.__init__ 参数: {DataSourceAdapter.__init__.__annotations__}")

        # 验证基类是否接受 priority 和 timeout 参数
        import inspect
        sig = inspect.signature(DataSourceAdapter.__init__)
        params = list(sig.parameters.keys())

        if 'priority' in params and 'timeout' in params:
            print("✓ 基类构造函数签名正常")
            return True
        else:
            print(f"✗ 基类构造函数签名不正确: {params}")
            return False
    except Exception as e:
        print(f"✗ 基类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("数据源配置修改测试")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("配置加载", test_config_loading()))
    results.append(("单例模式", test_aggregator_singleton()))
    results.append(("API方法", test_api_methods()))
    results.append(("方法名称", test_method_names()))
    results.append(("基类签名", test_base_class_signature()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")

    all_passed = all(r for _, r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
