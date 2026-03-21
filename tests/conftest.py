"""
pytest 配置文件
全局 fixture 和配置
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server.main import app
from common.database import Base, get_db


# 测试数据库 URL（与 docker-compose.test.yml 保持一致）
TEST_DATABASE_URL = "postgresql://postgres:postgres_test@test-db:5432/test_stock_market"


@pytest.fixture(scope="session")
def db_engine():
    """会话级别的数据库引擎（整个测试套件共享）"""
    # 创建测试数据库引擎
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        echo=False
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 测试结束后清理
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """函数级别的数据库 session（每个测试独立）"""
    # 创建新的连接和事务
    connection = db_engine.connect()
    transaction = connection.begin()

    # 创建新的 session
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    # 回滚事务并关闭连接
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    """测试客户端，自动注入数据库 session"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # 重写依赖注入
    app.dependency_overrides[get_db] = override_get_db

    # 创建测试客户端
    with TestClient(app) as client:
        yield client

    # 清理依赖重写
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def clean_database(db_session):
    """每个测试前自动清理数据库（TRUNCATE 所有表）"""
    # 获取所有表名（排除系统表）
    result = db_session.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT LIKE 'pg_%'
        AND tablename NOT LIKE 'sql_%'
        ORDER BY tablename
    """)
    tables = [row[0] for row in result]

    # 按依赖顺序删除数据（使用 CASCADE 处理外键）
    for table in reversed(tables):
        try:
            db_session.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        except Exception as e:
            # 某些表可能已被 CASCADE 清理，忽略错误
            pass

    db_session.commit()


@pytest.fixture
def mock_tushare_api():
    """
    Mock Tushare API 调用

    使用示例:
    ```python
    def test_something(mock_tushare_api):
        # mock_tushare_api 已经自动配置了常用端点
        # 你可以添加自定义响应:
        mock_tushare_api.add(
            responses.GET,
            "http://mock-api:9000/tushare/custom",
            json={"code": 0, "data": {"custom": "value"}},
            status=200
        )
        # 调用你的代码...
    ```
    """
    import responses

    with responses.RequestsMock() as rsps:
        # Mock Tushare 基础数据
        rsps.add(
            responses.GET,
            "http://mock-api:9000/tushare/stock/basic",
            json={
                "code": 0,
                "msg": "success",
                "data": {
                    "ts_code": "600519.SH",
                    "name": "贵州茅台",
                    "price": 1850.0,
                    "change_pct": 1.5
                }
            },
            status=200
        )

        # Mock Tushare K线数据
        rsps.add(
            responses.GET,
            "http://mock-api:9000/tushare/stock/kline",
            json={
                "code": 0,
                "msg": "success",
                "data": [
                    {
                        "trade_date": "20240101",
                        "open": 1840.0,
                        "high": 1860.0,
                        "low": 1835.0,
                        "close": 1850.0,
                        "volume": 10000
                    }
                ]
            },
            status=200
        )

        yield rsps


@pytest.fixture
def mock_investoday_api():
    """
    Mock Investoday API 调用
    """
    import responses

    with responses.RequestsMock() as rsps:
        # Mock Investoday 行情
        rsps.add(
            responses.GET,
            "http://mock-api:9000/investoday/stock/quote",
            json={
                "status": "success",
                "code": 200,
                "data": {
                    "symbol": "600519",
                    "price": 1850.0,
                    "change_pct": 1.5
                }
            },
            status=200
        )

        yield rsps


@pytest.fixture
def mock_all_external_apis(mock_tushare_api, mock_investoday_api):
    """同时 Mock 所有外部 API"""
    pass  # 通过参数自动激活两个 fixture


# 自定义标记
def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line(
        "markers", "unit: 标记为单元测试（不依赖数据库）"
    )
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试（需要数据库）"
    )
    config.addinivalue_line(
        "markers", "e2e: 标记为端到端测试（完整服务栈）"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )


def pytest_collection_modifyitems(items):
    """自动为未标记的测试添加默认标记"""
    for item in items:
        # 如果测试在 test_api_server 目录下且未标记，自动标记为 integration
        if "api_server" in item.nodeid and not any(
            marker.name in ["unit", "integration", "e2e", "slow"]
            for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.integration)
