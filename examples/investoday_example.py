"""
Investoday 数据源适配器使用示例

演示如何使用 Investoday 数据源获取股票数据，包括核心功能、特色功能和独家实体识别功能。
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources import DataSourceAggregator


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def check_api_key():
    """检查 API Key 配置"""
    api_key = os.environ.get("INVESTODAY_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 INVESTODAY_API_KEY 环境变量")
        print("请设置环境变量: export INVESTODAY_API_KEY=your_api_key_here")
        return False
    return True


def example_core_features(aggregator):
    """示例：核心功能"""
    print("\n=== 核心功能示例 ===")

    # 获取实时行情
    print("\n1. 获取单个股票实时行情:")
    quote = aggregator.get_realtime("600519")  # 贵州茅台
    if quote:
        print(f"   贵州茅台 ({quote.symbol}):")
        print(f"   价格: {quote.price:.2f} 元")
        print(f"   涨跌: {quote.change:+.2f} ({quote.percent:+.2%})")
        print(f"   成交量: {quote.volume:,} 股")
    else:
        print("   ❌ 无法获取实时行情数据")

    # 批量获取实时行情
    print("\n2. 批量获取实时行情:")
    symbols = ["600519", "000001", "601318"]  # 贵州茅台、平安银行、中国平安
    quotes = aggregator.batch_get_realtime(symbols)
    print(f"   获取到 {len(quotes)} 条行情数据:")
    for quote in quotes:
        print(f"   {quote.symbol}: {quote.price:.2f} 元 ({quote.percent:+.2%})")

    # 获取K线数据
    print("\n3. 获取历史K线数据:")
    klines = aggregator.get_kline(
        symbol="600519",
        interval="1d",
        start_date="2023-12-01",
        end_date="2023-12-31"
    )
    print(f"   获取到 {len(klines)} 条K线数据:")
    if klines:
        for kline in klines[:3]:  # 显示前3条
            print(f"   {kline.datetime.date()}: 开 {kline.open_price:.2f}, 高 {kline.high:.2f}, "
                  f"低 {kline.low:.2f}, 收 {kline.close:.2f}")

    # 获取财务报表
    print("\n4. 获取财务报表:")
    balance = aggregator.get_balance_sheet("600519", year=2023, quarter=3)
    if balance:
        print(f"   总资产: {balance.total_assets:,.2f} 元")
        print(f"   总负债: {balance.total_liabilities:,.2f} 元")
        print(f"   股东权益: {balance.shareholders_equity:,.2f} 元")
    else:
        print("   ❌ 无法获取资产负债表数据")


def example_feature_functions(aggregator):
    """示例：特色功能"""
    print("\n=== 特色功能示例 ===")

    # 技术指标
    print("\n1. 获取技术指标:")
    tech_indicators = aggregator.get_tech_indicators("600519")
    if tech_indicators:
        print(f"   获取到 {len(tech_indicators)} 条技术指标数据")
        # 显示第一条数据的概要
        first_indicator = tech_indicators[0]
        print(f"   日期: {first_indicator.get('tradeDate', 'N/A')}")
        print(f"   MACD: {first_indicator.get('macd', 'N/A')}")
        print(f"   RSI: {first_indicator.get('rsi', 'N/A')}")
    else:
        print("   ❌ 无法获取技术指标数据")

    # 资金流向
    print("\n2. 获取资金流向:")
    fund_flows = aggregator.get_fund_flows("600519")
    if fund_flows:
        print(f"   获取到 {len(fund_flows)} 条资金流向数据")
        first_flow = fund_flows[0]
        main_net_inflow = first_flow.get('mainNetInflow', 0)
        print(f"   主力净流入: {main_net_inflow:,.2f} 元")
    else:
        print("   ❌ 无法获取资金流向数据")

    # 估值指标
    print("\n3. 获取估值指标:")
    valuation = aggregator.get_valuation("600519")
    if valuation:
        print(f"   获取到 {len(valuation)} 条估值指标数据")
        first_val = valuation[0]
        pe_ratio = first_val.get('peRatio', 'N/A')
        pb_ratio = first_val.get('pbRatio', 'N/A')
        print(f"   PE比率: {pe_ratio}")
        print(f"   PB比率: {pb_ratio}")
    else:
        print("   ❌ 无法获取估值指标数据")

    # 财务指标
    print("\n4. 获取财务指标:")
    financial_indicators = aggregator.get_financial_indicators("600519")
    if financial_indicators:
        print(f"   获取到 {len(financial_indicators)} 条财务指标数据")
        first_fin = financial_indicators[0]
        roe = first_fin.get('roe', 'N/A')
        gross_margin = first_fin.get('grossMargin', 'N/A')
        print(f"   ROE: {roe}")
        print(f"   毛利率: {gross_margin}")
    else:
        print("   ❌ 无法获取财务指标数据")

    # 龙虎榜
    print("\n5. 获取龙虎榜数据:")
    dragon_tiger = aggregator.get_dragon_tiger("600519")
    if dragon_tiger:
        print(f"   获取到 {len(dragon_tiger)} 条龙虎榜数据")
        first_dt = dragon_tiger[0]
        buy_top5_amount = first_dt.get('buyTop5Amount', 0)
        sell_top5_amount = first_dt.get('sellTop5Amount', 0)
        print(f"   买入前五合计: {buy_top5_amount:,.2f} 元")
        print(f"   卖出前五合计: {sell_top5_amount:,.2f} 元")
    else:
        print("   ⚠️  龙虎榜数据可能仅在特定交易日可用")


def example_scenario_functions(aggregator):
    """示例：场景功能"""
    print("\n=== 场景功能示例 ===")

    # 杜邦分析
    print("\n1. 杜邦分析:")
    dupont_analysis = aggregator.get_dupont_analysis("600519")
    if dupont_analysis:
        print(f"   获取到 {len(dupont_analysis)} 条杜邦分析数据")
        first_dupont = dupont_analysis[0]
        roe = first_dupont.get('roe', 'N/A')
        profit_margin = first_dupont.get('profitMargin', 'N/A')
        asset_turnover = first_dupont.get('assetTurnover', 'N/A')
        equity_multiplier = first_dupont.get('equityMultiplier', 'N/A')
        print(f"   ROE: {roe}")
        print(f"   净利润率: {profit_margin}")
        print(f"   资产周转率: {asset_turnover}")
        print(f"   权益乘数: {equity_multiplier}")
    else:
        print("   ❌ 无法获取杜邦分析数据")

    # 每股指标
    print("\n2. 每股指标:")
    per_share_indicators = aggregator.get_per_share_indicators("600519")
    if per_share_indicators:
        print(f"   获取到 {len(per_share_indicators)} 条每股指标数据")
        first_psi = per_share_indicators[0]
        eps = first_psi.get('eps', 'N/A')
        bvps = first_psi.get('bvps', 'N/A')
        print(f"   每股收益(EPS): {eps}")
        print(f"   每股净资产(BVPS): {bvps}")
    else:
        print("   ❌ 无法获取每股指标数据")

    # 超买超卖指标
    print("\n3. 超买超卖指标:")
    osc_indicators = aggregator.get_osc_indicators("600519")
    if osc_indicators:
        print(f"   获取到 {len(osc_indicators)} 条超买超卖指标数据")
        first_osc = osc_indicators[0]
        rsi = first_osc.get('rsi', 'N/A')
        kdj_k = first_osc.get('kdjK', 'N/A')
        print(f"   RSI: {rsi}")
        print(f"   KDJ-K: {kdj_k}")
    else:
        print("   ❌ 无法获取超买超卖指标数据")

    # 基金净值
    print("\n4. 基金净值查询:")
    fund_quotes = aggregator.get_fund_quotes("000001")
    if fund_quotes:
        print(f"   获取到 {len(fund_quotes)} 条基金净值数据")
        first_fund = fund_quotes[0]
        nav = first_fund.get('nav', 'N/A')
        change_percent = first_fund.get('changePercent', 'N/A')
        print(f"   基金净值: {nav}")
        print(f"   涨跌幅: {change_percent}")
    else:
        print("   ❌ 无法获取基金净值数据")


def example_unique_features(aggregator):
    """示例：独家功能"""
    print("\n=== 独家功能示例 ===")

    # 实体识别（Investoday 独家功能）
    print("\n1. 实体识别 (Entity Recognition) - Investoday 独家功能:")
    text = "贵州茅台发布了2023年第三季度财报，营收同比增长15%，净利润增长18%"
    entities = aggregator.entity_recognition(text)

    if entities and 'entities' in entities:
        print(f"   输入文本: {text}")
        print(f"   识别到 {len(entities['entities'])} 个实体:")
        for entity in entities['entities']:
            entity_text = entity.get('text', 'N/A')
            entity_type = entity.get('type', 'N/A')
            print(f"   - {entity_text} ({entity_type})")
    else:
        print("   ❌ 无法进行实体识别")
        print(f"   输入文本: {text}")

    # 搜索功能
    print("\n2. 综合搜索:")
    search_results = aggregator.search("茅台")
    if search_results and 'items' in search_results:
        items = search_results['items']
        print(f"   搜索关键词: 茅台")
        print(f"   找到 {len(items)} 个相关结果:")
        for item in items[:3]:  # 显示前3个结果
            symbol = item.get('symbol', 'N/A')
            name = item.get('name', 'N/A')
            print(f"   - {symbol}: {name}")
    else:
        print("   ❌ 搜索功能不可用或无结果")
        print(f"   搜索关键词: 茅台")


def main():
    """主函数"""
    if not check_api_key():
        return

    setup_logging()

    print("=" * 80)
    print("Investoday 数据源适配器使用示例")
    print("=" * 80)
    print("💡 提示: 请确保已设置 INVESTODAY_API_KEY 环境变量")
    print("💡 提示: 部分功能可能需要特定的 API 权限")
    print("=" * 80)

    try:
        # 初始化数据源聚合器
        aggregator = DataSourceAggregator(config_path="config/sources.json")

        # 运行各个示例
        example_core_features(aggregator)
        example_feature_functions(aggregator)
        example_scenario_functions(aggregator)
        example_unique_features(aggregator)

        print("\n" + "=" * 80)
        print("✅ Investoday 示例运行完成!")
        print("💡 注意: 实际数据取决于您的 API Key 权限和网络连接")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 运行示例时发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()