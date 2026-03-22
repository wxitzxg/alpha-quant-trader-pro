# Portfolio Manager 实施路线图

## 一、总体目标

构建一个**稳定、可靠、易维护**的投资组合管理系统，支持：
- ✅ 精确的持仓管理（加权平均成本）
- ✅ 完整的交易流水（买入/卖出）
- ✅ 准确的盈亏计算（浮动盈亏 + 已实现盈亏）
- ✅ 灵活的手续费配置
- ✅ 事务一致性保证
- ✅ 高测试覆盖率（>80%）

---

## 二、阶段划分

### 📌 阶段 1：核心修复（Week 1）

**目标：** 解决 CRITICAL 问题，确保系统基本可用

#### 里程碑 1.1：修复 Repository 生命周期（Day 1-2）

**问题：** `commands_refactored.py` 中 Repository 持有已关闭的 session

**实施步骤：**
1. ✅ 重写 `PortfolioCommands.__init__`，移除 with 块中的 Repository 创建
2. ✅ 添加 `_with_services()` 上下文管理器，每次操作创建新的 session 和 Repository
3. ✅ 更新所有 public 方法（`buy`, `sell`, `positions` 等）使用新的服务获取方式
4. ✅ 测试验证：连续调用多次操作不报错

**代码示例：**
```python
class PortfolioCommands:
    def __init__(self):
        self.db_manager = DatabaseManager(db_url)
        self.fee_calculator = FeeCalculator(...)

    @contextmanager
    def _with_services(self):
        session = self.db_manager.get_session()
        try:
            repos = {
                'position_repo': PositionRepository(session),
                'transaction_repo': TransactionRepository(session),
                'cash_repo': CashBalanceRepository(session)
            }
            services = {
                'position_service': PositionService(repos['position_repo'], ...),
                'account_service': AccountService(repos['cash_repo'], ...),
                'transaction_service': TransactionService(
                    repos['transaction_repo'],
                    repos['position_repo'],
                    ...,
                    self.fee_calculator
                )
            }
            yield services
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def buy(self, symbol, quantity, price):
        with self._with_services() as services:
            return services['transaction_service'].record_buy(symbol, quantity, price)
```

**验收标准：**
- ✅ 可以连续执行：`buy()` → `sell()` → `account_summary()` → `positions()`
- ✅ 每次操作都有独立的 transaction
- ✅ 不出现 `Session is closed` 错误

**风险评估：**
- 🔴 高：影响所有功能
- ✅ 缓解：充分测试后再合并

---

#### 里程碑 1.2：修复实际盈亏计算（Day 2-3）

**问题：** `_calculate_realized_pl()` 只计算收入，没有扣除成本

**方案选择：**

| 方案 | 优点 | 缺点 | 选择 |
|---|---|---|---|
| FIFO 遍历交易历史 | 准确，符合会计准则 | 性能差，查询复杂 | ❌ |
| 在 Transaction 表加字段 | 性能好，查询简单 | 需要数据库迁移 | ✅ **推荐** |

**实施步骤：**
1. ✅ 修改 `database.py`，在 `Transaction` 表添加两个字段：
   - `cost_basis: DECIMAL(15, 4)` - 卖出时的成本基准
   - `realized_pl: DECIMAL(15, 4)` - 已实现盈亏
2. ✅ 在 `TransactionService._update_position_on_sell` 中计算成本
3. ✅ 更新 `AccountService._calculate_realized_pl` 直接 sum `realized_pl`
4. ✅ 编写单元测试验证

**代码示例：**
```python
# database.py
class Transaction(Base):
    ...
    cost_basis = Column(DECIMAL(15, 4), nullable=True)  # 卖出成本
    realized_pl = Column(DECIMAL(15, 4), nullable=True)  # 已实现盈亏

# transaction_service.py
def _update_position_on_sell(self, symbol, quantity):
    position = self.position_repo.get_by_symbol(symbol)

    # 计算成本 = 卖出数量 * 成本价
    cost_basis = Decimal(quantity) * position.cost_price

    # 更新 transaction（如果是刚创建的）
    if hasattr(self, '_current_transaction'):
        self._current_transaction.cost_basis = cost_basis
        self._current_transaction.realized_pl = (
            self._current_transaction.amount - cost_basis
        )

    # 更新持仓...

# account_service.py
def _calculate_realized_pl(self):
    session = self.cash_repo.session
    stmt = select(func.sum(Transaction.realized_pl))
    result = session.execute(stmt).scalar()
    return float(result) if result else 0.0
```

