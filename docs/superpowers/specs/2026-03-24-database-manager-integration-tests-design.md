# DatabaseManager 集成测试设计

## 概述

为 `common/database.py` 中的 `DatabaseManager` 类创建集成测试，验证其与 PostgreSQL 数据库的实际交互。

## 核心策略

### 环境配置
- **使用 `DATABASE_URL` 环境变量** 指定测试数据库
- 无需额外配置文件，保持简洁

### 测试流程
```python
# 每个测试会话
1. drop_all()  # 清空所有表
2. create_all()  # 重建所有表
3. 执行测试用例
4. drop_all()  # 清理
```

### 连接管理
- **模块级共享 DatabaseManager**（pytest fixture）
- 减少重复初始化开销

## 测试覆盖

### 1. 初始化测试
- ✅ 正常初始化（默认参数）
- ✅ 自定义连接池配置（pool_size, max_overflow）
- ✅ 连接预检（pool_pre_ping）

### 2. Session 管理测试
- ✅ `get_session()` 正常获取和使用
- ✅ 上下文管理器正确关闭 session
- ✅ session 自动提交（无异常时）
- ✅ session 自动回滚（异常时）

### 3. 表操作测试
- ✅ `create_all()` 创建所有表
- ✅ `drop_all()` 删除所有表
- ✅ 多次创建/删除的幂等性

### 4. 事务控制测试
- ✅ 成功事务自动提交
- ✅ 异常事务自动回滚
- ✅ 回滚后数据库状态正确

### 5. 资源管理测试
- ✅ `dispose()` 正确释放连接池
- ✅ 资源释放后无法再使用 session

## 实现要点

### 文件结构
```
tests/common/test_database_integration.py  # 测试文件
tests/common/conftest.py                   # pytest fixture
```

### Fixture 设计
```python
@pytest.fixture(scope="module")
def db_manager():
    """模块级共享 DatabaseManager"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL environment variable not set")

    manager = DatabaseManager(db_url)
    manager.drop_all()  # 清理旧数据
    manager.create_all()  # 创建表

    yield manager

    manager.drop_all()  # 清理
    manager.dispose()   # 释放资源
```

### 测试用例示例
```python
def test_session_context_manager(db_manager):
    """测试 session 上下文管理器"""
    with db_manager.get_session() as session:
        # 执行数据库操作
        result = session.execute("SELECT 1")
        assert result.scalar() == 1

    # session 应该已关闭
```

## 依赖

- 使用现有的数据模型（`common.database.Base.metadata`）
- pytest 框架（项目已配置）
- PostgreSQL 数据库（测试专用）

## 运行方式

```bash
# 设置环境变量
export DATABASE_URL="postgresql://test:test@localhost:5432/alpha_quant_test"

# 运行测试
pytest tests/common/test_database_integration.py -v
```
