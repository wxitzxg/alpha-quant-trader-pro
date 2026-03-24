# 🔄 Portfolio Sync Position Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 整合 `add_position()` 和 `update_position()` 为统一的 `sync_position()` 接口，实现"存在则覆盖，不存在则新增"的智能同步

**Architecture:** 在 `PositionService` 中实现 `sync_position()` 核心逻辑，向上层 `PortfolioService` 和 API 路由暴露接口，废弃旧方法

**Tech Stack:** Python, SQLAlchemy, FastAPI, Pydantic

---

## 🗂️ File Structure

### Core Layer
- **Modify:** `portfolio_manager/position_service.py` - 新增 `sync_position()`，标记旧方法废弃
- **Reference:** `portfolio_manager/database.py` - `Position` 模型和 `calculate_metrics()`
- **Reference:** `portfolio_manager/repositories/position_repository.py` - 仓储层

### Service Layer
- **Modify:** `api_server/services/portfolio_service.py` - 新增 `sync_position()` 服务方法

### API Layer
- **Modify:** `api_server/routers/portfolio.py` - 新增 `POST /portfolio/positions/sync` 路由

### Documentation
- **Modify:** `docs/developer-guide/04-module-guide/03-portfolio-manager.md`
- **Modify:** `docs/user-guide/07-portfolio-management.md`
- **Modify:** `docs/developer-guide/03-api-reference.md`

### Testing
- **Create:** `tests/portfolio_manager/test_position_service.py` - 单元测试
- **Create:** `tests/api_server/test_portfolio_sync.py` - 集成测试

---

## 📋 Tasks

### Task 1: Implement PositionService.sync_position()

**Files:**
- Modify: `portfolio_manager/position_service.py`
- Reference: `portfolio_manager/database.py`
- Reference: `portfolio_manager/repositories/position_repository.py`

#### Implementation Details

`portfolio_manager/position_service.py` 需要实现：

```python
def sync_position(
    self,
    symbol: str,
    quantity: int,
    cost_price: float,
    current_price: Optional[float] = None
) -> PositionModel:
    """
    同步持仓信息（存在则覆盖，不存在则新增）

    核心逻辑：
    1. 查询持仓是否存在
    2. 如果未提供 current_price，尝试从数据源查询
    3. 存在则更新，不存在则新增
    4. 自动计算指标（市值、盈亏等）
    5. 保存到数据库

    Args:
        symbol: 股票代码（必填）
        quantity: 持仓数量（必填）
        cost_price: 成本价（必填，支持负数）
        current_price: 当前价格（可选，未提供则自动查询）

    Returns:
        PositionModel

    Raises:
        ValueError: quantity <= 0
    """
    # 参数校验
    if quantity <= 0:
        raise ValueError(f"Quantity must be > 0, got {quantity}")

    # 查询现有持仓
    position = self.repo.get_by_symbol(symbol)

    # 如果未提供现价，尝试从数据源获取
    if current_price is None and self.data_source:
        try:
            quote = self.data_source.get_realtime(symbol)
            if quote and quote.price:
                current_price = quote.price
        except Exception:
            # 数据源异常，使用 None
            pass

    # 转换为 Decimal
    cost_price_decimal = Decimal(str(cost_price))
    current_price_decimal = Decimal(str(current_price)) if current_price is not None else None

    # 如果持仓存在，更新
    if position:
        position.quantity = quantity
        position.cost_price = cost_price_decimal
        position.current_price = current_price_decimal
    # 如果持仓不存在，创建新记录
    else:
        position = Position(
            symbol=symbol,
            quantity=quantity,
            cost_price=cost_price_decimal,
            current_price=current_price_decimal
        )

    # 计算指标
    position.calculate_metrics()

    # 保存到数据库
    if not position.id:  # 新记录
        self.repo.add(position)

    return self._to_pydantic(position)
```

- [ ] **Step 1: 在 position_service.py 中添加 sync_position() 方法**

将上述代码添加到 `PositionService` 类中

- [ ] **Step 2: 标记旧方法为废弃**

在 `add_position()` 和 `update_position()` 方法上添加警告：

```python
import warnings

def add_position(...) -> PositionModel:
    """
    DEPRECATED: Use sync_position() instead.

    新增持仓股（已废弃）
    ...
    """
    warnings.warn(
        "add_position() is deprecated, use sync_position() instead",
        DeprecationWarning,
        stacklevel=2
    )
    # ... 原有逻辑

def update_position(...) -> PositionModel:
    """
    DEPRECATED: Use sync_position() instead.

    更新持仓股（已废弃）
    ...
    """
    warnings.warn(
        "update_position() is deprecated, use sync_position() instead",
        DeprecationWarning,
        stacklevel=2
    )
    # ... 原有逻辑
```

