# Docker API Server 集成测试环境设计文档

**日期**: 2026-03-23
**状态**: 设计完成
**优先级**: 高
**相关文档**: [Docker 测试环境管理器设计](./2026-03-23-docker-test-environment-manager-design.md)

---

## 1. 概述

### 1.1 目标

构建一个完整的 Docker 测试环境，支持对外部 API Server 进行端到端的集成测试。

**核心价值**:
- ✅ **隔离性** - 测试环境与开发/生产环境完全隔离
- ✅ **可重复性** - 每次测试都在相同环境下运行
- ✅ **端到端验证** - 验证整个 API 服务层的功能完整性
- ✅ **快速反馈** - 一键启动环境并运行测试

### 1.2 范围

**包含**:
- Docker 测试环境管理（PostgreSQL + Redis + Mock API + API Server）
- 集成测试用例执行
- 测试结果报告生成
- 环境自动清理

**不包含**:
- 单元测试（已有）
- 前端测试
- 性能/压力测试

### 1.3 使用方式 A（外部运行）

测试在本地环境运行，通过 HTTP 调用 Docker 容器中的 API Server：

```
┌─────────────────────┐
│   pytest (本地)      │ ← 测试执行和结果输出
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌────────────────────────────────┐
│  Docker 测试环境 (容器化)       │
│  ┌──────────────────────────┐  │
│  │ api-server-test:8001     │  │ ← 被测试的 API 服务
│  └──────────┬───────────────┘  │
│             │                   │
│  ┌──────────▼───────────────┐  │
│  │ test-db:5433             │  │ ← PostgreSQL 15
│  │ test-redis:6380          │  │ ← Redis 7
│  │ mock-api:9000            │  │ ← Mock API Server
│  └──────────────────────────┘  │
└────────────────────────────────┘
```

**优势**:
- 调试方便：可以直接在本地看到测试输出和堆栈
- 速度快：无需构建额外的测试容器
- 灵活：可以快速修改测试代码并重新运行
- 资源节省：不需要运行完整的 Python 环境容器

---

## 2. 架构设计

### 2.1 系统组件

#### 2.1.1 测试环境容器（docker-compose.test.yml）

```yaml
services:
  # 1. 测试数据库
  test-db:
    image: postgres:15-alpine
    container_name: alpha-quant-test-db
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_DB=test_stock_market
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres_test
    volumes:
      - test-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  # 2. 测试 Redis
  test-redis:
    image: redis:7-alpine
    container_name: alpha-quant-test-redis
    ports:
      - "6380:6379"

  # 3. Mock API Server (外部 API 模拟)
  mock-api:
    build:
      context: .
      dockerfile: tests/Dockerfile.mock
    container_name: alpha-quant-mock-api
    ports:
      - "9000:9000"

  # 4. API Server (被测试对象)
  api-server-test:
    build:
      context: .
      dockerfile: tests/Dockerfile.test
    container_name: alpha-quant-api-test
    ports:
      - "8001:8000"
    environment:
      - APP_ENV=testing
      - DATABASE_URL=postgresql://postgres:postgres_test@test-db:5432/test_stock_market
      - REDIS_URL=redis://test-redis:6379/0
      - USE_MOCK_API=true
      - MOCK_API_URL=http://mock-api:9000
    depends_on:
      test-db:
        condition: service_healthy
      test-redis:
        condition: service_started
      mock-api:
        condition: service_started
```

#### 2.1.2 测试执行器（tests/run_tests.py）

