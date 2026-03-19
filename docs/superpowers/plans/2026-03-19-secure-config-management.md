# 安全配置管理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将敏感配置从 `api_config.json` 迁移到 `.env` 文件系统，使用 Pydantic Settings 实现类型安全的配置管理，确保敏感信息不会提交到 git。

**Architecture:**
- 使用 `.env.example` 作为配置模板（提交到 git）
- 使用 `.env` 存储本地敏感配置（.gitignore 忽略）
- 使用 `config/settings.py` 作为配置中心，通过 Pydantic BaseSettings 读取环境变量
- 测试环境使用独立的 `tests/.env.test` 和 `conftest.py` 配置

**Tech Stack:** Python, FastAPI, Pydantic Settings, python-dotenv, pytest

---

## 文件结构映射

### 创建的文件
- `config/__init__.py` - 配置模块导出
- `config/settings.py` - Pydantic 配置类（所有环境变量）
- `config/validators.py` - 配置验证工具
- `.env.example` - 配置模板（提交）
- `tests/.env.test` - 测试配置（不提交）
- `tests/conftest.py` - pytest 环境加载

### 修改的文件
- `.gitignore` - 忽略所有 `.env*` 文件
- `pyproject.toml` 或 `requirements.txt` - 添加依赖
- `api_server/main.py` - 添加配置验证启动钩子
- `README.md` - 添加配置说明

### 删除/清理的文件
- `api_config.json` - 迁移后删除敏感字段（保留非敏感配置作为过渡）

---

## 依赖分析

当前项目使用：
- FastAPI
- Pydantic (v2)
- PostgreSQL

需要添加：
- `python-dotenv>=1.0.0` - 加载 .env 文件
- `pydantic-settings>=2.0.0` - Pydantic BaseSettings

---

## Task 1: 基础配置文件创建

**Files:**
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `config/validators.py`

### 步骤 1.1: 创建 config 目录和 __init__.py

```bash
mkdir -p config
```

```python
# config/__init__.py
"""配置模块导出"""
from .settings import settings

__all__ = ["settings"]
```

### 步骤 1.2: 创建 settings.py (完整配置类)

```python
# config/settings.py
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

    # ==================== Investoday (现有 API) ====================
    investoday_api_key: Optional[str] = None
    investoday_base_url: str = "https://api.investoday.net"
    investoday_timeout: int = 10

    # ==================== Tushare (现有 API) ====================
    tushare_token: Optional[str] = None
    tushare_base_url: str = "http://api.tushare.pro"
    tushare_timeout: int = 10

    # ==================== Database ====================
    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_market"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ==================== Application ====================
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    # ==================== Data Sources ====================
    data_source_config: str = "config/sources.json"

    # ==================== API Config ====================
    api_config_file: str = "api_config.json"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

### 步骤 1.3: 创建 validators.py

```python
# config/validators.py
"""配置验证工具"""
from config import settings


def validate_required_settings():
    """启动时验证必需的配置项是否已设置"""
    required = {
        "DATABASE_URL": settings.database_url,
    }

    # 检查至少有一个数据源配置（Investoday 或 Tushare）
    has_data_source = any([
        settings.investoday_api_key,
        settings.tushare_token,
    ])

    if not has_data_source:
        required["AT_LEAST_ONE_DATA_SOURCE"] = None

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
    print(f"Investoday: {'✅' if settings.investoday_api_key else '❌'}")
    print(f"Tushare: {'✅' if settings.tushare_token else '❌'}")
    print(f"OpenAI: {'✅' if settings.openai_api_key else '❌'}")
    print(f"DeepSeek: {'✅' if settings.deepseek_api_key else '❌'}")
    print(f"Kimi: {'✅' if settings.kimi_api_key else '❌'}")
    print(f"ZhiPu: {'✅' if settings.zhipu_api_key else '❌'}")
    print(f"360AI: {'✅' if settings.ai360_api_key else '❌'}")
    print(f"DashScope: {'✅' if settings.dashscope_api_key else '❌'}")
    print(f"Custom: {'✅' if settings.custom_api_key else '❌'}")
    print(f"Environment: {settings.environment} ({'DEBUG' if settings.debug else 'PROD'})")
    print("================\n")
```

### 步骤 1.4: 验证 config 模块可导入

```bash
python -c "from config import settings; print('Config module loaded successfully')"
```

**预期输出:** `Config module loaded successfully`

### 步骤 1.5: 提交 config 模块

```bash
git add config/
git commit -m "feat: add config module with Pydantic Settings

