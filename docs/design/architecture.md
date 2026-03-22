# Portfolio Manager 架构设计方案

## 1. 系统概述

### 1.1 核心功能
- **持仓管理**：股票持仓的增删改查，支持加权平均成本计算
- **交易管理**：买入/卖出交易记录，自动更新持仓和资金
- **账户管理**：资金余额、账户汇总、盈亏计算
- **手续费计算**：支持买入/卖出不同费率，包含印花税、交易所费用、券商佣金

### 1.2 技术栈
- **语言**：Python 3.10+
- **ORM**：SQLAlchemy 2.0+
- **数据验证**：Pydantic 2.0+
- **依赖注入**：Dependency Injector
- **数据库**：PostgreSQL / SQLite（测试）
- **异常处理**：自定义异常体系

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        表示层 (Presentation)                 │
│                      PortfolioCommands                        │
│  (统一命令入口 - 用户交互接口)                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                        服务层 (Service)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Position     │  │Transaction  │  │Account      │         │
│  │Service      │  │Service      │  │Service      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  (业务逻辑)                                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                      仓库层 (Repository)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Position     │  │Transaction  │  │CashBalance  │         │
│  │Repository   │  │Repository   │  │Repository   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  (数据访问抽象)                                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                        数据层 (Data)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Position     │  │Transaction  │  │CashBalance  │         │
│  │(ORM Model)  │  │(ORM Model)  │  │(ORM Model)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  (数据库表映射)                                                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
                ┌──────────────┐
                │  PostgreSQL  │
                └──────────────┘
```

### 2.2 模块依赖关系

```
PortfolioCommands
    ├── Config (统一配置)
    ├── DatabaseManager (数据库连接池)
    ├── DataSourceAggregator (数据源 - 可选)
    ├── FeeCalculator (手续费计算器)
    ├── PositionService
    │   ├── PositionRepository
    │   └── DataSourceAggregator (可选)
    ├── AccountService
    │   ├── CashBalanceRepository
    │   └── PositionService
    └── TransactionService
        ├── TransactionRepository
        ├── PositionRepository
        ├── PositionService
        ├── AccountService
        └── FeeCalculator
```

### 2.3 数据流图

#### 2.3.1 买入交易流程

```
用户调用: portfolio.buy("600519", 100, 150.5)
         │
         ▼
    [输入验证]
         │ (TransactionCreateSchema)
         ▼
    [检查现金余额]
         │ (AccountService.get_cash_balance)
         ▼
    [计算手续费]
         │ (FeeCalculator.calculate_buy_fee)
         │ amount = 100 * 150.5 = 15050
         │ fee = exchange_fee + broker_commission = 0.9 + 5.0 = 5.9
         │ total = 15055.9
         ▼
    [开启事务]
         │ (SQLAlchemy transaction)
         ├──► [创建交易记录] (TransactionRepository.add)
         ├──► [更新持仓] (PositionRepository)
         │      ├── 已有持仓 → 加权平均成本
         │      └── 新增持仓 → 创建记录
         └──► [扣减现金] (CashBalanceRepository.update_balance)
         ▼
    [提交事务]
         │ (commit) 或 [回滚] (rollback)
         ▼
    [返回 TransactionModel]
```

#### 2.3.2 卖出交易流程

```
用户调用: portfolio.sell("600519", 50, 160.0)
         │
         ▼
    [输入验证]
         │ (TransactionCreateSchema)
         ▼
    [检查持仓数量]
         │ (PositionService.get_position)
         ▼
    [计算手续费]
         │ (FeeCalculator.calculate_sell_fee)
         │ amount = 50 * 160.0 = 8000
         │ fee = stamp_duty + exchange_fee + broker_commission
         │     = 4.0 + 0.48 + 5.0 = 9.48
         │ total = 7990.52 (实际到账)
         ▼
    [开启事务]
         │ (SQLAlchemy transaction)
         ├──► [创建交易记录] (TransactionRepository.add)
         ├──► [更新持仓] (PositionRepository)
         │      ├── 全部卖出 → 删除记录
         │      └── 部分卖出 → 更新数量（成本价不变）
         └──► [增加现金] (CashBalanceRepository.update_balance)
         ▼
    [提交事务]
         ▼
    [返回 TransactionModel]
