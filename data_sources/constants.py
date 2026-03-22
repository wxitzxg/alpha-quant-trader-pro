"""
Constants module

Common constants used across data sources
"""

# 涨跌停阈值 (百分比 %)
# A股涨停板限制为10%，考虑到浮点计算误差使用9.9
LIMIT_UP_THRESHOLD = 9.9  # 涨停阈值
LIMIT_DOWN_THRESHOLD = -9.9  # 跌停阈值

# 默认超时配置 (秒)
DEFAULT_TIMEOUT = 10  # 单次请求默认超时
BATCH_TIMEOUT = 20  # 批量请求超时

# 分页配置
DEFAULT_PAGE_SIZE = 500  # 默认每页数量
MAX_PAGE_SIZE = 1000  # 每页最大数量

# 重试配置
MAX_RETRIES = 2  # 最大重试次数
RETRY_DELAY = 0.5  # 重试延迟 (秒)

# 优先级配置
DEFAULT_PRIORITY = 100  # 默认优先级 (低优先级)
HIGH_PRIORITY = 50  # 高优先级
MEDIUM_PRIORITY = 75  # 中优先级
LOW_PRIORITY = 100  # 低优先级