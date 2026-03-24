# 🔄 Portfolio Sync Position Design

> **Date**: 2026-03-24
> **Status**: Approved
> **Version**: 1.0
> **Priority**: High

---

## 📋 Executive Summary

整合 `add_position()` 和 `update_position()` 为单一 `sync_position()` 接口，实现"存在则覆盖，不存在则新增"的智能同步行为。

**核心价值**：
- ✅ **简化接口**：统一新增/更新逻辑
- ✅ **自动补全**：现价未提供时自动查询数据源
- ✅ **必填校验**：无法计算的数据（数量、成本价）必须提供
- ✅ **向后兼容**：保留旧接口标记为 deprecated

---

## 🎯 Requirements

### Functional Requirements

1. **智能同步**：
   - 持仓不存在 → 新增
   - 持仓已存在 → 覆盖更新

2. **必填字段**：
   - `symbol`（股票代码）✅ 必填
   - `quantity`（数量）✅ 必填
   - `cost_price`（成本价）✅ 必填

3. **可选字段**：
   - `current_price`（现价）⭕ 可选
     - 未提供 → 自动从 `DataSourceAggregator` 查询
     - 查询失败 → 保持 None

4. **自动计算**：
   - 调用 `calculate_metrics()` 计算：
     - `market_value`（市值）
     - `cost_value`（持仓成本）
     - `floating_pl`（浮动盈亏）

5. **数据源集成**：
   - 复用现有 `DataSourceAggregator`
   - 支持多数据源降级（akshare、sina、tushare）

---

## 🏗️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  POST /portfolio/positions/sync                     │  │
│  │  { symbol, quantity, cost_price, current_price? }   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Service Layer (portfolio_service.py)           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  PortfolioService.sync_position()                   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         Core Layer (portfolio_manager/position_service.py) │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  PositionService.sync_position()                    │  │
│  │  ├─ Check existence (repo.get_by_symbol)           │  │
│  │  ├─ Query data source (if current_price None)       │  │
│  │  ├─ Create/Update Position model                    │  │
│  │  └─ Calculate metrics (calculate_metrics)           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Data Layer (repositories/position_repository)│
│  ┌─────────────────────────────────────────────────────┐  │
│  │  PositionRepository.add() / update()                │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### 1. PositionService.sync_position()

**Signature**:
```python
def sync_position(
    self,
    symbol: str,
    quantity: int,
    cost_price: float,
    current_price: Optional[float] = None
) -> PositionModel:
```

**Logic**:
```python
1. 查询持仓是否存在 (self.repo.get_by_symbol(symbol))
2. 如果未提供 current_price:
   2.1 尝试从 self.data_source.get_realtime(symbol) 获取
   2.2 失败则保持 None
3. 如果持仓存在:
   3.1 更新 quantity, cost_price, current_price
4. 如果持仓不存在:
   4.1 创建新 Position 记录
5. 调用 position.calculate_metrics()
6. 保存到数据库
7. 返回 PositionModel
```

**Error Handling**:
- 数据源查询失败 → 忽略，继续流程
- 数据库操作失败 → 抛出异常（由调用方处理）

---

### 2. PortfolioService.sync_position()

**Signature**:
```python
def sync_position(
    self,
    symbol: str,
    quantity: int,
    cost_price: float,
    current_price: Optional[float] = None
) -> Dict:
```

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "600519",
    "quantity": 100,
    "cost_price": 1600.0,
    "current_price": 1650.0,
    "market_value": 165000.0,
    "cost_value": 160000.0,
    "floating_pl": 5000.0,
    "last_updated": "2026-03-24T10:30:00"
  },
  "message": "Position synced successfully"
}
```

---

### 3. API Endpoint

**Route**: `POST /portfolio/positions/sync`

**Request Body**:
```json
{
  "symbol": "600519",
  "quantity": 100,
  "cost_price": 1600.0,
  "current_price": 1650.0  // Optional
}
```

**Required Fields**:
- `symbol` (string)
- `quantity` (integer)
- `cost_price` (float)

**Optional Fields**:
- `current_price` (float)

---

### 4. Deprecation Strategy

**保留旧接口，标记为废弃**:

```python
def add_position(...) -> PositionModel:
    """
    DEPRECATED: Use sync_position() instead.

    新增持仓股（已废弃）
    """
    # ... 原有逻辑
    warnings.warn("add_position() is deprecated, use sync_position() instead", DeprecationWarning)