```

#### 2.3.3 账户汇总流程

```
用户调用: portfolio.account_summary()
         │
         ▼
    [获取所有持仓]
         │ (PositionService.get_all_positions)
         ├──► [刷新当前价格] (DataSourceAggregator.batch_get_realtime)
         ├──► [计算股票市值] sum(position.market_value)
         └──► [计算浮动盈亏] sum(position.floating_pl)
         │
         ▼
    [获取现金余额]
         │ (CashBalanceRepository.get_current_balance)
         │
         ▼
    [计算总市值]
         │ total_market_value = stock_market_value + cash
         │
         ▼
    [计算实际盈亏]
         │ (AccountService._calculate_realized_pl)
         │ 方法1: FIFO 成本核算（遍历交易历史）
         │ 方法2: 使用 Transaction.cost_basis（推荐）
         │
         ▼
    [返回 AccountSummary]
```

---

## 3. 数据库设计

### 3.1 表结构

#### 3.1.1 positions 表（持仓）

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    quantity INTEGER NOT NULL,
    cost_price DECIMAL(10, 4) NOT NULL,  -- 支持负数
    current_price DECIMAL(10, 4),
    market_value DECIMAL(15, 4) NOT NULL DEFAULT 0,
    cost_value DECIMAL(15, 4) NOT NULL DEFAULT 0,
    floating_pl DECIMAL(15, 4) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbol ON positions(symbol);
```

**字段说明：**
- `cost_price`：支持负数（高位卖出留底仓场景）
- `market_value`：市值 = quantity * current_price
- `cost_value`：持仓成本 = quantity * cost_price
- `floating_pl`：浮动盈亏 = market_value - cost_value

#### 3.1.2 transactions 表（交易记录）

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 4) NOT NULL,
    amount DECIMAL(15, 4) NOT NULL,         -- 交易金额（不含手续费）
    fee DECIMAL(10, 4) NOT NULL,            -- 手续费
    cost_basis DECIMAL(15, 4),              -- 卖出时记录成本（用于盈亏计算）
    realized_pl DECIMAL(15, 4),             -- 已实现盈亏
    transaction_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transaction_symbol ON transactions(symbol);
