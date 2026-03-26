# 股票收藏管理功能设计文档

**日期**: 2026-03-26
**模块**: portfolio_manager
**状态**: 待实现

---

## 1. 概述

在 `portfolio_manager` 模块新增股票收藏管理功能，支持用户管理自选股列表和策略候选池。

### 1.1 核心需求

- 自选股追踪：用户关注但未持有的股票
- 策略候选池：供回测或模拟交易使用的候选股票

### 1.2 设计决策

| 决策项 | 选择 |
|--------|------|
| 分组/标签 | 扁平列表 + 单标签字段（自由文本） |
| 备注 | 支持简短文字说明 |
| 排序 | 按添加时间倒序 |
| 架构 | 独立模块，遵循 Repository/Service 分层 |
| API 风格 | 动作风格（语义化接口名称） |

---

## 2. 数据模型

### 2.1 StockFavorite 表

```sql
CREATE TABLE stock_favorites (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    tag VARCHAR(50),
    note VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stock_favorites_created_at ON stock_favorites(created_at DESC);
```

### 2.2 字段说明

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, Auto | 主键 |
| symbol | String(10) | NOT NULL, UNIQUE | 股票代码 |
| tag | String(50) | NULL | 标签，自由文本 |
| note | String(200) | NULL | 备注说明 |
| created_at | DateTime | NOT NULL | 添加时间 |

---

## 3. 文件结构

```
portfolio_manager/
├── database.py              # 新增 StockFavorite 模型
├── repositories/
│   ├── __init__.py          # 导出 FavoriteRepository
│   └── favorite_repository.py    # 新增
├── services/
│   ├── __init__.py          # 新建，导出 FavoriteService
│   └── favorite_service.py  # 新增
├── schemas/
│   ├── __init__.py          # 导出收藏相关 schema
│   └── favorite_schemas.py  # 新增
```

---

## 4. API 接口设计

### 4.1 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/portfolio/favorites` | GET | 获取收藏列表（分页） |
| `/portfolio/favorites/add` | POST | 添加收藏 |
| `/portfolio/favorites/remove` | POST | 移除收藏 |
| `/portfolio/favorites/update` | POST | 更新标签/备注 |

### 4.2 请求/响应模型

#### 添加收藏请求
```python
class AddFavoriteRequest(BaseModel):
    symbol: str          # 股票代码
    tag: Optional[str]   # 标签
    note: Optional[str]  # 备注
```

#### 移除收藏请求
```python
class RemoveFavoriteRequest(BaseModel):
    symbol: str  # 股票代码
```

#### 更新收藏请求
```python
class UpdateFavoriteRequest(BaseModel):
    symbol: str           # 股票代码
    tag: Optional[str]    # 新标签
    note: Optional[str]   # 新备注
```

#### 收藏信息响应
```python
class FavoriteInfo(BaseModel):
    symbol: str
    tag: Optional[str]
    note: Optional[str]
    created_at: datetime
```

---

## 5. 业务逻辑

### 5.1 添加收藏

1. 验证股票代码不为空
2. 检查是否已存在（symbol 唯一）
3. 创建收藏记录并保存

### 5.2 移除收藏

1. 根据股票代码查找记录
2. 不存在则返回错误
3. 存在则删除

### 5.3 更新收藏

1. 根据股票代码查找记录
2. 不存在则返回错误
3. 更新 tag 和/或 note 字段

### 5.4 获取列表

1. 支持分页（page, page_size）
2. 按创建时间倒序排序
3. 返回总数和分页信息

---

## 6. 测试要点

### 6.1 单元测试

- FavoriteRepository CRUD 操作
- FavoriteService 业务逻辑
- 重复添加处理
- 不存在的股票更新/删除处理

### 6.2 集成测试

- API 接口完整流程
- 分页功能
- 边界条件

---

## 7. 实现顺序

1. 数据模型：`database.py` 新增 StockFavorite
2. Schema：`schemas/favorite_schemas.py`
3. Repository：`repositories/favorite_repository.py`
4. Service：`services/favorite_service.py`
5. API 路由：`api_server/routers/portfolio.py` 新增接口
