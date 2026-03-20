# Docker Compose 测试栈设计方案

## 日期
2026-03-20

## 概述

为 `api_server` 模块构建完整的 Docker Compose 测试栈，确保测试代码能够真实验证接口的可部署性，解决数据库依赖和外部 API 密钥配置问题。

## 问题分析

### 当前痛点
1. **环境依赖复杂**：API 服务需要 PostgreSQL、Redis 以及多个外部 API 密钥（TUSHARE_TOKEN、INVESTODAY_API_KEY）
2. **测试不完整**：现有集成测试在数据库不可用时直接 `pytest.skip()`，无法验证真实场景
3. **环境不一致**：本地开发、CI/CD、生产环境配置分散，容易出错
4. **外部依赖不可控**：真实调用外部 API 成本高、速度慢、不稳定

### 核心目标
- ✅ 一键启动完整的测试环境
- ✅ 验证数据库迁移和真实集成
- ✅ 隔离测试环境，不污染开发环境
- ✅ 支持 CI/CD 自动化
- ✅ 外部 API 可控（Mock + 真实调用可选）

---

## 设计方案

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Compose Test Stack              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐     ┌─────────────┐    ┌───────────┐  │
│  │ PostgreSQL  │     │    Redis    │    │  Mock     │  │
│  │ (test_db)   │     │   (test)    │    │  Server   │  │
│  └──────┬──────┘     └──────┬──────┘    └─────┬─────┘  │
│         │                   │                 │         │
│         └───────────────────┴─────────────────┘         │
│                           │                              │
│                  ┌────────▼─────────┐                   │
│                  │  API Server      │                   │
│                  │  (with test      │                   │
│                  │   fixtures)      │                   │
│                  └────────┬─────────┘                   │
│                           │                              │
│                  ┌────────▼─────────┐                   │
│                  │   pytest         │                   │
│                  │   (with coverage)│                   │
│                  └──────────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. 测试专用 Docker Compose 配置

**文件**: `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  # 测试数据库
  test-db:
    image: postgres:15-alpine
    container_name: alpha-quant-test-db
    environment:
      - POSTGRES_DB=test_stock_market
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres_test
    ports:
      - "5433:5432"  # 避免与开发环境冲突
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - test-network

  # 测试 Redis
  test-redis:
    image: redis:7-alpine
    container_name: alpha-quant-test-redis
    ports:
      - "6380:6379"
    networks:
      - test-network

  # Mock API Server (用于外部 API Mock)
  mock-api:
    build:
      context: .
      dockerfile: tests/Dockerfile.mock
    container_name: alpha-quant-mock-api
    ports:
      - "9000:9000"
    networks:
      - test-network

  # API Server (测试模式)
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
      - TUSHARE_TOKEN=${TUSHARE_TOKEN:-mock_token}
      - INVESTODAY_API_KEY=${INVESTODAY_API_KEY:-mock_key}
      - API_KEY_SECRET=test_secret_key_123456
      - USE_MOCK_API=${USE_MOCK_API:-true}
      - MOCK_API_URL=http://mock-api:9000
    depends_on:
      test-db:
        condition: service_healthy
      test-redis:
        condition: service_started
    volumes:
      - ./logs/test:/app/logs
      - ./tests:/app/tests
    networks:
      - test-network

volumes:
  test-db-data:
  test-redis-data:

networks:
  test-network:
    driver: bridge
```

#### 2. 测试专用环境变量配置

**文件**: `.env.test.example` (提交到 git)
```bash
# 测试环境配置示例
# 复制为 .env.test 并填入真实值

# ========== 应用配置 ==========
APP_ENV=testing
DEBUG=true
TZ=Asia/Shanghai

# ========== 数据库配置 ==========
DATABASE_URL=postgresql://postgres:postgres_test@test-db:5432/test_stock_market

# ========== Redis配置 ==========
REDIS_URL=redis://test-redis:6379/0

# ========== API服务器配置 ==========
API_SERVER__HOST=0.0.0.0
API_SERVER__PORT=8000
API_SERVER__API_KEY_SECRET=test_secret_key_123456

# ========== 外部API配置 ==========
# 用于真实测试外部API时使用
TUSHARE_TOKEN=your_test_token_here
INVESTODAY_API_KEY=your_test_key_here

# ========== 测试配置 ==========
USE_MOCK_API=true
MOCK_API_URL=http://mock-api:9000

# ========== 限流配置 ==========
API_SERVER__RATE_LIMIT_FREE=1000
API_SERVER__RATE_LIMIT_STANDARD=10000
API_SERVER__RATE_LIMIT_PREMIUM=100000
```

**文件**: `.env.test` (添加到 `.gitignore`)
```
.env.test
.env.local
```

#### 3. Mock API Server

**文件**: `tests/Dockerfile.mock`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.test.txt .
RUN pip install --no-cache-dir -r requirements.test.txt

COPY tests/mock_api_server.py .

EXPOSE 9000

CMD ["python", "tests/mock_api_server.py"]
```

**文件**: `tests/mock_api_server.py`
```python
"""
Mock API Server for external dependencies
模拟外部 API 服务，用于测试
"""
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Mock 数据
MOCK_STOCK_DATA = {
    "600519": {
        "price": 1850.0,
        "volume": 10000,
        "change_pct": 1.5
    }
}

@app.route('/tushare/stock/basic', methods=['GET'])
def mock_tushare_basic():
    """Mock Tushare 基础数据接口"""
    code = request.args.get('ts_code')
    if code in MOCK_STOCK_DATA:
        return jsonify({
            "code": 0,
            "msg": "success",
            "data": MOCK_STOCK_DATA[code]
        })
    return jsonify({"code": -1, "msg": "not found"}), 404

