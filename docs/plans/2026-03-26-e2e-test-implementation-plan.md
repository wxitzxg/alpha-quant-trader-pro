# E2E 测试重构实施计划

## 概述

基于设计文档 `docs/superpowers/specs/2026-03-26-e2e-test-refactor-design.md`，实施 E2E 测试重构。

## 任务列表

### 阶段 1: 清理旧测试文件

**任务 1.1: 删除旧测试目录和文件**

删除以下内容：
- `tests/adapters/` 目录
- `tests/api_server/` 目录
- `tests/backtest/` 目录
- `tests/common/` 目录
- `tests/portfolio_manager/` 目录
- `tests/stock_market/` 目录
- `tests/mock_api_server.py`
- `tests/run_tests.py`
- `tests/__init__.py`

命令：
```bash
rm -rf tests/adapters tests/api_server tests/backtest tests/common tests/portfolio_manager tests/stock_market
rm -f tests/mock_api_server.py tests/run_tests.py tests/__init__.py
```

---

### 阶段 2: 创建基础设施

**任务 2.1: 创建目录结构**

```bash
mkdir -p tests/e2e
```

**任务 2.2: 创建 `tests/e2e/__init__.py`**

空文件，标记为 Python 包。

**任务 2.3: 创建 `tests/e2e/config.py`**

```python
"""E2E 测试配置"""
E2E_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "timeout": 30.0,
    "test_stocks": ["600011", "601611"],
    "default_stock": "600011",
}
```

**任务 2.4: 创建 `tests/e2e/conftest.py`**

```python
"""E2E 测试 pytest fixtures"""
import pytest
import httpx
from .config import E2E_CONFIG

@pytest.fixture(scope="session")
def api_base_url():
    return E2E_CONFIG["api_base_url"]

@pytest.fixture(scope="session")
def client(api_base_url):
    with httpx.Client(base_url=api_base_url, timeout=E2E_CONFIG["timeout"]) as c:
        yield c

@pytest.fixture(scope="session")
def test_stocks():
    return E2E_CONFIG["test_stocks"]

@pytest.fixture(scope="session")
def default_stock():
    return E2E_CONFIG["default_stock"]
```

---

### 阶段 3: 实现测试文件（按顺序）

**任务 3.1: `tests/e2e/test_01_health.py`**

测试端点：
- `GET /health`
- `GET /api/v1/health`

验证：状态码 200，返回 `success: true`

**任务 3.2: `tests/e2e/test_02_stock_sync.py`**

测试端点：
- `POST /api/v1/market/stock/sync` - 同步股票列表
- `GET /api/v1/market/stock/sync-status` - 获取同步状态
- `POST /api/v1/market/kline/sync/{stock_code}` - 同步 K 线（使用测试股票）

验证：同步成功返回 `success: true`

**任务 3.3: `tests/e2e/test_03_data_source.py`**

测试端点：
- `GET /api/v1/stock/list` - 股票列表
- `GET /api/v1/stock/info/{stock_code}` - 股票详情
- `GET /api/v1/quote/realtime/{stock_code}` - 实时行情
- `POST /api/v1/quote/batch` - 批量行情
- `GET /api/v1/kline/{stock_code}` - K 线数据
- `GET /api/v1/kline/stats/{stock_code}` - K 线统计
- `GET /api/v1/financial/indicators/{stock_code}` - 财务指标

验证：数据结构正确，包含必要字段

**任务 3.4: `tests/e2e/test_04_analysis.py`**

测试端点：
- `POST /api/v1/analysis/five-dimension` - 五维共振分析
- `GET /api/v1/analysis/strategies/{stock_code}` - 策略分析
- `GET /api/v1/analysis/indicator/{stock_code}` - 技术指标
- `GET /api/v1/analysis/report/{stock_code}` - 分析报告
- `GET /api/v1/analysis/strategy/vcp/{stock_code}` - VCP 策略
- `GET /api/v1/analysis/strategy/td/{stock_code}` - 九转策略
- `GET /api/v1/analysis/strategy/divergence/{stock_code}` - 背离策略

验证：分析结果包含预期字段

**任务 3.5: `tests/e2e/test_05_portfolio.py`**

