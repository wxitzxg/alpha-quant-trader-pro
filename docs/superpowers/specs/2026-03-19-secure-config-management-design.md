# 安全配置管理设计方案

**日期**: 2026-03-19
**状态**: 已批准
**作者**: Claude Code (Superpowers)

## 1. 概述

### 1.1 问题描述
项目中 `.env` 文件和 `api_config.json` 包含敏感的 API keys 和配置信息，这些信息：
- **不能**提交到 git（安全风险）
- **需要**在本地进行 end-to-end 测试时可用
- **需要**方便团队成员配置自己的环境

### 1.2 解决方案
采用 **环境变量 + .env 模板** 方案，将所有敏感配置统一管理在 `.env` 文件中，使用 Pydantic Settings 进行类型安全的配置加载。

## 2. 架构设计

### 2.1 目录结构
```
project/
├── .env.example                 # 配置模板（提交到 git）
├── .env                         # 本地配置（.gitignore，不提交）
├── .env.test                    # 测试配置（.gitignore，不提交）
├── config/
│   ├── __init__.py              # 配置导出
│   ├── settings.py              # Pydantic Settings 配置类
│   └── validators.py            # 配置验证
├── tests/
│   ├── conftest.py              # pytest 配置
│   └── .env.test                # 测试环境变量
├── api_config.json              # 保留，仅包含非敏感配置（过渡期）
├── .gitignore                   # 更新：忽略所有 .env*
└── .pre-commit-config.yaml      # pre-commit 钩子，防止误提交
```

### 2.2 配置加载流程
1. 应用启动时，根据环境自动加载对应的 `.env` 文件
2. `config/settings.py` 使用 Pydantic `BaseSettings` 读取环境变量
3. 代码中统一通过 `from config import settings` 访问配置
4. 测试运行时，`conftest.py` 自动加载 `tests/.env.test`

### 2.3 配置优先级
```
环境变量 (最高) > .env.test > .env.local > .env (默认) > 默认值 (最低)
```

## 3. 配置文件设计

### 3.1 .env.example（提交到 git）
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_ENABLED=true
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Kimi
KIMI_API_KEY=your_kimi_api_key_here
KIMI_API_SECRET=your_kimi_api_secret_here
KIMI_ENABLED=true
KIMI_MODEL=kimi-1.5
KIMI_BASE_URL=https://api.kimi.ai/v1

# ZhiPu
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_ENABLED=true
ZHIPU_MODEL=glt-4
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 360 AI
AI360_API_KEY=your_360ai_api_key_here
AI360_ENABLED=true
AI360_MODEL=360GPT
AI360_BASE_URL=https://api.360ai.com/v1

