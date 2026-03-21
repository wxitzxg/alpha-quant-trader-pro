# 测试指南

## 快速开始

### 1. 准备测试环境

```bash
# 复制测试配置
cp .env.test.example .env.test

# （可选）编辑 .env.test 配置真实 API 密钥
# vim .env.test
```

### 2. 运行测试

```bash
# 一键运行所有测试（推荐）
./tests/run_test_suite.sh

# 或者手动控制
docker-compose -f docker-compose.test.yml up -d
docker-compose -f docker-compose.test.yml exec api-server-test pytest tests/api_server/ -v
docker-compose -f docker-compose.test.yml down -v
```

### 3. 查看结果

- **覆盖率报告**: `reports/coverage/index.html`
- **测试结果**: `reports/test-results.xml`
- **日志**: `logs/test/`

---

## 测试架构

### 环境依赖

- **Docker**: 容器化测试环境
- **PostgreSQL**: 测试数据库（端口 5433）
- **Redis**: 测试缓存（端口 6380）
- **Mock API Server**: 模拟外部 API（端口 9000）

### 配置文件

| 文件 | 说明 |
|------|------|
| `docker-compose.test.yml` | 测试专用 Docker Compose 配置 |
| `.env.test` | 测试环境变量（复制自 `.env.test.example`） |
| `tests/conftest.py` | pytest 配置和 fixtures |
| `tests/mock_api_server.py` | Flask Mock API 服务器 |
| `tests/run_test_suite.sh` | 一键测试脚本 |

---

## 测试策略

### 1. 完全 Mock 模式（默认）

**配置**:
```bash
# .env.test
USE_MOCK_API=true
TUSHARE_TOKEN=mock_token
INVESTODAY_API_KEY=mock_key
```

**特点**:
- ✅ 速度快（秒级）
- ✅ 不依赖外部网络
- ✅ 成本低（免费）
- ✅ 可控性强

**适用场景**:
- 日常开发
- 单元测试
- 集成测试

### 2. 混合模式

**配置**:
```bash
# .env.test
USE_MOCK_API=false
TUSHARE_TOKEN=your_real_test_token
INVESTODAY_API_KEY=your_real_test_key
```

**特点**:
- ⚡ 速度中等（分钟级）
- 💰 可能产生费用
- ✅ 验证真实 API 集成

**适用场景**:
- 回归测试
- 验证 Mock 准确性

### 3. 真实调用模式

**配置**:
```bash
# .env.test
USE_MOCK_API=false
# 填入真实 API 密钥
```

**特点**:
- ⏱️ 速度慢（可能受 API 限流影响）
- 💸 产生真实费用
- ✅ 100% 真实性

**适用场景**:
- 发布前最终验证
- 端到端测试

---

## 测试分类

### 单元测试 (`@pytest.mark.unit`)

- 不依赖数据库
- 不调用外部 API
- 运行速度快（毫秒级）

```python
@pytest.mark.unit
def test_calculation():
    result = calculate_something()
    assert result == expected
```

### 集成测试 (`@pytest.mark.integration`)

- 使用测试数据库
- Mock 外部 API
- 验证数据库操作

```python
@pytest.mark.integration
def test_create_account(test_client, db_session):
    response = test_client.post("/api/v1/account", json={...})
    assert response.status_code == 200
```

### 端到端测试 (`@pytest.mark.e2e`)

- 完整服务栈
- 可选真实外部 API
- 验证完整业务流程

```python
@pytest.mark.e2e
def test_complete_workflow(test_client):
    # 1. 创建账户
    # 2. 买入股票
    # 3. 卖出股票
    # 4. 验证收益
    pass
```

---

## 常用命令

### 基础命令

```bash
# 运行所有测试
./tests/run_test_suite.sh

# 运行单个测试文件
pytest tests/api_server/test_stock_market_router.py -v

# 运行特定测试函数
pytest tests/api_server/test_stock_market_router.py::test_get_stock_info -v

# 运行并查看输出
pytest tests/ -v -s

# 运行失败的测试
pytest tests/ --lf
```

### 测试分组

