#!/usr/bin/env python3
"""
Technical Analysis Module Usage Example - 技术分析模块使用示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import DatabaseManager
from technical_analysis.services import AnalysisService


def example_five_dimension_analysis():
    """示例 1: 五维共振分析"""
    print("=" * 60)
    print("📊 示例 1: 五维共振分析")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")

    with db.get_session() as session:
        analysis_service = AnalysisService(session)

        # 分析贵州茅台 (需要先同步数据)
        result = analysis_service.analyze_stock(
            symbol="600519",
            interval="1d",
            days=120
        )

        if 'error' in result:
            print(f"❌ 错误: {result['message']}")
            print("💡 提示: 请先使用 stock_market 同步 K 线数据")
            return

        print(f"\n📈 股票: {result['symbol']}")
        print(f"📊 总分: {result['total_score']}/{result['max_score']} ({result['score_percentage']:.1f}%)")
        print(f"🎯 决策: {result['action']}")
        print(f"⭐ 置信度: {result['confidence_level']} 级")
        print(f"💰 建议仓位: {result['position_suggestion'] * 100:.0f}%")

        print("\n【维度详情】")
        for dim_id, score in result['dimension_scores'].items():
            details = result['dimension_details'].get(dim_id, {})
            print(f"  • {dim_id}: {score}分 - {details}")


def example_strategy_analysis():
    """示例 2: 三大策略分析"""
    print("\n" + "=" * 60)
    print("🎯 示例 2: 三大策略分析")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")

    with db.get_session() as session:
        analysis_service = AnalysisService(session)

        result = analysis_service.analyze_with_strategies(
            symbol="600519",
            interval="1d",
            days=120
        )

        if 'error' in result:
            print(f"❌ 错误: {result['message']}")
            return

        print(f"\n📈 股票: {result['symbol']}")
        print(f"📊 VCP 突破策略: {result['strategies']['vcp_breakout']['signal']}")
        print(f"   得分: {result['strategies']['vcp_breakout']['score']}")
        print(f"   置信度: {result['strategies']['vcp_breakout']['confidence']}")

        print(f"\n💎 九转黄金坑策略: {result['strategies']['td_golden_pit']['signal']}")
        print(f"   得分: {result['strategies']['td_golden_pit']['score']}")
        print(f"   置信度: {result['strategies']['td_golden_pit']['confidence']}")

        print(f"\n🚨 顶部背离策略: {result['strategies']['top_divergence']['signal']}")
        print(f"   得分: {result['strategies']['top_divergence']['score']}")
        print(f"   风险等级: {result['strategies']['top_divergence']['risk_level']}")


def example_generate_report():
    """示例 3: 生成完整分析报告"""
    print("\n" + "=" * 60)
    print("📝 示例 3: 生成完整分析报告")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")

    with db.get_session() as session:
        analysis_service = AnalysisService(session)

        report = analysis_service.generate_analysis_report(
            symbol="600519",
            interval="1d",
            days=120
        )

        print(report)


def example_technical_indicators():
    """示例 4: 获取技术指标"""
    print("\n" + "=" * 60)
    print("📈 示例 4: 获取技术指标")
    print("=" * 60)

    db = DatabaseManager("postgresql://postgres:postgres@localhost:5432/stock_market")

    with db.get_session() as session:
        analysis_service = AnalysisService(session)

        indicators = analysis_service.get_technical_indicators(
            symbol="600519",
            interval="1d",
            days=60
        )

        if 'error' in indicators:
            print(f"❌ 错误: {indicators['message']}")
            return

        print(f"\n📈 股票: {indicators['symbol']}")
        print(f"💰 当前价格: ¥{indicators['current_price']:.2f}")

        print("\n【最新信号】")
        signals = indicators['latest_signals']
        print(f"  均线趋势: {signals['ma_trend']}")
        print(f"  MACD 信号: {signals['macd_signal']}")
        print(f"  RSI 状态: {signals['rsi_condition']}")
        print(f"  布林带位置: {signals['bb_position']}")
        print(f"  成交量状态: {signals['volume_condition']}")


if __name__ == "__main__":
    print("\n🚀 技术分析模块使用示例")
    print("=" * 60)

    # 示例 1: 五维共振分析
    try:
        example_five_dimension_analysis()
    except Exception as e:
        print(f"❌ 示例 1 出错: {e}")

    # 示例 2: 三大策略分析
    try:
        example_strategy_analysis()
    except Exception as e:
        print(f"❌ 示例 2 出错: {e}")

    # 示例 3: 生成报告
    try:
        example_generate_report()
    except Exception as e:
        print(f"❌ 示例 3 出错: {e}")

    # 示例 4: 技术指标
    try:
        example_technical_indicators()
    except Exception as e:
        print(f"❌ 示例 4 出错: {e}")

    print("\n✅ 所有示例执行完毕!")
