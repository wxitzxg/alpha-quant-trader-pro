# Docker Compose 测试栈实施计划

## 日期
2026-03-20

## 目标
为 `api_server` 模块构建完整的 Docker Compose 测试栈，确保测试代码能够真实验证接口的可部署性，解决数据库依赖和外部 API 密钥配置问题。

---

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

## 选定方案

**方案一 + 方案三的混合**：完整的 Docker Compose 测试栈 + 分层测试策略

**外部 API 策略**：完全 Mock 模式（默认）+ 混合模式（可选）

---

## 实施步骤

### 阶段 1：基础设施文件（8 个文件）

#### 1.1 测试专用 Docker Compose 配置
**文件**: `docker-compose.test.yml`

**内容**:
```yaml
version: '3.8'

services:
  test-db:
    image: postgres:15-alpine
    container_name: alpha-quant-test-db
    environment:
      - POSTGRES_DB=test_stock_market
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres_test
    ports:
      - "5433:5432"
    volumes:
      - test-db-data:/var/lib/postgresql/data
    healthcheck: ...
    networks:
      - test-network

  test-redis:
    image: redis:7-alpine
    container_name: alpha-quant-test-redis
    ports:
      - "6380:6379"
    volumes:
      - test-redis-data:/data
    networks:
      - test-network

  mock-api:
    build:
      context: .
      dockerfile: tests/Dockerfile.mock
    container_name: alpha-quant-mock-api
    ports:
      - "9000:9000"
    networks:
      - test-network

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

#### 1.2 测试环境配置模板
**文件**: `.env.test.example`

**内容**:
```bash
# 测试环境配置示例

APP_ENV=testing
DEBUG=true
TZ=Asia/Shanghai

DATABASE_URL=postgresql://postgres:postgres_test@test-db:5432/test_stock_market
REDIS_URL=redis://test-redis:6379/0

API_SERVER__HOST=0.0.0.0
API_SERVER__PORT=8000
API_SERVER__API_KEY_SECRET=test_secret_key_123456

TUSHARE_TOKEN=mock_token
INVESTODAY_API_KEY=mock_key

USE_MOCK_API=true
MOCK_API_URL=http://mock-api:9000

API_SERVER__RATE_LIMIT_FREE=1000
API_SERVER__RATE_LIMIT_STANDARD=10000
API_SERVER__RATE_LIMIT_PREMIUM=100000
```

#### 1.3 测试专用依赖
**文件**: `requirements.test.txt`

**内容**:
```txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.0.0
pytest-dotenv>=0.5.0
responses>=0.23.0
pytest-xdist>=3.0.0
flask>=2.0.0
```

#### 1.4 Mock API Server 镜像
**文件**: `tests/Dockerfile.mock`

**内容**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.test.txt .
RUN pip install --no-cache-dir -r requirements.test.txt

COPY tests/mock_api_server.py .

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

CMD ["python", "mock_api_server.py"]
```

#### 1.5 测试专用 API Server 镜像
**文件**: `tests/Dockerfile.test`