**主要功能**:
```python
class TestEnvironmentManager:
    """
    测试环境管理器
    """

    def setup_test_environment(self, include_api_server=False):
        """启动测试环境"""
        # 1. 检查 Docker 和 Docker Compose
        # 2. 检查端口可用性 (5433, 6380, 9000, 8001)
        # 3. 检查 .env.test 配置文件
        # 4. 启动 Docker Compose 服务
        # 5. 等待所有服务健康检查通过
        # 6. (可选) 等待 API Server 健康检查

    def teardown_test_environment(self, force=False, purge=False):
        """停止测试环境"""
        # 1. 确认 (除非 force=True)
        # 2. 停止所有容器
        # 3. (可选) 清理数据卷

    def verify_test_environment(self):
        """验证测试环境是否可用"""
        # 1. 检查所有容器是否运行
        # 2. 设置本地测试环境变量
        # 3. 返回可用性状态

    def run_integration_tests(self, test_files=None, pytest_args=None):
        """运行集成测试"""
        # 1. 验证环境
        # 2. 配置环境变量 (DATABASE_URL, REDIS_URL 等)
        # 3. 构建 pytest 命令
        # 4. 执行 pytest
        # 5. 返回退出码

    def setup_and_run_tests(self, test_files=None, pytest_args=None):
        """一键测试: 启动环境 + 运行测试"""
        # 1. 启动测试环境 (包含 api-server-test)
        # 2. 运行集成测试
        # 3. 生成测试报告
        # 4. (失败时) 保留环境供调试
```

#### 2.1.3 集成测试用例（tests/api_server/test_integration.py）

**测试场景**:
```python
# 场景 1: 完整模拟交易工作流
def test_complete_simulation_workflow():
    # 创建账户 → 买入 → 查询持仓 → 卖出 → 查询收益 → 删除账户

# 场景 2: 回测工作流
def test_backtest_workflow():
    # 创建回测任务 → 获取结果 → 生成报告

# 场景 3: 技术分析工作流
def test_analysis_workflow():
    # 五维共振分析 → 策略分析 → 技术指标

# 场景 4: 账户管理
def test_simulation_account_management():
    # 批量创建 → 查询列表 → 批量删除

# 场景 5: 错误处理
def test_simulation_error_handling():
    # 余额不足 → 不存在账户 → 不存在持仓
```

### 2.2 数据流

```
测试执行流程:

1. 环境启动阶段
   ┌─────────────────────────────────────────────┐
   │ 用户执行: python tests/run_tests.py         │
   │           --setup-and-run                   │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 检查依赖 (Docker, 端口, 配置文件)            │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 启动 Docker Compose 服务:                   │
   │ - test-db (PostgreSQL)                      │
   │ - test-redis (Redis)                        │
   │ - mock-api (Mock Server)                    │
   │ - api-server-test (API Server)              │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 等待健康检查通过 (最长 60 秒)                │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 设置本地环境变量:                           │
   │ DATABASE_URL=postgresql://localhost:5433    │
   │ REDIS_URL=redis://localhost:6380            │
   │ MOCK_API_URL=http://localhost:9000          │
   └───────────────┬─────────────────────────────┘

2. 测试执行阶段
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ pytest 加载测试用例                          │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ TestClient 调用 http://localhost:8001       │
   │ (FastAPI TestClient)                        │
   └───────────────┬─────────────────────────────┘
                   │ HTTP Request
                   ▼
   ┌─────────────────────────────────────────────┐
   │ API Server 处理请求                          │
   │ - 验证参数                                   │
   │ - 调用 Service 层                            │
   │ - 访问数据库/Redis/Mock API                  │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 返回 HTTP Response                          │
   │ (JSON 格式)                                  │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ pytest 验证响应:                            │
   │ - 状态码 (200, 400, 404, 500)               │
   │ - 响应数据结构                               │
   │ - 业务逻辑正确性                             │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 生成测试报告:                               │
   │ - 通过/失败统计                              │
   │ - 覆盖率报告 (可选)                          │
   │ - 失败详情和堆栈跟踪                         │
   └───────────────┬─────────────────────────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────────┐
   │ 环境清理:                                   │
   │ - 测试成功: 停止容器 (可选)                  │
   │ - 测试失败: 保留环境供调试                   │
   └─────────────────────────────────────────────┘
```

### 2.3 环境变量配置

**本地测试环境变量**（pytest 进程）:
```python
# tests/test_config.py
TEST_ENV_VARS = {
    # API Server 地址
    "API_SERVER_URL": "http://localhost:8001",

    # 数据库连接 (本地端口)
    "DATABASE_URL": "postgresql://postgres:postgres_test@localhost:5433/test_stock_market",

    # Redis 连接 (本地端口)
    "REDIS_URL": "redis://localhost:6380/0",

    # Mock API 地址 (本地端口)
    "MOCK_API_URL": "http://localhost:9000",

    # 测试标志
    "USE_MOCK_API": "true",
    "APP_ENV": "testing",
}
```