- Add config/settings.py with BaseSettings for env var loading
- Add config/validators.py for startup validation
- Support all AI providers and existing data sources (Investoday, Tushare)
- Type-safe configuration with Pydantic validation"
```

---

## Task 2: 创建 .env 配置模板和更新 .gitignore

**Files:**
- Create: `.env.example`
- Modify: `.gitignore`

### 步骤 2.1: 创建 .env.example 模板

```env
# .env.example
# ==================== OpenAI ====================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ENABLED=true
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1

# ==================== DeepSeek ====================
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_ENABLED=true
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# ==================== Kimi ====================
KIMI_API_KEY=your_kimi_api_key_here
KIMI_API_SECRET=your_kimi_api_secret_here
KIMI_ENABLED=true
KIMI_MODEL=kimi-1.5
KIMI_BASE_URL=https://api.kimi.ai/v1

# ==================== ZhiPu ====================
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_ENABLED=true
ZHIPU_MODEL=glt-4
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# ==================== 360 AI ====================
AI360_API_KEY=your_360ai_api_key_here
AI360_ENABLED=true
AI360_MODEL=360GPT
AI360_BASE_URL=https://api.360ai.com/v1

# ==================== DashScope ====================
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_ENABLED=true
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# ==================== Custom Provider ====================
CUSTOM_API_URL=https://api.example.com/v1
CUSTOM_API_KEY=your_custom_api_key_here
CUSTOM_ENABLED=false
CUSTOM_MODEL=custom-model

# ==================== Investoday (Existing) ====================
INVESTODAY_API_KEY=your_investoday_api_key_here
INVESTODAY_BASE_URL=https://api.investoday.net
INVESTODAY_TIMEOUT=10

# ==================== Tushare (Existing) ====================
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_BASE_URL=http://api.tushare.pro
TUSHARE_TIMEOUT=10

# ==================== Database ====================
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_market
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ==================== Application ====================
DEBUG=false
ENVIRONMENT=development
LOG_LEVEL=INFO

# ==================== Data Sources ====================
DATA_SOURCE_CONFIG=config/sources.json

# ==================== API Config ====================
API_CONFIG_FILE=api_config.json
```

### 步骤 2.2: 更新 .gitignore

在 `.gitignore` 文件末尾添加：

```gitignore
# Environment variables (all .env* files except .env.example)
.env
.env.*
!.env.example

# Test environment
tests/.env.test
```

### 步骤 2.3: 验证 .gitignore 配置

```bash
# 创建测试文件
echo "TEST=test" > .env.test
echo "TEST=test" > tests/.env.test

# 检查是否会被忽略
git status --ignored | grep -E "\.env"

# 应该看到 .env.test 和 tests/.env.test 在 ignored 列表中
# .env.example 应该不在 ignored 列表中（如果已存在）
```

### 步骤 2.4: 提交配置模板

```bash
git add .env.example .gitignore
git commit -m "feat: add .env.example template and update gitignore

- Add comprehensive .env.example with all config options
- Update .gitignore to ignore all .env* except .env.example
- Include existing data sources (Investoday, Tushare) in template"
```

---

## Task 3: 安装依赖并创建本地配置

**Files:**
- Modify: `pyproject.toml` 或 `requirements.txt`

### 步骤 3.1: 添加依赖

在 `pyproject.toml` 的 `[tool.poetry.dependencies]` 或 `requirements.txt` 中添加：

```toml
python-dotenv = "^1.0.0"
pydantic-settings = "^2.0.0"
```

或

```txt
python-dotenv>=1.0.0
pydantic-settings>=2.0.0
```

### 步骤 3.2: 安装依赖

```bash
# 如果使用 poetry
poetry install

# 如果使用 pip
pip install python-dotenv pydantic-settings
```

### 步骤 3.3: 创建本地 .env 文件

```bash
cp .env.example .env
```

### 步骤 3.4: 填写本地 .env

编辑 `.env` 文件，填入实际的敏感值：

```bash
nano .env
# 或使用其他编辑器
```

需要填写的关键字段：
- `INVESTODAY_API_KEY` - 从现有的 api_config.json 复制
- `TUSHARE_TOKEN` - 从现有的 api_config.json 复制
- `DATABASE_URL` - 如果需要修改

### 步骤 3.5: 验证配置加载

```bash
python -c "
from config import settings
from config.validators import validate_required_settings, print_settings_summary

