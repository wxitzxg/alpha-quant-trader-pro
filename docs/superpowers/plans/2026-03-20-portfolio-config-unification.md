# Portfolio Config Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the redundant `portfolio_manager/config.py` module and ensure all configuration in the `@portfolio_manager/` module is loaded exclusively from the unified `common/config.py` system.

**Architecture:** Replace all references to `PortfolioConfig` in `commands.py` and `commands_refactored.py` with the unified configuration system. The `PortfolioConfig` class is completely redundant since all its functionality (database URL and fee config) already exists in `Config.get_database_url()` and `Config.get_fee_config()`.

**Tech Stack:** Python, Pydantic, SQLAlchemy

---

### Task 1: Review Existing Configuration Structure

**Files:**
- Read: `common/config.py`
- Read: `portfolio_manager/config.py`
- Read: `portfolio_manager/commands.py`
- Read: `portfolio_manager/commands_refactored.py`
- Read: `portfolio_manager/containers.py`
- Read: `portfolio_manager/fee_calculator.py`

- [ ] **Step 1: Verify unified config provides all needed methods**

Check that `common/config.py` has:
- `Config.get_database_url()` - returns database connection string
- `Config.get_fee_config()` - returns `FeeConfig` object

- [ ] **Step 2: Verify current usage of PortfolioConfig**

Confirm that `commands.py` and `commands_refactored.py`:
- Import `PortfolioConfig` from `portfolio_manager.config`
- Call `PortfolioConfig(config_path)` in `__init__`
- Call `self.config.get_database_url()` in `_init_database()`
- Call `self.config.get_fee_config()` for `FeeCalculator`

- [ ] **Step 3: Verify unified config is already used elsewhere**

Confirm that:
- `containers.py` uses `get_config()` correctly
- `fee_calculator.py` uses `get_config()` correctly

---

### Task 2: Update commands.py to Use Unified Config

**Files:**
- Modify: `portfolio_manager/commands.py`
- Delete: `portfolio_manager/config.py`

- [ ] **Step 1: Update imports in commands.py**

```python
# BEFORE:
from portfolio_manager.config import PortfolioConfig

# AFTER:
from common.config import get_config
```

- [ ] **Step 2: Update __init__ method to use unified config**

```python
# BEFORE:
def __init__(self, config_path: Optional[str] = None):
    """初始化投资组合命令"""
    # 加载配置
    self.config = PortfolioConfig(config_path)

    # 初始化数据库连接
    self.db = self._init_database()

    # ...
    # 初始化服务
    self.fee_calculator = FeeCalculator(self.config.get_fee_config())

# AFTER:
def __init__(self, config_path: Optional[str] = None):
    """初始化投资组合命令"""
    # 加载配置（使用统一配置）
    self.config = get_config()

    # 初始化数据库连接
    self.db = self._init_database()

    # ...
    # 初始化服务（直接从统一配置获取手续费配置）
    self.fee_calculator = FeeCalculator(self.config.get_fee_config())
```

- [ ] **Step 3: Update _init_database method to use unified config**

```python
# BEFORE:
def _init_database(self) -> Session:
    """初始化数据库连接"""
    db_url = self.config.get_database_url()

# AFTER (no change needed - method signature stays the same):
def _init_database(self) -> Session:
    """初始化数据库连接"""
    db_url = self.config.get_database_url()
```

Note: The `_init_database` method doesn't need changes because both `PortfolioConfig.get_database_url()` and `Config.get_database_url()` have the same signature and return type.

- [ ] **Step 4: Run syntax check**

```bash
python -m py_compile portfolio_manager/commands.py
```
Expected: No syntax errors

- [ ] **Step 5: Commit changes**

```bash
git add portfolio_manager/commands.py
git commit -m "refactor(portfolio): update commands.py to use unified config"
```

---

### Task 3: Update commands_refactored.py to Use Unified Config

**Files:**
- Modify: `portfolio_manager/commands_refactored.py`

- [ ] **Step 1: Update imports in commands_refactored.py**

```python
# BEFORE:
from portfolio_manager.config import PortfolioConfig

# AFTER:
from common.config import get_config
```

- [ ] **Step 2: Update __init__ method**

