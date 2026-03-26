# E2E 测试重构设计文档

## 概述

重构测试架构，删除所有现有测试文件，建立基于 Docker 真实环境的端到端测试体系。

## 目标

- 使用真实 HTTP 请求调用 Docker 中的 API Server
- 按业务流程顺序执行测试
- 覆盖所有 API 端点
- 使用真实数据源 API Key

## 测试股票

| 代码 | 名称 |
|------|------|
| 600011 | 华能国际 |
| 601611 | 中国核建 |

## 架构设计

### 目录结构

```
tests/e2e/
├── __init__.py
├── conftest.py              # pytest fixtures
├── config.py                # 测试配置
├── run_e2e_tests.py         # 运行脚本
├── test_01_health.py        # 健康检查
├── test_02_stock_sync.py    # 股票同步
├── test_03_data_source.py   # 数据查询
├── test_04_analysis.py      # 技术分析
├── test_05_portfolio.py     # 持仓管理
├── test_06_backtest.py      # 回测系统
├── test_07_simulation.py    # 模拟交易
└── test_08_other_routers.py # 其他路由
```

### 测试流程

```
1. 健康检查
   └─ GET /health, GET /api/v1/health

2. 股票同步
   └─ POST /api/v1/market/stock/sync
   └─ GET /api/v1/market/stock/sync-status

3. 数据查询
   └─ GET /api/v1/stock/list
   └─ GET /api/v1/stock/info/{stock_code}
   └─ GET /api/v1/quote/realtime/{stock_code}
   └─ POST /api/v1/quote/batch
   └─ GET /api/v1/kline/{stock_code}
   └─ GET /api/v1/kline/stats/{stock_code}

4. 技术分析
   └─ POST /api/v1/analysis/five-dimension
   └─ GET /api/v1/analysis/strategies/{stock_code}
   └─ GET /api/v1/analysis/indicator/{stock_code}
   └─ GET /api/v1/analysis/report/{stock_code}
   └─ GET /api/v1/analysis/strategy/vcp/{stock_code}
   └─ GET /api/v1/analysis/strategy/td/{stock_code}
   └─ GET /api/v1/analysis/strategy/divergence/{stock_code}

5. 持仓管理
   └─ GET /api/v1/portfolio/account/summary
   └─ GET /api/v1/portfolio/positions
   └─ POST /api/v1/portfolio/trade/buy
   └─ POST /api/v1/portfolio/trade/sell
   └─ GET /api/v1/portfolio/transactions
   └─ POST /api/v1/portfolio/favorites/add
   └─ GET /api/v1/portfolio/favorites
   └─ POST /api/v1/portfolio/favorites/remove

6. 回测系统
   └─ POST /api/v1/backtest/single
   └─ POST /api/v1/backtest/portfolio
   └─ POST /api/v1/backtest/compare
   └─ GET /api/v1/backtest/result/{task_id}

7. 模拟交易
   └─ 模拟交易相关端点

8. 其他路由
   └─ 资金流向、新闻、财务数据等
```

### 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| HTTP 客户端 | httpx | 支持 async，API 简洁 |
| 测试框架 | pytest | 文件名排序确保执行顺序 |
| 断言方式 | assert | 直接断言响应状态码和数据结构 |

### 配置设计

```python
# config.py
E2E_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "timeout": 30.0,
    "test_stocks": ["600011", "601611"],
    "default_stock": "600011",
}
```

### conftest.py 设计

```python
import pytest
import httpx

@pytest.fixture(scope="session")
def api_base_url():
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def client(api_base_url):
    with httpx.Client(base_url=api_base_url, timeout=30.0) as c:
        yield c
```

## 删除范围

删除 `tests/` 目录下所有现有文件，仅保留新创建的 `tests/e2e/` 目录：

- `tests/adapters/` - 删除
- `tests/api_server/` - 删除
- `tests/backtest/` - 删除
- `tests/common/` - 删除
- `tests/portfolio_manager/` - 删除
- `tests/stock_market/` - 删除
- `tests/mock_api_server.py` - 删除
- `tests/run_tests.py` - 删除

## 运行脚本设计

```bash
# 启动并运行测试
python tests/e2e/run_e2e_tests.py

# 仅运行测试（假设服务已启动）
python tests/e2e/run_e2e_tests.py --skip-setup

# 查看状态
python tests/e2e/run_e2e_tests.py --status
```

## 实施步骤

1. 删除旧测试文件
2. 创建 `tests/e2e/` 目录结构
3. 实现 `conftest.py` 和 `config.py`
4. 按顺序实现各测试文件
5. 实现运行脚本
6. 验证测试通过