```bash
# 只运行单元测试
pytest tests/ -m "unit" -v

# 只运行集成测试
pytest tests/ -m "integration" -v

# 排除集成测试
pytest tests/ -m "not integration" -v
```

### 并行测试

```bash
# 自动检测 CPU 核心数并行
pytest tests/ -n auto -v
```

### 覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=api_server --cov-report=html

# 覆盖率要求
pytest tests/ --cov=api_server --cov-fail-under=80
```

---

## 调试技巧

### 查看日志

```bash
# 查看 API Server 日志
docker-compose -f docker-compose.test.yml logs api-server-test

# 实时查看
docker-compose -f docker-compose.test.yml logs -f api-server-test
```

### 进入容器调试

```bash
# 进入 API Server 容器
docker-compose -f docker-compose.test.yml exec api-server-test bash

# 进入数据库容器
docker-compose -f docker-compose.test.yml exec test-db psql -U postgres -d test_stock_market
```

### 数据库检查

```bash
# 连接测试数据库
docker-compose -f docker-compose.test.yml exec test-db \
    psql -U postgres -d test_stock_market

# 常用 SQL
\dt                          # 列出所有表
SELECT * FROM accounts;      # 查看账户数据
SELECT COUNT(*) FROM positions;  # 统计持仓数量
```

---

## Mock API 使用

### 默认 Mock 端点

| 端点 | 说明 |
|------|------|
| `GET /tushare/stock/basic` | Tushare 基础数据 |
| `GET /tushare/stock/kline` | Tushare K线数据 |
| `GET /investoday/stock/quote` | Investoday 行情 |
| `GET /investoday/stock/kline` | Investoday K线 |
| `GET /health` | 健康检查 |

### 测试 Mock API

```bash
# 启动 Mock API
docker-compose -f docker-compose.test.yml up -d mock-api

# 测试端点
curl http://localhost:9000/health
curl "http://localhost:9000/tushare/stock/basic?ts_code=600519.SH"
curl "http://localhost:9000/investoday/stock/quote?symbol=600519"
```

---

## CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_stock_market
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres_test
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements.test.txt

      - name: Run tests
        run: |
          pytest tests/api_server/ \
            -v \
            --cov=api_server \
            --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres_test@localhost:5432/test_stock_market

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 常见问题

### Q: 测试启动失败

**A**: 检查 Docker 是否运行：
```bash
docker info
```

### Q: 数据库连接失败

**A**: 检查数据库是否启动：
```bash
docker-compose -f docker-compose.test.yml ps
docker-compose -f docker-compose.test.yml logs test-db
```

### Q: 测试速度慢

**A**:
1. 使用 `-n auto` 并行测试
2. 跳过慢速测试: `-m "not slow"`
3. 使用完全 Mock 模式

---

## 最佳实践

1. ✅ **测试先行**: 新功能先写测试
2. ✅ **单元测试为主**: 80% 单元测试，20% 集成测试
3. ✅ **快速反馈**: 单元测试应该在秒级完成
4. ✅ **隔离测试**: 每个测试应该独立，不依赖其他测试
5. ✅ **清理数据**: 使用 `clean_database` fixture 确保数据隔离
6. ✅ **Mock 外部依赖**: 避免真实调用外部 API
7. ✅ **覆盖率要求**: 保持 80%+ 覆盖率
8. ✅ **定期回归**: 每周运行一次完整测试套件

---

## 文件结构

```
.
├── docker-compose.test.yml      # 测试专用 Docker Compose
├── .env.test.example            # 测试环境配置模板
├── requirements.test.txt        # 测试依赖
├── tests/
│   ├── Dockerfile.mock          # Mock API 镜像
│   ├── Dockerfile.test          # 测试镜像
│   ├── conftest.py              # pytest 配置
│   ├── mock_api_server.py       # Mock API 服务器
│   ├── run_test_suite.sh        # 一键测试脚本
│   ├── api_server/              # API 测试
│   │   └── test_*.py            # 测试文件
│   └── ...
└── reports/                     # 测试报告（.gitignore）
    ├── coverage/                # 覆盖率报告
    └── test-results.xml         # JUnit 测试结果
```
