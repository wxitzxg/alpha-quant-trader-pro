"""测试并发同步使用配置"""
import pytest
from unittest.mock import Mock, patch
from stock_market.sync.concurrent_sync import ConcurrentSyncManager


def test_concurrent_sync_uses_config_by_default():
    """测试默认使用配置中的 concurrency 值"""
    mock_db = Mock()

    with patch('stock_market.sync.concurrent_sync.get_config') as mock_get_config:
        # 模拟配置
        mock_config = Mock()
        mock_config.stock_market.sync.concurrency = 10
        mock_get_config.return_value = mock_config

        manager = ConcurrentSyncManager(mock_db)

        # 应该使用配置中的值
        assert manager.max_workers == 10


def test_concurrent_sync_can_override():
    """测试可以覆盖配置值"""
    mock_db = Mock()

    with patch('stock_market.sync.concurrent_sync.get_config') as mock_get_config:
        # 即使配置是 5，显式传递的值应该被使用
        mock_config = Mock()
        mock_config.stock_market.sync.concurrency = 5
        mock_get_config.return_value = mock_config

        manager = ConcurrentSyncManager(mock_db, max_workers=8)

        assert manager.max_workers == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
