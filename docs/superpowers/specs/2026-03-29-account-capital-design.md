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
| `initial_capital` | DECIMAL(15,4) | 0 | 初始资金（累计投入，从 capital_adjustments 汇总） |

完整表结构：

```python
class CashBalance(Base):
    __tablename__ = 'cash_balance'

    id = Column(Integer, primary_key=True, default=1)
    amount = Column(DECIMAL(15,4), nullable=False, default=0, comment='当前现金余额')
    initial_capital = Column(DECIMAL(15,4), nullable=False, default=0, comment='初始资金')
    version = Column(Integer, nullable=False, default=0, comment='乐观锁版本号')
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
```

> 注意：移除了 `total_pl` 缓存字段，改为每次查询时实时计算，避免缓存与实际值不一致。

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
| 总盈亏 | `(当前现金 + 股票市值) - 初始资金` | 实时计算（不缓存） |

**验证公式：**
```
总盈亏 = 浮动盈亏 + 实际盈亏
       = (股票市值 - 持仓成本) + 已实现盈亏
       = (当前现金 + 股票市值) - 初始资金
```

**新账户处理：**
- 无 `capital_adjustments` 记录时，`initial_capital = 0`
- 总盈亏 = 当前现金 + 股票市值（即全部为盈利）
- 建议用户首次使用时先执行一笔转入操作

### 3. API 接口

#### 调整初始资金

```
POST /api/portfolio/account/capital/adjust
```

**请求 Schema（`portfolio_manager/schemas/capital_schemas.py`）：**

```python
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AdjustmentType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"

class CapitalAdjustRequest(BaseModel):
    amount: float = Field(..., gt=0, description="调整金额（必须大于0）")
    adjustment_type: AdjustmentType = Field(..., description="调整类型")
    reason: Optional[str] = Field(None, max_length=200, description="调整原因")

class CapitalAdjustResponse(BaseModel):
    adjustment_id: int
    new_initial_capital: float
    adjustment_type: AdjustmentType
    amount: float
    new_cash_balance: float

class CapitalAdjustmentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    adjustment_type: AdjustmentType
    reason: Optional[str]
    created_at: datetime

class CapitalAdjustmentHistory(BaseModel):
    items: list[CapitalAdjustmentItem]
    total: int
```

请求体示例：
```json
{
  "amount": 50000.00,
  "adjustment_type": "deposit",
  "reason": "追加投资"
}
```

响应示例：
```json
{
  "adjustment_id": 1,
  "new_initial_capital": 150000.00,
  "adjustment_type": "deposit",
  "amount": 50000.00,
  "new_cash_balance": 53380.18
}
```

业务逻辑：
1. 验证请求参数（金额 > 0）
2. 创建 `capital_adjustments` 记录
3. 更新 `cash_balance.initial_capital`（累加或扣减）
4. 如果是转入，同时增加 `cash_balance.amount`（现金余额）
5. 如果是转出，检查现金是否充足后扣减

#### 获取调整历史

```
GET /api/portfolio/account/capital/history
```

响应示例：
```json
{
  "items": [
    {
      "id": 1,
      "amount": 100000.00,
      "adjustment_type": "deposit",
      "reason": "初始资金",
      "created_at": "2026-03-29T10:00:00"
    }
  ],
  "total": 1
}
```

#### 获取账户汇总

```
GET /api/portfolio/account/summary
```

**需要修改的文件：**
- `portfolio_manager/models.py` - 内部 AccountSummary 模型
- `api_server/models/portfolio.py` - API 响应 AccountSummary 模型

**内部模型（`portfolio_manager/models.py`）：**

```python
class AccountSummary(BaseModel):
    total_market_value: float = 0.0    # 总市值
    stock_market_value: float = 0.0    # 股票市值
    cash: float = 0.0                  # 现金
    initial_capital: float = 0.0       # 初始资金（新增）
    total_pl: float = 0.0              # 总盈亏（新增）
    total_floating_pl: float = 0.0     # 浮动盈亏
    total_realized_pl: float = 0.0     # 实际盈亏
    positions_count: int = 0           # 持仓数量
```

**API 响应模型（`api_server/models/portfolio.py`）：**

```python
class AccountSummary(BaseModel):
    """账户汇总"""
    total_market_value: float = Field(..., description="总市值")
    total_cash: float = Field(..., description="总现金")
    stock_market_value: float = Field(0.0, description="股票市值")
    initial_capital: float = Field(0.0, description="初始资金")  # 新增
    total_pl: float = Field(0.0, description="总盈亏")          # 新增
    total_profit: float = Field(..., description="总盈亏（兼容旧字段）")
    total_profit_rate: float = Field(..., description="总盈亏率")
    position_count: int = Field(..., description="持仓股票数")
    today_profit: float = Field(..., description="今日盈亏")
```

响应示例：
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
    def adjust_capital(
        self,
        amount: float,
        adjustment_type: str,
        reason: Optional[str]
    ) -> CapitalAdjustment:
        """
        调整初始资金

        流程：
        1. 验证金额 > 0
        2. 如果是转出，检查现金充足性
        3. 创建 capital_adjustments 记录
        4. 更新 cash_balance.initial_capital
        5. 更新 cash_balance.amount（转入增加，转出减少）
        """

    def get_initial_capital(self) -> float:
        """
        获取初始资金

        逻辑：从 capital_adjustments 汇总
        - 无记录时返回 0
        - SUM(CASE WHEN type='deposit' THEN amount ELSE -amount END)
        """

    def get_adjustment_history(self, limit: int = 20) -> List[CapitalAdjustment]:
        """获取调整历史"""