**容器内环境变量**（docker-compose.test.yml）:
```yaml
environment:
  # 数据库连接 (容器网络)
  - DATABASE_URL=postgresql://postgres:postgres_test@test-db:5432/test_stock_market

  # Redis 连接 (容器网络)
  - REDIS_URL=redis://test-redis:6379/0

  # Mock API 地址 (容器网络)
  - MOCK_API_URL=http://mock-api:9000

  # 应用配置
  - APP_ENV=testing
  - USE_MOCK_API=true
```

---

## 3. 详细实现

### 3.1 测试环境管理器扩展

#### 3.1.1 API Server 健康检查

```python
def wait_for_api_server_health(timeout=60, interval=2):
    """
    等待 API Server 健康检查通过

    流程:
    1. 使用 curl 或 requests 检查 /health 端点
    2. 每 2 秒检查一次
    3. 最多等待 60 秒
    4. 超时则失败

    返回:
        bool: 健康检查是否通过
    """
    print("⏳ 等待 API Server 启动...", end="", flush=True)

    start_time = time.time()
    health_url = "http://localhost:8001/health"

    while time.time() - start_time < timeout:
        try:
            import requests
            response = requests.get(health_url, timeout=2)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("\n✅ API Server 已启动")
                    return True

        except Exception:
            pass

        print(".", end="", flush=True)
        time.sleep(interval)

    print("\n❌ API Server 启动超时")
    return False
```

#### 3.1.2 一键测试模式

```python
def setup_and_run_integration_tests(
    test_files=None,
    pytest_args=None,
    cleanup_on_success=True
):
    """
    一键集成测试: 启动环境 + 运行测试 + 清理

    参数:
        test_files: 指定测试文件列表
        pytest_args: pytest 额外参数
        cleanup_on_success: 测试成功后是否清理环境

    返回:
        int: pytest 退出码 (0=成功)
    """
    print("\n🚀 一键集成测试模式")
    print("=" * 80)

    # 1. 启动测试环境
    print("\n📦 启动测试环境...")
    if not setup_test_environment(include_api_server=True):
        print("❌ 环境启动失败")
        return 1

    # 2. 配置本地测试环境变量
    print("\n⚙️  配置测试环境...")
    setup_local_test_env()

    # 3. 运行测试
    print("\n🧪 运行集成测试...\n")
    try:
        exit_code = run_integration_tests(
            test_files=test_files,
            pytest_args=pytest_args
        )

        # 4. 生成报告
        if exit_code == 0:
            print("\n✅ 所有集成测试通过！")
        else:
            print(f"\n❌ {exit_code} 个测试失败")
            print("\n💡 环境已保留以便调试:")
            print("   - API Server: http://localhost:8001/docs")
            print("   - Database: localhost:5433")
            print("   - Redis: localhost:6380")

        # 5. 清理环境
        if exit_code == 0 and cleanup_on_success:
            print("\n🧹 清理测试环境...")
            teardown_test_environment(force=True)
        else:
            print("\n⚠️  环境已保留供调试")
            print("   运行以下命令清理:")
            print("   python tests/run_tests.py --teardown")

        return exit_code

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        teardown_test_environment(force=True)
        return 130
```

### 3.2 集成测试用例优化

#### 3.2.1 路径修复

当前测试用例中存在路径重复问题，需要修复：

```python
# ❌ 错误: /api/v1/api/v1/simulation/account
# ✅ 正确: /api/v1/simulation/account

# 修复前
response = client.post(
    "/api/v1/api/v1/simulation/account",  # 重复
    json={...}
)

# 修复后
response = client.post(
    "/api/v1/simulation/account",  # 正确
    json={...}
)
```

#### 3.2.2 添加 fixture