CREATE INDEX idx_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_transaction_type ON transactions(transaction_type);
```

**字段说明：**
- `amount`：
  - 买入：quantity * price（不含手续费）
  - 卖出：quantity * price - fee（实际到账）
- `cost_basis`：卖出时记录对应持仓的成本（FIFO 核算）
- `realized_pl`：已实现盈亏 = amount - cost_basis

#### 3.1.3 cash_balance 表（现金余额）

```sql
CREATE TABLE cash_balance (
    id INTEGER PRIMARY KEY DEFAULT 1,       -- 固定 id=1
    amount DECIMAL(15, 4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 0       -- 乐观锁
);
```

**设计说明：**
- 单条记录设计（id 固定为 1）
- `version` 用于乐观锁并发控制

### 3.2 索引优化

| 表 | 索引 | 用途 |
|---|---|---|
| positions | idx_symbol (symbol) | 按股票代码查询 |
| transactions | idx_transaction_symbol (symbol) | 按股票代码查询交易 |
| transactions | idx_transaction_date (transaction_date) | 按日期范围查询 |
| transactions | idx_transaction_type (transaction_type) | 按交易类型过滤 |
| transactions | idx_symbol_date (symbol, transaction_date) | 组合索引，优化常用查询 |

### 3.3 事务隔离级别

```python
# 推荐使用 READ COMMITTED（默认）
engine = create_engine(
    db_url,
    isolation_level="READ COMMITTED",  # 防止脏读
    pool_pre_ping=True,                 # 连接池健康检查
    pool_size=10,                       # 连接池大小
    max_overflow=20                     # 最大溢出连接数
)
```

**隔离级别选择：**
- **READ COMMITTED**：默认级别，防止脏读
- 不使用 SERIALIZABLE（性能开销大）
- 通过乐观锁（version）处理并发更新

---

## 4. 服务层设计

### 4.1 Repository 生命周期管理

#### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|---|---|---|---|
| **单例 Session** | 简单直接 | 需手动管理，可能连接泄漏 | 简单脚本 |
| **Request Scope** | 自动管理，线程安全 | 需要上下文管理 | Web 应用（FastAPI） |
| **Operation Scope** | 每次操作独立 | 代码稍复杂 | **推荐 - 当前场景** |
| **Dependency Injector** | 依赖注入，易测试 | 配置复杂 | 大型应用 |

#### 推荐方案：Operation Scope（每次操作创建新 Session）

```python
class PortfolioCommands:
    def __init__(self):
        self.db_manager = DatabaseManager(db_url)
        self.fee_calculator = FeeCalculator(config.get_fee_config())
        self.data_source = DataSourceAggregator() if has_data_source else None

    @contextmanager
    def _with_services(self):
        """每次操作时创建新的服务实例"""
        session = self.db_manager.get_session()
        try:
            # 创建 Repository
            position_repo = PositionRepository(session)
            transaction_repo = TransactionRepository(session)
            cash_repo = CashBalanceRepository(session)

            # 创建 Service（依赖注入）
            position_service = PositionService(position_repo, self.data_source)
            account_service = AccountService(cash_repo, position_service)
            transaction_service = TransactionService(
                transaction_repo,
                position_repo,
                position_service,
                account_service,
                self.fee_calculator
            )

            yield {
                'session': session,
                'position_service': position_service,
                'account_service': account_service,
                'transaction_service': transaction_service
            }

            # 提交事务
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def buy(self, symbol: str, quantity: int, price: float):
        with self._with_services() as services:
            return services['transaction_service'].record_buy(symbol, quantity, price)
```

### 4.2 依赖注入方案

#### 使用 Dependency Injector

```python
# containers.py
from dependency_injector import containers, providers

class PortfolioManagerContainer(containers.DeclarativeContainer):
    """持仓管理模块容器"""

    # 配置
    config = providers.Configuration()

    # 数据库
    database_manager = providers.Singleton(
        DatabaseManager,
        db_url=config.database_url
    )

    # 会话工厂（每次请求创建新 session）
    session_factory = providers.Factory(
        lambda db_manager: db_manager.get_session(),
        db_manager=database_manager
    )

    # Repository
    position_repository = providers.Factory(
        PositionRepository,
        session=session_factory
    )

    transaction_repository = providers.Factory(
        TransactionRepository,
        session=session_factory
    )

    cash_balance_repository = providers.Factory(
        CashBalanceRepository,
        session=session_factory
    )

    # 服务
    fee_calculator = providers.Singleton(
        FeeCalculator,
        fee_config=config.fee_config
    )

    position_service = providers.Factory(
        PositionService,
        repository=position_repository,
        data_source_aggregator=providers.Dependency()
    )

    account_service = providers.Factory(
        AccountService,
        cash_repo=cash_balance_repository,
        position_service=position_service
    )

    transaction_service = providers.Factory(
        TransactionService,
        transaction_repo=transaction_repository,
        position_repo=position_repository,
        position_service=position_service,
        account_service=account_service,
        fee_calculator=fee_calculator
    )
```

**使用示例：**

```python
# 初始化容器
container = PortfolioManagerContainer()
container.config.from_dict({
    'database_url': 'postgresql://user:pass@localhost/portfolio',
    'fee_config': {
        'stamp_duty': 0.0005,
        'exchange_fee': 0.00006,
        'broker_commission': 0.00015,
        'min_commission': 5.0
    }
})

# 获取服务
transaction_service = container.transaction_service()
result = transaction_service.record_buy("600519", 100, 150.5)
```

---

## 5. 错误处理与事务管理

### 5.1 异常体系

```python
# common/exceptions.py

class PortfolioError(Exception):
    """投资组合模块基类异常"""
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)

