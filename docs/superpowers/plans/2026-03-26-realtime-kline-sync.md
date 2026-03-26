# 实时行情同步K线接口实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个API接口，从实时行情批量获取多只股票当日OHLC数据并同步到K线历史数据表。

**Architecture:** 扩展 Quote 模型增加 OHLC 字段，复用现有 SinaAdapter 实时行情接口，通过 KLineService 新增方法将实时行情转换为 KLine 记录并覆盖更新数据库。

**Tech Stack:** Python 3.x, FastAPI, Pydantic, SQLAlchemy

---

## File Structure

| 文件 | 职责 |
|------|------|
| `data_sources/models.py` | Pydantic 模型，定义 Quote 的 OHLC 字段（已完成） |
| `data_sources/adapters/sina_adapter.py` | 数据源适配器，解析新浪接口返回的 OHLC 数据 |
| `api_server/models/stock_market.py` | 请求/响应模型和错误码枚举 |
| `api_server/routers/stock_market.py` | API 路由定义 |
| `api_server/services/stock_market_service.py` | 服务层入口，协调数据源和 KLineService |
| `stock_market/services/kline_service.py` | K线同步核心逻辑 |
| `tests/api_server/test_realtime_kline_sync.py` | API 路由测试 |

---

### Task 1: 扩展 Quote 模型（已完成）

**Status:** 已在 `data_sources/models.py` 中完成 OHLC 字段添加。

- [x] Quote 模型已包含 `open_price`、`high`、`low` 字段

---

### Task 2: 新增错误码枚举和请求/响应模型（TDD：先定义接口契约）

**Files:**
- Modify: `api_server/models/stock_market.py`

- [ ] **Step 1: 添加必要的导入和错误码枚举**

在文件开头添加 `Enum` 导入，并在文件末尾添加新模型：

```python
from enum import Enum

# ... 现有代码 ...

class RealtimeSyncErrorCode(str, Enum):
    """实时同步错误码"""
    STOCK_NOT_FOUND = "stock_not_found"      # 股票代码不存在
    DATA_SOURCE_ERROR = "data_source_error"  # 数据源不可用
    NO_OHLC_DATA = "no_ohlc_data"           # 数据源不支持OHLC
    DB_ERROR = "db_error"                    # 数据库写入失败
    INVALID_PARAMS = "invalid_params"        # 参数校验失败


class RealtimeKLineSyncParams(BaseModel):
    """实时K线同步请求参数"""
    stock_codes: List[str] = Field(
        ...,
        description="股票代码列表，纯代码格式如 ['600519', '000001']",
        min_length=1,
        max_length=100
    )
    interval: str = Field(
        default="1d",
        description="周期，仅支持 1d（日线）"
    )


class RealtimeKLineSyncDetail(BaseModel):
    """单只股票同步结果"""
    symbol: str
    status: str  # "updated" | "failed" | "skipped"
    reason: Optional[RealtimeSyncErrorCode] = None


class RealtimeKLineSyncData(BaseModel):
    """实时K线同步响应数据"""
    total_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    details: List[RealtimeKLineSyncDetail]
```

- [ ] **Step 2: 验证模型定义正确**