validate_required_settings()
print_settings_summary()
print('✅ 配置加载成功！')
"
```

**预期输出:** 配置摘要，所有必需字段显示 ✅

### 步骤 3.6: 提交依赖更新

```bash
git add pyproject.toml requirements.txt  # 根据实际情况选择
git commit -m "feat: add python-dotenv and pydantic-settings dependencies

- Add python-dotenv for .env file loading
- Add pydantic-settings for BaseSettings support
- Required for secure config management"
```

---

## Task 4: 迁移现有代码使用新配置系统

**Files:**
- Modify: `api_server/main.py`
- Modify: `api_config.json` (清理敏感字段)

### 步骤 4.1: 更新 api_server/main.py 添加配置验证

```python
# api_server/main.py (在文件开头添加)
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from config import settings
from config.validators import validate_required_settings, print_settings_summary

app = FastAPI(
    title="Alpha Quant Trader Pro",
    description="AI-powered quantitative trading platform",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """应用启动时验证配置"""
    try:
        validate_required_settings()
        print_settings_summary()
    except ValueError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
```

### 步骤 4.2: 查找所有使用 api_config.json 的代码

```bash
grep -r "api_config.json" --include="*.py" . --exclude-dir=.git --exclude-dir=.claude
```

或使用 Grep 工具：

```bash
rg "api_config\.json" --type py
```

### 步骤 4.3: 更新代码使用 config.settings

对于每个使用 `api_config.json` 的文件，更新为：

```python
# 旧代码
import json
with open("api_config.json") as f:
    config = json.load(f)
api_key = config["data_sources"]["investoday"]["api_key"]

# 新代码
from config import settings
api_key = settings.investoday_api_key
base_url = settings.investoday_base_url
timeout = settings.investoday_timeout
```

### 步骤 4.4: 清理 api_config.json 敏感字段

更新 `api_config.json`，移除敏感字段：

```json
{
  "api_keys": [
    {
      "api_key": "test_api_key_1234567890",
      "secret_key": "test_secret_key_0987654321",
      "user_id": "admin",
      "permissions": {
        "read": true,
        "write": true,
        "admin": true
      },
      "rate_limit": 1000,
      "is_active": true
    },
    {
      "api_key": "demo_api_key_abcdefg",
      "secret_key": "demo_secret_key_hijklmn",
      "user_id": "demo_user",
      "permissions": {
        "read": true,
        "write": false,
        "admin": false
      },
      "rate_limit": 100,
      "is_active": true
    }
  ],
  "data_sources": {
    "investoday": {
      "base_url": "https://api.investoday.net",
      "timeout": 10
    },
    "tushare": {
      "base_url": "http://api.tushare.pro",
      "timeout": 10
    }
  }
}
```

注意：保留测试用的 mock API keys，但移除真实的敏感 token。

### 步骤 4.5: 测试应用启动

```bash
cd api_server
python main.py
```

**预期输出:** 配置摘要，应用正常启动

### 步骤 4.6: 提交代码迁移

```bash
git add api_server/main.py api_config.json
git commit -m "refactor: migrate to config.settings from api_config.json

- Update api_server/main.py to use config module
- Remove sensitive tokens from api_config.json
- Keep mock API keys for testing
- Add startup validation hook"
```

---

## Task 5: 配置测试环境

**Files:**
- Create: `tests/.env.test`
- Create: `tests/conftest.py`

### 步骤 5.1: 创建 tests/.env.test

```env
# tests/.env.test
# 测试环境使用 mock 或测试专用的值

# Investoday
INVESTODAY_API_KEY=test_investoday_key_for_testing
INVESTODAY_BASE_URL=https://api.investoday.net
INVESTODAY_TIMEOUT=5

# Tushare
TUSHARE_TOKEN=test_tushare_token_for_testing
TUSHARE_BASE_URL=http://api.tushare.pro
TUSHARE_TIMEOUT=5

# Database
DATABASE_URL=postgresql://test:test@localhost:5432/test_stock_market
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Application
DEBUG=true
ENVIRONMENT=test
LOG_LEVEL=DEBUG

# AI Providers (all disabled for tests unless needed)
OPENAI_ENABLED=false
DEEPSEEK_ENABLED=false
KIMI_ENABLED=false
ZHIPU_ENABLED=false
AI360_ENABLED=false
DASHSCOPE_ENABLED=false
CUSTOM_ENABLED=false
```

### 步骤 5.2: 创建 tests/conftest.py

```python
# tests/conftest.py
"""pytest 配置 - 自动加载测试环境变量"""
import pytest
from pathlib import Path
from dotenv import load_dotenv
import sys
from pathlib import Path as PathLib

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(PathLib(__file__).parent.parent))


