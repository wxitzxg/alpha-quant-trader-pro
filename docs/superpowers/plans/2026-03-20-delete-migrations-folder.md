# 删除 migrations 文件夹补充计划

## 重要说明

根据用户要求，**不保留 migrations 文件夹**，**不需要向后兼容**，**彻底废弃旧代码**。

## 背景

`stock_market/migrations/` 文件夹包含 Alembic 数据库迁移文件，但这些文件使用了旧的配置加载方式（`from stock_market.config import load_config`），与新的统一配置系统不兼容。

## 删除操作

### 步骤 1: 检查文件夹内容

```bash
cd /home/zxg/workspace/alpha-quant-trader-pro/.claude/worktrees/stockmarket
ls -la stock_market/migrations/
```

**预期输出**:
```
alembic.ini
env.py
script.py.mako
versions/
```

### 步骤 2: 确认不再需要

检查项目中是否还有其他地方使用 Alembic：

```bash
grep -r "alembic\|Alembic" --include="*.py" . 2>/dev/null | grep -v test | grep -v docs
```

如果输出为空或只在文档中提到，说明可以安全删除。

### 步骤 3: 备份（可选）

```bash
cp -r stock_market/migrations stock_market/migrations.backup
```

### 步骤 4: 彻底删除

```bash
rm -rf stock_market/migrations/
```

### 步骤 5: 从 Git 删除

```bash
git rm -r stock_market/migrations/
```

### 步骤 6: 验证删除

```bash
ls stock_market/ | grep migrations
# 应该没有输出
```

### 步骤 7: 检查 requirements.txt

```bash
grep -i "alembic" requirements.txt
```

如果找到 Alembic 依赖，考虑是否需要移除（如果项目完全不使用 Alembic）

### 步骤 8: 提交

```bash
git commit -m "refactor(stock_market): remove migrations folder completely

- Delete entire stock_market/migrations/ folder
- Remove all Alembic migration files
- No longer using Alembic for database migrations
- Clean slate for stock_market module

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

## 注意事项

1. **彻底删除** - migrations 文件夹将被完全删除，不再保留
2. **无向后兼容** - 不保留任何旧的迁移文件或兼容代码
3. **数据库迁移** - 项目将使用其他方式处理数据库迁移（如直接使用 SQLAlchemy 或其他工具）
4. **测试影响** - 删除后，所有引用 migrations 的测试也需要更新或删除

## 影响范围

### 删除的文件
- `stock_market/migrations/alembic.ini`
- `stock_market/migrations/env.py`
- `stock_market/migrations/script.py.mako`
- `stock_market/migrations/versions/__init__.py`
- 整个 `stock_market/migrations/` 目录

### 需要更新的文档
- 检查 `docs/` 目录中的文档，移除对 migrations 的引用
- 更新 README 或安装文档（如果提到 Alembic）

## 后续建议

1. **数据库迁移策略** - 确定新的数据库迁移策略（如使用 SQLAlchemy 直接管理，或使用其他迁移工具）
2. **现有数据库** - 如果有现有数据库，确保有备份和迁移方案
3. **测试** - 更新相关测试，确保不依赖已删除的 migrations
