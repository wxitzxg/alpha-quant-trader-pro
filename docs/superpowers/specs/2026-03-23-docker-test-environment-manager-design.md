# Docker 测试环境管理器设计方案

**日期：** 2026-03-23
**作者：** Claude Code
**状态：** 待批准
**相关文件：** `tests/run_tests.py`、`docker-compose.test.yml`、`tests/Dockerfile.test`

---

## 1. 需求概述

### 1.1 目标

基于 Docker 快速启动本地测试环境，并运行测试用例，支持以下场景：

- 本地开发调试时快速启动测试环境
- 测试 API Server 与数据库、Redis、Mock API 等组件的集成

### 1.2 核心需求

1. 宿主机运行 `pytest`，通过端口映射连接到测试容器中的服务
2. 统一入口脚本管理测试环境（启动/停止/状态检查）
3. 支持单个测试文件或整个测试套件运行
4. 支持覆盖率报告生成
5. 友好的错误提示和自动清理

---

## 2. 架构设计

### 2.1 核心组件

```
┌─────────────────────────────────────────────────────┐
│                测试环境管理器                        │
│           tests/run_tests.py (Python)               │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  test-db    │  │ test-redis  │  │  mock-api   │
│  (5433)     │  │  (6380)     │  │  (9000)     │
└─────────────┘  └─────────────┘  └─────────────┘
   PostgreSQL       Redis            Mock API
```

### 2.2 网络拓扑

```
宿主机 (pytest)
    ├─→ localhost:5433 (test-db)
    ├─→ localhost:6380 (test-redis)
    └─→ localhost:9000 (mock-api)
```

### 2.3 数据流

#### 2.3.1 环境启动流程

```
用户执行: python tests/run_tests.py --setup
    ↓
1. 检查 Docker 是否安装
    ↓
2. 检查 .env.test 是否存在（不存在则复制 .env.test.example）
    ↓
3. 调用 docker-compose -f docker-compose.test.yml up -d
    ↓
4. 轮询检查服务健康状态（间隔 2 秒，最多 60 秒）
    ├─→ test-db 健康检查
    ├─→ test-redis 运行状态
    └─→ mock-api 健康检查
    ↓
5. 显示启动成功 + 服务状态表格
```

#### 2.3.2 测试运行流程

```
用户执行: python tests/run_tests.py [pytest参数]
    ↓
1. 验证测试环境是否运行（docker-compose ps）
    ↓
2. 设置环境变量:
   - DATABASE_URL=postgresql://postgres:postgres_test@localhost:5433/test_stock_market
   - REDIS_URL=redis://localhost:6380/0
   - MOCK_API_URL=http://localhost:9000
    ↓
3. 执行 pytest 命令
    ↓
4. 捕获退出码并返回
```

#### 2.3.3 环境清理流程

```
用户执行: python tests/run_tests.py --teardown [--force] [--purge]
    ↓
1. 确认是否继续（--force 跳过确认）
    ↓
2. 调用 docker-compose down
    ↓
3. 清理数据卷（--purge 时）
    ↓
4. 显示清理结果
```

---

## 3. 组件设计

### 3.1 `run_tests.py` 核心功能

#### 3.1.1 环境管理命令

| 命令           | 说明          | 参数                               |
| ------------ | ----------- | -------------------------------- |
| `--setup`    | 启动测试环境      | 无                                |
| `--teardown` | 停止测试环境      | `--force`（跳过确认）、`--purge`（清理数据卷） |
| `--status`   | 检查服务状态      | 无                                |
| `--reset`    | 重置环境（停止+启动） | 无                                |

#### 3.1.2 测试运行命令

| 命令                | 说明         | 参数                              |
| ----------------- | ---------- | ------------------------------- |
| （无）               | 运行测试（默认行为） | `-k`（过滤）、`--cov`（覆盖）等 pytest 参数 |
| `--setup-and-run` | 一键启动并运行测试  | 同上                              |

#### 3.1.3 便捷命令

| 命令                               | 等价操作              |
| -------------------------------- | ----------------- |
| `python tests/run_tests.py test` | `--setup-and-run` |
| `python tests/run_tests.py up`   | `--setup`         |
| `python tests/run_tests.py down` | `--teardown`      |

### 3.2 关键配置

#### 3.2.1 环境变量（`.env.test`）

```bash
# 应用配置
APP_ENV=testing
DEBUG=true
TZ=Asia/Shanghai

# 数据库配置
DATABASE_URL=postgresql://postgres:postgres_test@localhost:5433/test_stock_market

# Redis 配置
REDIS_URL=redis://localhost:6380/0

# Mock API 配置
MOCK_API_URL=http://localhost:9000
USE_MOCK_API=true

# API 服务器配置
API_SERVER__API_KEY_SECRET=test_secret_key_123456
API_SERVER__RATE_LIMIT_FREE=1000
```

#### 3.2.2 Docker Compose 配置

**端口映射：**

- `test-db:5432` → `localhost:5433`
- `test-redis:6379` → `localhost:6380`
- `mock-api:9000` → `localhost:9000`

**数据卷：**

- `test-db-data`：数据库数据
- `test-redis-data`：Redis 数据

---

## 4. 错误处理设计

### 4.1 关键错误场景

