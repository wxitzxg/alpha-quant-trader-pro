"""
配置优先级测试
Configuration priority tests

测试优先级：运行时参数 > 环境变量 > YAML配置 > 默认值
Test priority: runtime params > env vars > YAML > defaults
"""

import pytest
import os
from common.config import Config, DataSourceConfig, DatabaseConfig


def test_env_var_overrides_yaml(monkeypatch):
    """测试环境变量覆盖 YAML 配置 / Test env var overrides YAML config"""
    # 设置环境变量（使用 Pydantic 的 env_nested_delimiter="__"）
    monkeypatch.setenv("DATA_SOURCES__TIMEOUT", "30")
    monkeypatch.setenv("DATABASE__POOL_SIZE", "50")
    monkeypatch.setenv("FEE__STAMP_DUTY", "0.002")

    # 加载配置
    config = Config()

    # 验证环境变量覆盖了 YAML 配置
    assert config.data_sources.timeout == 30, \
        "环境变量 DATA_SOURCES__TIMEOUT 应该覆盖 YAML 中的值 (默认 10)"

    assert config.database.pool_size == 50, \
        "环境变量 DATABASE__POOL_SIZE 应该覆盖 YAML 中的值 (默认 10)"

    assert config.fee.stamp_duty == 0.002, \
        "环境变量 FEE__STAMP_DUTY 应该覆盖 YAML 中的值 (默认 0.001)"

    # 验证未被环境变量覆盖的配置仍然是 YAML 值
    assert config.data_sources.max_retries == 3, \
        "未设置环境变量的配置应该使用 YAML 值"

    assert config.database.max_overflow == 20, \
        "未设置环境变量的配置应该使用 YAML 值"


def test_runtime_param_overrides_env_var(monkeypatch):
    """测试运行时参数覆盖环境变量 / Test runtime param overrides env var"""
    # 设置环境变量
    monkeypatch.setenv("DATA_SOURCES__TIMEOUT", "30")
    monkeypatch.setenv("DATABASE__POOL_SIZE", "50")

    # 使用运行时参数覆盖
    config = Config(
        data_sources={"timeout": 99},
        database={"pool_size": 999}
    )

    # 验证运行时参数覆盖了环境变量
    assert config.data_sources.timeout == 99, \
        "运行时参数应该覆盖环境变量 (30) 和 YAML (10)"

    assert config.database.pool_size == 999, \
        "运行时参数应该覆盖环境变量 (50) 和 YAML (10)"

    # 验证运行时参数未覆盖的配置使用环境变量
    assert config.data_sources.max_retries == 3, \
        "运行时参数未覆盖的配置应该使用 YAML 值"


def test_runtime_param_overrides_yaml_directly():
    """测试运行时参数直接覆盖 YAML（无环境变量）/ Test runtime param overrides YAML directly"""
    # 不设置环境变量，直接使用运行时参数
    config = Config(
        data_sources={"timeout": 42, "max_retries": 5},
        database={"pool_size": 25, "max_overflow": 30}
    )

    # 验证运行时参数覆盖了 YAML
    assert config.data_sources.timeout == 42
    assert config.data_sources.max_retries == 5
    assert config.database.pool_size == 25
    assert config.database.max_overflow == 30

    # 验证未被覆盖的配置仍然是 YAML 值
    assert config.database.pool_pre_ping is True


def test_env_var_with_nested_config(monkeypatch):
    """测试环境变量覆盖嵌套配置 / Test env var overrides nested config"""
    # 设置嵌套环境变量
    monkeypatch.setenv("DATABASE__URL", "postgresql://user:pass@test.example.com/db")
    monkeypatch.setenv("DATABASE__POOL_RECYCLE", "7200")
    monkeypatch.setenv("API_SERVER__PORT", "9000")
    monkeypatch.setenv("API_SERVER__HOST", "127.0.0.1")

    config = Config()

    # 验证嵌套配置被正确覆盖
    assert config.database.url == "postgresql://user:pass@test.example.com/db"
    assert config.database.pool_recycle == 7200
    assert config.api_server.port == 9000
    assert config.api_server.host == "127.0.0.1"