Run: `python -c "from api_server.models.stock_market import RealtimeKLineSyncParams, RealtimeKLineSyncData; print('OK')"`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add api_server/models/stock_market.py
git commit -m "feat: 新增实时K线同步请求/响应模型和错误码"
```

---

### Task 3: 编写 API 测试（TDD：先写失败的测试）

**Files:**
- Create: `tests/api_server/test_realtime_kline_sync.py`

- [ ] **Step 1: 创建测试文件**

```python
#!/usr/bin/env python3
"""实时K线同步接口测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api_server.main import app

client = TestClient(app)


class TestRealtimeKLineSync:
    """实时K线同步接口测试"""

    def test_sync_realtime_kline_single_stock(self):
        """测试单只股票同步成功"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 1,
                "failed_count": 0,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 1
        assert data["data"]["success_count"] == 1

    def test_sync_realtime_kline_multiple_stocks(self):
        """测试多只股票批量同步"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 2,
                "success_count": 2,
                "failed_count": 0,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None},
                    {"symbol": "000001", "status": "updated", "reason": None}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_count"] == 2
        assert data["data"]["success_count"] == 2

    def test_sync_realtime_kline_empty_list(self):
        """测试空列表返回422错误"""
        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": [], "interval": "1d"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_sync_realtime_kline_invalid_interval(self):
        """测试无效interval返回400错误"""
        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": ["600519"], "interval": "1w"}
        )

        assert response.status_code == 400

    def test_sync_realtime_kline_partial_failure(self):
        """测试部分失败响应"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 3,
                "success_count": 2,
                "failed_count": 1,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "updated", "reason": None},
                    {"symbol": "000001", "status": "updated", "reason": None},
                    {"symbol": "999999", "status": "failed", "reason": "stock_not_found"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001", "999999"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["failed_count"] == 1
        assert data["data"]["success_count"] == 2

    def test_sync_realtime_kline_max_limit(self):
        """测试超过100只返回422错误"""
        stock_codes = [f"600{i:03d}" for i in range(101)]

        response = client.post(
            "/market/kline/sync-realtime",
            json={"stock_codes": stock_codes, "interval": "1d"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_sync_realtime_kline_data_source_error(self):
        """测试数据源不可用"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 2,
                "success_count": 0,
                "failed_count": 2,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "failed", "reason": "data_source_error"},
                    {"symbol": "000001", "status": "failed", "reason": "data_source_error"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519", "000001"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["failed_count"] == 2
        assert data["data"]["details"][0]["reason"] == "data_source_error"

    def test_sync_realtime_kline_db_error(self):
        """测试数据库写入失败"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 0,
                "failed_count": 1,
                "skipped_count": 0,
                "details": [
                    {"symbol": "600519", "status": "failed", "reason": "db_error"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["details"][0]["reason"] == "db_error"

    def test_sync_realtime_kline_no_ohlc_data(self):
        """测试数据源不支持OHLC时跳过"""
        mock_result = {
            "success": True,
            "data": {
                "total_count": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 1,
                "details": [
                    {"symbol": "600519", "status": "skipped", "reason": "no_ohlc_data"}
                ]
            }
        }

        with patch('api_server.routers.stock_market.service.sync_realtime_to_kline') as mock_sync:
            mock_sync.return_value = mock_result

            response = client.post(
                "/market/kline/sync-realtime",
                json={"stock_codes": ["600519"], "interval": "1d"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["skipped_count"] == 1
        assert data["data"]["details"][0]["reason"] == "no_ohlc_data"
```

- [ ] **Step 2: 运行测试确认失败（TDD RED 阶段）**

Run: `python -m pytest tests/api_server/test_realtime_kline_sync.py -v 2>&1 | head -20`
Expected: 测试失败，提示路由不存在

- [ ] **Step 3: 提交测试文件**

```bash
git add tests/api_server/test_realtime_kline_sync.py
git commit -m "test: 新增实时K线同步接口测试（TDD RED）"
```

---

### Task 4: 修改 SinaAdapter 解析 OHLC 字段

**Files:**
- Modify: `data_sources/adapters/sina_adapter.py`

- [ ] **Step 1: 修改 get_realtime 方法传入 OHLC 字段**

找到 `return Quote(` 所在位置（约第137行），修改为：

```python
            return Quote(
                symbol=symbol,
                price=current,
                open_price=open_price,  # 新增
                high=high,              # 新增
                low=low,                # 新增
                change=change,
                percent=percent,
                volume=volume,
                amount=0.0,  # 新浪不直接提供成交额
                bid_price=bid_prices,
                bid_volume=bid_volumes,
                ask_price=ask_prices,
                ask_volume=ask_volumes,
                timestamp=datetime.now()
            )
```

- [ ] **Step 2: 修改 batch_get_realtime 方法传入 OHLC 字段**

找到 `quote = Quote(` 所在位置（约第191行），在前面添加 OHLC 解析：

```python
                # 解析 OHLC
                open_price = float(values[1]) if values[1] else 0.0
                current = float(values[3]) if values[3] else 0.0
                high = float(values[4]) if values[4] else 0.0
                low = float(values[5]) if values[5] else 0.0

                quote = Quote(
                    symbol=symbol,
                    price=current,
                    open_price=open_price,  # 新增
                    high=high,              # 新增
                    low=low,                # 新增
                    change=change,
                    percent=percent,
                    volume=int(values[8]) if values[8] else 0,
                    amount=0.0,
                    bid_price=[],
                    bid_volume=[],
                    ask_price=[],
                    ask_volume=[],
                    timestamp=datetime.now()
                )
```

- [ ] **Step 3: 验证修改无语法错误**

Run: `python -c "from data_sources.adapters.sina_adapter import SinaAdapter; print('OK')"`
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
git add data_sources/adapters/sina_adapter.py
git commit -m "feat: SinaAdapter 解析并传入 OHLC 字段"
```

---

### Task 5: 新增 sync_realtime_to_kline 服务方法

**Files:**
- Modify: `stock_market/services/kline_service.py`

- [ ] **Step 1: 添加必要的类型导入**

在文件顶部修改 `typing` 导入：

```python
from typing import List, Optional, Tuple, Dict, Any
```

- [ ] **Step 2: 在 KLineService 类中添加 sync_realtime_to_kline 方法**

在文件末尾添加新方法（注意：类已有 `@handle_exceptions` 装饰器，新方法自动继承异常处理）：

```python
    def sync_realtime_to_kline(
        self,
        symbols: List[str],
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        从实时行情同步今日K线

        Args:
            symbols: 股票代码列表
            interval: 周期（仅支持 1d）

        Returns:
            {
                "total_count": 10,
                "success_count": 8,
                "failed_count": 2,
                "skipped_count": 0,
                "details": [...]
            }
        """
        # 事务策略：每只股票独立提交，失败不影响其他股票
        from data_sources import DataSourceAggregator

        logger.info(f"Starting realtime to kline sync for {len(symbols)} symbols")

        aggregator = DataSourceAggregator()

        # 批量获取实时行情
        try:
            quotes = aggregator.batch_get_realtime(symbols)
        except Exception as e:
            logger.error(f"Failed to get realtime quotes: {e}")
            return {
                "total_count": len(symbols),
                "success_count": 0,
                "failed_count": len(symbols),
                "skipped_count": 0,
                "details": [
                    {"symbol": s, "status": "failed", "reason": "data_source_error"}
                    for s in symbols
                ]
            }

        today = date.today()
        details = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        # 用于记录哪些 symbol 在 quotes 中
        quote_symbols = {q.symbol for q in quotes}

        # 处理未返回行情的股票
        for symbol in symbols:
            if symbol not in quote_symbols:
                details.append({
                    "symbol": symbol,
                    "status": "failed",
                    "reason": "data_source_error"
                })
                failed_count += 1

        # 处理返回的行情
        for quote in quotes:
            # 检查 OHLC 数据是否完整
            if not quote.open_price or not quote.high or not quote.low:
                logger.warning(f"Quote for {quote.symbol} missing OHLC data")
                details.append({
                    "symbol": quote.symbol,
                    "status": "skipped",
                    "reason": "no_ohlc_data"
                })
                skipped_count += 1
                continue

            try:
                # 获取 stock_id
                stock = self.stock_repo.get_by_symbol(quote.symbol)
                if not stock:
                    logger.warning(f"Stock {quote.symbol} not found in database")
                    details.append({
                        "symbol": quote.symbol,
                        "status": "failed",
                        "reason": "stock_not_found"
                    })
                    failed_count += 1
                    continue

                # 查询当日K线是否存在
                existing = self.repo.get_by_symbol_and_date(
                    symbol=quote.symbol,
                    interval=interval,
                    start_date=today.strftime("%Y-%m-%d"),
                    end_date=today.strftime("%Y-%m-%d")
                )

                if existing and len(existing) > 0:
                    # 覆盖更新
                    kline = existing[0]
                    kline.open = quote.open_price
                    kline.high = quote.high
                    kline.low = quote.low
                    kline.close = quote.price
                    kline.volume = quote.volume
                    kline.amount = quote.amount
                    kline.sync_time = datetime.now()
                    logger.debug(f"Updated kline: {quote.symbol} {today}")
                else:
                    # 新增
                    kline = KLine(
                        stock_id=stock.id,
                        symbol=quote.symbol,
                        date=today,
                        interval=interval,
                        open=quote.open_price,
                        high=quote.high,
                        low=quote.low,
                        close=quote.price,
                        volume=quote.volume,
                        amount=quote.amount,
                        source="realtime",
                        sync_time=datetime.now()
                    )
                    self.repo.add(kline)
                    logger.debug(f"Added kline: {quote.symbol} {today}")

                # 提交单只股票的事务
                self.repo.session.commit()
                success_count += 1
                details.append({
                    "symbol": quote.symbol,
                    "status": "updated",
                    "reason": None
                })

            except Exception as e:
                logger.error(f"Failed to sync kline for {quote.symbol}: {e}")
                self.repo.session.rollback()
                details.append({
                    "symbol": quote.symbol,
                    "status": "failed",
                    "reason": "db_error"
                })
                failed_count += 1

        logger.info(
            f"Realtime sync completed: total={len(symbols)}, "
            f"success={success_count}, failed={failed_count}, skipped={skipped_count}"
        )

        return {
            "total_count": len(symbols),
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "details": details
        }
```

- [ ] **Step 3: 验证语法正确**

Run: `python -c "from stock_market.services.kline_service import KLineService; print('OK')"`
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
git add stock_market/services/kline_service.py
git commit -m "feat: KLineService 新增 sync_realtime_to_kline 方法"
```

---

### Task 6: 在 StockMarketService 中添加接口方法

**Files:**
- Modify: `api_server/services/stock_market_service.py`

- [ ] **Step 1: 添加 sync_realtime_to_kline 方法**

在 `StockMarketService` 类末尾添加：

```python
    def sync_realtime_to_kline(
        self,
        stock_codes: List[str],
        interval: str = "1d"
    ) -> Dict:
        """
        从实时行情同步今日K线

        Args:
            stock_codes: 股票代码列表
            interval: 周期

        Returns:
            同步结果
        """
        try:
            session, _, kline_service = self._get_services()

            result = kline_service.sync_realtime_to_kline(
                symbols=stock_codes,
                interval=interval
            )

            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

- [ ] **Step 2: 添加 List 类型导入**

在文件顶部导入中添加 `List`：

```python
from typing import Optional, List, Dict
```

- [ ] **Step 3: 验证语法正确**

Run: `python -c "from api_server.services.stock_market_service import StockMarketService; print('OK')"`
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
git add api_server/services/stock_market_service.py
git commit -m "feat: StockMarketService 新增 sync_realtime_to_kline 接口"
```

---

### Task 7: 新增 API 路由

**Files:**
- Modify: `api_server/routers/stock_market.py`

- [ ] **Step 1: 添加新的导入**

在文件顶部的导入部分添加：

```python
from ..models.stock_market import (
    StockSyncParams,
    KLineSyncParams,
    SyncStatusResponse,
    RealtimeKLineSyncParams,
    RealtimeKLineSyncData,
    RealtimeKLineSyncDetail
)
```

- [ ] **Step 2: 添加新的路由**

在文件末尾添加：

```python
@stock_market_router.post("/market/kline/sync-realtime", response_model=APIResponse[RealtimeKLineSyncData])
async def sync_realtime_kline(params: RealtimeKLineSyncParams):
    """
    从实时行情同步今日K线

    批量获取股票实时行情并同步到K线历史数据表。
    支持覆盖更新已存在的当日K线记录。

    - **stock_codes**: 股票代码列表，最多100只
    - **interval**: 周期，仅支持 1d（日线）
    """
    # 参数校验
    if params.interval != "1d":
        raise HTTPException(
            status_code=400,
            detail="Invalid interval, only '1d' is supported"
        )

    try:
        result = service.sync_realtime_to_kline(
            stock_codes=params.stock_codes,
            interval=params.interval
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to sync realtime kline")
            )

        data = result.get("data", {})

        return APIResponse(
            data=RealtimeKLineSyncData(
                total_count=data.get("total_count", 0),
                success_count=data.get("success_count", 0),
                failed_count=data.get("failed_count", 0),
                skipped_count=data.get("skipped_count", 0),
                details=[
                    RealtimeKLineSyncDetail(
                        symbol=d.get("symbol"),
                        status=d.get("status"),
                        reason=d.get("reason")
                    )
                    for d in data.get("details", [])
                ]
            ),
            message="同步完成"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing realtime kline: {str(e)}")
```

- [ ] **Step 3: 验证路由注册成功**

Run: `python -c "from api_server.routers.stock_market import stock_market_router; routes = [r.path for r in stock_market_router.routes]; print('sync-realtime' in ' '.join(routes))"`
Expected: `True`

- [ ] **Step 4: 提交**

```bash
git add api_server/routers/stock_market.py
git commit -m "feat: 新增 POST /market/kline/sync-realtime 路由"
```

---

### Task 8: 运行测试确认通过（TDD GREEN 阶段）

- [ ] **Step 1: 运行测试**

Run: `python -m pytest tests/api_server/test_realtime_kline_sync.py -v`
Expected: 所有测试通过

- [ ] **Step 2: 运行完整测试套件**

Run: `python -m pytest tests/ -v --tb=short`
Expected: 所有测试通过

- [ ] **Step 3: 提交测试通过状态**

```bash
git add -A
git commit -m "test: 实时K线同步接口测试通过（TDD GREEN）"
```

---

### Task 9: 集成验证

- [ ] **Step 1: 启动服务验证接口可用**

Run: `python -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 &`

Run: `curl -X POST http://localhost:8000/market/kline/sync-realtime -H "Content-Type: application/json" -d '{"stock_codes": ["600519"], "interval": "1d"}'`
Expected: 返回 JSON 响应

- [ ] **Step 2: 最终提交**

```bash
git add -A
git commit -m "feat: 实时行情同步K线接口实现完成"
```

---

## 验收标准

- [ ] `POST /market/kline/sync-realtime` 接口可正常调用
- [ ] 空列表、超过100只、无效 interval 返回 400/422 错误
- [ ] 成功同步返回正确的统计信息
- [ ] 部分失败时正确记录详情
- [ ] 数据源错误、数据库错误、OHLC缺失场景正确处理
- [ ] 所有测试通过
