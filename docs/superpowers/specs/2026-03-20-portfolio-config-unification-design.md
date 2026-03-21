# Portfolio Config Unification Design

## Overview

**Goal:** Remove the redundant `portfolio_manager/config.py` module and ensure all configuration in the `@portfolio_manager/` module is loaded exclusively from the unified `common/config.py` system.

**Date:** 2026-03-20

---

## Problem Statement

### Current State

The `portfolio_manager` module currently has:

1. **Redundant Local Config** (`portfolio_manager/config.py`):
   - Contains `PortfolioConfig` class with hard-coded values
   - Returns `postgresql://localhost/stock_market` for database URL
   - Returns empty `FeeConfig()` object with default values
   - Marked as "临时方案" (temporary solution)

2. **Mixed Configuration Sources**:
   - ✅ **Correctly using unified config**:
     - `containers.py` - uses `get_config()`
     - `fee_calculator.py` - uses `get_config()`
   - ❌ **Still using local config**:
     - `commands.py` - instantiates `PortfolioConfig`
     - `commands_refactored.py` - instantiates `PortfolioConfig`

3. **Duplicate Functionality**:
   - `PortfolioConfig.get_database_url()` duplicates `Config.get_database_url()`
   - `PortfolioConfig.get_fee_config()` duplicates `Config.get_fee_config()`

### Issues

1. **Configuration Inconsistency**: Two sources of truth for the same configuration
2. **Hard-coded Values**: Local config has hard-coded database URL and empty fee config
3. **Maintenance Burden**: Changes to configuration require updating multiple places
4. **Code Duplication**: The same functionality exists in both `PortfolioConfig` and `Config`
5. **Misleading API**: `PortfolioConfig.__init__(config_path)` accepts a parameter that is never used

---

## Solution Design

### Approach

**Remove the redundant `PortfolioConfig` class entirely** and update all usages to use the unified configuration system from `common/config.py`.

The unified `Config` class already provides:
- `get_database_url()` - returns database connection string
- `get_fee_config()` - returns `FeeConfig` object with proper configuration

### Files to Modify

| File | Action | Reason |
|------|--------|--------|
| `portfolio_manager/commands.py` | Update | Replace `PortfolioConfig` with `get_config()` |
| `portfolio_manager/commands_refactored.py` | Update | Replace `PortfolioConfig` with `get_config()` |
| `portfolio_manager/config.py` | **DELETE** | Redundant, all functionality exists in unified config |

### Files to Keep Unchanged

| File | Reason |
|------|--------|
| `portfolio_manager/containers.py` | Already uses unified config correctly |
| `portfolio_manager/fee_calculator.py` | Already uses unified config correctly |
| `common/config.py` | Unified config source, no changes needed |

---

## Implementation Details

### 1. Update commands.py

**Before:**
```python
from portfolio_manager.config import PortfolioConfig

class PortfolioCommands:
    def __init__(self, config_path: Optional[str] = None):
        # 加载配置
        self.config = PortfolioConfig(config_path)

        # 初始化服务
        self.fee_calculator = FeeCalculator(self.config.get_fee_config())
```

**After:**
```python
from common.config import get_config

class PortfolioCommands:
    def __init__(self, config_path: Optional[str] = None):
        # 加载配置（使用统一配置）
        self.config = get_config()

        # 初始化服务（直接从统一配置获取手续费配置）
        self.fee_calculator = FeeCalculator(self.config.get_fee_config())
```

**Key Changes:**
- Import `get_config` from `common.config` instead of `PortfolioConfig`
- Call `get_config()` instead of `PortfolioConfig(config_path)`
- No changes to `_init_database()` method (signature is the same)
- No changes to service initialization (same method calls)

### 2. Update commands_refactored.py

Same changes as `commands.py`:
- Import `get_config` from `common.config`
- Call `get_config()` instead of `PortfolioConfig(config_path)`

### 3. Delete config.py

**Complete removal:**
```bash
rm portfolio_manager/config.py
```

**Rationale:**
- All functionality already exists in unified config
- No other modules depend on it (after updating commands.py and commands_refactored.py)
- Hard-coded values are not useful

---

## Configuration Flow

### Before (Current)

```
PortfolioCommands.__init__()
    ↓
    PortfolioConfig(config_path)
        ↓
        Hard-coded:
        - get_database_url() → "postgresql://localhost/stock_market"
        - get_fee_config() → FeeConfig() with defaults
```

### After (Unified)