**验收标准：**
- ✅ 买入 100 股 @ 10元（成本 1000），卖出 50 股 @ 15元（收入 750），显示盈利 250元
- ✅ 多次买入后卖出，使用加权平均成本计算
- ✅ `account_summary().total_realized_pl` 显示正确值

**风险评估：**
- 🟡 中：需要数据库迁移
- ✅ 缓解：编写迁移脚本，备份数据

---

#### 里程碑 1.3：修复现金余额表（Day 3-4）

**问题：** 每次更新创建新记录，可能多条"当前"余额

**实施步骤：**
1. ✅ 修改 `CashBalance` 表，固定 `id=1`
2. ✅ 添加 `version` 字段用于乐观锁
3. ✅ 重写 `CashBalanceRepository.get_current_balance()` 只查询 id=1
4. ✅ 实现乐观锁更新机制
5. ✅ 测试并发更新场景

**代码示例：**
```python
# database.py
class CashBalance(Base):
    __tablename__ = 'cash_balance'

    id = Column(Integer, primary_key=True, default=1)  # 固定
    amount = Column(DECIMAL(15, 4), nullable=False, default=0)
    version = Column(Integer, nullable=False, default=0)  # 乐观锁

# repositories/position_repository.py
class CashBalanceRepository:
    def get_current_balance(self):
        stmt = select(CashBalance).where(CashBalance.id == 1)
        result = self.session.execute(stmt).scalar_one_or_none()

        if not result:
            # 初始化
            result = CashBalance(id=1, amount=0, version=0)
            self.add(result)
            self.session.flush()

        return float(result.amount)

    def update_balance_with_optimistic_lock(self, amount):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stmt = select(CashBalance).where(CashBalance.id == 1).with_for_update()
                current = self.session.execute(stmt).scalar_one()

                current.amount += Decimal(str(amount))
                current.version += 1
                current.updated_at = datetime.now()

                self.session.flush()
                return current
            except IntegrityError:
                self.session.rollback()
                if attempt == max_retries - 1:
                    raise BusinessError("Concurrent update conflict")
```

**验收标准：**
- ✅ 数据库中只有一条现金余额记录
- ✅ 并发更新时抛出明确错误（而非创建多条记录）
- ✅ 可以正常增加/扣减现金

**风险评估：**
- 🟡 中：需要数据迁移
- ✅ 缓解：先查询现有余额，再初始化新记录

---

#### 里程碑 1.4：集成测试（Day 4-5）

**目标：** 验证阶段 1 的所有修复

**测试场景：**
1. ✅ **完整交易流程**：创建账户 → 增加现金 10000 → 买入 → 卖出 → 查看汇总
2. ✅ **错误处理**：现金不足时买入、持仓不足时卖出
3. ✅ **并发测试**：两个线程同时买入同一股票
4. ✅ **数据一致性**：强制中断，验证回滚

**测试脚本：**
```python
def test_complete_workflow():
    portfolio = PortfolioCommands()

    # 初始化
    portfolio.add_cash(10000)

    # 买入
    buy_tx = portfolio.buy("600519", 100, 100.0)
    assert buy_tx.amount == 10000
    assert buy_tx.fee > 0

    # 卖出
    sell_tx = portfolio.sell("600519", 50, 120.0)
    assert sell_tx.amount == 6000 - sell_tx.fee
    assert sell_tx.realized_pl > 0  # 应该有盈利

    # 查看汇总
    summary = portfolio.account_summary()
    assert summary.total_market_value > 0
    assert summary.total_realized_pl == sell_tx.realized_pl
```

**验收标准：**
- ✅ 所有测试通过
- ✅ 代码覆盖率 > 60%
- ✅ 无内存泄漏（连续运行 100 次不崩溃）