| 错误场景                 | 处理策略                         | 用户提示                                                    |
| -------------------- | ---------------------------- | ------------------------------------------------------- |
| Docker 未安装           | 检测失败，优雅退出                    | `❌ Docker 未安装或不可用，请安装 Docker 后重试`                       |
| `.env.test` 不存在      | 检测到 `.env.test.example`，提示复制 | `⚠️ 未找到 .env.test，已复制模板`                                |
| 端口冲突（5433/6380/9000） | 检测端口占用，退出                    | `❌ 端口 5433 已被占用，请停止冲突服务后重试`                             |
| 服务启动超时               | 轮询超时后停止并清理                   | `❌ test-db 启动超时，正在清理...`                                |
| 服务健康检查失败             | 停止所有服务并报告状态                  | `❌ mock-api 健康检查失败，详情：docker logs alpha-quant-mock-api` |
| 环境未启动就运行测试           | 检测失败，提示启动                    | `⚠️ 测试环境未运行，执行：python tests/run_tests.py --setup`       |
| 测试运行失败               | 返回非 0 退出码，保留环境               | `❌ 测试失败（退出码：{code}），环境已保留以便调试`                          |
| 网络或卷已存在              | 忽略错误，继续                      | `ℹ️ 网络/卷已存在，继续...`                                      |

### 4.2 错误处理原则

- **快速失败**：检测到错误立即停止，不继续执行
- **清晰提示**：提供可操作的错误信息和解决方案
- **安全清理**：失败时自动清理已启动的资源
- **保留调试信息**：测试失败时保留环境，便于调试

---

## 5. 测试覆盖设计

### 5.1 验证范围

#### 5.1.1 环境管理测试

- [ ] 启动：验证所有服务正常运行
- [ ] 状态检查：验证 `--status` 输出正确
- [ ] 清理：验证 `--teardown` 完全清理资源
- [ ] 端口冲突检测

#### 5.1.2 集成测试

- [ ] 数据库连接测试：创建表、插入数据、查询
- [ ] Redis 连接测试：设置/获取键值
- [ ] Mock API 调用测试：验证 Mock 服务响应
- [ ] API Server 路由测试：健康检查、认证

#### 5.1.3 现有测试兼容性

- [ ] 所有 `tests/api_server/test_*.py` 测试通过
- [ ] `conftest.py` 中的 fixture 正常工作
- [ ] 覆盖报告生成（`--cov`）

### 5.2 测试执行方式

```bash
# 基础测试（快速验证环境）
python tests/run_tests.py --setup
python tests/run_tests.py tests/api_server/test_health_router.py

# 完整测试套件
python tests/run_tests.py --setup-and-run

# 覆盖率测试
python tests/run_tests.py --setup-and-run --cov

# 单个测试文件
python tests/run_tests.py --setup-and-run -k "test_stock_market"
```

### 5.3 覆盖率目标

- 环境管理脚本：100%（命令行工具逻辑简单）
- 测试用例：80%+（沿用现有测试覆盖率要求）
- 集成测试：覆盖所有关键服务（数据库、Redis、Mock API）

---

## 6. 使用示例

### 6.1 基本工作流

```bash
# 1. 复制环境变量模板
cp .env.test.example .env.test

# 2. 启动测试环境
python tests/run_tests.py --setup

# 3. 运行测试
python tests/run_tests.py

# 4. 运行特定测试
python tests/run_tests.py -k "test_stock"

# 5. 运行并生成覆盖率报告
python tests/run_tests.py --cov

# 6. 停止测试环境
python tests/run_tests.py --teardown
```

### 6.2 一键测试

```bash
# 启动环境 + 运行测试 + 生成覆盖率
python tests/run_tests.py --setup-and-run --cov

# 等价于
python tests/run_tests.py test --cov
```

### 6.3 调试场景

```bash
# 查看服务状态
python tests/run_tests.py --status

# 重置环境（清理 + 重新启动）
python tests/run_tests.py --reset

# 强制清理（跳过确认）
python tests/run_tests.py --teardown --force --purge
```

---

## 7. 依赖与兼容性

### 7.1 依赖项

- Docker CLI（宿主机安装）
- Docker Compose v2.x
- Python 3.11+
- 现有测试依赖（已在 `requirements.test.txt` 中）

### 7.2 兼容性

- Linux（原生支持）
- macOS（Docker Desktop）
- Windows（Docker Desktop + WSL2）

---

## 8. 验收标准

- [ ] 执行 `python tests/run_tests.py --setup` 成功启动所有服务
- [ ] 执行 `python tests/run_tests.py --status` 显示正确的服务状态
- [ ] 执行 `python tests/run_tests.py` 成功运行测试并返回正确退出码
- [ ] 执行 `python tests/run_tests.py --teardown` 完全清理资源
- [ ] 所有现有测试用例在新环境中通过
- [ ] 错误场景有清晰的用户提示
- [ ] 支持覆盖率报告生成（`--cov`）
- [ ] 支持测试过滤（`-k`）

---

## 9. 未来扩展

- 支持测试数据预加载（初始化数据）
- 支持测试快照（保存/恢复数据库状态）
- 支持并行测试运行
- 支持测试报告生成（HTML/XML）

---

**设计评审状态：** 待批准
**批准人：** _________张新光  ________
**批准日期：** _________20260323________