class InsufficientFundsError(PortfolioError):
    """现金不足"""
    def __init__(self, required: float, available: float):
        super().__init__(
            f"Insufficient funds. Required: {required}, Available: {available}",
            context={'required': required, 'available': available}
        )

class InsufficientSharesError(PortfolioError):
    """持仓不足"""
    def __init__(self, required: int, available: int):
        super().__init__(
            f"Insufficient shares. Required: {required}, Available: {available}",
            context={'required': required, 'available': available}
        )

class NotFoundError(PortfolioError):
    """资源未找到"""
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            f"{resource_type} not found: {identifier}",
            context={'type': resource_type, 'id': identifier}
        )

class BusinessError(PortfolioError):
    """业务逻辑错误"""
    pass

class ValidationError(PortfolioError):
    """数据验证错误"""
    pass
```

### 5.2 事务管理策略

```python
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from contextlib import contextmanager

class BaseService:
    """服务基类 - 提供事务支持"""

    def __init__(self, session):
        self.session = session

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            # 显式开始事务
            self.session.begin_nested()
            yield
            # 提交
            self.session.commit()
        except (SQLAlchemyError, IntegrityError) as e:
            # 数据库错误
            self.session.rollback()
            raise BusinessError(f"Database error: {str(e)}") from e
        except Exception as e:
            # 其他错误
            self.session.rollback()
            raise

    def close(self):
        """关闭 session"""
        self.session.close()
```

**使用示例：**

```python
class TransactionService(BaseService):
    def record_buy(self, symbol, quantity, price):
        # 验证
        self._validate_buy(symbol, quantity, price)

        # 检查余额
        if not self._has_sufficient_funds(symbol, quantity, price):
            raise InsufficientFundsError(...)

        # 事务操作
        with self.transaction():
            # 1. 创建交易记录
            transaction = self._create_transaction(...)

            # 2. 更新持仓
            self._update_position_on_buy(...)

            # 3. 扣减现金
            self._deduct_cash(...)

            return transaction