def update_position(...) -> PositionModel:
    """
    DEPRECATED: Use sync_position() instead.

    更新持仓股（已废弃）
    """
    # ... 原有逻辑
    warnings.warn("update_position() is deprecated, use sync_position() instead", DeprecationWarning)
```

---

## 📚 Documentation Updates

### 1. Developer Guide (`docs/developer-guide/04-module-guide/03-portfolio-manager.md`)

**新增示例**:
```python
# 同步持仓（推荐）
position = commands.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0
)
print(f"Position value: {position.market_value}")

# 旧接口（已废弃）
position = commands.add_position("600519", 100, 1600)  # Deprecated
```

---

### 2. User Guide (`docs/user-guide/07-portfolio-management.md`)

**新增章节**:
```markdown
## 🔄 同步持仓

### 智能同步

```python
# 自动判断：存在则覆盖，不存在则新增
portfolio.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0
)

# 可选：手动指定现价
portfolio.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0,
    current_price=1650.0
)
```

**特点**:
- ✅ 无需判断持仓是否存在
- ✅ 现价未提供时自动查询
- ✅ 自动计算市值、盈亏等指标
```

---

### 3. API Reference (`docs/developer-guide/03-api-reference.md`)

**新增接口**:
```markdown
### POST /portfolio/positions/sync

**Description**: 同步持仓信息（存在则覆盖，不存在则新增）

**Body**:
```json
{
  "symbol": "600519",
  "quantity": 100,
  "cost_price": 1600.0,
  "current_price": 1650.0  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "symbol": "600519",
    "quantity": 100,
    "cost_price": 1600.0,
    "current_price": 1650.0,
    "market_value": 165000.0,
    "floating_pl": 5000.0
  }
}
```
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# Test 1: 新增持仓
def test_sync_position_new():
    service = PositionService(repo, data_source)
    result = service.sync_position("600519", 100, 1600.0)
    assert result.symbol == "600519"
    assert result.quantity == 100

# Test 2: 覆盖现有持仓
def test_sync_position_update():
    service = PositionService(repo, data_source)
    service.sync_position("600519", 100, 1600.0)  # First
    result = service.sync_position("600519", 150, 1550.0)  # Update
    assert result.quantity == 150
    assert result.cost_price == 1550.0

# Test 3: 自动查询现价
def test_sync_position_auto_query_price(mocker):
    data_source = mocker.Mock()
    data_source.get_realtime.return_value = Quote(price=1650.0)
    service = PositionService(repo, data_source)
    result = service.sync_position("600519", 100, 1600.0)
    assert result.current_price == 1650.0
```

### Integration Tests

- API endpoint 测试
- 数据源集成测试
- 数据库事务测试

---

## 🔒 Security Considerations

1. **输入验证**:
   - `quantity` > 0
   - `cost_price` 支持负数（允许负成本场景）
   - `symbol` 格式校验

2. **SQL Injection**:
   - 使用 SQLAlchemy ORM，自动参数化

3. **数据一致性**:
   - 数据库事务保证原子性

---

## 📊 Impact Analysis

### Breaking Changes

- ❌ **无破坏性变更**
- ✅ 旧接口保留（标记废弃）
- ✅ 新接口向后兼容

### Migration Path

**旧代码**:
```python
portfolio.add_position("600519", 100, 1600)
portfolio.update_position("600519", quantity=150)
```

**新代码**:
```python
portfolio.sync_position("600519", 100, 1600)
portfolio.sync_position("600519", 150, 1550)
```

---

## 🚀 Next Steps

1. ✅ **设计审批通过**
2. 🔄 **生成实施计划**（writing-plans）
3. 🛠️ **实施开发**
4. 🧪 **单元测试**
5. 📝 **文档更新**
6. ✅ **代码审查**

---

**Approved by**: zxg
**Date**: 2026-03-24
**Status**: ✅ Ready for Implementation