```python
# tests/api_server/conftest.py
import pytest
from fastapi.testclient import TestClient
from api_server.main import app

@pytest.fixture(scope="session")
def api_client():
    """API Test Client fixture"""
    return TestClient(app, base_url="http://localhost:8001")

@pytest.fixture(scope="function")
def test_account(api_client):
    """创建测试账户 fixture"""
    # 创建账户
    response = api_client.post(
        "/api/v1/simulation/account",
        json={"account_name": "测试账户", "initial_capital": 100000}
    )
    account_id = response.json()["data"]["account_id"]

    yield account_id

    # 清理账户
    api_client.delete(f"/api/v1/simulation/account/{account_id}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境变量"""
    import os
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres_test@localhost:5433/test_stock_market"
    os.environ["REDIS_URL"] = "redis://localhost:6380/0"
    os.environ["USE_MOCK_API"] = "true"
    os.environ["MOCK_API_URL"] = "http://localhost:9000"
```

#### 3.2.3 测试用例重构

```python
# tests/api_server/test_integration.py

def test_complete_simulation_workflow(api_client, test_account):
    """完整模拟交易工作流测试"""
    account_id = test_account

    # 1. 买入股票
    response = api_client.post(
        "/api/v1/simulation/buy",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1850.0,
            "quantity": 10
        }
    )
    assert response.status_code == 200

    # 2. 查询持仓
    response = api_client.get(f"/api/v1/simulation/positions/{account_id}")
    assert response.status_code == 200
    positions = response.json()["data"]["positions"]
    assert len(positions) == 1

    # 3. 卖出股票
    response = api_client.post(
        "/api/v1/simulation/sell",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1900.0,
            "quantity": 5
        }
    )
    assert response.status_code == 200

    # 4. 查询收益
    response = api_client.get(f"/api/v1/performance/account/{account_id}")
    assert response.status_code == 200

    # 5. 测试账户在 fixture 中自动清理
```

### 3.3 命令行接口扩展

```python
def run_tests_cli():
    """扩展命令行接口"""
    parser = argparse.ArgumentParser(
        description="API Server 集成测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 一键集成测试 (启动环境 + 运行测试)
  python tests/run_tests.py --integration

  # 仅启动测试环境 (包含 API Server)
  python tests/run_tests.py --setup --include-api-server

  # 运行集成测试 (环境已启动)
  python tests/run_tests.py --run-integration

  # 查看测试环境状态
  python tests/run_tests.py --status

  # 停止测试环境
  python tests/run_tests.py --teardown

  # 重置测试环境
  python tests/run_tests.py --reset

  # 运行特定测试用例
  python tests/run_tests.py --integration -k "simulation"

  # 带覆盖率报告
  python tests/run_tests.py --integration --cov
        """
    )

    # 集成测试专用命令
    parser.add_argument(
        "--integration", "--integ", "-i",
        action="store_true",
        help="运行集成测试 (一键模式: 启动环境 + 运行测试)"
    )

    parser.add_argument(
        "--run-integration", "--run-integ",
        action="store_true",
        help="运行集成测试 (假设环境已启动)"
    )

    parser.add_argument(
        "--include-api-server", "--with-api",
        action="store_true",
        help="启动 API Server 容器 (与 --setup 配合使用)"
    )

    # 其他参数 (复用现有)
    # ... (setup, teardown, status, reset, pytest args 等)

    args = parser.parse_args()

    # 处理集成测试命令
    if args.integration:
        pytest_args = []
        if args.verbose:
            pytest_args.append("-v")
        if args.k:
            pytest_args.extend(["-k", args.k])
        if args.cov:
            pytest_args.extend([
                "--cov=api_server",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])

        # 运行集成测试
        from tests.run_tests import setup_and_run_integration_tests
        test_files = args.test_files or ["tests/api_server/test_integration.py"]
        exit_code = setup_and_run_integration_tests(
            test_files=test_files,
            pytest_args=pytest_args
        )
        sys.exit(exit_code)

    elif args.run_integration:
        # 仅运行测试
        pytest_args = ["-v"] if args.verbose else []
        if args.k:
            pytest_args.extend(["-k", args.k])

        test_files = args.test_files or ["tests/api_server/test_integration.py"]
        exit_code = run_tests(test_files=test_files, pytest_args=pytest_args)
        sys.exit(exit_code)

    # 其他命令处理...
```

