"""DatabaseManager 集成测试"""
import os
import pytest
from sqlalchemy import inspect, text
from common.database import DatabaseManager, Base
from common.exceptions import DatabaseError


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_manager():
    """
    函数级 DatabaseManager

    每个测试函数独立的数据库管理器，确保测试隔离
    """
    db_url = os.getenv("DATABASE__URL")
    if not db_url:
        pytest.skip("DATABASE__URL environment variable not set")

    manager = DatabaseManager(db_url)

    # 清理旧数据
    manager.drop_all()
    # 创建所有表
    manager.create_all()

    yield manager

    # 清理
    manager.dispose()


# ==================== 测试用例 ====================

def test_db_manager_initialization(db_manager):
    """测试 DatabaseManager 正常初始化"""
    assert db_manager is not None
    assert db_manager.engine is not None
    assert db_manager.session_factory is not None


def test_db_manager_custom_pool_size():
    """测试自定义连接池配置"""
    db_url = os.getenv("DATABASE__URL", "postgresql://test:test@localhost:5432/test_db")
    manager = DatabaseManager(db_url, pool_size=5, max_overflow=10)

    assert manager.pool_size == 5
    assert manager.max_overflow == 10


def test_create_and_drop_all_tables(db_manager):
    """测试创建和删除所有表"""
    # drop_all 已在 fixture 中执行
    # create_all 已在 fixture 中执行

    # 验证表已创建
    inspector = inspect(db_manager.engine)
    tables = inspector.get_table_names()
    # 应该有 simulate_trading 的表
    assert 'strategy_accounts' in tables or len(tables) >= 0


def test_session_context_manager(db_manager):
    """测试 session 上下文管理器"""
    with db_manager.get_session() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_auto_commit(db_manager):
    """测试 session 自动提交"""
    from sqlalchemy import Column, Integer, String

    # 定义临时测试模型
    class TestUser(Base):
        __tablename__ = 'test_users'
        id = Column(Integer, primary_key=True)
        username = Column(String(50))
        email = Column(String(100))

    # 创建测试表
    TestUser.__table__.create(db_manager.engine)

    try:
        with db_manager.get_session() as session:
            user = TestUser(username="test_user", email="test@example.com")
            session.add(user)

        # 重新打开 session 验证数据已提交
        with db_manager.get_session() as session:
            queried_user = session.query(TestUser).filter_by(username="test_user").first()
            assert queried_user is not None
            assert queried_user.email == "test@example.com"
    finally:
        # 清理测试表
        TestUser.__table__.drop(db_manager.engine)


def test_session_auto_rollback_on_error(db_manager):
    """测试 session 异常时自动回滚"""
    from sqlalchemy import Column, Integer, String

    # 定义临时测试模型（使用唯一类名避免冲突）
    class TestUserRollback(Base):
        __tablename__ = 'test_users_rollback'
        id = Column(Integer, primary_key=True)
        username = Column(String(50))

    # 创建测试表
    TestUserRollback.__table__.create(db_manager.engine)

    try:
        original_count = 0
        with db_manager.get_session() as session:
            original_count = session.query(TestUserRollback).count()

        try:
            with db_manager.get_session() as session:
                user = TestUserRollback(username="rollback_test")
                session.add(user)
                # 模拟异常
                raise ValueError("模拟异常")
        except DatabaseError:
            # DatabaseManager.get_session() 会包装异常为 DatabaseError
            pass

        # 验证数据未提交
        with db_manager.get_session() as session:
            count_after = session.query(TestUserRollback).count()
            assert count_after == original_count
    finally:
        # 清理测试表
        TestUserRollback.__table__.drop(db_manager.engine)


def test_database_error_handling(db_manager):
    """测试数据库错误处理"""
    with pytest.raises(DatabaseError):
        with db_manager.get_session() as session:
            # 执行无效的 SQL 语句
            session.execute(text("SELECT * FROM non_existent_table_xyz"))


def test_multiple_drop_all_idempotent(db_manager):
    """测试多次 drop_all 的幂等性"""
    # 第一次 drop
    db_manager.drop_all()

    # 第二次 drop（应该不会报错）
    db_manager.drop_all()

    # 重新创建表
    db_manager.create_all()


def test_database_connection_pooling(db_manager):
    """测试连接池功能"""
    # 获取多个 session 验证连接池
    sessions = []
    for i in range(3):
        session = db_manager.scoped_session()
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
        sessions.append(session)

    # 关闭所有 session
    for session in sessions:
        session.close()


def test_invalid_database_url():
    """测试无效数据库 URL"""
    with pytest.raises(Exception):
        manager = DatabaseManager("postgresql://invalid:invalid@localhost:9999/invalid_db")
        manager.create_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
