# 股票收藏管理功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 portfolio_manager 模块新增股票收藏管理功能，支持用户添加、移除、更新和查询收藏股票。

**Architecture:** 遵循现有的 Repository/Service 分层架构。新增 StockFavorite 数据模型、FavoriteRepository、FavoriteService、API 接口。所有收藏相关的代码独立于持仓管理，职责清晰。

**Tech Stack:** Python 3.x, FastAPI, SQLAlchemy, Pydantic, pytest

---

## 文件结构

```
portfolio_manager/
├── database.py              # 修改：新增 StockFavorite 模型
├── repositories/
│   ├── __init__.py          # 修改：导出 FavoriteRepository
│   └── favorite_repository.py    # 新增
├── services/
│   ├── __init__.py          # 新增
│   └── favorite_service.py  # 新增
├── schemas/
│   ├── __init__.py          # 修改：导出收藏相关 schema
│   └── favorite_schemas.py  # 新增
├── containers.py            # 修改：注册 FavoriteService

api_server/
└── routers/
    └── portfolio.py         # 修改：新增收藏 API 接口

tests/
└── portfolio_manager/
    └── test_favorite_service.py  # 新增
```

---

## Task 1: 数据模型 StockFavorite

**Files:**
- Modify: `portfolio_manager/database.py`
- Test: `tests/portfolio_manager/test_database.py`

- [ ] **Step 1: 在 database.py 添加 StockFavorite 模型**

在 `portfolio_manager/database.py` 文件末尾添加：

```python
class StockFavorite(Base):
    """股票收藏表"""
    __tablename__ = 'stock_favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, comment='股票代码')
    tag = Column(String(50), nullable=True, comment='标签')
    note = Column(String(200), nullable=True, comment='备注')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_stock_favorites_created_at', created_at.desc()),
    )

    def __repr__(self):
        return f"<StockFavorite({self.symbol}, tag={self.tag})>"
```

需要导入：`from sqlalchemy import Index`（如果尚未导入）

- [ ] **Step 2: 运行测试验证模型定义**

Run: `python -c "from portfolio_manager.database import StockFavorite; print(StockFavorite.__tablename__)"`

Expected: `stock_favorites`

- [ ] **Step 3: Commit**

```bash
git add portfolio_manager/database.py
git commit -m "feat(portfolio): add StockFavorite model"
```

---

## Task 2: Pydantic Schemas

**Files:**
- Create: `portfolio_manager/schemas/favorite_schemas.py`
- Modify: `portfolio_manager/schemas/__init__.py`

- [ ] **Step 1: 创建 favorite_schemas.py**

创建文件 `portfolio_manager/schemas/favorite_schemas.py`：

```python
"""
股票收藏数据验证模型（Pydantic Schemas）
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AddFavoriteRequest(BaseModel):
    """添加收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    tag: Optional[str] = Field(None, max_length=50, description="标签")
    note: Optional[str] = Field(None, max_length=200, description="备注")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "自选股",
                "note": "业绩超预期"
            }
        }
    }


class RemoveFavoriteRequest(BaseModel):
    """移除收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")


class UpdateFavoriteRequest(BaseModel):
    """更新收藏请求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    tag: Optional[str] = Field(None, max_length=50, description="新标签（不传表示不修改）")
    note: Optional[str] = Field(None, max_length=200, description="新备注（不传表示不修改）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "策略池",
                "note": "突破形态"
            }
        }
    }


class FavoriteResponse(BaseModel):
    """收藏信息响应"""
    symbol: str
    tag: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "600519",
                "tag": "自选股",
                "note": "业绩超预期",
                "created_at": "2026-03-26T10:00:00",
                "updated_at": "2026-03-26T10:00:00"
            }
        }
    }
```

- [ ] **Step 2: 更新 schemas/__init__.py 导出**

在 `portfolio_manager/schemas/__init__.py` 添加导入和导出：

```python
from .favorite_schemas import (
    AddFavoriteRequest,
    RemoveFavoriteRequest,
    UpdateFavoriteRequest,
    FavoriteResponse
)

__all__ = [
    # ... 现有导出 ...
    'AddFavoriteRequest',
    'RemoveFavoriteRequest',
    'UpdateFavoriteRequest',
    'FavoriteResponse'
]
```

