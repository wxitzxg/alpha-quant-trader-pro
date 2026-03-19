# Pydantic v1 to v2 迁移指南

## 📋 迁移概述

本次迁移将项目中所有 Pydantic v1 API 升级到 Pydantic v2，确保与 `pydantic>=2.0.0` 完全兼容。

**迁移日期：** 2026-03-17
**Pydantic 版本要求：** >= 2.0.0

---

## 🔧 主要变更

### 1. 验证器装饰器变更

#### Pydantic v1:
```python
from pydantic import validator

class Model(BaseModel):
    price: float

    @validator('price')
    def check_price(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v
```

#### Pydantic v2:
```python
from pydantic import field_validator

class Model(BaseModel):
    price: float

    @field_validator('price')
    @classmethod
    def check_price(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v
```

**关键变化：**
- `@validator` → `@field_validator`
- 必须添加 `@classmethod` 装饰器
- 验证器函数的第一个参数从 `cls` 变为显式 `cls`

### 2. 配置类变更

#### Pydantic v1:
```python
class Model(BaseModel):
    name: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {"name": "test"}
        }
```

#### Pydantic v2:
```python
class Model(BaseModel):
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {"name": "test"}
        }
    }
```

**关键变化：**
- `class Config:` → `model_config = {...}`
- 所有配置项作为字典键值对

### 3. ConfigDict (可选)

对于更复杂的配置，可以使用 `ConfigDict`:

```python
from pydantic import ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        extra="forbid"
    )
```

### 4. SettingsConfigDict (Pydantic Settings)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
```

### 5. Annotated 类型注解（解决字段名冲突）

当字段名与类型名冲突时，使用 `Annotated`:

```python
from typing import Annotated
from datetime import date

class Model(BaseModel):
    trade_date: Annotated[date, Field(..., description="交易日期")]
```

---

## 📁 修复的文件列表

### stock_market 模块
- `stock_market/schemas/kline_schemas.py`
  - 迁移 `@validator` → `@field_validator`
  - 迁移 `class Config:` → `model_config`
  - 使用 `Annotated` 解决 `date` 字段名冲突

- `stock_market/schemas/stock_schemas.py`
  - 迁移 `class Config:` → `model_config`

### data_sources 模块
- `data_sources/models.py`
  - 迁移所有 `class Config:` → `model_config`
  - 更新 `arbitrary_types_allowed` 配置

### portfolio_manager 模块
- `portfolio_manager/schemas/account_schemas.py`
  - 迁移 `class Config:` → `model_config`

- `portfolio_manager/schemas/position_schemas.py`
  - 迁移 `class Config:` → `model_config`

- `portfolio_manager/schemas/transaction_schemas.py`
  - 迁移 `class Config:` → `model_config`

### api_server 模块
- `api_server/config.py`
  - 迁移 `class Config:` → `model_config`
  - 使用 `SettingsConfigDict` 代替旧版配置

### common 模块
- `common/config.py`
  - 已经使用 Pydantic v2 API，无需修改

---

## ✅ 验证测试

运行以下命令验证迁移成功：

```bash
# 测试所有模型导入
python3 -c "
import sys
sys.path.insert(0, '.')
from stock_market.schemas.kline_schemas import KLineCreateSchema
from stock_market.schemas.stock_schemas import StockCreateSchema
from data_sources.models import Quote, KLine
from portfolio_manager.schemas.account_schemas import AccountSummarySchema
print('✓ All models imported successfully')
"

# 运行测试套件（如果有）
pytest tests/ -v
```

---

## 🚀 向后兼容性

**注意：** 此次迁移不向后兼容 Pydantic v1。升级后必须使用 Pydantic >= 2.0.0。

在 `requirements.txt` 中确保：
```txt
pydantic>=2.0.0
pydantic-settings>=2.1.0
```

---

## 📚 参考资料

- [Pydantic v2 官方迁移指南](https://docs.pydantic.dev/latest/migration/)
- [Pydantic v2 文档](https://docs.pydantic.dev/latest/)
- [Pydantic Settings v2](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## 🔍 常见问题

### Q: 为什么需要使用 `Annotated`?
A: 当字段名（如 `date`）与类型名（`date` from datetime）相同时，Pydantic v2 会混淆。使用 `Annotated[date, Field(...)]` 明确指定字段类型。

### Q: `@classmethod` 装饰器是必须的吗?
A: 是的。在 Pydantic v2 中，所有字段验证器都必须是类方法。

### Q: 还有哪些其他变更？
A: 完整变更列表请参考官方迁移指南。本项目只使用了基础功能，主要变更已涵盖。

---

**迁移完成时间：** 2026-03-17
**测试状态：** ✅ 通过
