"""
Constants module

Common constants used across data sources
"""

# Price limit thresholds (percentage)
LIMIT_UP_THRESHOLD = 9.9  # 涨停阈值
LIMIT_DOWN_THRESHOLD = -9.9  # 跌停阈值

# Default timeout values (seconds)
DEFAULT_TIMEOUT = 10
BATCH_TIMEOUT = 20

# Pagination defaults
DEFAULT_PAGE_SIZE = 500
MAX_PAGE_SIZE = 1000

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 0.5

# Priority defaults
DEFAULT_PRIORITY = 100
HIGH_PRIORITY = 50
MEDIUM_PRIORITY = 75
LOW_PRIORITY = 100