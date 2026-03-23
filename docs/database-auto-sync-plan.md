# 数据库自动同步方案

## 一、数据库模型梳理

### 1.1 模型分布

#### **模块1: stock_market** (股票市场)
**Base类**: `stock_market.database.Base`

| 表名 | 模型类 | 功能描述 | 关键字段 |
|------|--------|----------|----------|
| `stocks` | `Stock` | 股票基础信息表 | symbol, name, exchange, list_date, industry |
| `klines` | `KLine` | K线数据表 | symbol, date, interval, open, high, low, close, volume |
| `sync_records` | `SyncRecord` | 同步记录表 | sync_type, symbol, interval, status, records_count |

#### **模块2: portfolio_manager** (组合管理)
**Base类**: `portfolio_manager.database.Base`

| 表名 | 模型类 | 功能描述 | 关键字段 |
|------|--------|----------|----------|
| `positions` | `Position` | 持仓表 | symbol, quantity, cost_price, market_value, floating_pl |
| `transactions` | `Transaction` | 交易记录表 | symbol, transaction_type, quantity, price, fee, amount |
| `cash_balance` | `CashBalance` | 现金余额表 | amount, version (单记录表) |

#### **模块3: data_sources** (数据源)
**Base类**: **无SQLAlchemy模型** (仅Pydantic模型)
- `Quote`: 实时行情数据
- `KLine`: K线数据 (Pydantic)
- `FinancialStatement`: 财务报表基础类
- `BalanceSheet`: 资产负债表
- `IncomeStatement`: 利润表
- `CashFlowStatement`: 现金流量表

**说明**: `data_sources`模块只提供数据获取和转换，不直接管理数据库表。

#### **模块4: technical_analysis** (技术分析)
**Base类**: **无独立模型** (使用stock_market的KLine模型)

---

## 二、问题分析

### 2.1 当前状态
1. **Base类分散**: 每个模块使用独立的`Base`类
   - `stock_market.database.Base`
   - `portfolio_manager.database.Base`
   - `common.database.Base` (统一管理器)

2. **表创建分散**:
   - `portfolio_manager.commands.py`中使用`Base.metadata.create_all()`
   - `common.database.DatabaseManager`提供`create_all()`方法
   - **stock_market模块无自动创建表的机制**

3. **启动时未同步**:
   - `api_server/main.py`的lifespan中**没有数据库同步逻辑**
   - 系统启动后表可能不存在或结构不一致

### 2.2 风险
- 首次部署时表未创建，导致运行时错误
- 模型变更后数据库未同步，引发字段不匹配
- 多模块间表依赖关系未处理

---

## 三、解决方案

### 3.1 方案一: 统一Base类 (推荐)

**核心思想**: 所有模块共享同一个`Base`类，确保`metadata`包含所有表定义。

#### 实施步骤:

**步骤1: 确保Base导入顺序**
在各模块的模型文件中，必须先导入`common.database.Base`:

```python
# stock_market/database.py
from common.database import Base  # ✅ 使用统一Base

# portfolio_manager/database.py
from common.database import Base  # ✅ 使用统一Base
```

**步骤2: 在main.py中自动同步**
```python
# api_server/main.py
from common.database import DatabaseManager, Base
from common.config import get_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("API Server 启动中...")

    # 初始化数据库管理器
    config = get_config()
    db_url = config.get_database_url()

    db_manager = DatabaseManager(db_url)

    # ✅ 自动创建所有表 (如果不存在)
    logger.info("正在同步数据库表...")
    db_manager.create_all()
    logger.info("数据库表同步完成")

    app.state.db_manager = db_manager

    yield

    # 关闭时
    db_manager.dispose()
    logger.info("API Server 正在关闭...")
```

#### 优点:
- ✅ 单一入口，集中管理
- ✅ 自动检测新表，无需手动维护
- ✅ 符合FastAPI生命周期最佳实践
- ✅ 未来添加新模块只需导入模型

#### 缺点:
- ⚠️ 需要确保所有模型文件在`create_all()`前被导入

---

### 3.2 方案二: 分模块同步

**核心思想**: 每个模块独立管理自己的表，由主程序协调。

#### 实施步骤:

**步骤1: 各模块提供初始化方法**
```python
# stock_market/database.py
def init_tables(engine):
    """初始化股票市场表"""
    from .models import Stock, KLine, SyncRecord  # 触发模型注册
    Base.metadata.create_all(engine)
    logger.info("股票市场表初始化完成")
```

**步骤2: 主程序按依赖顺序初始化**
```python
# api_server/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = DatabaseManager(db_url)

    # 按依赖顺序初始化
    logger.info("正在初始化股票市场模块...")
    from stock_market.database import init_tables as init_stock_tables
    init_stock_tables(db_manager.engine)

    logger.info("正在初始化组合管理模块...")
    from portfolio_manager.database import init_tables as init_portfolio_tables
    init_portfolio_tables(db_manager.engine)

    app.state.db_manager = db_manager
    yield
    db_manager.dispose()
```