```

#### 修改 `AccountService.get_account_summary()`

更新计算逻辑：
1. 调用 `CapitalService.get_initial_capital()` 获取初始资金
2. 实时计算总盈亏 = (现金 + 股票市值) - 初始资金

### 5. 数据迁移

#### 迁移脚本设计

```python
# scripts/migrate_capital.py

def migrate():
    """
    数据迁移脚本

    步骤：
    1. 为 cash_balance 表添加 initial_capital 字段
    2. 创建 capital_adjustments 表
    3. 根据现有数据计算 initial_capital：
       - initial_capital = 当前现金 + 股票市值 - 已实现盈亏
       - 或直接让用户手动设置
    4. 创建初始 capital_adjustment 记录
    """
    pass

def rollback():
    """
    回滚方案：
    1. 删除 capital_adjustments 表
    2. 移除 cash_balance.initial_capital 字段
    """
    pass
```

**迁移验证：**
- 验证表结构正确
- 验证初始数据一致性：`initial_capital = SUM(adjustments)`
- 验证账户汇总计算正确

### 6. 安全性设计

#### API 权限验证

> **注意：** 当前项目未实现用户认证机制。资金调整接口暂时无需认证。后续如需增加认证，可实现以下方案：

**未来认证方案（可选）：**

```python
# api_server/routers/portfolio.py

@router.post("/account/capital/adjust")
async def adjust_capital(
    request: CapitalAdjustRequest,
    # current_user: User = Depends(get_current_user)  # 未来添加认证
):
    """资金调整接口"""
    pass
```

**建议后续实现：**
1. JWT Token 认证
2. API Key 认证（适用于内部服务）
3. IP 白名单限制

在 `capital_adjustments` 表中已包含：
- `created_at` - 操作时间
- `reason` - 操作原因

建议增加（可选）：
- `operator_id` - 操作人 ID
- `ip_address` - 操作 IP

#### 大额操作限制

```python
LARGE_AMOUNT_THRESHOLD = 100000  # 10万以上需要二次确认

if amount >= LARGE_AMOUNT_THRESHOLD:
    # 返回需要确认的响应
    return {"require_confirmation": True, "message": "大额操作需确认"}
```

### 7. 测试设计

#### 单元测试 `tests/portfolio_manager/test_capital.py`

```python
class TestCapitalService:
    """资金调整服务测试"""

    def test_deposit_success(self):
        """正常转入"""

    def test_withdraw_success(self):
        """正常转出"""

    def test_withdraw_insufficient_cash(self):
        """转出金额超过现金余额"""

    def test_deposit_zero_amount(self):
        """转入金额为0 - 应拒绝"""

    def test_deposit_negative_amount(self):
        """转入金额为负数 - 应拒绝"""

    def test_new_account_initial_capital_is_zero(self):
        """新账户初始资金为0"""

    def test_get_initial_capital_sum_correctly(self):
        """初始资金正确汇总"""

    def test_concurrent_adjustment_optimistic_lock(self):
        """并发调整 - 乐观锁处理"""

class TestAccountSummary:
    """账户汇总测试"""

    def test_total_pl_calculation(self):
        """总盈亏计算正确"""

    def test_total_pl_with_no_initial_capital(self):
        """无初始资金时总盈亏等于总市值"""

class TestCapitalAPI:
    """API 测试"""

    def test_adjust_capital_api_success(self):
        """API 正常调用"""

    def test_adjust_capital_unauthorized(self):
        """未认证请求被拒绝"""
```

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `portfolio_manager/database.py` | 修改 | 新增 CapitalAdjustment 模型，修改 CashBalance 模型 |
| `portfolio_manager/models.py` | 修改 | 更新 AccountSummary 模型，新增 initial_capital 和 total_pl 字段 |
| `portfolio_manager/schemas/capital_schemas.py` | 新增 | CapitalAdjustRequest/Response 等 Schema |
| `portfolio_manager/schemas/__init__.py` | 修改 | 导出 capital_schemas |
| `portfolio_manager/repositories/capital_repository.py` | 新增 | CapitalAdjustmentRepository |
| `portfolio_manager/repositories/__init__.py` | 修改 | 导出 CapitalAdjustmentRepository |
| `portfolio_manager/capital_service.py` | 新增 | 资金调整服务 |
| `portfolio_manager/account_service.py` | 修改 | 更新账户汇总计算逻辑（新增 initial_capital、total_pl） |
| `api_server/models/portfolio.py` | 修改 | 更新 AccountSummary 响应模型 |
| `api_server/services/portfolio_service.py` | 修改 | 更新 get_account_summary 返回值 |
| `api_server/routers/portfolio.py` | 修改 | 新增资金调整接口 |
| `scripts/migrate_capital.py` | 新增 | 数据迁移脚本 |
| `tests/portfolio_manager/test_capital.py` | 新增 | 单元测试 |

## 风险点

1. **数据迁移** - 现有账户需要初始化 initial_capital，需提供迁移脚本
2. **并发安全** - 资金调整需使用乐观锁，重试机制
3. **负数处理** - 转出时需检查现金充足性
4. **新账户** - 无调整记录时 initial_capital=0，建议首次使用先转入