```
PortfolioCommands.__init__()
    ↓
    get_config() → Config instance
        ↓
        Config methods:
        - get_database_url() → self.database.url (from config.yaml)
        - get_fee_config() → self.fee (FeeConfig from config.yaml)
```

---

## Unified Config Source

The unified `Config` class (in `common/config.py`) loads configuration from:

1. **YAML files** (`config/config.yaml` or `config/config.{env}.yaml`)
2. **Environment variables** (via Pydantic `BaseSettings`)
3. **Runtime parameters** (highest priority)

Example configuration in `config/config.yaml`:

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/stock_market"
  pool_size: 10
  max_overflow: 20

fee:
  stamp_duty: 0.001
  exchange_fee: 0.00002
  broker_commission: 0.0003
  min_commission: 5.0
```

---

## Impact Analysis

### Breaking Changes

**YES - Breaking Change:**

The `PortfolioConfig` class will be removed. Any code that directly instantiates it will break:

```python
# This will break:
from portfolio_manager.config import PortfolioConfig
config = PortfolioConfig()

# Migration path:
from common.config import get_config
config = get_config()
```

### Migration Path

For any external code using `PortfolioConfig`:

1. Replace `from portfolio_manager.config import PortfolioConfig` with `from common.config import get_config`
2. Replace `PortfolioConfig()` with `get_config()`
3. All method calls remain the same (`get_database_url()`, `get_fee_config()`)

### Backward Compatibility

**Not maintained.** This is a clean-up/refactoring task with explicit instruction to remove the redundant module. The `PortfolioConfig` class was marked as "临时方案" (temporary solution) and should not be relied upon.

---

## Testing Strategy

### Manual Verification

1. **Syntax Check:**
   ```bash
   python -m py_compile portfolio_manager/commands.py
   python -m py_compile portfolio_manager/commands_refactored.py
   ```

2. **Import Verification:**
   ```bash
   python -c "from portfolio_manager.commands import PortfolioCommands; print('OK')"
   python -c "from portfolio_manager.commands_refactored import PortfolioCommands; print('OK')"
   ```

3. **No References Check:**
   ```bash
   grep -r "PortfolioConfig" portfolio_manager/
   ```
   Expected: No results

4. **File Deletion Check:**
   ```bash
   ls portfolio_manager/config.py
   ```
   Expected: "No such file or directory"

### Automated Tests

If tests exist:
```bash
pytest tests/ -v -k portfolio
```

If no tests exist (likely), manual verification above is sufficient.

---

## Benefits

1. **Single Source of Truth**: All configuration comes from one place (`common/config.py`)
2. **No Hard-coded Values**: Configuration loaded from YAML files and environment variables
3. **Consistent Configuration**: Same config used by all modules
4. **Easier Maintenance**: Changes to configuration only need to be made in one place
5. **Proper Configuration Management**: Uses Pydantic's `BaseSettings` with proper validation
6. **Code Cleanup**: Removes 20 lines of redundant code

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| External code depends on `PortfolioConfig` | Breaking change is intentional; migration path is straightforward |
| Configuration values change unexpectedly | Unified config loads from same YAML files, values should remain the same |
| Import errors after deletion | Update all imports before deleting the file |

---

## Acceptance Criteria

- [ ] `portfolio_manager/config.py` file is deleted
- [ ] `commands.py` imports and uses `get_config()` from `common.config`
- [ ] `commands_refactored.py` imports and uses `get_config()` from `common.config`
- [ ] No references to `PortfolioConfig` exist in `portfolio_manager/` module
- [ ] All files compile without syntax errors
- [ ] All imports work correctly
- [ ] Existing functionality is preserved

---

## Notes

### Why Not Keep Both?

Keeping both would:
- Maintain configuration inconsistency
- Increase maintenance burden
- Confuse developers about which config to use
- Violate DRY principle

### Why Unified Config is Better

The unified `Config` class:
- Uses Pydantic for validation and type safety
- Supports multiple configuration sources (YAML, env vars, runtime)
- Is already used by other modules (`containers.py`, `fee_calculator.py`)
- Provides proper configuration management patterns
- Has comprehensive configuration options (database, fee, logging, etc.)

---

## Conclusion

This design proposes a simple, straightforward refactoring to remove redundant code and unify the configuration system. The changes are minimal, low-risk, and provide immediate benefits in terms of code quality and maintainability.

The unified configuration system is already in place and working correctly in other parts of the module. This change simply extends its usage to the remaining files that still use the old, redundant configuration approach.