- [ ] **Step 3: Commit**

```bash
git add portfolio_manager/position_service.py
git commit -m "feat(position_service): add sync_position method

- 新增 sync_position()：智能同步持仓（存在则覆盖，不存在则新增）
- 自动查询现价（如果未提供）
- 自动计算指标（市值、盈亏）
- 标记 add_position() 和 update_position() 为废弃"
```

---

### Task 2: Update PortfolioService

**Files:**
- Modify: `api_server/services/portfolio_service.py`

#### Implementation Details

`api_server/services/portfolio_service.py` 需要添加：

```python
def sync_position(
    self,
    symbol: str,
    quantity: int,
    cost_price: float,
    current_price: Optional[float] = None
) -> Dict:
    """
    同步持仓信息（存在则覆盖，不存在则新增）

    Args:
        symbol: 股票代码（必填）
        quantity: 持仓数量（必填）
        cost_price: 成本价（必填）
        current_price: 当前价格（可选）

    Returns:
        {
            "success": bool,
            "data": PositionInfo | None,
            "message": str
        }
    """
    try:
        _, position_service, _, _, _ = self._get_services()

        position = position_service.sync_position(
            symbol=symbol,
            quantity=quantity,
            cost_price=cost_price,
            current_price=current_price
        )

        return {
            "success": True,
            "data": {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "cost_price": position.cost_price,
                "current_price": position.current_price,
                "market_value": position.market_value,
                "cost_value": position.cost_value,
                "floating_pl": position.floating_pl,
                "last_updated": position.last_updated.isoformat()
            },
            "message": f"Position {symbol} synced successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to sync position: {str(e)}"
        }
```

- [ ] **Step 1: 在 PortfolioService 类中添加 sync_position() 方法**

将上述代码添加到 `PortfolioService` 类中

- [ ] **Step 2: 标记旧方法为废弃（可选）**

在 `add_position()` 和 `update_position()` 方法添加警告：

```python
def add_position(...) -> Dict:
    """
    DEPRECATED: Use sync_position() instead.
    ...
    """
    import warnings
    warnings.warn(
        "add_position() is deprecated, use sync_position() instead",
        DeprecationWarning,
        stacklevel=2
    )
    # ... 原有逻辑

def update_position(...) -> Dict:
    """
    DEPRECATED: Use sync_position() instead.
    ...
    """
    import warnings
    warnings.warn(
        "update_position() is deprecated, use sync_position() instead",
        DeprecationWarning,
        stacklevel=2
    )
    # ... 原有逻辑
```

- [ ] **Step 3: Commit**

```bash
git add api_server/services/portfolio_service.py
git commit -m "feat(portfolio_service): add sync_position endpoint

- 新增 sync_position() 服务方法
- 调用 position_service.sync_position()
- 返回统一的 API 响应格式
- 标记旧方法为废弃（可选）"
```

---

### Task 3: Add API Router Endpoint

**Files:**
- Modify: `api_server/routers/portfolio.py`
- Reference: `api_server/models/portfolio.py` (检查是否需要新增 Pydantic 模型)

#### Implementation Details

首先检查是否需要新的 Pydantic 模型（可能已存在）：

```python
# 如果不存在，需要在 api_server/models/portfolio.py 中添加
class PositionSyncRequest(BaseModel):
    """持仓同步请求"""
    stock_code: str = Field(..., description="股票代码", example="600519")
    quantity: int = Field(..., gt=0, description="持仓数量", example=100)
    cost_price: float = Field(..., description="成本价", example=1600.0)
    current_price: Optional[float] = Field(None, description="当前价格", example=1650.0)
```

然后在 `portfolio.py` 中添加路由：

```python
from ..models.portfolio import PositionSyncRequest  # 如果需要

@portfolio_router.post("/portfolio/positions/sync", response_model=APIResponse)
async def sync_position(request: PositionSyncRequest):
    """同步持仓信息（存在则覆盖，不存在则新增）"""
    try:
        result = service.sync_position(
            symbol=request.stock_code,
            quantity=request.quantity,
            cost_price=request.cost_price,
            current_price=request.current_price
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to sync position"))

        return APIResponse(
            data=result.get("data"),
            message=result.get("message", "Position synced successfully")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing position: {str(e)}")
```

