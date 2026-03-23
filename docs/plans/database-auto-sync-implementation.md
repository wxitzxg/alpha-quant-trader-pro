# 数据库自动同步实施计划
## Plan ID: database-auto-sync-2026-03-22
## Status: Pending Approval
## Priority: High

---

## 1. 背景

当前系统存在数据库表同步问题：
- **stock_market** 模块有表但未在启动时自动创建
- **portfolio_manager** 在 `commands.py` 中手动创建表
- **api_server** 启动时未同步数据库
- 各模块使用不同 `Base` 类，导致表分散管理

## 2. 目标

- ✅ 统一所有模块使用 `common.database.Base`
- ✅ 在系统启动时自动同步所有数据库表
- ✅ 确保测试环境和生产环境的一致性
- ✅ 保留向后兼容性（不破坏现有代码）

## 3. 决策记录

| 问题 | 决定 | 理由 |
|------|------|------|
| **Base 类统一** | 统一使用 `common.database.Base` | 避免表分散，便于集中管理 |
| **同步时机** | 系统启动时同步 | 保证服务可用性，快速失败优于运行时错误 |
| **测试处理** | 保持现有测试机制 | `conftest.py` 已有完善的测试数据库管理 |

## 4. 实施步骤

### 阶段 1: Base 类统一 (5分钟)

#### 4.1.1 修改 `portfolio_manager/database.py`

```python
# Before
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# After
from common.database import Base
```

**受影响文件**:
- `portfolio_manager/database.py` (修改 Base 导入)
- `portfolio_manager/models.py` (Pydantic 模型，无需修改)
- `portfolio_manager/commands.py` (验证 Base 一致性)

**验证命令**:
```bash
python -c "
from common.database import Base as common_base
from stock_market.database import Base as stock_base
from portfolio_manager.database import Base as portfolio_base

print('common_base:', id(common_base))
print('stock_base:', id(stock_base))
print('portfolio_base:', id(portfolio_base))
print('Are they same?', common_base is stock_base is portfolio_base)
"
```

---

### 阶段 2: 启动同步逻辑 (3分钟)

#### 4.2.1 修改 `api_server/main.py`

在 `lifespan` 函数中添加数据库同步逻辑：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("API Server 启动中...")
    logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")

    # ✅ 初始化数据库管理器并同步表
    from common.database import DatabaseManager
    from common.config import get_config

    config = get_config()
    db_url = config.get_database_url()

    db_manager = DatabaseManager(db_url)

    # ✅ 自动创建所有表 (如果不存在)
    logger.info("正在同步数据库表...")
    db_manager.create_all()
    logger.info("数据库表同步完成")

    # 存储到 app.state 供其他地方使用
    app.state.db_manager = db_manager

    yield

    # ✅ 关闭时释放连接池
    logger.info("API Server 正在关闭...")
    db_manager.dispose()
```

**受影响文件**:
- `api_server/main.py` (修改 lifespan 函数)

---

### 阶段 3: 代码清理 (2分钟)

#### 4.3.1 移除重复代码

`portfolio_manager/commands.py` 中的 `_init_database` 方法可以简化，因为表已自动创建：

```python
# Before
def _init_database(self) -> Session:
    db_url = self.config.get_database_url()
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)

    # ❌ 冗余：表会在启动时自动创建
    from portfolio_manager.database import Base
    Base.metadata.create_all(engine)  # ← 可以移除

    return Session()
```

**建议**: 保留此代码以支持独立使用 `PortfolioCommands`（不通过 API 启动）

---

### 阶段 4: 测试验证 (10分钟)

#### 4.4.1 单元测试

```python
# tests/test_database_sync.py
def test_base_consistency():
    """测试所有模块使用统一的 Base"""
    from common.database import Base as common_base
    from stock_market.database import Base as stock_base
    from portfolio_manager.database import Base as portfolio_base

    assert common_base is stock_base is portfolio_base

def test_tables_registered():
    """测试所有表都已注册到 metadata"""
    from common.database import Base
    table_names = Base.metadata.tables.keys()

    expected_tables = {'stocks', 'klines', 'sync_records', 'positions', 'transactions', 'cash_balance'}
    assert expected_tables.issubset(table_names)