---

## 4. 测试场景设计

### 4.1 核心业务流程测试

#### 4.1.1 模拟交易全流程

```
测试用例: test_complete_simulation_workflow

步骤:
1. 创建模拟账户 (POST /api/v1/simulation/account)
   → 验证: 返回 account_id, initial_capital 正确

2. 买入股票 (POST /api/v1/simulation/buy)
   → 验证: 交易成功, 持仓数量正确

3. 查询持仓 (GET /api/v1/simulation/positions/{account_id})
   → 验证: 持仓列表包含买入的股票

4. 卖出部分股票 (POST /api/v1/simulation/sell)
   → 验证: 卖出成功, 持仓数量减少

5. 查询账户信息 (GET /api/v1/simulation/account/{account_id})
   → 验证: 总值、盈亏计算正确

6. 查询收益统计 (GET /api/v1/performance/account/{account_id})
   → 验证: 收益率、胜率等指标正确

7. 删除账户 (DELETE /api/v1/simulation/account/{account_id})
   → 验证: 账户删除成功

预期结果:
✅ 所有步骤成功执行
✅ 数据库状态正确
✅ Redis 缓存一致性
✅ API 响应格式正确
```

#### 4.1.2 回测引擎测试

```
测试用例: test_backtest_workflow

步骤:
1. 创建回测任务 (POST /api/v1/backtest/single)
   → 参数: 股票代码、策略、时间范围
   → 验证: 返回 task_id

2. 获取回测结果 (GET /api/v1/backtest/result/{task_id})
   → 验证: 返回完整的性能指标
   → 包含: 年化收益、最大回撤、夏普比率等

3. 生成报告 (POST /api/v1/backtest/report)
   → 格式: JSON / HTML
   → 验证: 报告内容完整

预期结果:
✅ 回测引擎正确执行
✅ 性能指标计算准确
✅ 报告格式正确
```

#### 4.1.3 技术分析测试

```
测试用例: test_analysis_workflow

步骤:
1. 五维共振分析 (POST /api/v1/analysis/five-dimension)
   → 验证: 返回评分和详细维度数据

2. 策略分析 (GET /api/v1/analysis/strategies/{stock_code})
   → 验证: 返回多个策略的信号

3. 技术指标 (GET /api/v1/analysis/indicators/{stock_code})
   → 验证: MACD/KDJ/RSI 等指标正确

预期结果:
✅ 分析算法正确执行
✅ 指标数据格式正确
✅ 边界条件处理正确
```

### 4.2 错误处理测试

#### 4.2.1 业务错误

```
测试用例: test_business_errors

场景:
1. 余额不足时买入
   → 预期: 400 Bad Request + 错误消息

2. 卖出不存在的持仓
   → 预期: 400 Bad Request + 错误消息

3. 重复创建同名账户
   → 预期: 400 Bad Request + 错误消息

4. 查询不存在的账户
   → 预期: 404 Not Found
```

#### 4.2.2 参数验证

```
测试用例: test_validation_errors

场景:
1. 缺少必填参数
   → 预期: 422 Unprocessable Entity

2. 参数类型错误
   → 预期: 422 Unprocessable Entity

3. 参数范围错误 (如负数价格)
   → 预期: 400 Bad Request
```

### 4.3 并发和边界测试

```
测试用例: test_concurrent_access

场景:
1. 同时创建多个账户
   → 验证: 不会出现冲突

2. 同一账户并发交易
   → 验证: 数据一致性 (使用数据库事务)

测试用例: test_boundary_conditions

场景:
1. 最大持仓数量
2. 最小交易金额
3. 超长股票代码
4. 特殊字符处理
```

---

## 5. 错误处理和恢复

### 5.1 常见错误场景