- [ ] **Step 1: 检查是否需要新的 Pydantic 模型**

```bash
grep -n "PositionSyncRequest" api_server/models/portfolio.py
```

如果不存在，创建 `PositionSyncRequest` 模型

- [ ] **Step 2: 在 portfolio.py 中添加 sync_position 路由**

将路由代码添加到 `portfolio_router` 中

- [ ] **Step 3: 测试 API 端点**

使用 curl 测试：

```bash
curl -X POST "http://localhost:8000/portfolio/positions/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "quantity": 100,
    "cost_price": 1600.0
  }'
```

- [ ] **Step 4: Commit**

```bash
git add api_server/routers/portfolio.py
git add api_server/models/portfolio.py  # 如果创建了新模型
git commit -m "feat(api): add POST /portfolio/positions/sync endpoint

- 新增持仓同步 API 端点
- 支持智能同步（存在则覆盖，不存在则新增）
- 自动查询现价（可选参数）
- 返回持仓详细信息"
```

---

### Task 4: Write Unit Tests for PositionService

**Files:**
- Create: `tests/portfolio_manager/test_position_service.py`

#### Test Cases

```python
import pytest
from unittest.mock import Mock, MagicMock
from portfolio_manager.position_service import PositionService
from portfolio_manager.database import Position
from portfolio_manager.models import PositionModel

class TestPositionService:
    """Test PositionService.sync_position()"""

    @pytest.fixture
    def mock_repo(self):
        repo = Mock()
        repo.get_by_symbol = Mock(return_value=None)
        repo.add = Mock()
        return repo

    @pytest.fixture
    def mock_data_source(self):
        ds = Mock()
        ds.get_realtime = Mock(return_value=None)
        return ds

    @pytest.fixture
    def service(self, mock_repo, mock_data_source):
        return PositionService(mock_repo, mock_data_source)

    def test_sync_new_position(self, service, mock_repo):
        """Test syncing a new position (create)"""
        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=1600.0
        )

        assert result.symbol == "600519"
        assert result.quantity == 100
        assert result.cost_price == 1600.0
        mock_repo.add.assert_called_once()

    def test_sync_existing_position(self, service, mock_repo):
        """Test syncing an existing position (update)"""
        # 模拟已有持仓
        existing = Position(
            id=1,
            symbol="600519",
            quantity=50,
            cost_price=1500.0
        )
        mock_repo.get_by_symbol.return_value = existing

        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=1600.0
        )

        assert result.symbol == "600519"
        assert result.quantity == 100
        assert result.cost_price == 1600.0
        mock_repo.add.assert_not_called()  # 不应调用 add

    def test_sync_with_auto_query_price(self, service, mock_repo, mock_data_source):
        """Test syncing with automatic price query"""
        mock_data_source.get_realtime.return_value = Mock(price=1650.0)

        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=1600.0
            # 不提供 current_price，应自动查询
        )

        assert result.current_price == 1650.0
        mock_data_source.get_realtime.assert_called_once_with("600519")

    def test_sync_with_provided_price(self, service, mock_repo, mock_data_source):
        """Test syncing with provided price (should not query)"""
        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=1600.0,
            current_price=1650.0  # 提供了现价
        )

        assert result.current_price == 1650.0
        mock_data_source.get_realtime.assert_not_called()

    def test_sync_calculates_metrics(self, service, mock_repo):
        """Test that metrics are calculated"""
        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=1600.0,
            current_price=1650.0
        )

        assert result.market_value == 165000.0
        assert result.cost_value == 160000.0
        assert result.floating_pl == 5000.0

    def test_sync_with_negative_cost_price(self, service, mock_repo):
        """Test syncing with negative cost price (allowed scenario)"""
        result = service.sync_position(
            symbol="600519",
            quantity=100,
            cost_price=-100.0  # 高位卖出留底仓场景
        )

        assert result.cost_price == -100.0
```

- [ ] **Step 1: 创建测试文件**

将上述测试代码保存到 `tests/portfolio_manager/test_position_service.py`

- [ ] **Step 2: 运行测试**

```bash
pytest tests/portfolio_manager/test_position_service.py -v
```

- [ ] **Step 3: 修复失败的测试**

根据测试结果修复代码

- [ ] **Step 4: 再次运行测试**

确保所有测试通过

- [ ] **Step 5: Commit**

```bash
git add tests/portfolio_manager/test_position_service.py
git commit -m "test(position_service): add sync_position unit tests

- 测试新增持仓
- 测试覆盖现有持仓
- 测试自动查询现价
- 测试手动提供现价
- 测试指标计算
- 测试负成本价场景"
```

