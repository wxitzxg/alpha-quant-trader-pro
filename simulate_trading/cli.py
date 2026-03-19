#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易命令行接口

用法:
    python -m simulate_trading.cli start     # 启动所有策略
    python -m simulate_trading.cli stop      # 停止所有策略
    python -m simulate_trading.cli status    # 查看状态
    python -m simulate_trading.cli report    # 生成对比报告
    python -m simulate_trading.cli cycle     # 执行单次交易周期
    python -m simulate_trading.cli daily     # 生成每日报告
"""

import sys
import json
import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from simulate_trading.controller import TradingController
from simulate_trading.models import StrategyAccount, StrategyTrade, DailyReport


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/simulate_trading.log', encoding='utf-8')
        ]
    )


def init_database():
    """初始化数据库"""
    # 从环境变量获取数据库URL，或使用默认值
    import os
    db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/stock_market')

    engine = create_engine(db_url, echo=False)

    # 创建表
    StrategyAccount.metadata.create_all(engine)
    StrategyTrade.metadata.create_all(engine)
    DailyReport.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


def print_banner():
    """打印横幅"""
    print("=" * 70)
    print("🚀 Alpha Quant Trader Pro - 模拟交易系统")
    print("=" * 70)


def main():
    """主函数"""
    setup_logging()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    # 初始化数据库
    try:
        db = init_database()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return

    # 初始化控制器
    controller = TradingController()
    controller.initialize_db(db)

    print_banner()

    try:
        if command == 'start':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("🔄 启动所有策略...\n")
            controller.start_all_strategies()
            print("\n✅ 所有策略已启动\n")

        elif command == 'stop':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("⏹️  停止所有策略...\n")
            controller.stop_all_strategies()
            print("\n✅ 所有策略已停止\n")

        elif command == 'status':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n📊 策略状态:\n")
            status = controller.status()

            for strategy_name, data in status['strategies'].items():
                print(f"{'─' * 70}")
                print(f"📈 策略: {strategy_name}")
                print(f"{'─' * 70}")
                print(f"  初始资金: {data['initial_cash']:,.2f} 元")
                print(f"  当前现金: {data['current_cash']:,.2f} 元")
                print(f"  总资产:   {data['total_value']:,.2f} 元")
                print(f"  总收益:   {data['total_profit']:+,.2f} 元 ({data['total_profit_pct']:+.2f}%)")
                print(f"  持仓数量: {data['position_count']} 只\n")

            print(f"{'=' * 70}\n")

        elif command == 'report':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n📊 策略对比报告:\n")
            report = controller.generate_comparison_report()

            print(f"{'=' * 70}")
            print("🏆 策略收益率排名")
            print(f"{'=' * 70}\n")

            for item in report['rankings']:
                print(f"  {item['rank']}. {item['strategy']}: {item['profit_pct']:+.2f}%")

            print(f"\n{'─' * 70}\n")

            for strategy_name, data in report['strategies'].items():
                print(f"📈 {strategy_name}")
                print(f"{'─' * 70}")
                print(f"  报告日期: {data['report_date']}")
                print(f"  总资产:   {data['total_assets']:,.2f} 元")
                print(f"  收益率:   {data['profit_pct']:+.2f}%")
                print(f"  交易次数: {data['total_trades']} 次")
                print(f"  持仓数:   {data['position_count']} 只\n")

            print(f"{'=' * 70}\n")

        elif command == 'cycle':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n🔄 执行单次交易周期...\n")
            results = controller.execute_single_cycle()

            print(f"\n{'=' * 70}")
            print("📊 交易周期执行结果")
            print(f"{'=' * 70}\n")

            for strategy_name, result in results.items():
                print(f"📈 {strategy_name}")
                print(f"  总资产: {result.total_value:,.2f} 元")
                print(f"  收益:   {result.profit:+,.2f} 元 ({result.profit_pct:+.2f}%)")
                print(f"  执行交易: {len(result.executed_trades)} 笔")
                print(f"  跳过交易: {len(result.skipped_trades)} 笔\n")

            print(f"{'=' * 70}\n")

        elif command == 'daily':
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n📊 生成每日报告...\n")
            controller.generate_daily_report()
            print("\n✅ 每日报告生成完成\n")

        else:
            print(__doc__)
            return

    except Exception as e:
        print(f"\n❌ 执行失败: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