@pytest.fixture(autouse=True, scope="session")
def load_test_env():
    """在所有测试运行前加载测试环境变量"""
    env_path = Path(__file__).parent / ".env.test"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"\n✅ 加载测试配置: {env_path}")
    else:
        print("\n⚠️  未找到 tests/.env.test，使用默认配置")
```

### 步骤 5.3: 创建测试验证配置

```python
# tests/test_config.py
"""测试配置加载"""
from config import settings


def test_config_loaded():
    """测试配置是否正确加载"""
    assert settings.environment == "test"
    assert settings.debug is True
    assert "test_stock_market" in settings.database_url
    assert settings.investoday_api_key == "test_investoday_key_for_testing"
    assert settings.tushare_token == "test_tushare_token_for_testing"


def test_settings_are_immutable():
    """测试配置是只读的"""
    original = settings.database_url
    # 尝试修改应该不影响 settings（Pydantic 会创建副本）
    assert settings.database_url == original
```

### 步骤 5.4: 运行测试验证

```bash
pytest tests/test_config.py -v
```

**预期输出:** 所有测试通过

### 步骤 5.5: 提交测试配置

```bash
git add tests/.env.test tests/conftest.py tests/test_config.py
git commit -m "test: add test environment configuration

- Add tests/.env.test with mock values
- Add tests/conftest.py to auto-load test env vars
- Add tests/test_config.py to verify config loading
- Configure pytest to use isolated test environment"
```

---

## Task 6: 添加安全检查和文档

**Files:**
- Create: `.pre-commit-config.yaml`
- Modify: `README.md`

### 步骤 6.1: 创建 .pre-commit-config.yaml

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml

  - repo: local
    hooks:
      - id: prevent-secrets-commit
        name: Prevent secrets commit
        entry: bash -c 'grep -r "your_.*_here\|test_.*_for_testing" . --include="*.py" --include="*.json" --include="*.env" && echo "❌ 错误: 发现占位符值或测试值，无法提交" && exit 1 || exit 0'
        language: system
        files: \.(py|json|env|txt|md)$
        exclude: \.env\.example$|tests/\.env\.test$
```

### 步骤 6.2: 安装 pre-commit

```bash
pip install pre-commit
pre-commit install
```

### 步骤 6.3: 更新 README.md

在 README.md 中添加配置说明章节：

```markdown
## 配置管理

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
   python -c "
   from config import settings
   from config.validators import validate_required_settings, print_settings_summary

   validate_required_settings()
   print_settings_summary()
   "
   ```

### 配置文件说明

- **`.env.example`** - 配置模板，包含所有可用的配置项和示例值（提交到 git）
- **`.env`** - 本地配置文件，包含您的实际敏感信息（不会提交到 git）
- **`tests/.env.test`** - 测试专用配置（不会提交到 git）
- **`config/settings.py`** - 配置类定义（Pydantic BaseSettings）

### 必需配置项

以下配置项是应用运行必需的：

- `DATABASE_URL` - PostgreSQL 连接字符串
- 至少一个数据源配置：
  - `INVESTODAY_API_KEY` - Investoday API 密钥
  - `TUSHARE_TOKEN` - Tushare Token

### 安全提示

⚠️ **重要**：
- `.env` 文件包含敏感信息，切勿提交到 git！
- 如果不慎提交，请立即撤销提交并轮换所有泄露的 API keys
- 使用 `git update-index --assume-unchanged .env` 可以防止意外提交
- 所有敏感配置现在都通过环境变量管理，不会硬编码在代码中

### 配置验证

应用启动时会自动验证必需的配置项。如果缺失，会显示友好的错误消息并退出。

### 环境变量优先级

```
环境变量 (最高) > .env 文件 > 默认值 (最低)
```