```

#### 4.4.2 集成测试

```python
# tests/api_server/test_database_sync.py
def test_server_startup_syncs_tables(test_client):
    """测试服务器启动时自动同步表"""
    # test_client 会触发 app 启动
    response = test_client.get("/health")
    assert response.status_code == 200

    # 验证表存在
    from sqlalchemy import text
    from common.database import get_db

    with test_client.app.dependency_overrides.get(get_db)() as session:
        result = session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """))
        tables = {row[0] for row in result}

        assert 'stocks' in tables
        assert 'positions' in tables
```

#### 4.4.3 手动验证

```bash
# 1. 清理测试数据库
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d

# 2. 运行测试
pytest tests/test_database_sync.py -v

# 3. 启动 API 服务
python -m api_server.main

# 4. 检查日志
# 应该看到:
# - "正在同步数据库表..."
# - "数据库表同步完成"
# - "API Server 启动中..."

# 5. 连接数据库验证
psql -h localhost -U postgres -d alpha_quant -c "\dt"
# 应该看到所有表: stocks, klines, positions, transactions, cash_balance, sync_records
```

---

## 5. 风险评估

| 风险 | 严重性 | 缓解措施 |
|------|--------|----------|
| **Base 不一致导致表丢失** | 高 | 阶段 1 严格验证 Base 一致性 |
| **启动时数据库连接失败** | 中 | 添加异常处理和重试机制 |
| **向后兼容性问题** | 低 | 保留 `commands.py` 中的创建逻辑 |
| **测试环境冲突** | 低 | `conftest.py` 已有独立的测试数据库管理 |

---

## 6. 向后兼容性

### 6.1 现有代码不受影响

- `PortfolioCommands` 仍可独立使用
- 测试使用独立的数据库引擎
- API 端点无需修改

### 6.2 配置文件无需修改

- 数据库配置保持不变 (`config/database.yaml`)
- 环境变量无需调整

---

## 7. 验收标准

- [ ] 所有模块使用统一的 `Base`
- [ ] 服务器启动日志显示"数据库表同步完成"
- [ ] 数据库中存在所有 6 张表
- [ ] 所有现有测试通过
- [ ] `PortfolioCommands` 独立使用仍正常工作

---

## 8. 时间估算

| 阶段 | 任务 | 估计时间 |
|------|------|----------|
| 1 | Base 统一 | 5 分钟 |
| 2 | 启动同步 | 3 分钟 |
| 3 | 代码清理 | 2 分钟 |
| 4 | 测试验证 | 10 分钟 |
| **总计** | | **20 分钟** |

---

## 9. 后续优化 (可选)

### 9.1 引入 Alembic 迁移管理

**时机**: 生产环境部署前

```bash
# 初始化 Alembic
alembic init alembic

# 配置 env.py 导入所有模型
# 生成初始迁移
alembic revision --autogenerate -m "initial schema"

# 应用迁移
alembic upgrade head
```

### 9.2 添加健康检查

在 `/health` 端点中添加数据库连接检查：

```python
@app.get("/health")
async def health_check():
    try:
        # 检查数据库连接
        with app.state.db_manager.get_session() as session:
            session.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": settings.API_VERSION
    }
```

### 9.3 性能优化

- 添加连接池监控
- 配置慢查询日志
- 优化索引

---

## 10. 回滚计划

如果出现问题，可以快速回滚：

1. **恢复代码**:
   ```bash
   git checkout HEAD~1 -- portfolio_manager/database.py api_server/main.py
   ```

2. **手动创建表** (临时方案):
   ```python
   from common.database import DatabaseManager
   from common.config import get_config

   config = get_config()
   db_manager = DatabaseManager(config.get_database_url())
   db_manager.create_all()
   ```

---

## 11. 相关文档

- [数据库自动同步方案](../database-auto-sync-plan.md)
- [数据库模型定义](database-models.md)
- [测试指南](../developer-guide/07-testing.md)

---

## 12. 测试环境处理

### 12.1 当前测试机制

**测试数据库**: 使用独立的测试数据库 (`test_stock_market`)

**测试 fixture**: `tests/conftest.py` 中的 `db_engine` fixture

```python
@pytest.fixture(scope="session")
def db_engine():
    """会话级别的数据库引擎（整个测试套件共享）"""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        echo=False
    )

    # ✅ 测试时自动创建表
    Base.metadata.create_all(bind=engine)

    yield engine

    # ✅ 测试结束后自动删除表
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
```

### 12.2 不需要修改测试代码

**原因**:
1. 测试使用独立的 `db_engine` fixture
2. 测试数据库与生产数据库分离
3. `conftest.py` 已有完善的表创建/清理逻辑

### 12.3 验证测试兼容性

```bash
# 运行所有测试
pytest tests/ -v --tb=short

# 应该全部通过，包括：
# - tests/conftest.py 中的 fixture
# - tests/api_server/ 中的集成测试
# - tests/portfolio_manager/ 中的单元测试
```

---

## 13. 补充说明

### 13.1 为什么测试不需要修改？

测试使用了独立的数据库连接和 fixture 机制：

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, ...)
    Base.metadata.create_all(bind=engine)  # ← 测试时自动创建
    yield engine
    Base.metadata.drop_all(bind=engine)    # ← 测试后自动清理
```

这个机制与生产环境的启动同步是**完全独立**的：
- **生产环境**: `api_server/main.py` 中的 `lifespan` → `db_manager.create_all()`
- **测试环境**: `tests/conftest.py` 中的 `db_engine` fixture → `Base.metadata.create_all()`

### 13.2 多进程/多实例考虑

如果部署多个 API 实例：
- **第一次启动**: 创建表
- **后续启动**: `create_all()` 会检测表已存在，不做任何操作
- **无竞争条件**: SQLAlchemy 的 `create_all()` 是幂等的

### 13.3 开发环境 vs 生产环境

| 环境 | 数据库 | 表创建方式 |
|------|--------|------------|
| **开发** | `alpha_quant` | 启动时自动同步 |
| **测试** | `test_stock_market` | pytest fixture 自动管理 |
| **生产** | `alpha_quant` (生产库) | 启动时自动同步 + 后续用 Alembic 迁移 |

---

## 14. 总结

### 核心变更
1. **统一 Base**: 所有模块使用 `common.database.Base`
2. **启动同步**: `api_server/main.py` 中添加自动同步逻辑
3. **测试不变**: 保持现有的测试机制

### 优势
- ✅ 单一入口管理所有表
- ✅ 首次部署自动初始化
- ✅ 零配置，开箱即用
- ✅ 向后兼容现有代码

### 下一步
批准后立即实施，预计 20 分钟完成。