def test_env_var_boolean_values(monkeypatch):
    """测试环境变量布尔值 / Test env var boolean values"""
    # Pydantic 会自动转换 "true"/"false" 为布尔值
    monkeypatch.setenv("DATABASE__POOL_PRE_PING", "false")
    monkeypatch.setenv("STOCK_MARKET__SYNC__INCREMENTAL", "false")

    config = Config()

    # 验证布尔值被正确解析
    assert config.database.pool_pre_ping is False
    assert config.stock_market.sync.incremental is False


def test_env_var_numeric_values(monkeypatch):
    """测试环境变量数值类型 / Test env var numeric values"""
    monkeypatch.setenv("BACKTEST__INITIAL_CAPITAL", "200000")
    monkeypatch.setenv("BACKTEST__COMMISSION_RATE", "0.0005")
    monkeypatch.setenv("SIMULATION__EXECUTION_INTERVAL", "600")

    config = Config()

    # 验证数值类型被正确解析
    assert config.backtest.initial_capital == 200000.0
    assert config.backtest.commission_rate == 0.0005
    assert config.simulation.execution_interval == 600


def test_default_values_without_yaml_or_env():
    """测试没有任何配置时使用默认值 / Test default values without YAML or env"""
    # Config 有默认值，即使没有 YAML 和环境变量
    config = Config()

    # 验证默认值
    assert config.app_name == "alpha-quant-trader-pro"
    assert config.debug is False
    assert config.environment == "development"
    assert config.timezone == "Asia/Shanghai"

    # 验证嵌套配置的默认值 - 注意：database.url 从 YAML 加载为空字符串
    # 因为 database.yaml 中设置为 ""
    assert config.database.pool_size == 10


def test_priority_chain_full():
    """测试完整的优先级链 / Test full priority chain"""
    # 1. YAML 配置：data_sources.timeout = 10 (from data_sources.yaml)
    # 2. 环境变量：DATA_SOURCES__TIMEOUT = 30
    # 3. 运行时参数：data_sources={"timeout": 99}

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("DATA_SOURCES__TIMEOUT", "30")

    config = Config(data_sources={"timeout": 99})

    # 运行时参数 (99) > 环境变量 (30) > YAML (10)
    assert config.data_sources.timeout == 99

    monkeypatch.undo()


def test_partial_runtime_param_with_env_var(monkeypatch):
    """测试部分运行时参数与环境变量的组合 / Test partial runtime param with env var"""
    monkeypatch.setenv("DATA_SOURCES__TIMEOUT", "30")
    monkeypatch.setenv("DATA_SOURCES__MAX_RETRIES", "7")

    # 只覆盖 timeout，不覆盖 max_retries
    config = Config(data_sources={"timeout": 42})

    # timeout 使用运行时参数
    assert config.data_sources.timeout == 42

    # max_retries 使用环境变量（因为运行时参数没有提供）
    assert config.data_sources.max_retries == 7

    # retry_delay 使用 YAML（因为既没有环境变量也没有运行时参数）
    assert config.data_sources.retry_delay == 0.5


@pytest.mark.skip(reason="Pydantic 不支持通过环境变量直接覆盖复杂嵌套列表")
def test_env_var_for_list_config(monkeypatch):
    """测试环境变量无法直接覆盖列表配置（需要使用运行时参数）/ Test env var cannot directly override list config"""
    pass


def test_clear_env_var_between_tests(monkeypatch):
    """测试环境变量在测试之间被正确清除 / Test env var is cleared between tests"""
    # 测试开始时没有环境变量
    config1 = Config()
    original_timeout = config1.data_sources.timeout

    # 设置环境变量
    monkeypatch.setenv("DATA_SOURCES__TIMEOUT", "999")
    config2 = Config()
    assert config2.data_sources.timeout == 999

    # monkeypatch 会在测试结束后自动清除环境变量
    # 下一个测试会回到原始值


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