| 错误类型 | 检测方式 | 处理策略 |
|---------|---------|---------|
| Docker 未安装 | `docker --version` | 提示安装并退出 |
| 端口占用 | `netstat` / socket 检查 | 列出占用进程, 提示停止 |
| 容器启动失败 | `docker compose ps` | 显示日志, 自动清理 |
| 健康检查超时 | HTTP 请求超时 | 重试 3 次后报错 |
| 数据库连接失败 | psycopg2 异常 | 检查连接字符串, 重试 |
| API Server 无响应 | HTTP 5xx / 连接错误 | 显示错误详情, 保留环境 |

### 5.2 自动恢复机制

```python
def robust_test_execution():
    """健壮的测试执行流程"""

    # 1. 环境检查
    if not check_prerequisites():
        print("❌ 环境检查失败")
        return 1

    # 2. 启动环境 (带重试)
    max_retries = 3
    for attempt in range(max_retries):
        if setup_test_environment():
            break
        print(f"⚠️  启动失败, 重试 {attempt + 1}/{max_retries}...")
        time.sleep(5)
    else:
        print("❌ 环境启动失败")
        return 1

    # 3. 运行测试
    try:
        exit_code = run_tests()

        # 4. 成功后清理
        if exit_code == 0:
            teardown_test_environment(force=True)

        return exit_code

    except Exception as e:
        print(f"❌ 测试执行异常: {e}")
        print("\n💡 环境已保留供调试")
        import traceback
        traceback.print_exc()
        return 1
```

---

## 6. 性能和资源考虑

### 6.1 启动时间优化

**目标**: 整个环境启动时间 < 30 秒

**优化措施**:
- 使用轻量级镜像 (alpine)
- 并行启动非依赖服务 (test-redis, mock-api)
- 串行启动依赖服务 (test-db → api-server-test)
- 启用 Docker BuildKit 加速镜像构建

### 6.2 资源消耗

**预估资源**:
- 内存: ~500MB (test-db: 200MB, test-redis: 50MB, api-server: 200MB, mock-api: 50MB)
- CPU: < 1 核
- 磁盘: ~100MB (数据卷)

**清理策略**:
- 测试成功后自动清理容器
- 手动执行 `--purge` 清理数据卷
- 定期清理无用镜像: `docker image prune -f`

---

## 7. 安全考虑

### 7.1 测试环境隔离

- 使用独立的数据库 (test_stock_market)
- 使用独立的端口 (5433, 6380, 8001, 9000)
- 使用独立的 Docker 网络 (test-network)

### 7.2 敏感信息处理

- 测试环境使用 mock token 和 mock key
- `.env.test` 不包含真实 API 密钥
- 所有外部 API 调用通过 mock-api 代理

### 7.3 容器安全

- 使用非 root 用户运行容器 (可在 Dockerfile 中配置)
- 限制容器资源使用 (memory, cpu)
- 禁用容器间不必要的网络访问

---

## 8. 监控和日志

### 8.1 日志输出

```
测试执行日志:

✅ [00:00] 检查 Docker: Docker version 24.0.7
✅ [00:01] 检查端口: 5433, 6380, 8001, 9000 可用
✅ [00:02] 启动 Docker Compose 服务
✅ [00:05] test-db 启动成功
✅ [00:06] test-redis 启动成功
✅ [00:07] mock-api 启动成功
✅ [00:15] api-server-test 启动成功
✅ [00:16] 配置测试环境变量
✅ [00:17] 运行集成测试...

测试结果:
✅ test_complete_simulation_workflow
✅ test_backtest_workflow
✅ test_analysis_workflow
✅ test_simulation_account_management
✅ test_simulation_error_handling

✅ 5/5 测试通过 (耗时: 8.23 秒)
✅ 覆盖率: 83% (api_server/services/)
```

### 8.2 容器日志查看

```bash
# 查看 API Server 日志
docker logs alpha-quant-api-test --tail 100 -f

# 查看数据库日志
docker logs alpha-quant-test-db --tail 50

# 查看所有容器日志
docker compose -f docker-compose.test.yml logs
```

---

## 9. 扩展性考虑

### 9.1 添加新的测试场景

**步骤**:
1. 在 `tests/api_server/` 下创建新的测试文件
2. 使用 `@pytest.mark.integration` 标记
3. 复用现有的 fixture (api_client, test_account)
4. 运行测试: `python tests/run_tests.py --integration -k "新测试名"`