```

### 5.3 并发控制

#### 乐观锁（Optimistic Locking）

```python
class CashBalanceRepository(BaseRepository):
    def update_balance_with_optimistic_lock(self, amount: float) -> CashBalance:
        """使用乐观锁更新余额"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # 查询当前记录（加锁）
                stmt = select(CashBalance).where(CashBalance.id == 1).with_for_update()
                current = self.session.execute(stmt).scalar_one()

                # 检查版本号
                old_version = current.version

                # 更新
                current.amount += Decimal(str(amount))
                current.version += 1
                current.updated_at = datetime.now()

                self.session.flush()
                return current

            except IntegrityError:
                # 版本冲突，重试
                self.session.rollback()
                if attempt == max_retries - 1:
                    raise BusinessError("Concurrent update conflict, please retry")

            except Exception as e:
                self.session.rollback()
                raise
```

#### 悲观锁（Pessimistic Locking）

```python
# 对于持仓更新，使用 SELECT ... FOR UPDATE
def _update_position_on_buy(self, symbol, quantity, price):
    """买入后更新持仓（悲观锁）"""
    # 查询时加锁
    stmt = select(Position).where(Position.symbol == symbol).with_for_update()
    position = self.session.execute(stmt).scalar_one_or_none()

    if position:
        # 更新持仓（已加锁，安全）
        ...
    else:
        # 新增
        ...
```

---

## 6. 核心算法设计

### 6.1 加权平均成本计算

```python
def calculate_weighted_average_cost(
    old_quantity: int, old_cost: Decimal,
    new_quantity: int, new_price: Decimal
) -> Decimal:
    """
    计算加权平均成本

    公式: (旧持仓成本 + 新买入成本) / 总数量
         = (old_quantity * old_cost + new_quantity * new_price) / (old_quantity + new_quantity)
    """
    total_quantity = old_quantity + new_quantity
    total_cost = (old_quantity * old_cost) + (new_quantity * new_price)

    return total_cost / total_quantity if total_quantity > 0 else Decimal('0')
```

### 6.2 FIFO 盈亏计算（卖出时）

```python
from collections import deque

class FIFOCostCalculator:
    """FIFO（先进先出）成本核算器"""

    def __init__(self, session):
        self.session = session

    def calculate_sell_cost_basis(self, symbol: str, sell_quantity: int) -> tuple:
        """
        计算卖出成本（FIFO）

        返回: (总成本, 盈亏明细列表)
        """
        # 获取该股票的所有买入交易（按时间排序）
        buy_transactions = self.session.query(Transaction).filter_by(
            symbol=symbol,
            transaction_type='buy'
        ).order_by(Transaction.transaction_date).all()

        # 构建买入队列
        buy_queue = deque()
        for tx in buy_transactions:
            buy_queue.append({
                'quantity': tx.quantity,
                'cost_per_share': (tx.amount + tx.fee) / tx.quantity
            })

        remaining = sell_quantity
        total_cost = Decimal('0')
        details = []

        # FIFO：先卖出最早买入的
        while remaining > 0 and buy_queue:
            buy = buy_queue[0]
            sell_qty = min(remaining, buy['quantity'])

            # 计算这部分的成本
            cost = sell_qty * buy['cost_per_share']
            total_cost += cost

            # 记录明细
            details.append({
                'quantity': sell_qty,
                'cost_per_share': buy['cost_per_share'],
                'total_cost': cost
            })

            # 更新买入队列
            buy['quantity'] -= sell_qty
            if buy['quantity'] == 0:
                buy_queue.popleft()

            remaining -= sell_qty

        if remaining > 0:
            raise BusinessError(f"Insufficient historical buy records for {symbol}")

        return total_cost, details
```

### 6.3 手续费计算

```python
class FeeCalculator:
    """手续费计算器"""

    def calculate_buy_fee(self, amount: float) -> float:
        """
        买入手续费 = 交易所费用 + 券商佣金

        注意：买入不收印花税
        """
        amount_d = Decimal(str(amount))

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee  # 0.006%

        # 券商佣金（最低5元）
        broker_commission = amount_d * self.broker_commission  # 0.015%
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        return float(exchange_fee + broker_commission)

    def calculate_sell_fee(self, amount: float) -> float:
        """
        卖出手续费 = 印花税 + 交易所费用 + 券商佣金
        """
        amount_d = Decimal(str(amount))

        # 印花税（仅卖出）
        stamp_duty = amount_d * self.stamp_duty  # 0.05%

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee

        # 券商佣金（最低5元）
        broker_commission = amount_d * self.broker_commission
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        return float(stamp_duty + exchange_fee + broker_commission)
```

---

## 7. 实施路线图

### 阶段 1：核心修复（1-2 天）

#### 里程碑 1.1：修复 Repository 生命周期

**任务：**
- [ ] 重写 `PortfolioCommands.__init__` 使用 Operation Scope
- [ ] 添加 `_with_services` 上下文管理器
- [ ] 更新所有 public 方法使用新的服务获取方式
- [ ] 测试：验证多次调用不会出现 session 关闭错误

**验收标准：**
- ✅ 可以连续调用 `buy()` → `sell()` → `account_summary()` 而不报错
- ✅ 每次操作都有独立的 transaction

#### 里程碑 1.2：修复实际盈亏计算

**任务：**
- [ ] 在 `Transaction` 表添加 `cost_basis` 和 `realized_pl` 字段
- [ ] 在 `TransactionService._update_position_on_sell` 中计算成本
- [ ] 更新 `AccountService._calculate_realized_pl` 使用新字段
- [ ] 编写单元测试验证盈亏计算

**验收标准：**
- ✅ 买入 100 股 @ 10元，卖出 50 股 @ 15元，显示盈利 250元
- ✅ 支持多次买入后的 FIFO 成本核算

#### 里程碑 1.3：修复现金余额表

**任务：**
- [ ] 修改 `CashBalance` 表结构（固定 id=1）
- [ ] 实现乐观锁机制（version 字段）
- [ ] 更新 `CashBalanceRepository` 使用乐观锁
- [ ] 测试并发更新场景

**验收标准：**
- ✅ 只有一条现金余额记录
- ✅ 并发更新时抛出明确错误，而非创建多条记录

---

### 阶段 2：稳定性提升（2-3 天）

#### 里程碑 2.1：添加事务管理

**任务：**
- [ ] 创建 `BaseService` 基类提供事务支持
- [ ] 在 `TransactionService` 中使用事务上下文
- [ ] 在 `PositionService` 中使用事务
- [ ] 测试：模拟异常，验证数据一致性

**验收标准：**
- ✅ 买入交易中任何步骤失败，全部回滚
- ✅ 不会出现"交易记录已创建但持仓未更新"的情况

#### 里程碑 2.2：添加输入验证

**任务：**
- [ ] 在 `PortfolioCommands.buy()` 中使用 `TransactionCreateSchema` 验证
- [ ] 在 `PortfolioCommands.sell()` 中使用 `TransactionCreateSchema` 验证
- [ ] 在 `PortfolioCommands.add_position()` 中使用 `PositionCreateSchema` 验证
- [ ] 添加自定义异常 `ValidationError`

**验收标准：**
- ✅ 传入 `quantity=-1` 抛出 `ValidationError`
- ✅ 传入 `symbol=""` 抛出 `ValidationError`

#### 里程碑 2.3：修复小数精度问题

**任务：**
- [ ] 修改 `PositionModel` 使用 `Decimal` 而非 `float`
- [ ] 修改 `TransactionModel` 使用 `Decimal`
- [ ] 在 `_to_pydantic` 方法中使用 `quantize()`
- [ ] 测试：验证 0.1 + 0.2 不等于 0.30000000000000004

**验收标准：**
- ✅ 所有金额字段精度为 2 位小数
- ✅ 所有价格字段精度为 4 位小数

---

### 阶段 3：代码质量提升（3-5 天）

#### 里程碑 3.1：添加单元测试

**任务：**
- [ ] 搭建 pytest 测试框架
- [ ] 为 `FeeCalculator` 编写测试
- [ ] 为 `PositionService` 编写测试
- [ ] 为 `TransactionService` 编写测试
- [ ] 为 `AccountService` 编写测试
- [ ] 配置 pytest-cov，目标覆盖率 80%+

**测试示例：**
```python
# tests/test_fee_calculator.py
def test_buy_fee_calculation():
    config = FeeConfig(
        stamp_duty=0.0005,
        exchange_fee=0.00006,
        broker_commission=0.00015,
        min_commission=5.0
    )
    calculator = FeeCalculator(config)

    # 交易金额 10000 元
    fee = calculator.calculate_buy_fee(10000)

    # 交易所费用: 10000 * 0.00006 = 0.6
    # 券商佣金: 10000 * 0.00015 = 1.5 (< 5, 使用最低佣金 5)
    # 总计: 0.6 + 5 = 5.6
    assert abs(fee - 5.6) < 0.01
```

**验收标准：**
- ✅ 核心服务测试覆盖率 > 80%
- ✅ 所有测试通过

#### 里程碑 3.2：添加日志记录

**任务：**
- [ ] 配置 Python logging
- [ ] 在关键操作添加 INFO 级别日志
- [ ] 在异常处理添加 ERROR 级别日志
- [ ] 添加调试日志（DEBUG 级别）

**验收标准：**
- ✅ 可以查看每次交易的详细日志
- ✅ 异常时可以追踪完整堆栈

#### 里程碑 3.3：性能优化

**任务：**
- [ ] 在 `PositionRepository.bulk_upsert` 中使用 SQLAlchemy bulk 操作
- [ ] 在 `TransactionRepository.get_transaction_history` 中优化查询
- [ ] 添加缓存（LRU Cache）到频繁查询的方法
- [ ] 压测：1000 次交易操作 < 5 秒

**验收标准：**
- ✅ 批量导入 100 条持仓 < 1 秒
- ✅ 查询交易历史（1000 条）< 0.5 秒

---

### 阶段 4：文档与部署（2-3 天）

#### 里程碑 4.1：完善文档

**任务：**
- [ ] 编写 API 文档（使用 FastAPI 自动生成）
- [ ] 编写用户手册（Markdown）
- [ ] 编写开发者指南
- [ ] 添加代码注释（Google Style）

**验收标准：**
- ✅ 新开发者可以在 1 小时内理解架构
- ✅ 用户可以独立使用所有功能

#### 里程碑 4.2：数据库迁移

**任务：**
- [ ] 编写 Alembic 迁移脚本
- [ ] 支持从旧版本平滑升级
- [ ] 测试迁移脚本
- [ ] 编写迁移指南

**验收标准：**
- ✅ 可以从旧数据库结构迁移到新结构
- ✅ 迁移过程不丢失数据

#### 里程碑 4.3：部署准备

**任务：**
- [ ] 配置 Dockerfile
- [ ] 配置 docker-compose.yml（开发环境）
- [ ] 编写部署文档
- [ ] 配置 CI/CD（GitHub Actions）

**验收标准：**
- ✅ `docker-compose up` 可以启动服务
- ✅ CI 流程包含测试、lint、build

---

## 8. 技术债务管理

### 已知技术债务

| 问题 | 严重程度 | 计划解决时间 | 负责人 |
|---|---|---|---|
| `commands.py` 与 `commands_refactored.py` 重复 | 中 | 阶段 4 | - |
| 实际盈亏计算逻辑简化 | 高 | 阶段 1 | - |
| Repository 生命周期问题 | 高 | 阶段 1 | - |
| 缺少单元测试 | 高 | 阶段 3 | - |
| 缺少日志记录 | 中 | 阶段 3 | - |

### 预防措施

1. **Code Review**：每次 PR 必须经过 Code Review
2. **自动化测试**：新增功能必须有测试
3. **静态检查**：使用 flake8、mypy 进行代码检查
4. **文档同步**：代码变更时同步更新文档

---

## 9. 监控与运维

### 9.1 关键指标

- **交易成功率**：`成功交易数 / 总交易数`
- **平均响应时间**：`总耗时 / 交易数`
- **数据库连接数**：监控连接池使用情况
- **错误率**：`错误次数 / 总请求次数`

### 9.2 告警规则

- 交易失败率 > 1%：立即告警
- 响应时间 > 5 秒：警告
- 数据库连接池使用率 > 80%：警告

---

## 10. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|---|---|---|---|
| 数据不一致 | 中 | 高 | 添加事务管理，严格测试 |
| 并发冲突 | 中 | 中 | 使用乐观锁，重试机制 |
| 性能瓶颈 | 低 | 中 | 优化查询，添加缓存 |
| 精度丢失 | 高 | 高 | 全面使用 Decimal，严格测试 |

---

**文档版本：** v1.0
**创建日期：** 2026-03-22
**下次评审：** 2026-04-05
