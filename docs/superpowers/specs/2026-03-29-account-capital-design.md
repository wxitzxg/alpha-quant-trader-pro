# 账户资金计算优化设计

## 背景

当前 `cash_balance` 表只存储当前现金余额，缺少初始资金和盈亏追踪，导致无法准确计算账户整体盈亏状况。

## 问题分析

现有逻辑：
- 现金余额 = 初始金额 - 买入支出 - 手续费 + 卖出收入
- 总市值 = 股票市值 + 现金余额
- 缺少：初始资金追踪、总盈亏计算

用户期望：
- 真实账户不追溯"初始资金"概念，只关注当前状态
- 需要支持资金转入/转出
- 总盈亏基于市值反推

## 设计方案

### 1. 数据库表变更

#### 修改 `cash_balance` 表

新增字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `initial_capital` | DECIMAL(15,4) | 0 | 初始资金（累计投入） |
| `total_pl` | DECIMAL(15,4) | 0 | 总盈亏（缓存字段，可计算） |

完整表结构：

```python
class CashBalance(Base):
    __tablename__ = 'cash_balance'

    id = Column(Integer, primary_key=True, default=1)
    amount = Column(DECIMAL(15,4), nullable=False, default=0, comment='当前现金余额')
    initial_capital = Column(DECIMAL(15,4), nullable=False, default=0, comment='初始资金')
    total_pl = Column(DECIMAL(15,4), nullable=False, default=0, comment='总盈亏')
    version = Column(Integer, nullable=False, default=0, comment='乐观锁版本号')
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
```

#### 新建 `capital_adjustments` 表

记录初始资金的调整历史：

```python
class CapitalAdjustment(Base):
    __tablename__ = 'capital_adjustments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(DECIMAL(15,4), nullable=False, comment='调整金额')
    adjustment_type = Column(String(20), nullable=False, comment='类型: deposit/withdraw')
    reason = Column(String(200), nullable=True, comment='调整原因')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_capital_adjustments_created_at', created_at.desc()),
    )
```

### 2. 计算逻辑

| 指标 | 计算方式 | 数据来源 |
|------|----------|----------|
| 初始资金 | `SUM(转入) - SUM(转出)` | capital_adjustments 表汇总 |
| 当前现金 | 交易流水累计 | cash_balance.amount |
| 股票市值 | `SUM(持仓数量 × 当前价格)` | positions 表实时计算 |
| 总盈亏 | `(当前现金 + 股票市值) - 初始资金` | 实时计算 |

**验证公式：**
```
总盈亏 = 浮动盈亏 + 实际盈亏
       = (股票市值 - 持仓成本) + 已实现盈亏
       = (当前现金 + 股票市值) - 初始资金
```

### 3. API 接口

#### 调整初始资金

```
POST /api/capital/adjust
```

请求体：
```json
{
  "amount": 50000.00,
  "adjustment_type": "deposit",
  "reason": "追加投资"
}
```

响应：
```json
{
  "success": true,
  "data": {
    "adjustment_id": 1,
    "new_initial_capital": 150000.00,
    "adjustment_type": "deposit",
    "amount": 50000.00
  }
}
```

业务逻辑：
1. 创建 `capital_adjustments` 记录
2. 更新 `cash_balance.initial_capital`
3. 如果是转入，同时增加 `cash_balance.amount`（现金余额）
4. 如果是转出，检查现金是否充足后扣减

#### 获取账户汇总

```
GET /api/account/summary
```

响应：
```json
{
  "cash": 3380.18,
  "stock_market_value": 98500.00,
  "total_market_value": 101880.18,
  "initial_capital": 100000.00,
  "total_pl": 1880.18,
  "total_floating_pl": 1500.00,
  "total_realized_pl": 380.18,
  "positions_count": 5
}
```

### 4. 服务层变更

#### 新增 `CapitalService`

```python
class CapitalService:
    def adjust_capital(self, amount: float, adjustment_type: str, reason: str) -> CapitalAdjustment:
        """调整初始资金"""

    def get_initial_capital(self) -> float:
        """获取初始资金（从 capital_adjustments 汇总）"""

    def get_adjustment_history(self) -> List[CapitalAdjustment]:
        """获取调整历史"""
```

#### 修改 `AccountService.get_account_summary()`

更新计算逻辑：
1. 从 `capital_adjustments` 汇总初始资金
2. 实时计算总盈亏 = (现金 + 股票市值) - 初始资金

### 5. 数据迁移

对于已有数据，执行迁移脚本：
1. 为 `cash_balance` 表添加新字段
2. 创建 `capital_adjustments` 表
3. 将现有现金余额的"初始来源"记录为第一条 capital_adjustment

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `portfolio_manager/database.py` | 修改 | 新增 CapitalAdjustment 模型，修改 CashBalance 模型 |
| `portfolio_manager/models.py` | 修改 | 更新 AccountSummary 模型 |
| `portfolio_manager/repositories/position_repository.py` | 修改 | 新增 CapitalAdjustmentRepository |
| `portfolio_manager/capital_service.py` | 新增 | 资金调整服务 |
| `portfolio_manager/account_service.py` | 修改 | 更新账户汇总计算逻辑 |
| `api_server/routers/portfolio.py` | 修改 | 新增资金调整接口 |
| `tests/portfolio_manager/test_capital.py` | 新增 | 单元测试 |

## 风险点

1. **数据迁移** - 现有账户需要初始化 initial_capital
2. **并发安全** - 资金调整需使用乐观锁
3. **负数处理** - 转出时需检查现金充足性