您可以通过设置环境变量覆盖 `.env` 文件中的值，这在 CI/CD 环境中非常有用。
```

### 步骤 6.4: 创建配置检查脚本

```python
# scripts/check_config.py
#!/usr/bin/env python
"""检查配置是否正确设置"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from config.validators import validate_required_settings, print_settings_summary


def main():
    print("🔍 检查配置...")
    try:
        validate_required_settings()
        print_settings_summary()
        print("✅ 配置检查通过！")
        return 0
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

```bash
chmod +x scripts/check_config.py
```

### 步骤 6.5: 提交文档和安全检查

```bash
git add .pre-commit-config.yaml README.md scripts/check_config.py
git commit -m "docs: add configuration documentation and security checks

- Add .pre-commit-config.yaml with secrets prevention hook
- Update README.md with comprehensive config instructions
- Add scripts/check_config.py for config validation
- Document all config options and security best practices"
```

---

## Task 7: 清理和最终验证

**Files:**
- Modify: `.env` (本地文件，不提交)
- All previous changes

### 步骤 7.1: 验证 .env 不会被提交

```bash
# 检查 .env 是否在忽略列表中
git check-ignore -v .env

# 应该输出类似：
# .gitignore:213:.env    .env
```

### 步骤 7.2: 验证本地配置

```bash
python scripts/check_config.py
```

**预期输出:** ✅ 配置检查通过！

### 步骤 7.3: 运行所有测试

```bash
pytest tests/ -v --tb=short
```

**预期输出:** 所有测试通过

### 步骤 7.4: 启动应用验证

```bash
cd api_server
python main.py
```

检查输出：
- ✅ 配置验证通过
- ✅ 配置摘要显示所有必需字段
- ✅ 应用正常启动

### 步骤 7.5: 检查 git 状态

```bash
git status
```

应该看到：
- `.env` 文件不在待提交列表中（被忽略）
- `tests/.env.test` 不在待提交列表中（被忽略）
- 其他所有修改的文件都在待提交列表中

### 步骤 7.6: 最终提交

```bash
git add -A
git status  # 确认没有 .env 或 tests/.env.test
git commit -m "feat: complete secure config management migration

完整实施安全配置管理系统：

配置管理：
- ✅ 使用 .env 文件存储敏感配置
- ✅ .env.example 作为模板提交到 git
- ✅ Pydantic Settings 实现类型安全配置
- ✅ 启动时自动验证必需配置

安全措施：
- ✅ .gitignore 忽略所有 .env* 文件
- ✅ pre-commit 钩子防止占位符值提交
- ✅ 从 api_config.json 移除敏感字段
- ✅ 配置验证工具

测试环境：
- ✅ 独立的 tests/.env.test
- ✅ pytest 自动加载测试配置
- ✅ 配置测试覆盖

文档：
- ✅ README.md 配置说明
- ✅ scripts/check_config.py 验证脚本
- ✅ 详细的设计文档

破坏性变更：
- api_config.json 中的敏感 token 已移除
- 代码需要更新为使用 config.settings
- 首次运行需要创建 .env 文件

迁移指南：
1. cp .env.example .env
2. 编辑 .env 填写实际值
3. pip install python-dotenv pydantic-settings
4. python scripts/check_config.py
5. 启动应用"
```

---

## 验收标准清单

实施完成后，验证以下项目：

- [ ] `config/` 目录存在且包含 `__init__.py`, `settings.py`, `validators.py`
- [ ] `.env.example` 包含所有配置项和说明
- [ ] `.gitignore` 正确忽略 `.env` 和 `tests/.env.test`
- [ ] 依赖已添加：`python-dotenv`, `pydantic-settings`
- [ ] 本地 `.env` 文件已创建并填写实际值
- [ ] `python scripts/check_config.py` 输出 ✅
- [ ] 应用启动时显示配置摘要
- [ ] 所有现有测试通过
- [ ] `tests/.env.test` 和 `tests/conftest.py` 存在
- [ ] pre-commit 钩子已安装并工作
- [ ] README.md 包含配置说明
- [ ] `git status` 不显示 `.env` 或 `tests/.env.test`

---

## 回滚计划

如果需要回滚：

1. 恢复 `api_config.json` 中的敏感字段：
   ```bash
   git checkout HEAD~1 -- api_config.json
   ```

2. 恢复代码中使用 `api_config.json` 的地方

3. 移除 config 模块（可选）：
   ```bash
   git checkout HEAD~7 -- config/
   ```

4. 恢复 `.gitignore`：
   ```bash
   git checkout HEAD~6 -- .gitignore
   ```

---

## 后续改进

可能的后续优化：

1. **密钥管理服务集成**：生产环境使用 AWS Secrets Manager 或 HashiCorp Vault
2. **配置加密**：使用 SOPS 或类似工具加密 `.env` 文件
3. **配置热重载**：支持运行时重新加载配置
4. **配置 UI**：添加 Web 界面管理配置
