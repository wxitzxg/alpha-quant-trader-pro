"""验证 migrations 文件夹已删除"""
import pytest
from pathlib import Path


def test_migrations_folder_deleted():
    """测试 migrations 文件夹已彻底删除"""
    migrations_path = Path(__file__).parent.parent.parent / "stock_market" / "migrations"
    assert not migrations_path.exists(), f"migrations folder still exists: {migrations_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