- [ ] **Step 3: 验证 schema 导入**

Run: `python -c "from portfolio_manager.schemas import AddFavoriteRequest; print(AddFavoriteRequest.__name__)"`

Expected: `AddFavoriteRequest`

- [ ] **Step 4: Commit**

```bash
git add portfolio_manager/schemas/favorite_schemas.py portfolio_manager/schemas/__init__.py
git commit -m "feat(portfolio): add favorite schemas"
```

---

## Task 3: FavoriteRepository

**Files:**
- Create: `portfolio_manager/repositories/favorite_repository.py`
- Modify: `portfolio_manager/repositories/__init__.py`
- Test: `tests/portfolio_manager/test_favorite_repository.py`（新建）

- [ ] **Step 1: 编写 FavoriteRepository 测试**

创建文件 `tests/portfolio_manager/test_favorite_repository.py`：

```python
"""FavoriteRepository 单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from portfolio_manager.repositories.favorite_repository import FavoriteRepository
from portfolio_manager.database import StockFavorite


class TestFavoriteRepository:
    """FavoriteRepository 测试"""

    @pytest.fixture
    def session(self):
        return Mock()

    @pytest.fixture
    def repository(self, session):
        return FavoriteRepository(session)

    def test_get_by_symbol_found(self, repository, session):
        """测试根据 symbol 查找收藏（找到）"""
        mock_favorite = Mock(spec=StockFavorite)
        mock_favorite.symbol = "600519"
        mock_favorite.tag = "自选股"
        mock_favorite.note = "测试备注"

        session.execute.return_value.scalar_one_or_none.return_value = mock_favorite

        result = repository.get_by_symbol("600519")

        assert result == mock_favorite

    def test_get_by_symbol_not_found(self, repository, session):
        """测试根据 symbol 查找收藏（未找到）"""
        session.execute.return_value.scalar_one_or_none.return_value = None

        result = repository.get_by_symbol("999999")

        assert result is None

    def test_get_all(self, repository, session):
        """测试获取所有收藏"""
        mock_favorites = [Mock(spec=StockFavorite), Mock(spec=StockFavorite)]
        session.execute.return_value.scalars.return_value.all.return_value = mock_favorites

        result = repository.get_all()

        assert result == mock_favorites

    def test_get_all_paginated(self, repository, session):
        """测试分页获取收藏"""
        mock_favorites = [Mock(spec=StockFavorite)]
        session.execute.return_value.scalars.return_value.all.return_value = mock_favorites

        result = repository.get_all_paginated(page=1, page_size=10)

        assert result == mock_favorites

    def test_count(self, repository, session):
        """测试统计收藏数量"""
        session.execute.return_value.scalar.return_value = 5

        result = repository.count()

        assert result == 5
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/portfolio_manager/test_favorite_repository.py -v`

Expected: FAIL (module not found)

- [ ] **Step 3: 实现 FavoriteRepository**

创建文件 `portfolio_manager/repositories/favorite_repository.py`：

```python
"""股票收藏数据仓库层"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from common.repositories.base import BaseRepository
from portfolio_manager.database import StockFavorite


class FavoriteRepository(BaseRepository[StockFavorite]):
    """股票收藏仓库"""

    def __init__(self, session: Session):
        super().__init__(session, StockFavorite)

    def get_by_symbol(self, symbol: str) -> Optional[StockFavorite]:
        """根据股票代码获取收藏"""
        return self.get_by(symbol=symbol)

    def get_all(self) -> List[StockFavorite]:
        """获取所有收藏（按创建时间倒序）"""
        stmt = select(StockFavorite).order_by(StockFavorite.created_at.desc())
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> List[StockFavorite]:
        """分页获取收藏（按创建时间倒序）"""
        offset = (page - 1) * page_size
        stmt = (
            select(StockFavorite)
            .order_by(StockFavorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def count(self) -> int:
        """获取收藏总数"""
        stmt = select(func.count(StockFavorite.id))
        result = self.session.execute(stmt).scalar()
        return result or 0

    def exists(self, symbol: str) -> bool:
        """检查股票是否已收藏"""
        return self.get_by_symbol(symbol) is not None
```

- [ ] **Step 4: 更新 repositories/__init__.py**

在 `portfolio_manager/repositories/__init__.py` 添加：