### 9.2 添加新的依赖服务

**场景**: 需要 Elasticsearch 进行日志搜索

**修改**:
1. 在 `docker-compose.test.yml` 添加新服务
2. 在 `setup_test_environment()` 中添加健康检查
3. 在 `.env.test` 中添加配置
4. 在 API Server Dockerfile 中安装客户端库

### 9.3 支持多个测试环境

**场景**: 同时运行单元测试和集成测试

**实现**:
```python
# 使用不同的端口和容器名
INTEGRATION_ENV = {
    "api_port": 8001,
    "db_port": 5433,
    "container_prefix": "integration-"
}

E2E_ENV = {
    "api_port": 8002,
    "db_port": 5434,
    "container_prefix": "e2e-"
}
```

---

## 10. 文档和使用指南

### 10.1 快速开始

```bash
# 1. 启动测试环境
python tests/run_tests.py --setup --include-api-server

# 2. 运行集成测试
python tests/run_tests.py --run-integration

# 3. 一键测试 (推荐)
python tests/run_tests.py --integration

# 4. 查看状态
python tests/run_tests.py --status

# 5. 停止环境
python tests/run_tests.py --teardown
```

### 10.2 常见问题

**Q: 端口被占用怎么办?**
A: 运行 `python tests/run_tests.py --teardown` 停止旧环境，或修改 `docker-compose.test.yml` 中的端口映射。

**Q: 测试失败如何调试?**
A: 环境会自动保留，可以:
- 访问 http://localhost:8001/docs 测试 API
- 查看容器日志: `docker logs alpha-quant-api-test`
- 连接数据库: `psql -h localhost -p 5433 -U postgres test_stock_market`

**Q: 如何运行单个测试?**
A: `python tests/run_tests.py --integration -k "test_name"`

---

## 11. 验收标准

### 11.1 功能验收

- ✅ 可以通过单条命令启动测试环境并运行集成测试
- ✅ 测试环境包含: PostgreSQL + Redis + Mock API + API Server
- ✅ 所有集成测试用例能够成功执行
- ✅ 测试失败时环境会保留供调试
- ✅ 测试成功后可以自动清理环境

### 11.2 质量验收

- ✅ 代码覆盖率 ≥ 80%
- ✅ 所有测试用例有清晰的注释
- ✅ 错误处理完善, 不会出现未捕获异常
- ✅ 日志输出清晰, 易于排查问题

### 11.3 性能验收

- ✅ 环境启动时间 < 30 秒
- ✅ 单个测试用例执行时间 < 5 秒
- ✅ 所有测试执行时间 < 60 秒
- ✅ 内存占用 < 500MB

---

## 12. 未来改进方向

1. **测试数据工厂**: 创建测试数据生成器, 支持不同场景的数据准备
2. **性能基准测试**: 添加响应时间监控, 确保性能不退化
3. **可视化测试报告**: 生成 HTML 格式的测试报告
4. **CI/CD 集成**: 在 GitHub Actions 中自动运行集成测试
5. **数据库快照**: 支持保存/恢复数据库状态, 加速测试

---

## 附录

### A. 文件清单

- `docker-compose.test.yml` - Docker 测试环境定义
- `tests/run_tests.py` - 测试环境管理器 (扩展)
- `tests/Dockerfile.test` - API Server 测试镜像
- `tests/Dockerfile.mock` - Mock API Server 镜像
- `tests/api_server/test_integration.py` - 集成测试用例
- `tests/api_server/conftest.py` - pytest fixture
- `.env.test.example` - 测试环境配置模板
- `docs/superpowers/specs/2026-03-23-docker-api-server-integration-test-design.md` - 本文档

### B. 依赖项

**本地依赖**:
- Python 3.11+
- pytest
- requests
- Docker 24.0+
- Docker Compose V2+

**容器依赖**:
- postgres:15-alpine
- redis:7-alpine
- python:3.11-slim

### C. 参考资料

- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**文档版本**: 1.0
**最后更新**: 2026-03-23
**作者**: Claude Code
