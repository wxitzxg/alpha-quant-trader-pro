# tests/portfolio_manager/test_config.py
"""配置加载测试"""

import pytest
import json
import tempfile
from pathlib import Path
from portfolio_manager.config import PortfolioConfig


def test_config_default():
    """测试默认配置"""
    config = PortfolioConfig()

    # 测试数据库配置
    db_url = config.get_database_url()
    assert 'localhost' in db_url
    assert 'portfolio_db' in db_url

    # 测试手续费配置
    fee_config = config.get_fee_config()
    assert fee_config.stamp_duty == 0.0005
    assert fee_config.broker_commission == 0.00015


def test_config_from_file():
    """测试从文件加载配置"""
    # 创建临时配置文件
    config_data = {
        'database': {
            'host': 'test-host',
            'port': 5433,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        },
        'fee_config': {
            'stamp_duty': 0.001,
            'broker_commission': 0.0002,
            'min_commission': 10.0
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = PortfolioConfig(temp_path)

        # 测试数据库配置
        db_url = config.get_database_url()
        assert 'test-host' in db_url
        assert '5433' in db_url

        # 测试手续费配置
        fee_config = config.get_fee_config()
        assert fee_config.stamp_duty == 0.001
        assert fee_config.broker_commission == 0.0002
        assert fee_config.min_commission == 10.0
    finally:
        Path(temp_path).unlink()