```python
from .favorite_repository import FavoriteRepository

__all__ = [
    # ... 现有导出 ...
    'FavoriteRepository'
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/portfolio_manager/test_favorite_repository.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add portfolio_manager/repositories/favorite_repository.py portfolio_manager/repositories/__init__.py tests/portfolio_manager/test_favorite_repository.py
git commit -m "feat(portfolio): add FavoriteRepository with tests"
```

---

## Task 4: FavoriteService

**Files:**
- Create: `portfolio_manager/services/__init__.py`
- Create: `portfolio_manager/services/favorite_service.py`
- Test: `tests/portfolio_manager/test_favorite_service.py`（新建）

- [ ] **Step 1: 编写 FavoriteService 测试**

创建文件 `tests/portfolio_manager/test_favorite_service.py`：

```python
"""FavoriteService 单元测试"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from portfolio_manager.services.favorite_service import FavoriteService
from portfolio_manager.database import StockFavorite
from portfolio_manager.schemas.favorite_schemas import FavoriteResponse
from common.exceptions import NotFoundError, BusinessError


class TestFavoriteService:
    """FavoriteService 测试"""

    @pytest.fixture
    def favorite_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, favorite_repo):
        return FavoriteService(repository=favorite_repo)

    # === add_favorite 测试 ===
    def test_add_favorite_success(self, service, favorite_repo):
        """测试添加收藏成功"""
        favorite_repo.exists.return_value = False
        favorite_repo.get_by_symbol.return_value = Mock(
            spec=StockFavorite,
            symbol="600519",
            tag="自选股",
            note="测试",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = service.add_favorite(symbol="600519", tag="自选股", note="测试")

        favorite_repo.add.assert_called_once()
        assert result.symbol == "600519"

    def test_add_favorite_duplicate_raises_error(self, service, favorite_repo):
        """测试重复添加收藏抛出异常"""
        favorite_repo.exists.return_value = True

        with pytest.raises(BusinessError, match="已收藏"):
            service.add_favorite(symbol="600519")

    # === remove_favorite 测试 ===
    def test_remove_favorite_success(self, service, favorite_repo):
        """测试移除收藏成功"""
        mock_favorite = Mock(spec=StockFavorite)
        favorite_repo.get_by_symbol.return_value = mock_favorite

        service.remove_favorite(symbol="600519")

        favorite_repo.delete.assert_called_once_with(mock_favorite)

    def test_remove_favorite_not_found_raises_error(self, service, favorite_repo):
        """测试移除不存在的收藏抛出异常"""
        favorite_repo.get_by_symbol.return_value = None

        with pytest.raises(NotFoundError, match="Favorite"):
            service.remove_favorite(symbol="999999")

    # === update_favorite 测试 ===
    def test_update_favorite_success(self, service, favorite_repo):
        """测试更新收藏成功"""
        mock_favorite = Mock(
            spec=StockFavorite,
            symbol="600519",
            tag="旧标签",
            note="旧备注",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        favorite_repo.get_by_symbol.return_value = mock_favorite

        result = service.update_favorite(symbol="600519", tag="新标签", note="新备注")

        assert mock_favorite.tag == "新标签"
        assert mock_favorite.note == "新备注"

    def test_update_favorite_not_found_raises_error(self, service, favorite_repo):
        """测试更新不存在的收藏抛出异常"""
        favorite_repo.get_by_symbol.return_value = None

        with pytest.raises(NotFoundError, match="Favorite"):
            service.update_favorite(symbol="999999", tag="标签")

    def test_update_favorite_no_fields_raises_error(self, service, favorite_repo):
        """测试更新时未提供任何字段抛出异常"""
        mock_favorite = Mock(spec=StockFavorite)
        favorite_repo.get_by_symbol.return_value = mock_favorite

        with pytest.raises(BusinessError, match="至少提供一个更新字段"):
            service.update_favorite(symbol="600519")

    # === get_all 测试 ===
    def test_get_all_success(self, service, favorite_repo):
        """测试获取所有收藏"""
        mock_favorites = [
            Mock(spec=StockFavorite, symbol="600519", created_at=datetime.now(), updated_at=datetime.now()),
            Mock(spec=StockFavorite, symbol="000001", created_at=datetime.now(), updated_at=datetime.now())
        ]
        favorite_repo.get_all.return_value = mock_favorites

        result = service.get_all()

        assert len(result) == 2

    # === get_paginated 测试 ===
    def test_get_paginated_success(self, service, favorite_repo):
        """测试分页获取收藏"""
        mock_favorites = [Mock(spec=StockFavorite, symbol="600519")]
        favorite_repo.get_all_paginated.return_value = mock_favorites
        favorite_repo.count.return_value = 25

        favorites, total, total_pages = service.get_paginated(page=1, page_size=20)

        assert len(favorites) == 1
        assert total == 25
        assert total_pages == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/portfolio_manager/test_favorite_service.py -v`

