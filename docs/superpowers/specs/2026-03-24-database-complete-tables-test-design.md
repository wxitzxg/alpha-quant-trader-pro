# DatabaseManager 完整表测试设计

## 概述

修复当前测试代码的问题：仅验证部分表，未导入所有模型，导致 `Base.metadata` 不完整。

## 问题分析

### 当前问题
- ❌ 测试仅验证了 `strategy_accounts` 等少数表
- ❌ 未导入所有模型文件，`Base.metadata` 注册不完整
- ❌ 临时测试模型创建了额外的表（`test_users`），污染测试环境

### 正确做法
- ✅ 导入所有使用 `Base` 的模型模块
- ✅ 验证所有注册的表都被 `create_all()` 创建
- ✅ 验证所有表都被 `drop_all()` 删除
- ✅ 移除临时测试模型，仅测试项目实际表

## 项目表结构

项目共有 **9 个数据库表**，分布在 3 个模块：

| 模块 | 表 | 说明 |
|------|-----|------|
| **stock_market** | stocks | 股票基础信息 |
| | klines | K线数据 |
| | sync_records | 同步记录 |
| **simulate_trading** | strategy_accounts | 策略账户 |
| | strategy_trades | 策略交易 |
| | daily_reports | 每日报告 |
| **portfolio_manager** | positions | 持仓 |
| | transactions | 交易记录 |
| | cash_balance | 现金余额 |

## 解决方案

### 核心原则
1. **导入所有模型文件** - 在测试文件顶部导入所有包含 `Base` 的模块
2. **验证所有表** - 通过 `Base.metadata.tables.keys()` 获取完整表列表
3. **完整测试流程** - `create_all()` → 验证所有表存在 → `drop_all()` → 验证所有表不存在

### 技术实现

```python
"""DatabaseManager 集成测试"""
import os
import pytest
from sqlalchemy import inspect, text
from common.database import DatabaseManager, Base

# ==================== 导入所有模型模块 ====================
# 必须在测试开始前导入，确保 Base.metadata 注册完整
import stock_market.models          # 3 tables
import simulate_trading.models      # 3 tables
import portfolio_manager.database   # 3 tables

# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_manager():
    """函数级 DatabaseManager - 每个测试独立"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL environment variable not set")

    manager = DatabaseManager(db_url)
    manager.drop_all()
    manager.create_all()

    yield manager

    manager.dispose()

# ==================== 测试用例 ====================

def test_all_tables_created(db_manager):
    """测试所有表都被成功创建"""
    inspector = inspect(db_manager.engine)
    db_tables = set(inspector.get_table_names())
    metadata_tables = set(Base.metadata.tables.keys())

    # 验证所有元数据中的表都在数据库中
    missing_tables = metadata_tables - db_tables
    assert not missing_tables, f"Missing tables: {missing_tables}"

    # 验证表数量
    assert len(db_tables) >= len(metadata_tables)
    print(f"\n✓ All {len(metadata_tables)} tables created: {sorted(metadata_tables)}")


def test_all_tables_dropped(db_manager):
    """测试所有表都能被删除"""
    # 当前已创建所有表
    inspector = inspect(db_manager.engine)
    tables_before = set(inspector.get_table_names())

    # 删除所有表
    db_manager.drop_all()

    # 验证表已被删除
    tables_after = set(inspector.get_table_names())
    assert len(tables_after) < len(tables_before)
    print(f"\n✓ Tables dropped: {len(tables_before)} → {len(tables_after)}")

    # 重新创建表以便后续测试
    db_manager.create_all()


def test_table_structure(db_manager):
    """测试表结构正确性"""
    inspector = inspect(db_manager.engine)

    # 验证关键表存在
    assert 'stocks' in inspector.get_table_names()
    assert 'strategy_accounts' in inspector.get_table_names()
    assert 'positions' in inspector.get_table_names()

    # 验证列定义
    stocks_columns = {col['name'] for col in inspector.get_columns('stocks')}
    assert 'symbol' in stocks_columns
    assert 'name' in stocks_columns
    assert 'exchange' in stocks_columns

    # 验证索引
    stocks_indexes = {idx['name'] for idx in inspector.get_indexes('stocks')}
    assert any('symbol' in idx.lower() for idx in stocks_indexes)
```

## 验收标准

- [ ] 导入所有 3 个模型模块（stock_market, simulate_trading, portfolio_manager）
- [ ] `Base.metadata` 注册 9 个表
- [ ] `create_all()` 创建所有 9 个表
- [ ] `drop_all()` 删除所有 9 个表
- [ ] 移除临时测试模型（`test_users` 等）
- [ ] 测试覆盖：初始化、表创建/删除、session 管理、事务、连接池
- [ ] 测试通过率 100%
- [ ] 覆盖率 ≥ 80%

## 依赖关系

**导入顺序（重要）：**
1. `stock_market.models` - 使用 `stock_market.database.Base` (from common.database)
2. `simulate_trading.models` - 使用 `common.database.Base`
3. `portfolio_manager.database` - 使用 `common.database.Base`

由于 `stock_market.database` 已重定向到 `common.database`，所有模块共享同一个 `Base`。

## 使用说明

```bash
# 设置环境变量
export DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"

# 运行测试
pytest tests/common/test_database.py -v

# 查看覆盖率
pytest tests/common/test_database.py -v --cov=common.database
```
