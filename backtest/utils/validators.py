"""Input Validators - 输入验证"""


def validate_date_format(date_str: str) -> bool:
    """验证日期格式 (YYYY-MM-DD)"""
    import re
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def validate_positive_number(value: float, name: str = "value") -> None:
    """验证正数"""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_percentage(value: float, name: str = "percentage") -> None:
    """验证百分比 (0-1)"""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    return bool(symbol and len(symbol) <= 10)