Expected: FAIL (module not found)

- [ ] **Step 3: 创建 services 目录和 __init__.py**

创建 `portfolio_manager/services/__init__.py`：

```python
"""服务层模块"""

from .favorite_service import FavoriteService

__all__ = ['FavoriteService']
```

- [ ] **Step 4: 实现 FavoriteService**

创建 `portfolio_manager/services/favorite_service.py`：

```python
"""
股票收藏管理服务
"""

from typing import List, Tuple, Optional
from datetime import datetime
from portfolio_manager.database import StockFavorite
from portfolio_manager.schemas.favorite_schemas import FavoriteResponse
from common.exceptions import NotFoundError, BusinessError
import math


class FavoriteService:
    """股票收藏管理服务"""

    def __init__(self, repository):
        """
        初始化收藏服务

        Args:
            repository: FavoriteRepository 实例（依赖注入）
        """
        self.repo = repository

    def add_favorite(
        self,
        symbol: str,
        tag: Optional[str] = None,
        note: Optional[str] = None
    ) -> FavoriteResponse:
        """
        添加收藏

        Args:
            symbol: 股票代码
            tag: 标签（可选）
            note: 备注（可选）

        Returns:
            FavoriteResponse

        Raises:
            BusinessError: 股票已收藏
        """
        # 检查是否已收藏
        if self.repo.exists(symbol):
            raise BusinessError(f"股票 {symbol} 已收藏", context={"symbol": symbol})

        # 创建收藏记录
        favorite = StockFavorite(
            symbol=symbol,
            tag=tag,
            note=note
        )

        # 保存到数据库
        self.repo.add(favorite)

        # 重新获取以获取完整数据（包括时间戳）
        saved = self.repo.get_by_symbol(symbol)
        return self._to_response(saved)

    def remove_favorite(self, symbol: str) -> None:
        """
        移除收藏

        Args:
            symbol: 股票代码

        Raises:
            NotFoundError: 收藏不存在
        """
        favorite = self.repo.get_by_symbol(symbol)
        if not favorite:
            raise NotFoundError("Favorite", symbol)

        self.repo.delete(favorite)

    def update_favorite(
        self,
        symbol: str,
        tag: Optional[str] = None,
        note: Optional[str] = None
    ) -> FavoriteResponse:
        """
        更新收藏

        Args:
            symbol: 股票代码
            tag: 新标签（None 表示不修改）
            note: 新备注（None 表示不修改）

        Returns:
            FavoriteResponse

        Raises:
            NotFoundError: 收藏不存在
            BusinessError: 未提供任何更新字段
        """
        # 检查是否提供了更新字段
        if tag is None and note is None:
            raise BusinessError("至少提供一个更新字段（tag 或 note）")

        # 查找收藏
        favorite = self.repo.get_by_symbol(symbol)
        if not favorite:
            raise NotFoundError("Favorite", symbol)

        # 更新字段
        if tag is not None:
            favorite.tag = tag
        if note is not None:
            favorite.note = note

        return self._to_response(favorite)

    def get_all(self) -> List[FavoriteResponse]:
        """
        获取所有收藏

        Returns:
            FavoriteResponse 列表
        """
        favorites = self.repo.get_all()
        return [self._to_response(f) for f in favorites]

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[FavoriteResponse], int, int]:
        """
        分页获取收藏

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (favorites, total, total_pages)
        """
        favorites = self.repo.get_all_paginated(page=page, page_size=page_size)
        total = self.repo.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return [self._to_response(f) for f in favorites], total, total_pages

    def _to_response(self, favorite: StockFavorite) -> FavoriteResponse:
        """转换为响应模型"""
        return FavoriteResponse(
            symbol=favorite.symbol,
            tag=favorite.tag,
            note=favorite.note,
            created_at=favorite.created_at or datetime.now(),
            updated_at=favorite.updated_at or datetime.now()
        )
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/portfolio_manager/test_favorite_service.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add portfolio_manager/services/ tests/portfolio_manager/test_favorite_service.py
git commit -m "feat(portfolio): add FavoriteService with tests"
```

