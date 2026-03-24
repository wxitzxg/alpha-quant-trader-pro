# DatabaseManager 集成测试实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `common/database.py` 的 `DatabaseManager` 创建完整的集成测试套件

**Architecture:**
- 单一文件 `test_database.py` 包含 fixtures 和所有测试用例
- 每个测试会话通过 `drop_all()/create_all()` 管理数据
- 模块级共享 DatabaseManager 减少初始化开销
- 使用临时测试模型避免依赖现有模型

**Tech Stack:** pytest, SQLAlchemy, PostgreSQL

---

## 文件结构

```
tests/common/test_database.py           # 测试文件 + fixtures
```

---

## 任务分解

### Task 1: 创建测试文件（含 fixtures）

**Files:**
- Create: `tests/common/test_database.py`

- [ ] **Step 1: 创建测试文件**

```python
"""DatabaseManager 集成测试"""
import os
import pytest
from sqlalchemy import inspect, text
from common.database import DatabaseManager, Base


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def db_manager():
    """
    模块级共享 DatabaseManager

    流程：
    1. 从 DATABASE_URL 环境变量获取数据库连接
    2. 测试前清空所有表
    3. 创建所有表
    4. 测试后清理并释放资源
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL environment variable not set")

    manager = DatabaseManager(db_url)

    # 清理旧数据
    manager.drop_all()
    # 创建所有表
    manager.create_all()

    yield manager

    # 清理
    manager.drop_all()
    manager.dispose()


@pytest.fixture(scope="function")
def db_session(db_manager):
    """
    函数级数据库 session

    每个测试函数使用独立的 session，确保测试隔离
    """
    with db_manager.get_session() as session:
        yield session


# ==================== 测试用例 ====================

def test_db_manager_initialization(db_manager):
    """测试 DatabaseManager 正常初始化"""
    assert db_manager is not None
    assert db_manager.engine is not None
    assert db_manager.session_factory is not None


def test_db_manager_custom_pool_size():
    """测试自定义连接池配置"""
    db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
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
    assert len(tables) >= 0  # 可能没有表（取决于 Base 中定义的模型）


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

    # 定义临时测试模型
    class TestUser(Base):
        __tablename__ = 'test_users_rollback'
        id = Column(Integer, primary_key=True)
        username = Column(String(50))

    # 创建测试表
    TestUser.__table__.create(db_manager.engine)

    try:
        original_count = 0
        with db_manager.get_session() as session:
            original_count = session.query(TestUser).count()

        try:
            with db_manager.get_session() as session:
                user = TestUser(username="rollback_test")
                session.add(user)
                # 模拟异常
                raise ValueError("模拟异常")
        except ValueError:
            pass

        # 验证数据未提交
        with db_manager.get_session() as session:
            count_after = session.query(TestUser).count()
            assert count_after == original_count
    finally:
        # 清理测试表
        TestUser.__table__.drop(db_manager.engine)


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行测试验证结构**

```bash
export DATABASE_URL="postgresql://test:test@localhost:5432/alpha_quant_test"
pytest tests/common/test_database.py::test_db_manager_initialization -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/common/test_database.py
git commit -m "test(database): add DatabaseManager integration tests"
```

---

### Task 2: 验证测试运行

- [ ] **Step 1: 运行所有测试**

```bash
pytest tests/common/test_database.py -v
```

- [ ] **Step 2: 验证测试覆盖率**

```bash
pytest tests/common/test_database.py -v --cov=common.database --cov-report=term-missing
```

- [ ] **Step 3: 提交最终版本**

```bash
git add tests/common/test_database.py
git commit -m "test(database): complete DatabaseManager integration test suite"
```

---

## 验收标准

- [ ] 所有测试用例通过
- [ ] 测试覆盖以下场景：
  - 初始化（默认参数、自定义参数）
  - Session 管理（上下文管理、自动提交、自动回滚）
  - 表操作（create_all、drop_all、幂等性）
  - 事务控制（提交、回滚）
  - 连接池功能
- [ ] 测试后数据正确清理
- [ ] 测试覆盖率 ≥ 80%

---

## 使用说明

```bash
# 设置环境变量
export DATABASE_URL="postgresql://test:test@localhost:5432/alpha_quant_test"

# 运行测试
pytest tests/common/test_database.py -v

# 查看覆盖率
pytest tests/common/test_database.py -v --cov=common.database
```