@app.route('/investoday/stock/quote', methods=['GET'])
def mock_investoday_quote():
    """Mock Investoday 行情接口"""
    code = request.args.get('symbol')
    if code in MOCK_STOCK_DATA:
        return jsonify({
            "status": "success",
            "data": MOCK_STOCK_DATA[code]
        })
    return jsonify({"status": "error", "message": "not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
```

**文件**: `requirements.test.txt`
```bash
flask>=2.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.0.0
responses>=0.23.0
pytest-dotenv>=0.5.0
```

#### 4. 测试运行脚本

**文件**: `tests/run_test_suite.sh`
```bash
#!/bin/bash
set -e

echo "======================================"
echo "  Alpha Quant Trader Pro - 测试套件"
echo "======================================"

# 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
    echo "✗ Docker 未运行或未安装"
    exit 1
fi

# 检查 .env.test 文件
if [ ! -f .env.test ]; then
    if [ -f .env.test.example ]; then
        cp .env.test.example .env.test
        echo "⚠ 请编辑 .env.test 填入真实的 API 密钥"
    else
        echo "✗ 未找到 .env.test 或 .env.test.example"
        exit 1
    fi
fi

# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 等待服务健康
sleep 15

# 运行数据库迁移
docker-compose -f docker-compose.test.yml exec -T api-server-test alembic upgrade head

# 运行测试
docker-compose -f docker-compose.test.yml exec -T api-server-test \
    pytest tests/api_server/ \
        -v \
        --cov=api_server \
        --cov-report=term-missing \
        --cov-report=html \
        --junitxml=reports/test-results.xml

# 停止并清理
docker-compose -f docker-compose.test.yml down -v
```

#### 5. 测试配置文件

**文件**: `tests/conftest.py`
```python
"""
pytest 配置文件
全局 fixture 和配置
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from api_server.main import app
from common.database import Base, get_db

# 测试数据库 URL
TEST_DATABASE_URL = "postgresql://postgres:postgres_test@test-db:5432/test_stock_market"

# 创建测试数据库引擎
test_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def db_engine():
    """会话级别的数据库引擎"""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """函数级别的数据库 session（每个测试独立）"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session):
    """测试客户端，自动注入数据库 session"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
def clean_database(db_session):
    """每个测试前自动清理数据库"""
    # 获取所有表名
    result = db_session.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname='public' AND tablename NOT LIKE 'pg_%'
    """)
    tables = [row[0] for row in result]

    # 按依赖顺序删除数据
    for table in reversed(tables):
        try:
            db_session.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        except Exception:
            pass

    db_session.commit()
```

---

## 工作流程

### 本地开发测试流程

```mermaid
graph TD
    A[开发者运行测试] --> B{是否有 .env.test?}
    B -->|否| C[复制 .env.test.example 并配置]
    B -->|是| D[启动 Docker Compose 测试栈]
    C --> D
    D --> E[运行数据库迁移]
    E --> F[执行 pytest 测试]
    F --> G[生成覆盖率报告]
    G --> H[清理测试环境]
    H --> I{测试通过?}
    I -->|是| J[✅ 测试成功]
    I -->|否| K[❌ 查看失败原因]
```

### 命令行使用

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行迁移
docker-compose -f docker-compose.test.yml exec api-server-test alembic upgrade head

# 运行测试
docker-compose -f docker-compose.test.yml exec api-server-test pytest tests/api_server/ -v

# 停止环境
docker-compose -f docker-compose.test.yml down -v
```

---

## 外部 API 依赖处理策略

### 策略 1: 完全 Mock（推荐，用于快速迭代）

**优点**：
- ✅ 测试速度快（秒级）
- ✅ 不依赖外部网络
- ✅ 成本低（无需真实 API 调用）
- ✅ 可控性强（可以模拟各种场景）

### 策略 2: 混合模式（Mock + 真实调用）

**配置**：
```bash
# .env.test
USE_MOCK_API=false  # 设置为 false 使用真实 API
TUSHARE_TOKEN=your_real_test_token
INVESTODAY_API_KEY=your_real_test_key
```

### 策略 3: 真实调用（用于回归测试）

**使用场景**：
- 每周一次的回归测试
- 发布前的集成测试

---

## 测试分类

### 1. 单元测试（Unit Tests）

**标记**: `@pytest.mark.unit`

**特点**：
- 不依赖数据库
- 不调用外部 API
- 运行速度快（毫秒级）

### 2. 集成测试（Integration Tests）

**标记**: `@pytest.mark.integration`

**特点**：
- 使用测试数据库
- Mock 外部 API
- 验证数据库操作
- 运行速度中等（秒级）

### 3. 端到端测试（E2E Tests）

**标记**: `@pytest.mark.e2e`

**特点**：
- 完整的服务栈
- 可选真实外部 API
- 验证完整业务流程
- 运行速度慢（分钟级）

---

## 成功标准

### ✅ 功能性
- [ ] 所有测试用例通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] 数据库迁移正常
- [ ] 外部 API 调用可控

### ✅ 可用性
- [ ] 一键启动测试环境
- [ ] 测试运行时间 < 5 分钟
- [ ] 清晰的测试报告

---

## 下一步行动

1. **立即实施**：
   - [ ] 创建 `docker-compose.test.yml`
   - [ ] 创建 `.env.test.example`
   - [ ] 创建 `tests/run_test_suite.sh`
   - [ ] 创建 `tests/conftest.py`

2. **完善测试**：
   - [ ] 将现有测试标记为 `@pytest.mark.integration`
   - [ ] 添加数据库清理逻辑
   - [ ] 添加 Mock API 支持

3. **集成 CI/CD**：
   - [ ] 配置 GitHub Actions
   - [ ] 设置密钥管理
   - [ ] 配置覆盖率报告