#### 优点:
- ✅ 模块间解耦，独立演进
- ✅ 可以控制初始化顺序
- ✅ 适合大型微服务架构

#### 缺点:
- ⚠️ 需要手动维护初始化顺序
- ⚠️ 容易遗漏新模块
- ⚠️ 重复代码较多

---

### 3.3 方案三: Alembic迁移 (生产推荐)

**核心思想**: 使用Alembic管理数据库迁移，而非自动创建。

#### 实施步骤:

**步骤1: 初始化Alembic**
```bash
cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/init-db
alembic init alembic
```

**步骤2: 配置alembic.ini**
```ini
[alembic]
script_location = alembic
prepend_sys_path = .

[post_write_hooks]
```

**步骤3: 配置env.py**
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入所有模型，确保注册到Base
from common.database import Base
from stock_market.models import Stock, KLine, SyncRecord
from portfolio_manager.database import Position, Transaction, CashBalance

target_metadata = Base.metadata
```

**步骤4: 生成初始迁移**
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

**步骤5: 主程序调用迁移**
```python
# api_server/main.py
from alembic.config import Config
from alembic import command

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 自动运行迁移
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield
```

#### 优点:
- ✅ 版本控制，可回滚
- ✅ 支持复杂的结构变更
- ✅ 适合团队协作和生产环境
- ✅ 可以生成SQL变更脚本

#### 缺点:
- ⚠️ 初期设置复杂
- ⚠️ 需要学习Alembic

---

## 四、推荐方案及实施

### 4.1 推荐方案: **方案一 + 方案三组合**

**开发环境**: 使用**方案一**(统一Base自动同步)
**生产环境**: 使用**方案三**(Alembic迁移)

### 4.2 实施路线图

#### 阶段1: 统一Base类 (立即执行)
```bash
# 1. 确保所有模型使用common.database.Base
# stock_market/database.py - 已完成 ✓
# portfolio_manager/database.py - 已完成 ✓

# 2. 验证Base一致性
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

#### 阶段2: 添加启动同步 (立即执行)
```python
# 修改 api_server/main.py
# 在lifespan中添加数据库同步逻辑
```

#### 阶段3: 引入Alembic (可选，生产环境)
```bash
# 初始化Alembic
alembic init alembic

# 生成初始迁移
alembic revision --autogenerate -m "initial schema"

# 应用迁移
alembic upgrade head
```

---

## 五、验证清单

- [ ] 所有模型使用`common.database.Base`
- [ ] `api_server/main.py`的lifespan中调用`create_all()`
- [ ] 启动服务，检查日志是否显示"数据库表同步完成"
- [ ] 连接数据库，验证表是否存在:
  ```sql
  \dt  -- PostgreSQL
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public';
  ```
- [ ] 检查表结构是否正确
- [ ] 测试API调用，确认无数据库错误

---

## 六、附录: 表结构速查

### stock_market模块
```sql
-- stocks: 股票信息
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    list_date DATE NOT NULL,
    ...
);

-- klines: K线数据
CREATE TABLE klines (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    interval VARCHAR(10) NOT NULL,
    open NUMERIC(10,2) NOT NULL,
    high NUMERIC(10,2) NOT NULL,
    low NUMERIC(10,2) NOT NULL,
    close NUMERIC(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    ...
    UNIQUE(symbol, date, interval)
);

-- sync_records: 同步记录
CREATE TABLE sync_records (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(20) NOT NULL,
    symbol VARCHAR(10),
    interval VARCHAR(10),
    status VARCHAR(20) NOT NULL,
    records_count INTEGER DEFAULT 0,
    ...
);
```

### portfolio_manager模块
```sql
-- positions: 持仓
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    quantity INTEGER NOT NULL,
    cost_price DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4),
    market_value DECIMAL(15,4) DEFAULT 0,
    cost_value DECIMAL(15,4) DEFAULT 0,
    floating_pl DECIMAL(15,4) DEFAULT 0,
    ...
);

-- transactions: 交易记录
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    amount DECIMAL(15,4) NOT NULL,
    fee DECIMAL(10,4) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    ...
);

-- cash_balance: 现金余额 (单记录)
CREATE TABLE cash_balance (
    id INTEGER PRIMARY KEY DEFAULT 1,
    amount DECIMAL(15,4) DEFAULT 0,
    version INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 七、后续优化建议

1. **添加索引优化**: 根据查询模式添加复合索引
2. **分区表**: 对`klines`表按日期分区
3. **读写分离**: 生产环境配置主从复制
4. **监控告警**: 监控表大小、索引使用率
5. **定期维护**: VACUUM ANALYZE、索引重建