---

## Task 5: DI 容器注册

**Files:**
- Modify: `portfolio_manager/containers.py`

- [ ] **Step 1: 在 containers.py 添加 FavoriteRepository 和 FavoriteService**

在 `portfolio_manager/containers.py` 中添加：

1. 导入部分添加：
```python
from portfolio_manager.repositories import PositionRepository, TransactionRepository, CashBalanceRepository, FavoriteRepository
from portfolio_manager.services import FavoriteService
```

2. 在 `# ========== 仓库层 ==========` 部分添加：
```python
    favorite_repository = providers.Factory(
        FavoriteRepository,
        session=db_session
    )
```

3. 在 `# ========== 服务层 ==========` 部分添加：
```python
    favorite_service = providers.Factory(
        FavoriteService,
        repository=favorite_repository
    )
```

4. 在 `get_services` 方法中添加：
```python
def get_services(self):
    """获取所有服务实例"""
    return {
        'position_service': self.position_service(),
        'transaction_service': self.transaction_service(),
        'account_service': self.account_service(),
        'favorite_service': self.favorite_service()
    }
```

- [ ] **Step 2: 验证容器配置**

Run: `python -c "from portfolio_manager.containers import PortfolioManagerContainer; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add portfolio_manager/containers.py
git commit -m "feat(portfolio): register FavoriteService in DI container"
```

---

## Task 6: API 接口

**Files:**
- Modify: `api_server/routers/portfolio.py`
- Modify: `api_server/models/portfolio.py`（如需添加请求模型）

- [ ] **Step 1: 在 portfolio.py 路由中添加收藏接口**

在 `api_server/routers/portfolio.py` 文件末尾添加收藏相关接口：

```python
# ==================== 股票收藏管理 ====================

from portfolio_manager.schemas.favorite_schemas import (
    AddFavoriteRequest,
    RemoveFavoriteRequest,
    UpdateFavoriteRequest,
    FavoriteResponse
)
from portfolio_manager.services.favorite_service import FavoriteService


def _get_favorite_service():
    """获取收藏服务实例"""
    from common.di_container import container
    db_session = container.database_manager().get_session()
    return container.portfolio_manager_container(db_session=db_session).favorite_service()


@portfolio_router.get("/portfolio/favorites", response_model=APIResponse)
async def get_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取收藏列表（分页）"""
    try:
        service = _get_favorite_service()
        favorites, total, total_pages = service.get_paginated(page=page, page_size=page_size)

        return APIResponse(
            data={
                "favorites": [f.model_dump() for f in favorites],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="Favorites retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting favorites: {str(e)}")


@portfolio_router.post("/portfolio/favorites/add", response_model=APIResponse)
async def add_favorite(request: AddFavoriteRequest):
    """添加收藏"""
    try:
        service = _get_favorite_service()
        result = service.add_favorite(
            symbol=request.symbol,
            tag=request.tag,
            note=request.note
        )

        return APIResponse(
            data=result.model_dump(),
            message=f"Stock {request.symbol} added to favorites"
        )
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding favorite: {str(e)}")


@portfolio_router.post("/portfolio/favorites/remove", response_model=APIResponse)
async def remove_favorite(request: RemoveFavoriteRequest):
    """移除收藏"""
    try:
        service = _get_favorite_service()
        service.remove_favorite(symbol=request.symbol)

        return APIResponse(
            data={"symbol": request.symbol},
            message=f"Stock {request.symbol} removed from favorites"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing favorite: {str(e)}")


@portfolio_router.post("/portfolio/favorites/update", response_model=APIResponse)
async def update_favorite(request: UpdateFavoriteRequest):
    """更新收藏"""
    try:
        service = _get_favorite_service()
        result = service.update_favorite(
            symbol=request.symbol,
            tag=request.tag,
            note=request.note
        )

        return APIResponse(
            data=result.model_dump(),
            message=f"Favorite {request.symbol} updated successfully"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating favorite: {str(e)}")
```

