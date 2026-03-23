# 快速开始 - 环境变量配置

## 5分钟快速配置

### 步骤 1: 复制环境变量模板

```bash
cp .env.example .env
```

### 步骤 2: 编辑配置

打开 `.env` 文件，修改数据库配置：

```bash
# 修改数据库连接
DATABASE_URL=postgresql://你的用户名:你的密码@localhost:5432/alpha_quant
```

### 步骤 3: 验证配置

```bash
python3 config/check_config.py
```

应该看到：
```
✅ 所有检查通过！
```

### 步骤 4: 启动应用

```bash
python -m api_server.main
```

应该看到日志：
```
INFO - 正在同步数据库表...
INFO - 数据库表同步完成
INFO - Application startup complete.
```

## 测试环境配置

```bash
# 创建测试配置
cp .env.example .env.test

# 编辑 .env.test，修改为测试数据库
# DATABASE_URL=postgresql://postgres:postgres_test@localhost:5432/test_stock_market

# 运行测试
pytest tests/ -v
```

## 配置优先级

环境变量 > YAML 配置 > 默认值

示例：
```bash
# 覆盖 YAML 中的 pool_size
DATABASE__POOL_SIZE=20

# 覆盖 API 端口
API_SERVER__PORT=9000
```

## 安全提示

- ✅ `.env.example` 可以提交到 Git
- ❌ `.env` **不要**提交到 Git
- ❌ `.env.test` **不要**提交到 Git

Git 已配置忽略这些文件，但请务必确认。

## 常见问题

**Q: 数据库连接失败？**

A: 检查 DATABASE_URL 格式和数据库服务是否运行

**Q: 配置未生效？**

A: 重启应用使配置生效

**Q: 如何查看当前配置？**

A: 
```bash
python3 -c "from dotenv import load_dotenv; load_dotenv(); from common.config import get_config; config = get_config(); print(f'DB: {config.database.url}')"
```

## 更多文档

- `README.env.md` - 完整的环境变量配置指南
- `MIGRATION_GUIDE.md` - 迁移指南
- `config/README.md` - 配置目录说明
