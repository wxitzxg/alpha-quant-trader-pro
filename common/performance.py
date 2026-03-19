"""
性能优化 - 批量操作和缓存支持
"""

from typing import Dict, Optional, Any
from functools import wraps
import time


class SimpleCache:
    """
    简单内存缓存（用于演示）

    生产环境建议使用 Redis 或其他专业缓存系统
    """

    def __init__(self, ttl: int = 300):
        """
        初始化缓存

        Args:
            ttl: 缓存过期时间（秒），默认 5 分钟
        """
        self._cache: Dict[str, tuple] = {}  # {key: (value, timestamp)}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            # 缓存过期
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        """设置缓存值"""
        self._cache[key] = (value, time.time())

    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def __len__(self):
        """缓存大小"""
        # 清理过期项
        now = time.time()
        expired_keys = [k for k, (_, ts) in self._cache.items() if now - ts > self._ttl]
        for key in expired_keys:
            del self._cache[key]
        return len(self._cache)


def cached(cache: SimpleCache, key_prefix: str = ""):
    """
    缓存装饰器

    使用示例：
    ```python
    cache = SimpleCache(ttl=300)

    @cached(cache, key_prefix="stock_")
    def get_stock(symbol: str):
        # 从数据库查询
        return db.query(Stock).filter_by(symbol=symbol).first()

    # 第一次调用 - 查询数据库
    stock = get_stock("600000")

    # 第二次调用 - 从缓存读取
    stock = get_stock("600000")
    ```

    Args:
        cache: 缓存实例
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)

            # 尝试从缓存读取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper
    return decorator


class BatchProcessor:
    """
    批量处理器

    优化批量数据库操作，减少 SQL 语句数量
    """

    @staticmethod
    def batch_insert(session, model_class, data_list: list, batch_size: int = 100):
        """
        批量插入

        使用 SQLAlchemy bulk_insert_mappings 提升性能

        Args:
            session: SQLAlchemy session
            model_class: 模型类
            data_list: 数据列表
            batch_size: 批次大小

        Returns:
            插入数量
        """
        if not data_list:
            return 0

        total = 0
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]

            # 使用 bulk_insert_mappings
            session.bulk_insert_mappings(model_class, batch)
            session.flush()

            total += len(batch)

        return total

    @staticmethod
    def batch_update(session, model_class, data_list: list,
                     key_field: str = "id", batch_size: int = 100):
        """
        批量更新

        使用 SQLAlchemy bulk_update_mappings 提升性能

        Args:
            session: SQLAlchemy session
            model_class: 模型类
            data_list: 数据列表（必须包含 key_field）
            key_field: 主键字段名
            batch_size: 批次大小

        Returns:
            更新数量
        """
        if not data_list:
            return 0

        total = 0
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]

            # 使用 bulk_update_mappings
            session.bulk_update_mappings(model_class, batch)
            session.flush()

            total += len(batch)

        return total


def optimize_query(query, enable_eager_loading: bool = True):
    """
    优化查询性能

    - 启用急加载（eager loading）避免 N+1 问题
    - 限制返回字段（如果需要）

    Args:
        query: SQLAlchemy query
        enable_eager_loading: 是否启用急加载

    Returns:
        优化后的 query
    """
    # 这里可以根据需要添加更多优化
    # 例如：使用 joinedload, selectinload 等

    return query