- [ ] **Step 2: 运行 API 服务器验证接口**

Run: `python -c "from api_server.routers.portfolio import portfolio_router; print('Routes:', [r.path for r in portfolio_router.routes if 'favorite' in r.path])"`

Expected: 显示 4 个收藏相关路由

- [ ] **Step 3: Commit**

```bash
git add api_server/routers/portfolio.py
git commit -m "feat(api): add stock favorites API endpoints"
```

---

## Task 7: 集成测试

**Files:**
- Create: `tests/api_server/test_favorite_api.py`

- [ ] **Step 1: 编写 API 集成测试**

创建 `tests/api_server/test_favorite_api.py`：

```python
"""股票收藏 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api_server.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_favorite_service():
    with patch('api_server.routers.portfolio._get_favorite_service') as mock:
        yield mock


class TestFavoriteAPI:
    """收藏 API 测试"""

    def test_get_favorites(self, client, mock_favorite_service):
        """测试获取收藏列表"""
        mock_service = Mock()
        mock_service.get_paginated.return_value = ([], 0, 0)
        mock_favorite_service.return_value = mock_service

        response = client.get("/portfolio/favorites")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_add_favorite(self, client, mock_favorite_service):
        """测试添加收藏"""
        from datetime import datetime
        mock_service = Mock()
        mock_service.add_favorite.return_value = Mock(
            model_dump=lambda: {
                "symbol": "600519",
                "tag": "自选股",
                "note": "测试",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        )
        mock_favorite_service.return_value = mock_service

        response = client.post(
            "/portfolio/favorites/add",
            json={"symbol": "600519", "tag": "自选股"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_add_favorite_duplicate(self, client, mock_favorite_service):
        """测试重复添加收藏"""
        from common.exceptions import BusinessError
        mock_service = Mock()
        mock_service.add_favorite.side_effect = BusinessError("股票已收藏")
        mock_favorite_service.return_value = mock_service

        response = client.post(
            "/portfolio/favorites/add",
            json={"symbol": "600519"}
        )

        assert response.status_code == 400

    def test_remove_favorite(self, client, mock_favorite_service):
        """测试移除收藏"""
        mock_service = Mock()
        mock_service.remove_favorite.return_value = None
        mock_favorite_service.return_value = mock_service

        response = client.post(
            "/portfolio/favorites/remove",
            json={"symbol": "600519"}
        )

        assert response.status_code == 200

    def test_remove_favorite_not_found(self, client, mock_favorite_service):
        """测试移除不存在的收藏"""
        from common.exceptions import NotFoundError
        mock_service = Mock()
        mock_service.remove_favorite.side_effect = NotFoundError("Favorite", "999999")
        mock_favorite_service.return_value = mock_service

        response = client.post(
            "/portfolio/favorites/remove",
            json={"symbol": "999999"}
        )

        assert response.status_code == 404

    def test_update_favorite(self, client, mock_favorite_service):
        """测试更新收藏"""
        from datetime import datetime
        mock_service = Mock()
        mock_service.update_favorite.return_value = Mock(
            model_dump=lambda: {
                "symbol": "600519",
                "tag": "新标签",
                "note": "新备注",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        )
        mock_favorite_service.return_value = mock_service

        response = client.post(
            "/portfolio/favorites/update",
            json={"symbol": "600519", "tag": "新标签"}
        )

        assert response.status_code == 200
```

- [ ] **Step 2: 运行集成测试**

Run: `python -m pytest tests/api_server/test_favorite_api.py -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/api_server/test_favorite_api.py
git commit -m "test(api): add favorite API integration tests"
```

---

## 最终验证

- [ ] **运行所有测试**

Run: `python -m pytest tests/ -v --tb=short`

Expected: 所有测试通过

- [ ] **启动 API 服务器验证**

Run: `python -m uvicorn api_server.main:app --reload --port 8000`

手动测试 API：
- GET http://localhost:8000/portfolio/favorites
- POST http://localhost:8000/portfolio/favorites/add
- POST http://localhost:8000/portfolio/favorites/remove
- POST http://localhost:8000/portfolio/favorites/update