# DashScope (Aliyun)
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_ENABLED=true
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Custom Provider
CUSTOM_API_URL=https://api.example.com/v1
CUSTOM_API_KEY=your_custom_api_key_here
CUSTOM_ENABLED=false
CUSTOM_MODEL=custom-model

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# API Config
API_CONFIG_FILE=api_config.json
```

### 3.2 config/settings.py
```python
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类 - 所有配置通过环境变量或 .env 文件加载"""

    # ==================== OpenAI ====================
    openai_api_key: Optional[str] = None
    openai_enabled: bool = True
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"

    # ==================== DeepSeek ====================
    deepseek_api_key: Optional[str] = None
    deepseek_enabled: bool = True
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # ==================== Kimi ====================
    kimi_api_key: Optional[str] = None
    kimi_api_secret: Optional[str] = None
    kimi_enabled: bool = True
    kimi_model: str = "kimi-1.5"
    kimi_base_url: str = "https://api.kimi.ai/v1"

    # ==================== ZhiPu ====================
    zhipu_api_key: Optional[str] = None
    zhipu_enabled: bool = True
    zhipu_model: str = "glt-4"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"

    # ==================== 360 AI ====================
    ai360_api_key: Optional[str] = None
    ai360_enabled: bool = True
    ai360_model: str = "360GPT"
    ai360_base_url: str = "https://api.360ai.com/v1"

    # ==================== DashScope ====================
    dashscope_api_key: Optional[str] = None
    dashscope_enabled: bool = True
    dashscope_model: str = "qwen-max"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"

    # ==================== Custom Provider ====================
    custom_api_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_enabled: bool = False
    custom_model: str = "custom-model"

    # ==================== Database ====================
    database_url: str = "postgresql://user:password@localhost:5432/dbname"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ==================== API Config ====================
    api_config_file: str = "api_config.json"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

### 3.3 config/__init__.py
```python
"""配置模块导出"""
from .settings import settings

__all__ = ["settings"]
```

### 3.4 config/validators.py
```python
"""配置验证工具"""
from config import settings


def validate_required_settings():
    """启动时验证必需的配置项是否已设置"""
    required = {
        "DATABASE_URL": settings.database_url,
    }

    # 检查至少有一个 AI provider 配置
    has_provider = any([
        settings.openai_api_key,
        settings.deepseek_api_key,
        settings.kimi_api_key,
        settings.zhipu_api_key,
        settings.ai360_api_key,
        settings.dashscope_api_key,
        settings.custom_api_key,
    ])

    if not has_provider:
        required["AT_LEAST_ONE_AI_PROVIDER"] = None

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(
            f"❌ 缺少必需的环境变量: {', '.join(missing)}\n"
            "💡 请复制 .env.example 到 .env 并填写实际值:\n"
            "   cp .env.example .env\n"
            "   nano .env"
        )

    print("✅ 配置验证通过")


def print_settings_summary():
    """打印配置摘要（用于调试）"""
    print("\n=== 配置摘要 ===")
    print(f"Database: {settings.database_url}")
    print(f"OpenAI: {'✅' if settings.openai_api_key else '❌'}")
    print(f"DeepSeek: {'✅' if settings.deepseek_api_key else '❌'}")
    print(f"Kimi: {'✅' if settings.kimi_api_key else '❌'}")
    print(f"ZhiPu: {'✅' if settings.zhipu_api_key else '❌'}")
    print(f"360AI: {'✅' if settings.ai360_api_key else '❌'}")
    print(f"DashScope: {'✅' if settings.dashscope_api_key else '❌'}")
    print(f"Custom: {'✅' if settings.custom_api_key else '❌'}")
    print("================\n")
```

## 4. 测试环境配置

### 4.1 tests/.env.test
```env
# 测试环境使用 mock 或测试专用的 API keys
OPENAI_API_KEY=test_openai_key_for_testing
DEEPSEEK_API_KEY=test_deepseek_key_for_testing
KIMI_API_KEY=test_kimi_key_for_testing
KIMI_API_SECRET=test_kimi_secret_for_testing
ZHIPU_API_KEY=test_zhipu_key_for_testing
AI360_API_KEY=test_360ai_key_for_testing
DASHSCOPE_API_KEY=test_dashscope_key_for_testing

# 测试数据库
DATABASE_URL=postgresql://test:test@localhost:5432/test_db

# 测试配置
OPENAI_ENABLED=false
DEEPSEEK_ENABLED=false
KIMI_ENABLED=false
ZHIPU_ENABLED=false
AI360_ENABLED=false
DASHSCOPE_ENABLED=false
CUSTOM_ENABLED=false
```

### 4.2 tests/conftest.py
```python
"""pytest 配置 - 自动加载测试环境变量"""
import pytest
from pathlib import Path
from dotenv import load_dotenv


@pytest.fixture(autouse=True, scope="session")
def load_test_env():
    """在所有测试运行前加载测试环境变量"""
    env_path = Path(__file__).parent / ".env.test"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✅ 加载测试配置: {env_path}")
    else:
        print("⚠️  未找到 tests/.env.test，使用默认配置")
```

## 5. 代码使用示例

### 5.1 应用入口（main.py 或类似）
```python
from fastapi import FastAPI
from config import settings
from config.validators import validate_required_settings, print_settings_summary

app = FastAPI()

# 启动时验证配置
@app.on_event("startup")
async def startup_event():
    validate_required_settings()
    print_settings_summary()
```

### 5.2 业务代码中使用配置
```python
from config import settings

# 使用 OpenAI
if settings.openai_api_key and settings.openai_enabled:
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": "Hello"}]
    )
```

## 6. 安全措施

### 6.1 .gitignore 配置
```gitignore
# 环境变量文件（所有 .env* 文件都不提交）
.env
.env.*
!.env.example  # 但保留 .env.example

# 测试专用配置
tests/.env.test

# 其他敏感文件
api_config.json  # 过渡期后可以删除或清空敏感字段
```

### 6.2 pre-commit 钩子
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: no-commit-to-branch
      - id: check-yaml
      - id: end-of-file-fixer

  - repo: local
    hooks:
      - id: prevent-secrets-commit
        name: Prevent secrets commit
        entry: bash -c 'grep -r "your_.*_here\|test_.*_for_testing" . --include="*.py" --include="*.json" && echo "❌ 发现占位符值，无法提交" && exit 1 || exit 0'
        language: system
        files: \.(py|json|env)$
        exclude: \.env\.example$
```

### 6.3 README 配置说明
```markdown
## 配置设置

### 快速开始

1. 复制配置模板：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 并填写实际的 API keys：
   ```bash
   nano .env
   ```

3. 验证配置：
   ```bash
   python -c "from config import settings; from config.validators import validate_required_settings; validate_required_settings()"
   ```

### 配置文件说明

- **`.env.example`** - 配置模板，包含所有可用的配置项和示例值
- **`.env`** - 本地配置文件，包含您的实际敏感信息（不会提交到 git）
- **`tests/.env.test`** - 测试专用配置

⚠️ **安全提示**：
- `.env` 文件包含敏感信息，切勿提交到 git！
- 如果不慎提交，请立即撤销提交并轮换所有泄露的 API keys
- 使用 `git update-index --assume-unchanged .env` 可以防止意外提交
```

## 7. 迁移策略

### 7.1 策略：完全迁移到配置类（推荐）
- **目标**：所有配置集中管理在 `config/settings.py`
- **优点**：
  - 类型安全（Pydantic 验证）
  - 集中管理，易于维护
  - 与 FastAPI 生态完美集成
- **缺点**：
  - 需要更新现有代码中读取 `api_config.json` 的地方

### 7.2 迁移步骤

**阶段 1：基础配置搭建**
1. 创建 `config/` 目录和配置文件
2. 创建 `.env.example` 模板
3. 更新 `.gitignore`
4. 安装依赖：`python-dotenv`, `pydantic-settings`

**阶段 2：代码迁移**
5. 识别所有使用 `api_config.json` 的代码位置
6. 逐步更新代码，改用 `from config import settings`
7. 清空 `api_config.json` 中的敏感字段

**阶段 3：测试配置**
8. 创建 `tests/.env.test`
9. 更新测试代码
10. 运行测试验证

**阶段 4：文档与验证**
11. 更新 README
12. 验证 git 忽略配置
13. 清理旧配置文件

## 8. 依赖要求

```toml
# requirements.txt 或 pyproject.toml
python-dotenv>=1.0.0
pydantic-settings>=2.0.0
pydantic>=2.0.0
```

## 9. 验收标准

- [ ] `.env.example` 包含所有必需配置项和说明
- [ ] `.env` 和 `.env.test` 被 `.gitignore` 正确忽略
- [ ] 所有敏感配置可以从 `config.settings` 访问
- [ ] 启动时验证缺失的必需配置
- [ ] 测试环境可以独立运行
- [ ] pre-commit 钩子防止占位符值提交
- [ ] README 包含清晰的配置说明
- [ ] 现有测试全部通过

## 10. 变更记录

- **2026-03-19**: 初始设计创建，方案批准