**内容**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY requirements.test.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements.test.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN mkdir -p /app/logs/test

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["tail", "-f", "/dev/null"]
```

#### 1.6 Mock API Server
**文件**: `tests/mock_api_server.py`

**功能**:
- Flask 服务器，端口 9000
- 支持 Tushare Mock 端点:
  - `GET /tushare/stock/basic`
  - `GET /tushare/stock/kline`
- 支持 Investoday Mock 端点:
  - `GET /investoday/stock/quote`
  - `GET /investoday/stock/kline`
- 健康检查: `GET /health`
- 统计信息: `GET /stats`
- 内置贵州茅台、平安银行等 Mock 数据

#### 1.7 pytest 配置
**文件**: `tests/conftest.py`

**功能**:
- `db_engine`: 会话级数据库引擎（整个测试套件共享）
- `db_session`: 函数级数据库 session（每个测试独立）
- `test_client`: FastAPI 测试客户端（自动注入 db session）
- `clean_database`: 每个测试前自动清理数据库（TRUNCATE 所有表）
- `mock_tushare_api`: Mock Tushare API fixture
- `mock_investoday_api`: Mock Investoday API fixture
- `mock_all_external_apis`: 同时 Mock 所有外部 API
- 自动标记未标记的测试为 `integration`

#### 1.8 一键测试脚本
**文件**: `tests/run_test_suite.sh`

**功能**:
1. 检查 Docker 环境
2. 检查 `.env.test` 配置
3. 清理旧容器
4. 启动测试环境
5. 等待服务健康
6. 运行数据库迁移
7. 执行 pytest 并行测试
8. 生成覆盖率报告
9. 自动清理环境
10. 显示测试结果和报告路径

---

### 阶段 2：文档文件（2 个文件）

#### 2.1 设计文档
**文件**: `docs/superpowers/specs/2026-03-20-docker-compose-test-stack-design.md`

**内容**:
- 问题分析
- 架构设计（图表）
- 核心组件详细说明
- 工作流程
- 外部 API 依赖处理策略（3 种模式对比）
- 测试分类（单元/集成/E2E）
- 性能优化
- 安全考虑
- 监控和调试
- 维护指南
- 成功标准
- 下一步行动

#### 2.2 使用指南
**文件**: `TESTING_GUIDE.md`

**内容**:
- 快速开始（3 步）
- 测试架构说明
- 测试策略详解（完全 Mock/混合/真实调用）
- 测试分类和标记
- 常用命令（基础/分组/并行/覆盖率）
- 调试技巧（日志/容器/数据库）
- Mock API 使用方法
- CI/CD 集成示例（GitHub Actions）
- 常见问题解答
- 最佳实践建议
- 文件结构说明

---

## 更新的配置文件

### 3.1 .gitignore
**添加内容**:
```gitignore
# 测试相关
.env.test
reports/
logs/test/
```

---

## 预期结果

### 1. 文件清单
创建以下 11 个文件：
- [ ] `docker-compose.test.yml`
- [ ] `.env.test.example`
- [ ] `requirements.test.txt`
- [ ] `tests/Dockerfile.mock`
- [ ] `tests/Dockerfile.test`
- [ ] `tests/mock_api_server.py`
- [ ] `tests/conftest.py`
- [ ] `tests/run_test_suite.sh`
- [ ] `docs/superpowers/specs/2026-03-20-docker-compose-test-stack-design.md`
- [ ] `TESTING_GUIDE.md`
- [ ] `.gitignore` (更新)

### 2. 功能验证
- [ ] `docker-compose -f docker-compose.test.yml up -d` 正常启动
- [ ] `./tests/run_test_suite.sh` 成功运行测试
- [ ] 生成覆盖率报告到 `reports/coverage/`
- [ ] Mock API 正常响应
- [ ] 数据库自动迁移和清理

### 3. 使用流程
```bash
# 1. 复制配置
cp .env.test.example .env.test

# 2. 运行测试
./tests/run_test_suite.sh

# 3. 查看报告
open reports/coverage/index.html
```

---

## 时间估算

- **基础设施文件**: 30 分钟
- **文档文件**: 20 分钟
- **测试验证**: 10 分钟
- **总计**: 约 60 分钟

---

## 风险和注意事项

1. **Docker 环境要求**: 用户需要安装 Docker 和 Docker Compose
2. **磁盘空间**: 首次运行需要拉取镜像（约 1-2GB）
3. **端口冲突**: 确保 5433、6380、8001、9000 端口未被占用
4. **配置文件**: `.env.test` 需要用户手动复制和配置
5. **数据库迁移**: 如果项目没有使用 Alembic，需要调整脚本

---

## 后续优化

1. **CI/CD 集成**: 配置 GitHub Actions 自动运行测试
2. **测试覆盖率**: 添加覆盖率门槛（如 80%）
3. **性能优化**: 添加测试缓存、增量测试
4. **监控集成**: 集成测试报告到项目看板
5. **文档完善**: 添加视频教程、常见问题库
