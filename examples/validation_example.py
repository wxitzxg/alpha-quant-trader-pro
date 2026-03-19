"""
数据验证使用示例

演示如何使用 Pydantic Schemas 进行数据验证
"""

from datetime import date
from stock_market.schemas import (
    StockCreateSchema,
    StockUpdateSchema,
    KLineCreateSchema
)
from portfolio_manager.schemas import (
    PositionCreateSchema,
    TransactionCreateSchema
)


def example_stock_validation():
    """股票数据验证示例"""
    print("=" * 60)
    print("股票数据验证示例")
    print("=" * 60)
    
    # 1. 创建股票数据验证
    try:
        stock_data = {
            "symbol": "600000",
            "name": "浦发银行",
            "exchange": "SH",
            "list_date": date(1999, 11, 10),
            "industry": "银行",
            "total_shares": 29352080397
        }
        
        # 验证数据
        validated_stock = StockCreateSchema(**stock_data)
        print("✅ 股票数据验证通过")
        print(f"  股票代码: {validated_stock.symbol}")
        print(f"  股票名称: {validated_stock.name}")
        print(f"  交易所: {validated_stock.exchange}")
        
    except Exception as e:
        print(f"❌ 股票数据验证失败: {e}")
    
    # 2. 更新股票数据验证
    try:
        update_data = {
            "industry": "银行",
            "is_active": True
        }
        
        validated_update = StockUpdateSchema(**update_data)
        print("\n✅ 股票更新数据验证通过")
        print(f"  行业: {validated_update.industry}")
        print(f"  是否活跃: {validated_update.is_active}")
        
    except Exception as e:
        print(f"\n❌ 股票更新数据验证失败: {e}")


def example_kline_validation():
    """K线数据验证示例"""
    print("\n" + "=" * 60)
    print("K线数据验证示例")
    print("=" * 60)
    
    # 创建K线数据
    try:
        kline_data = {
            "symbol": "600000",
            "date": date(2023, 1, 1),
            "interval": "1d",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000
        }
        
        validated_kline = KLineCreateSchema(**kline_data)
        print("✅ K线数据验证通过")
        print(f"  股票代码: {validated_kline.symbol}")
        print(f"  日期: {validated_kline.date}")
        print(f"  OHLC: {validated_kline.open}, {validated_kline.high}, {validated_kline.low}, {validated_kline.close}")
        
    except Exception as e:
        print(f"❌ K线数据验证失败: {e}")
    
    # 测试价格验证
    try:
        invalid_kline = {
            "symbol": "600000",
            "date": date(2023, 1, 1),
            "interval": "1d",
            "open": 10.0,
            "high": 9.5,  # 错误：最高价低于开盘价
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000
        }
        
        KLineCreateSchema(**invalid_kline)
        print("\n❌ 价格验证未触发（应该失败）")
        
    except Exception as e:
        print(f"\n✅ 价格验证生效: {e}")


def example_portfolio_validation():
    """持仓数据验证示例"""
    print("\n" + "=" * 60)
    print("持仓数据验证示例")
    print("=" * 60)
    
    # 创建持仓
    try:
        position_data = {
            "symbol": "600000",
            "quantity": 100,
            "cost_price": 10.0,
            "current_price": 10.5
        }
        
        validated_position = PositionCreateSchema(**position_data)
        print("✅ 持仓数据验证通过")
        print(f"  股票代码: {validated_position.symbol}")
        print(f"  持仓数量: {validated_position.quantity}")
        print(f"  成本价: {validated_position.cost_price}")
        
    except Exception as e:
        print(f"❌ 持仓数据验证失败: {e}")
    
    # 创建交易
    try:
        transaction_data = {
            "symbol": "600000",
            "transaction_type": "buy",
            "quantity": 100,
            "price": 10.0
        }
        
        validated_transaction = TransactionCreateSchema(**transaction_data)
        print("\n✅ 交易数据验证通过")
        print(f"  交易类型: {validated_transaction.transaction_type}")
        print(f"  数量: {validated_transaction.quantity}")
        print(f"  价格: {validated_transaction.price}")
        
    except Exception as e:
        print(f"\n❌ 交易数据验证失败: {e}")


def example_using_decorator():
    """使用验证装饰器示例"""
    print("\n" + "=" * 60)
    print("使用验证装饰器示例")
    print("=" * 60)
    
    from common.validators import validate_schema
    
    @validate_schema(StockCreateSchema)
    def create_stock(data):
        """创建股票，自动验证输入"""
        print(f"  ✅ 数据已验证: {data['symbol']} - {data['name']}")
    
    # 正确的数据
    try:
        create_stock({
            "symbol": "600000",
            "name": "浦发银行",
            "exchange": "SH",
            "list_date": "1999-11-10"
        })
    except Exception as e:
        print(f"  ❌ {e}")
    
    # 错误的数据
    try:
        create_stock({
            "symbol": "",  # 错误：空字符串
            "name": "测试",
            "exchange": "SH",
            "list_date": "1999-11-10"
        })
    except Exception as e:
        print(f"  ✅ 捕获验证错误: {e}")


if __name__ == "__main__":
    example_stock_validation()
    example_kline_validation()
    example_portfolio_validation()
    example_using_decorator()
    
    print("\n" + "=" * 60)
    print("✅ 所有验证示例执行完毕")
    print("=" * 60)
