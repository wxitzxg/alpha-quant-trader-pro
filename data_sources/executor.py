"""
降级执行器模块

按优先级执行数据源，失败时自动降级到备用源
"""

import time
import logging
from typing import List, Callable, Optional, TypeVar, Dict, Any
from .base import DataSourceAdapter
from .exceptions import DataSourceError

T = TypeVar('T')

logger = logging.getLogger(__name__)


class FallbackExecutor:
    """
    降级执行器

    根据配置的优先级顺序执行数据源
    当某个数据源失败时，自动降级到下一个数据源
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 配置字典，包含 fallback 和 sources 配置
        """
        self.config = config
        self.logger = logger

    def execute_with_fallback(
        self,
        adapters: List[DataSourceAdapter],
        operation: Callable[[DataSourceAdapter], T],
        operation_name: str
    ) -> Optional[T]:
        """
        执行操作，失败时降级到下一个数据源

        Args:
            adapters: 已排序的适配器列表（按优先级）
            operation: 要执行的操作函数，接受一个适配器参数
            operation_name: 操作名称（用于日志）

        Returns:
            操作结果，所有数据源都失败返回 None
        """
        fallback_config = self.config.get('fallback', {})
        max_retries = fallback_config.get('max_retries', 2)
        retry_delay = fallback_config.get('retry_delay', 0.5)
        log_failures = fallback_config.get('log_failures', True)

        # 遍历所有适配器（按优先级）
        for adapter in adapters:
            # 检查适配器是否可用
            if not adapter.is_available():
                self.logger.debug(f"Skipping unavailable adapter: {adapter.name}")
                continue

            # 获取该数据源的配置
            timeout = self._get_source_timeout(adapter.name, operation_name)

            # 对每个适配器进行重试
            for attempt in range(max_retries):
                try:
                    self.logger.info(
                        f"Executing {operation_name} on {adapter.name} "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    # 执行操作
                    result = operation(adapter)

                    # 检查结果
                    if result is not None:
                        self.logger.info(
                            f"✓ {operation_name} succeeded on {adapter.name}"
                        )
                        return result

                    self.logger.warning(
                        f"{operation_name} returned None on {adapter.name}"
                    )

                except DataSourceError as e:
                    if log_failures:
                        self.logger.error(
                            f"✗ {operation_name} failed on {adapter.name}: {e}"
                        )

                    # 最后一次重试，继续降级
                    if attempt >= max_retries - 1:
                        break

                    # 等待后重试
                    time.sleep(retry_delay)

                except Exception as e:
                    if log_failures:
                        self.logger.error(
                            f"✗ {operation_name} crashed on {adapter.name}: {e}",
                            exc_info=True
                        )

                    # 非预期异常，直接降级
                    break

            # 当前数据源所有重试都失败，继续降级到下一个
            continue

        # 所有数据源都失败
        self.logger.error(f"All sources failed for {operation_name}")
        return None

    def _get_source_timeout(self, source_name: str, operation_name: str) -> int:
        """
        获取数据源的超时配置

        Args:
            source_name: 数据源名称
            operation_name: 操作类别

        Returns:
            超时时间（秒），默认 5
        """
        sources_config = self.config.get('sources', {})
        category_config = sources_config.get(operation_name, [])

        for cfg in category_config:
            if cfg.get('name') == source_name:
                return cfg.get('timeout', 5)

        return 5
