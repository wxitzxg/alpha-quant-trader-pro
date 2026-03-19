"""
通用数据验证器

提供常用的验证函数和装饰器
"""

from functools import wraps
from typing import Callable, Any, Optional
from pydantic import ValidationError
from .exceptions import ValidationError as TradingValidationError


def validate_schema(schema_class):
    """
    验证输入数据的装饰器
    
    使用示例：
        @validate_schema(StockCreateSchema)
        def create_stock(self, data: dict):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取第一个参数（通常是 data 或 kwargs）
            data = kwargs.get('data') or (args[1] if len(args) > 1 else None)
            
            if data is not None:
                try:
                    # 验证数据
                    validated_data = schema_class(**data)
                    # 用验证后的数据替换原始数据
                    if 'data' in kwargs:
                        kwargs['data'] = validated_data.model_dump()
                    elif len(args) > 1:
                        args = list(args)
                        args[1] = validated_data.model_dump()
                        args = tuple(args)
                except ValidationError as e:
                    # 转换为系统异常
                    errors = []
                    for error in e.errors():
                        field = '.'.join(map(str, error['loc']))
                        msg = error['msg']
                        errors.append(f"{field}: {msg}")
                    
                    raise TradingValidationError(
                        message=f"数据验证失败: {'; '.join(errors)}",
                        field=errors[0].split(':')[0] if errors else None
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_positive(value: Any, field_name: str = "value") -> None:
    """验证数值为正数"""
    if isinstance(value, (int, float)) and value <= 0:
        raise TradingValidationError(
            message=f"{field_name} 必须为正数",
            field=field_name
        )


def validate_not_empty(value: Any, field_name: str = "value") -> None:
    """验证值不为空"""
    if not value:
        raise TradingValidationError(
            message=f"{field_name} 不能为空",
            field=field_name
        )


def validate_range(value: Any, min_val: Any, max_val: Any, field_name: str = "value") -> None:
    """验证值在范围内"""
    if value < min_val or value > max_val:
        raise TradingValidationError(
            message=f"{field_name} 必须在 {min_val} 到 {max_val} 之间",
            field=field_name
        )