---

### 📌 阶段 2：稳定性提升（Week 2）

**目标：** 解决 HIGH 优先级问题，提升系统稳定性

#### 里程碑 2.1：添加事务管理（Day 1-2）

**问题：** 交易记录、持仓更新、现金扣减没有原子性

**实施步骤：**
1. ✅ 创建 `BaseService` 基类，提供事务上下文管理器
2. ✅ 在 `TransactionService.record_buy` 和 `record_sell` 中使用事务
3. ✅ 在 `PositionService` 的写操作中使用事务
4. ✅ 测试：模拟异常，验证全部回滚

**代码示例：**
```python
class BaseService:
    @contextmanager
    def transaction_scope(self):
        try:
            self.session.begin()
            yield
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise BusinessError(f"Database error: {e}") from e
        except Exception as e:
            self.session.rollback()
            raise

class TransactionService(BaseService):
    def record_buy(self, symbol, quantity, price):
        # 验证...

        with self.transaction_scope():
            # 1. 创建交易记录
            transaction = Transaction(...)
            self.transaction_repo.add(transaction)

            # 2. 更新持仓
            self._update_position_on_buy(symbol, quantity, price)

            # 3. 扣减现金
            self.account_service.deduct_cash(total_amount)

            return self._to_pydantic(transaction)
```

**验收标准：**
- ✅ 模拟第三步失败，验证前两步回滚
- ✅ 不会出现"交易已记录但持仓未更新"的情况

---

#### 里程碑 2.2：添加输入验证（Day 2-3）

**问题：** 没有验证股票代码、数量、价格的合法性

**实施步骤：**
1. ✅ 在 `PortfolioCommands.buy()` 中使用 `TransactionCreateSchema` 验证
2. ✅ 在 `PortfolioCommands.sell()` 中使用 `TransactionCreateSchema` 验证
3. ✅ 添加自定义异常 `ValidationError`
4. ✅ 测试边界值（数量=0、价格=-100 等）

**代码示例：**
```python
def buy(self, symbol, quantity, price):
    try:
        validated = TransactionCreateSchema(
            symbol=symbol,
            transaction_type='buy',
            quantity=quantity,
            price=price
        )
    except ValidationError as e:
        raise ValidationError(f"Invalid input: {e.errors()}")

    return self.transaction_service.record_buy(
        validated.symbol,
        validated.quantity,
        validated.price
    )
```

**验收标准：**
- ✅ 传入 `quantity=0` 抛出 `ValidationError`
- ✅ 传入 `price=-100` 抛出 `ValidationError`
- ✅ 传入 `symbol=""` 抛出 `ValidationError`

---

#### 里程碑 2.3：修复小数精度（Day 3-4）

**问题：** 使用 `float` 导致金融计算精度丢失

**实施步骤：**
1. ✅ 修改 `PositionModel` 使用 `Decimal` 而非 `float`
2. ✅ 修改 `TransactionModel` 使用 `Decimal`
3. ✅ 在 `_to_pydantic` 方法中使用 `quantize()`
4. ✅ 测试：验证 0.1 + 0.2 = 0.3

**验收标准：**
- ✅ 所有金额字段精度为 2 位小数
- ✅ 所有价格字段精度为 4 位小数
- ✅ 金融计算无精度误差

---

#### 里程碑 2.4：集成测试（Day 4-5）

**目标：** 验证阶段 2 的所有改进

**测试重点：**
- ✅ 事务原子性（模拟异常）
- ✅ 输入验证（边界值）
- ✅ 精度计算（大量小数运算）

---

### 📌 阶段 3：代码质量提升（Week 3）

**目标：** 达到生产级代码质量标准

#### 里程碑 3.1：添加单元测试（Day 1-3）

**任务：**
- ✅ 搭建 pytest + pytest-cov
- ✅ 为 `FeeCalculator` 编写测试（100% 覆盖）
- ✅ 为 `PositionService` 编写测试（>80%）
- ✅ 为 `TransactionService` 编写测试（>80%）
- ✅ 配置 CI（GitHub Actions）