---

### Task 5: Write Integration Tests for API

**Files:**
- Create: `tests/api_server/test_portfolio_sync.py`

#### Test Cases

```python
import pytest
from fastapi.testclient import TestClient
from api_server.main import app

client = TestClient(app)

class TestPortfolioSyncAPI:
    """Test portfolio sync API endpoint"""

    def test_sync_new_position(self):
        """Test syncing a new position via API"""
        response = client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 100,
                "cost_price": 1600.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["symbol"] == "600519"
        assert data["data"]["quantity"] == 100

    def test_sync_existing_position(self):
        """Test syncing an existing position via API"""
        # First sync
        client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 100,
                "cost_price": 1600.0
            }
        )

        # Second sync (should update)
        response = client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 150,
                "cost_price": 1550.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["quantity"] == 150
        assert data["data"]["cost_price"] == 1550.0

    def test_sync_with_current_price(self):
        """Test syncing with provided current price"""
        response = client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 100,
                "cost_price": 1600.0,
                "current_price": 1650.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["current_price"] == 1650.0

    def test_sync_invalid_quantity(self):
        """Test syncing with invalid quantity"""
        response = client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 0,  # 无效数量
                "cost_price": 1600.0
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_sync_missing_required_field(self):
        """Test syncing with missing required field"""
        response = client.post(
            "/portfolio/positions/sync",
            json={
                "stock_code": "600519",
                "quantity": 100
                # 缺少 cost_price
            }
        )

        assert response.status_code == 422  # Pydantic validation error
```

- [ ] **Step 1: 创建测试文件**

将上述测试代码保存到 `tests/api_server/test_portfolio_sync.py`

- [ ] **Step 2: 启动 API 服务器**

```bash
python -m api_server.main
```

- [ ] **Step 3: 运行集成测试**

```bash
pytest tests/api_server/test_portfolio_sync.py -v
```

- [ ] **Step 4: 修复失败的测试**

根据测试结果修复代码

- [ ] **Step 5: Commit**

```bash
git add tests/api_server/test_portfolio_sync.py
git commit -m "test(api): add portfolio sync integration tests

- 测试新增持仓 API
- 测试覆盖现有持仓 API
- 测试提供现价参数
- 测试参数验证"
```

---

### Task 6: Update Developer Guide

**Files:**
- Modify: `docs/developer-guide/04-module-guide/03-portfolio-manager.md`

#### Updates

```markdown
## Usage Examples

### Sync Position (Recommended)

```python
from portfolio_manager import PortfolioCommands

commands = PortfolioCommands()

# 同步持仓（存在则覆盖，不存在则新增）
position = commands.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0
)
print(f"Position value: {position.market_value}")

# 可选：手动指定现价
position = commands.sync_position(
    symbol="600519",
    quantity=100,
    cost_price=1600.0,
    current_price=1650.0
)
```

### Legacy Methods (Deprecated)

```python
# ⚠️ 已废弃，建议使用 sync_position()
position = commands.add_position("600519", quantity=100, cost_price=1600.0)  # Deprecated
position = commands.update_position("600519", quantity=150, cost_price=1550.0)  # Deprecated
```
```

- [ ] **Step 1: 更新文档**

在 `docs/developer-guide/04-module-guide/03-portfolio-manager.md` 中添加上述内容

- [ ] **Step 2: Commit**

```bash
git add docs/developer-guide/04-module-guide/03-portfolio-manager.md
git commit -m "docs: update portfolio manager guide with sync_position

- 添加 sync_position() 使用示例
- 标记旧方法为废弃
- 提供推荐用法和遗留用法对比"
```

---

### Task 7: Update User Guide

**Files:**
- Modify: `docs/user-guide/07-portfolio-management.md`

#### Updates

在文件中添加新章节：

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

### 迁移指南

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
```

- [ ] **Step 1: 更新用户指南**

在 `docs/user-guide/07-portfolio-management.md` 中添加上述内容

- [ ] **Step 2: Commit**

```bash
git add docs/user-guide/07-portfolio-management.md
git commit -m "docs(user): add sync_position guide to portfolio management

- 添加同步持仓功能说明
- 提供使用示例
- 添加迁移指南（旧方法 → 新方法）"
```

---

### Task 8: Update API Reference

**Files:**
- Modify: `docs/developer-guide/03-api-reference.md`

#### Updates

```markdown
### POST /portfolio/positions/sync

