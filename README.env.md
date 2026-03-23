# 环境变量配置指南

## 目录结构

```
项目根目录/
├── .env.example          # 环境变量模板（提交到 Git）
├── .env                  # 开发环境配置（不提交）
├── .env.test             # 测试环境配置（不提交）
├── .env.production       # 生产环境配置（不提交）
└── config/
    ├── database.yaml     # 数据库配置（敏感信息为空）
    └── .gitignore        # 配置目录的忽略规则
```

## 配置文件说明

### 1. .env.example (模板)

这是环境变量的示例文件，**提交到 Git**，用于说明如何配置环境变量。

**不要修改此文件中的实际值**，它只作为文档和模板使用。

### 2. .env (开发环境)

**不提交到 Git**，包含开发环境的真实配置。

创建方法：
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 3. .env.test (测试环境)

**不提交到 Git**，用于运行测试。

```bash
cp .env.example .env.test
# 修改数据库连接为测试数据库
```

### 4. .env.production (生产环境)

**不提交到 Git**，生产环境使用。

```bash
cp .env.example .env.production
# 填入生产环境的真实配置
```

## 配置优先级

系统使用以下优先级（从高到低）：

1. **运行时参数** - 代码中直接传入的参数
2. **环境变量** - `.env` 文件或系统环境变量
3. **YAML 配置** - `config/*.yaml` 文件
4. **默认值** - 配置模型中的默认值

## 常用配置项

### 数据库配置

```bash
# 基础配置
DATABASE_URL=postgresql://user:password@host:port/database

# 嵌套配置（覆盖 YAML 中的特定字段）
DATABASE__POOL_SIZE=20
DATABASE__MAX_OVERFLOW=30
```

### Redis 配置

```bash
REDIS_URL=redis://localhost:6379/0
```

### API 服务器配置

```bash
API_SERVER__HOST=0.0.0.0
API_SERVER__PORT=8000
API_SERVER__API_KEY_SECRET=your-secret-key
```

### 回测配置

```bash
BACKTEST__INITIAL_CAPITAL=100000
BACKTEST__COMMISSION_RATE=0.00025
```

## 环境变量命名规则

- **扁平配置**: `DATABASE_URL`
- **嵌套配置**: `SECTION__FIELD` (使用双下划线)
  
示例：
```bash
# 覆盖 config/database.yaml 中的 pool_size
DATABASE__POOL_SIZE=20

# 覆盖 config/api_server.yaml 中的 api_key_secret
API_SERVER__API_KEY_SECRET=secret-key
```

## 安全注意事项

1. **永远不要提交包含真实密码的文件到 Git**
   - `.env`
   - `.env.test`
   - `.env.production`

2. **使用 .env.example 作为模板**
   - 包含示例值
   - 包含配置说明

3. **密码中的特殊字符**
   - 如果密码包含特殊字符，需要用引号包裹
   - 示例: `DATABASE_URL="postgresql://user:p@ss:w0rd@host/db"`

## Git 配置检查

确保以下文件已添加到 `.gitignore`:

```
.env
.env.local
.env.*.local
.env.test
.env.production
config/local.yaml
config/config.local.yaml
```

验证命令：
```bash
# 检查 .env 文件是否被忽略
git check-ignore -v .env

# 检查这些文件是否在 Git 中
git ls-files | grep "\.env"
# 应该只显示 .env.example
```

## 故障排查

### 配置未生效

1. 检查 `.env` 文件是否在项目根目录
2. 检查环境变量命名是否正确（双下划线）
3. 重启应用使配置生效

### 数据库连接失败

1. 检查 `DATABASE_URL` 格式是否正确
2. 验证数据库服务是否运行
3. 检查用户名和密码是否正确

## 示例配置

### 开发环境 (.env)

```bash
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/alpha_quant
REDIS_URL=redis://localhost:6379/0

LOG_LEVEL=DEBUG
```

### 测试环境 (.env.test)

```bash
APP_ENV=testing
DEBUG=true

DATABASE_URL=postgresql://postgres:postgres_test@test-db:5432/test_stock_market
REDIS_URL=redis://test-redis:6379/0

LOG_LEVEL=INFO
```

### 生产环境 (.env.production)

```bash
APP_ENV=production
DEBUG=false

DATABASE_URL=postgresql://alpha_quant:secure_password@prod-host:5432/alpha_quant
REDIS_URL=redis://prod-redis:6379/0

LOG_LEVEL=WARNING
```

## 相关文件

- `config/database.yaml` - 数据库基础配置（敏感信息为空）
- `.env.example` - 环境变量模板
- `.gitignore` - Git 忽略规则
