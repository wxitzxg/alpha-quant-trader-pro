"""测试环境变量覆盖配置"""
import pytest
import os
from common.config import Config, reload_config


def test_env_var_override():
    """测试环境变量可以覆盖配置"""
    # 设置环境变量
    os.environ['STOCK_MARKET__SYNC__CONCURRENCY'] = '20'
    os.environ['STOCK_MARKET__SYNC__KLINE_WORKERS'] = '15'

    # 重新加载配置
    reload_config()

    config = Config()

    # 环境变量应该覆盖 YAML 配置
    assert config.stock_market.sync.concurrency == 20
    assert config.stock_market.sync.kline_workers == 15

    # 清理
    del os.environ['STOCK_MARKET__SYNC__CONCURRENCY']
    del os.environ['STOCK_MARKET__SYNC__KLINE_WORKERS']
    reload_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
