"""
类型注解使用示例
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal


# 1. 基本类型注解
def add_numbers(a: int, b: int) -> int:
    """添加两个数字"""
    return a + b


# 2. 可选类型
def get_user(name: str) -> Optional[str]:
    """获取用户，可能返回 None"""
    if name == "admin":
        return "管理员"
    return None


# 3. 列表和字典
def process_data(items: List[str]) -> Dict[str, int]:
    """处理数据列表"""
    result = {}
    for item in items:
        result[item] = len(item)
    return result


# 4. 复杂类型
def get_stock_info() -> Tuple[str, float, datetime]:
    """获取股票信息"""
    return ("600000", 10.5, datetime.now())


# 5. 泛型类型
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    def get(self, id: int) -> Optional[T]:
        """获取单个对象"""
        pass
    
    def list(self) -> List[T]:
        """获取对象列表"""
        pass


# 6. 类型别名
from typing import NewType

StockSymbol = NewType('StockSymbol', str)
Price = NewType('Price', float)

def buy_stock(symbol: StockSymbol, price: Price) -> None:
    """买入股票"""
    print(f"买入 {symbol} @ {price}")


# 7. Union 类型
from typing import Union

def parse_value(value: Union[int, float, str]) -> float:
    """解析值"""
    return float(value)


# 8. Python 3.10+ 的新语法
def new_syntax(value: int | float | str) -> int | float:
    """使用 | 语法"""
    return float(value)


# 9. 类型注解示例类
class Stock:
    """股票类"""
    
    symbol: str
    name: str
    price: float
    change: Optional[float]
    tags: List[str]
    metadata: Dict[str, Any]
    
    def __init__(
        self,
        symbol: str,
        name: str,
        price: float,
        change: Optional[float] = None
    ):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.change = change
        self.tags = []
        self.metadata = {}


# 10. 异步函数类型注解
import asyncio
from typing import Awaitable

async def fetch_data() -> Awaitable[List[Stock]]:
    """异步获取数据"""
    await asyncio.sleep(0.1)
    return []


if __name__ == "__main__":
    # 使用示例
    result = add_numbers(1, 2)
    print(f"结果: {result}")
    
    user = get_user("admin")
    print(f"用户: {user}")
    
    stock = Stock("600000", "浦发银行", 10.5)
    print(f"股票: {stock.symbol} - {stock.name}")
    
    buy_stock(StockSymbol("600519"), Price(1600.0))