测试端点：
- `GET /api/v1/portfolio/account/summary` - 账户汇总
- `GET /api/v1/portfolio/positions` - 持仓列表
- `GET /api/v1/portfolio/account/cash` - 现金余额
- `POST /api/v1/portfolio/account/cash/add` - 充值
- `POST /api/v1/portfolio/trade/buy` - 买入
- `GET /api/v1/portfolio/positions/{stock_code}` - 持仓详情
- `POST /api/v1/portfolio/trade/sell` - 卖出
- `GET /api/v1/portfolio/transactions` - 交易历史
- `POST /api/v1/portfolio/favorites/add` - 添加收藏
- `GET /api/v1/portfolio/favorites` - 收藏列表
- `POST /api/v1/portfolio/favorites/remove` - 移除收藏

验证：交易流程正确，数据一致性

**任务 3.6: `tests/e2e/test_06_backtest.py`**

测试端点：
- `POST /api/v1/backtest/single` - 单股回测
- `POST /api/v1/backtest/portfolio` - 组合回测
- `POST /api/v1/backtest/compare` - 策略比较
- `GET /api/v1/backtest/result/{task_id}` - 回测结果

验证：回测结果包含绩效指标

**任务 3.7: `tests/e2e/test_07_simulation.py`**

测试端点：
- `POST /api/v1/simulation/account` - 创建账户
- `GET /api/v1/simulation/accounts` - 账户列表
- `GET /api/v1/simulation/account/{account_id}` - 账户详情
- `POST /api/v1/simulation/buy` - 买入
- `GET /api/v1/simulation/positions/{account_id}` - 持仓
- `POST /api/v1/simulation/sell` - 卖出
- `GET /api/v1/simulation/trades/{account_id}` - 交易历史
- `DELETE /api/v1/simulation/account/{account_id}` - 删除账户

验证：模拟交易流程完整

**任务 3.8: `tests/e2e/test_08_other_routers.py`**

测试端点：
- `GET /api/v1/fundflow/{stock_code}` - 资金流向
- `GET /api/v1/fundflow/dragon-tiger/{stock_code}` - 龙虎榜
- `GET /api/v1/news/list` - 新闻列表
- `GET /api/v1/news/search` - 新闻搜索
- `GET /api/v1/financial/indicators/{stock_code}` - 财务指标

验证：返回数据结构正确

---

### 阶段 4: 运行脚本

**任务 4.1: 创建 `tests/e2e/run_e2e_tests.py`**

功能：
- `--setup` - 检查 Docker 服务状态
- `--run` - 运行测试（默认）
- `--status` - 显示服务状态
- `--skip-setup` - 跳过环境检查
- `-v` - 详细输出
- `-k` - 过滤测试

---

### 阶段 5: 验证

**任务 5.1: 安装依赖**

确保 `httpx` 已安装：
```bash
pip install httpx
```

**任务 5.2: 启动 Docker 服务**

```bash
docker compose up -d
```

**任务 5.3: 运行测试**

```bash
python tests/e2e/run_e2e_tests.py
```

**任务 5.4: 验证所有测试通过**

确认 pytest 输出显示所有测试通过。

---

## 文件清单

| 文件路径 | 操作 |
|---------|------|
| `tests/adapters/` | 删除 |
| `tests/api_server/` | 删除 |
| `tests/backtest/` | 删除 |
| `tests/common/` | 删除 |
| `tests/portfolio_manager/` | 删除 |
| `tests/stock_market/` | 删除 |
| `tests/mock_api_server.py` | 删除 |
| `tests/run_tests.py` | 删除 |
| `tests/e2e/__init__.py` | 创建 |
| `tests/e2e/config.py` | 创建 |
| `tests/e2e/conftest.py` | 创建 |
| `tests/e2e/test_01_health.py` | 创建 |
| `tests/e2e/test_02_stock_sync.py` | 创建 |
| `tests/e2e/test_03_data_source.py` | 创建 |
| `tests/e2e/test_04_analysis.py` | 创建 |
| `tests/e2e/test_05_portfolio.py` | 创建 |
| `tests/e2e/test_06_backtest.py` | 创建 |
| `tests/e2e/test_07_simulation.py` | 创建 |
| `tests/e2e/test_08_other_routers.py` | 创建 |
| `tests/e2e/run_e2e_tests.py` | 创建 |

---

## 执行顺序

1. 阶段 1 → 2. 阶段 2 → 3. 阶段 3（按 3.1-3.8 顺序）→ 4. 阶段 4 → 5. 阶段 5
