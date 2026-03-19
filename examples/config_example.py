"""
统一配置系统使用示例
"""

from common.config import get_config, Config, save_config


def example_load_config():
    """示例：加载配置"""
    print("=" * 60)
    print("加载配置示例")
    print("=" * 60)

    # 方式 1：获取当前配置
    config = get_config()
    print(f"✓ 应用名称: {config.app_name}")
    print(f"✓ 环境: {config.environment}")
    print(f"✓ 调试模式: {config.debug}")

    # 方式 2：获取数据库配置
    db_url = config.get_database_url()
    print(f"✓ 数据库 URL: {db_url}")

    # 方式 3：获取手续费配置
    fee_config = config.get_fee_config()
    print(f"✓ 印花税: {fee_config.stamp_duty}")
    print(f"✓ 交易所费用: {fee_config.exchange_fee}")
    print(f"✓ 券商佣金: {fee_config.broker_commission}")
    print(f"✓ 最低佣金: {fee_config.min_commission}")


def example_override_config():
    """示例：覆盖配置"""
    print("\n" + "=" * 60)
    print("覆盖配置示例")
    print("=" * 60)

    # 创建自定义配置
    custom_config = Config(
        app_name="my-quant-app",
        debug=True,
        environment="testing"
    )

    print(f"✓ 应用名称: {custom_config.app_name}")
    print(f"✓ 环境: {custom_config.environment}")


def example_save_config():
    """示例：保存配置"""
    print("\n" + "=" * 60)
    print("保存配置示例")
    print("=" * 60)

    config = get_config()

    # 修改配置
    config.debug = True

    # 保存到文件
    save_config("config/local.json")
    print("✓ 配置已保存到 config/local.json")


def example_fee_calculator_with_config():
    """示例：手续费计算器使用统一配置"""
    print("\n" + "=" * 60)
    print("手续费计算器 - 使用统一配置")
    print("=" * 60)

    from portfolio_manager.fee_calculator import FeeCalculator

    # 创建计算器（自动从统一配置加载）
    calculator = FeeCalculator()

    # 计算手续费
    amount = 10000.0
    buy_fee = calculator.calculate_buy_fee(amount)
    sell_fee = calculator.calculate_sell_fee(amount)

    print(f"✓ 交易金额: {amount:.2f}")
    print(f"✓ 买入手续费: {buy_fee:.2f}")
    print(f"✓ 卖出手续费: {sell_fee:.2f}")


def example_configure_logging():
    """示例：配置日志"""
    print("\n" + "=" * 60)
    print("日志配置示例")
    print("=" * 60)

    import logging
    from common.config import get_config

    config = get_config()

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format
    )

    logger = logging.getLogger(__name__)
    logger.info("✓ 日志配置完成")


if __name__ == "__main__":
    example_load_config()
    example_override_config()
    example_fee_calculator_with_config()
    example_configure_logging()
    example_save_config()

    print("\n" + "=" * 60)
    print("✓ 所有配置示例执行完成")
    print("=" * 60)