**Description**: 同步持仓信息（存在则覆盖，不存在则新增）

**Request Body**:
```json
{
  "stock_code": "600519",
  "quantity": 100,
  "cost_price": 1600.0,
  "current_price": 1650.0  // Optional
}
```

**Required Fields**:
- `stock_code` (string): 股票代码
- `quantity` (integer): 持仓数量 (> 0)
- `cost_price` (float): 成本价

**Optional Fields**:
- `current_price` (float): 当前价格（未提供时自动查询）

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
  "message": "Position 600519 synced successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/portfolio/positions/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "quantity": 100,
    "cost_price": 1600.0
  }'
```

---

### Legacy Endpoints (Deprecated)

- `POST /portfolio/positions/add` - Use `sync` instead
- `PUT /portfolio/positions/{stock_code}` - Use `sync` instead
```

- [ ] **Step 1: 更新 API 参考文档**

在 `docs/developer-guide/03-api-reference.md` 中添加上述内容

- [ ] **Step 2: Commit**

```bash
git add docs/developer-guide/03-api-reference.md
git commit -m "docs(api): add sync_position to API reference

- 添加 POST /portfolio/positions/sync 接口文档
- 包含请求/响应示例
- 标记旧端点为废弃"
```

---

### Task 9: Final Integration Test

**Files:**
- None (test execution)

- [ ] **Step 1: 运行所有单元测试**

```bash
pytest tests/portfolio_manager/ -v --tb=short
```

- [ ] **Step 2: 运行所有集成测试**

```bash
pytest tests/api_server/ -v --tb=short
```

- [ ] **Step 3: 测试端到端流程**

```python
from portfolio_manager import PortfolioCommands

# 1. 初始化
portfolio = PortfolioCommands()

# 2. 同步新持仓
portfolio.sync_position("600519", 100, 1600.0)

# 3. 验证持仓存在
position = portfolio.get_position("600519")
assert position is not None
assert position.quantity == 100

# 4. 覆盖现有持仓
portfolio.sync_position("600519", 150, 1550.0)

# 5. 验证已更新
position = portfolio.get_position("600519")
assert position.quantity == 150
assert position.cost_price == 1550.0

print("✅ End-to-end test passed!")
```

- [ ] **Step 4: 验证 API 端点**

```bash
# 测试新增
curl -X POST "http://localhost:8000/portfolio/positions/sync" \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 100, "cost_price": 1600.0}'

# 测试覆盖
curl -X POST "http://localhost:8000/portfolio/positions/sync" \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "quantity": 150, "cost_price": 1550.0}'
```

- [ ] **Step 5: Commit**

```bash
git commit -m "test: final integration validation for sync_position

- 验证所有单元测试通过
- 验证所有集成测试通过
- 端到端测试通过
- API 端点验证通过"
```

---

### Task 10: Update Changelog

**Files:**
- Modify: `docs/project-docs/02-changelog.md`

#### Updates

```markdown
## [Unreleased]

### Added
- `sync_position()` 方法：智能同步持仓（存在则覆盖，不存在则新增）
- `POST /portfolio/positions/sync` API 端点
- 自动查询现价功能（可选）
- 完整的单元测试和集成测试

### Deprecated
- `add_position()` 方法（使用 `sync_position()` 替代）
- `update_position()` 方法（使用 `sync_position()` 替代）
- `POST /portfolio/positions/add` API 端点（使用 `sync` 替代）
- `PUT /portfolio/positions/{stock_code}` API 端点（使用 `sync` 替代）
```

- [ ] **Step 1: 更新 changelog**

在 `docs/project-docs/02-changelog.md` 中添加上述内容

- [ ] **Step 2: Final commit**

```bash
git add docs/project-docs/02-changelog.md
git commit -m "docs(changelog): add sync_position feature

- 记录新增的 sync_position() 功能
- 标记废弃的旧方法和 API 端点"
```

---

## ✅ Completion Checklist

- [ ] Task 1: 实现 PositionService.sync_position()
- [ ] Task 2: 更新 PortfolioService
- [ ] Task 3: 添加 API 路由端点
- [ ] Task 4: 编写 PositionService 单元测试
- [ ] Task 5: 编写 API 集成测试
- [ ] Task 6: 更新开发者指南
- [ ] Task 7: 更新用户指南
- [ ] Task 8: 更新 API 参考文档
- [ ] Task 9: 最终集成测试
- [ ] Task 10: 更新 changelog

---

**Plan complete! Ready for subagent-driven execution.**
