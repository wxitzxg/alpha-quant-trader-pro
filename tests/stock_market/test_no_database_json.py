"""验证 database.json 已删除"""
import pytest
from pathlib import Path


def test_database_json_deleted():
    """测试 database.json 已彻底删除"""
    database_json_path = Path(__file__).parent.parent.parent / "stock_market" / "config" / "database.json"
    assert not database_json_path.exists(), f"database.json still exists: {database_json_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