**验收标准：**
- ✅ 整体测试覆盖率 > 80%
- ✅ 所有测试通过
- ✅ CI 自动运行测试

---

#### 里程碑 3.2：添加日志记录（Day 3-4）

**任务：**
- ✅ 配置 Python logging（INFO/DEBUG/ERROR）
- ✅ 在关键操作添加日志
- ✅ 在异常处理添加错误日志

**验收标准：**
- ✅ 可以查看每次交易的详细日志
- ✅ 异常时可以追踪完整堆栈

---

#### 里程碑 3.3：性能优化（Day 4-5）

**任务：**
- ✅ 优化 `PositionRepository.bulk_upsert` 使用 SQLAlchemy bulk
- ✅ 添加 LRU Cache 到频繁查询方法
- ✅ 压测：1000 次交易 < 5 秒

**验收标准：**
- ✅ 批量导入 100 条持仓 < 1 秒
- ✅ 查询交易历史（1000 条）< 0.5 秒

---

### 📌 阶段 4：文档与部署（Week 4）

**目标：** 完善文档，准备部署

#### 里程碑 4.1：完善文档（Day 1-2）

**任务：**
- ✅ 编写 API 文档（使用 FastAPI 自动生成）
- ✅ 编写用户手册
- ✅ 编写开发者指南
- ✅ 添加代码注释

---

#### 里程碑 4.2：数据库迁移（Day 2-3）

**任务：**
- ✅ 编写 Alembic 迁移脚本
- ✅ 支持从旧版本平滑升级
- ✅ 测试迁移脚本

---

#### 里程碑 4.3：部署准备（Day 3-5）

**任务：**
- ✅ 配置 Dockerfile
- ✅ 配置 docker-compose.yml
- ✅ 编写部署文档
- ✅ 配置 CI/CD

---

## 三、资源规划

### 人力资源
- **后端开发**：1-2 人（全职 4 周）
- **测试**：1 人（兼职，阶段 3-4）
- **代码审查**：团队成员轮流

### 技术资源
- **开发环境**：Python 3.10+, PostgreSQL, Docker
- **测试环境**：独立的 PostgreSQL 实例
- **CI/CD**：GitHub Actions

---

## 四、风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|---|---|---|---|
| 数据不一致 | 高 | 高 | 添加事务管理，充分测试 |
| 性能瓶颈 | 中 | 中 | 优化查询，添加缓存 |
| 迁移失败 | 中 | 高 | 备份数据，先在测试环境验证 |
| 时间超期 | 中 | 中 | 每周评审进度，及时调整 |

---

## 五、里程碑验收清单

### 阶段 1 验收（Week 1）
- [ ] 修复 Repository 生命周期
- [ ] 修复实际盈亏计算
- [ ] 修复现金余额表
- [ ] 通过集成测试
- [ ] 代码 Review 通过

### 阶段 2 验收（Week 2）
- [ ] 添加事务管理
- [ ] 添加输入验证
- [ ] 修复小数精度
- [ ] 通过集成测试
- [ ] 代码 Review 通过

### 阶段 3 验收（Week 3）
- [ ] 单元测试覆盖率 > 80%
- [ ] 添加日志记录
- [ ] 性能优化完成
- [ ] CI/CD 配置完成
- [ ] 代码 Review 通过

### 阶段 4 验收（Week 4）
- [ ] 文档完善
- [ ] 数据库迁移完成
- [ ] 部署到测试环境
- [ ] 用户验收测试通过
- [ ] 上线准备完成

---

## 六、成功指标

- ✅ **功能完整性**：所有核心功能正常工作
- ✅ **数据一致性**：0 数据不一致事件
- ✅ **测试覆盖率**：> 80%
- ✅ **性能指标**：
  - 交易操作响应时间 < 100ms
  - 查询操作响应时间 < 50ms
  - 并发支持 > 100 请求/秒
- ✅ **代码质量**：
  - 0 个 CRITICAL 问题
  - 0 个 HIGH 问题
  - < 5 个 MEDIUM 问题

---

**文档版本：** v1.0
**创建日期：** 2026-03-22
**预计完成：** 2026-04-19
**负责人：** -
**评审人：** -