```python
# BEFORE:
def __init__(self, config_path: Optional[str] = None):
    """初始化投资组合命令"""
    # 加载配置
    self.config = PortfolioConfig(config_path)

    # 初始化数据库连接
    self.db = self._init_database()

    # ...
    # 初始化服务
    self.fee_calculator = FeeCalculator(self.config.get_fee_config())

# AFTER:
def __init__(self, config_path: Optional[str] = None):
    """初始化投资组合命令"""
    # 加载配置（使用统一配置）
    self.config = get_config()

    # 初始化数据库连接
    self.db = self._init_database()

    # ...
    # 初始化服务（直接从统一配置获取手续费配置）
    self.fee_calculator = FeeCalculator(self.config.get_fee_config())
```

- [ ] **Step 3: Run syntax check**

```bash
python -m py_compile portfolio_manager/commands_refactored.py
```
Expected: No syntax errors

- [ ] **Step 4: Commit changes**

```bash
git add portfolio_manager/commands_refactored.py
git commit -m "refactor(portfolio): update commands_refactored.py to use unified config"
```

---

### Task 4: Delete Redundant Config Module

**Files:**
- Delete: `portfolio_manager/config.py`

- [ ] **Step 1: Verify no other files import from portfolio_manager.config**

```bash
grep -r "from portfolio_manager.config" portfolio_manager/
```
Expected: No results (or only in commands.py and commands_refactored.py which we already updated)

- [ ] **Step 2: Delete the file**

```bash
rm portfolio_manager/config.py
```

- [ ] **Step 3: Verify deletion**

```bash
ls portfolio_manager/config.py
```
Expected: "No such file or directory"

- [ ] **Step 4: Commit deletion**

```bash
git add portfolio_manager/config.py
git commit -m "refactor(portfolio): remove redundant PortfolioConfig module"
```

---

### Task 5: Update Containers Documentation (Optional)

**Files:**
- Modify: `portfolio_manager/containers.py`

- [ ] **Step 1: Update module docstring to reflect unified config**

```python
# BEFORE:
"""
持仓管理模块依赖注入容器
"""

# AFTER:
"""
持仓管理模块依赖注入容器

配置来源：统一配置系统（common/config.py）
- fee_config: get_config().get_fee_config()
"""
```

- [ ] **Step 2: Commit documentation update**

```bash
git add portfolio_manager/containers.py
git commit -m "docs(portfolio): update containers.py docstring for unified config"
```

---

### Task 6: Run Tests

**Files:**
- Test: Any existing tests for portfolio_manager

- [ ] **Step 1: Find existing tests**

```bash
find . -name "test_*.py" -o -name "*_test.py" | grep -i portfolio
```

- [ ] **Step 2: Run tests**

If tests exist:
```bash
pytest tests/ -v -k portfolio
```

If no tests exist:
- Skip this step
- Note in PR that no tests exist for this module

---

### Task 7: Verify Changes

- [ ] **Step 1: Verify all imports are correct**

```bash
python -c "from portfolio_manager.commands import PortfolioCommands; print('OK')"
python -c "from portfolio_manager.commands_refactored import PortfolioCommands; print('OK')"
```
Expected: "OK" for both

- [ ] **Step 2: Verify unified config is being used**

```bash
grep -r "PortfolioConfig" portfolio_manager/
```
Expected: No results (the class should not be referenced anywhere)

- [ ] **Step 3: Verify config.py is deleted**

```bash
ls portfolio_manager/config.py
```
Expected: "No such file or directory"

- [ ] **Step 4: Check git status**

```bash
git status
```
Expected: Only modified/deleted files related to this task

---

### Task 8: Final Commit

- [ ] **Step 1: Stage all changes**

```bash
git add -A
```

- [ ] **Step 2: Review final diff**

```bash
git diff --cached
```

- [ ] **Step 3: Final commit**

```bash
git commit -m "feat(portfolio): unify configuration system

- Remove redundant portfolio_manager/config.py module
- Update commands.py to use unified config from common/config.py
- Update commands_refactored.py to use unified config
- All configuration now loaded from single source of truth

BREAKING CHANGE: PortfolioConfig class removed. Use get_config() instead."
```
