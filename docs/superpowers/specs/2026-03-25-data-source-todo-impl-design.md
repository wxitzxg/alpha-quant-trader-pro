# 数据源路由 TODO 实现设计

> **日期**: 2026-03-25
> **状态**: 待审核 (第2轮)
> **范围**: `api_server/routers/data_source.py` 9个TODO实现

---

## 1. 问题分析

### 1.1 现状

`api_server/routers/data_source.py` 中 9 个端点返回硬编码数据：

| 行号 | 端点 | 当前状态 |
|------|------|----------|
| 34 | `/stock/list` | 返回空列表 |
| 46 | `/stock/info/{stock_code}` | 返回空对象 |
| 59 | `/quote/realtime/{stock_code}` | 返回假数据 |
| 85 | `/quote/batch` | 返回空列表 |
| 101 | `/quote/top-list` | 返回空列表 |
| 120 | `/kline/{stock_code}` | 返回空列表 |
| 140 | `/kline/batch` | 返回空对象 |
| 156 | `/kline/stats/{stock_code}` | 返回假数据 |
| 179 | `/financial/indicators/{stock_code}` | 返回空对象 |

### 1.2 现有基础设施

```
┌─────────────────────────────────────────────────────────────┐
│                    已实现且可用                              │
├─────────────────────────────────────────────────────────────┤
│ data_sources/aggregator.py                                  │
│   - DataSourceAggregator (单例)                             │
│   - QuoteAPI.get_realtime()                                 │
│   - QuoteAPI.batch_get_realtime()                           │
│   - KLineAPI.get()                                          │
│   - FundamentalsAPI.get_indicators()                        │
├─────────────────────────────────────────────────────────────┤
│ data_sources/base.py (抽象接口)                              │
│   - get_stock_list()                                        │
│   - get_stock_detail()                                      │
│   - get_realtime()                                          │
│   - get_kline()                                             │
│   - get_financial_indicators()                              │
├─────────────────────────────────────────────────────────────┤
│ data_sources/adapters/akshare_adapter.py                    │
│   - 完整实现所有接口                                         │
├─────────────────────────────────────────────────────────────┤
│ api_server/services/data_source_service.py                  │
│   - get_realtime_quote() ✅                                 │
│   - get_batch_quotes() ✅                                   │
│   - get_kline() ✅                                          │
│   - get_batch_klines() ✅                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 根本原因

路由层未调用服务层，直接返回硬编码数据。

---

## 2. 设计方案

### 2.1 架构

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Router Layer   │────▶│   Service Layer  │────▶│  Data Sources    │
│  data_source.py  │     │ data_source_     │     │  aggregator.py   │
│                  │     │    service.py    │     │                  │
│ - 9 endpoints    │     │ - 扩展方法       │     │ - QuoteAPI       │
│ - 连接服务层     │     │ - 错误处理       │     │ - KLineAPI       │
│ - 响应格式化     │     │ - 数据转换       │     │ - StockListAPI   │
└──────────────────┘     └──────────────────┘     │ - TopListAPI     │
                                                  │ - KLineStatsAPI  │
                                                  │ - FundamentalsAPI│
                                                  └──────────────────┘
```

### 2.2 改动范围

| 文件 | 改动类型 | 改动量 |
|------|----------|--------|
| `data_sources/aggregator.py` | 扩展 | +120行 |
| `api_server/services/data_source_service.py` | 扩展 | +150行 |
| `api_server/routers/data_source.py` | 重写 | ~200行 |

---

## 3. 详细设计

### 3.1 聚合层扩展 (`data_sources/aggregator.py`)

> **注意**: `_get_sorted_adapters()` 私有方法已存在于 `DataSourceAggregator` 类中（第133-156行），无需新增。

**新增公共方法到 DataSourceAggregator 类:**

```python
def get_stock_list(self, exchange: Optional[str] = None) -> List[Dict]:
    """
    获取股票列表

    Args:
        exchange: 交易所筛选 (SH/SZ)，None 表示全部

    Returns:
        股票列表
    """
    adapters = self._get_sorted_adapters('realtime')
    for adapter in adapters:
        try:
            stocks = adapter.get_stock_list()
            if exchange:
                stocks = [s for s in stocks if s.get('exchange') == exchange]
            return stocks
        except DataSourceError:
            continue
    return []

def get_stock_detail(self, symbol: str) -> Optional[Dict]:
    """
    获取股票详情

    Args:
        symbol: 股票代码

    Returns:
        股票详情字典，失败返回 None
    """
    adapters = self._get_sorted_adapters('realtime')
    for adapter in adapters:
        try:
            return adapter.get_stock_detail(symbol)
        except DataSourceError:
            continue
    return None
```

**新增简化调用 API 类:**

```python
class StockListAPI:
    """股票列表 API"""

    @staticmethod
    def get(exchange: Optional[str] = None) -> List[Dict]:
        aggregator = DataSourceAggregator()
        return aggregator.get_stock_list(exchange=exchange)


class TopListAPI:
    """涨跌排行 API - 带内存缓存"""

    _cache: Dict[str, Tuple[List[Dict], float]] = {}
    _cache_ttl: int = 60  # 缓存60秒

    @staticmethod
    def get(type: str, date: Optional[str] = None) -> List[Dict]:
        cache_key = f"toplist_{type}_{date}"
        now = time.time()

        # 检查缓存
        if cache_key in TopListAPI._cache:
            data, timestamp = TopListAPI._cache[cache_key]
            if now - timestamp < TopListAPI._cache_ttl:
                return data

        # 获取所有股票行情
        aggregator = DataSourceAggregator()
        stocks = aggregator.get_stock_list()
        symbols = [s['symbol'] for s in stocks[:500]]  # 限制前500只

        quotes = aggregator.batch_get_realtime(symbols)

        # 转换并排序（映射到 TopListEntry 模型）
        # TopListEntry 需要: ts_code, symbol, name, change_pct, current_price, change, volume
        items = []
        for q in quotes:
            items.append({
                "ts_code": f"{q.symbol}.SH",  # 根据代码推导交易所
                "symbol": q.symbol,
                "name": getattr(q, 'name', ''),
                "current_price": q.price,       # Quote.price -> TopListEntry.current_price
                "change": q.change,
                "change_pct": q.percent * 100,
                "volume": q.volume
            })

        # 按涨跌幅排序
        reverse = (type == "gain")  # 涨幅榜降序，跌幅榜升序
        items.sort(key=lambda x: x["change_pct"], reverse=reverse)

        # 更新缓存
        TopListAPI._cache[cache_key] = (items[:100], now)
        return items[:100]


class KLineStatsAPI:
    """K线统计 API"""

    @staticmethod
    def get(symbol: str, period: str = "1y") -> Dict:
        # 计算日期范围
        end_date = datetime.now().strftime("%Y-%m-%d")
        days_map = {"1y": 365, "6m": 180, "3m": 90, "1m": 30}
        days = days_map.get(period, 365)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 获取K线数据
        aggregator = DataSourceAggregator()
        klines = aggregator.get_kline(symbol, "1d", start_date, end_date)

        if not klines:
            return {
                "symbol": symbol,
                "period": period,
                "total_trading_days": 0,
                "price_range": {"min": 0, "max": 0, "avg": 0},
                "volume_stats": {"min": 0, "max": 0, "avg": 0, "total": 0},
                "volatility": 0.0,
                "highest_price": {"price": 0, "date": ""},
                "lowest_price": {"price": 0, "date": ""}
            }

        # 计算统计（KLine 模型属性: close, datetime, open_price）
        prices = [k.close for k in klines]  # 使用 close 而非 price
        volumes = [k.volume for k in klines]

        max_price_idx = prices.index(max(prices))
        min_price_idx = prices.index(min(prices))

        # 计算波动率（标准差）
        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price * 100 if avg_price > 0 else 0

        return {
            "symbol": symbol,
            "name": getattr(klines[0], 'name', ''),
            "period": period,
            "total_trading_days": len(klines),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "avg": round(avg_price, 2)
            },
            "volume_stats": {
                "min": min(volumes),
                "max": max(volumes),
                "avg": int(sum(volumes) / len(volumes)),
                "total": sum(volumes)
            },
            "volatility": round(volatility, 2),
            "highest_price": {
                "price": max(prices),
                "date": str(klines[max_price_idx].datetime.date())  # 使用 datetime
            },
            "lowest_price": {
                "price": min(prices),
                "date": str(klines[min_price_idx].datetime.date())  # 使用 datetime
            }
        }
```

### 3.2 服务层扩展 (`api_server/services/data_source_service.py`)

新增 **6 个方法**（包括财务指标）：

```python
from data_sources import QuoteAPI, KLineAPI, FundamentalsAPI
from data_sources.aggregator import (
    DataSourceAggregator, StockListAPI, TopListAPI, KLineStatsAPI
)


class DataSourceService:
    # 现有方法保持不变...

    @staticmethod
    def get_stock_list(
        page: int = 1,
        page_size: int = 20,
        exchange: Optional[str] = None
    ) -> Dict:
        """获取股票列表（分页）"""
        try:
            all_stocks = StockListAPI.get(exchange=exchange)
            start = (page - 1) * page_size
            end = start + page_size

            return {
                "success": True,
                "data": {
                    "stocks": all_stocks[start:end],
                    "total": len(all_stocks),
                    "page": page,
                    "page_size": page_size
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to get stock list: {e}"}

    @staticmethod
    def get_stock_info(stock_code: str) -> Dict:
        """获取股票详情"""
        try:
            aggregator = DataSourceAggregator()
            detail = aggregator.get_stock_detail(stock_code)
            if detail:
                return {"success": True, "data": detail}
            return {"success": False, "message": f"Stock {stock_code} not found"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def get_top_list(type: str, date: Optional[str] = None) -> Dict:
        """获取涨跌排行"""
        try:
            items = TopListAPI.get(type=type, date=date)
            return {
                "success": True,
                "data": {
                    "type": type,
                    "date": date or datetime.now().strftime("%Y-%m-%d"),
                    "items": items,
                    "total": len(items)
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to get top list: {e}"}

    @staticmethod
    def get_kline_stats(symbol: str, period: str = "1y") -> Dict:
        """获取K线统计"""
        try:
            stats = KLineStatsAPI.get(symbol=symbol, period=period)
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "message": f"Failed to get kline stats: {e}"}

    @staticmethod
    def get_financial_indicators(stock_code: str) -> Dict:
        """获取财务指标"""
        try:
            # 使用当前年份和最新季度
            now = datetime.now()
            year = now.year
            quarter = (now.month - 1) // 3 + 1
            if quarter == 0:
                quarter = 4
                year -= 1

            indicators = FundamentalsAPI.get_indicators(stock_code, year, quarter)
            if indicators:
                return {"success": True, "data": indicators}
            return {"success": False, "message": f"No financial indicators for {stock_code}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to get financial indicators: {e}"}
```

### 3.3 路由层重写 (`api_server/routers/data_source.py`)

```python
#!/usr/bin/env python3
"""数据源聚合路由"""

from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional, List
from datetime import datetime

from ..models.common import APIResponse, PaginationParams
from ..models.stock import StockListResponse, StockFilterParams
from ..models.quote import RealtimeQuote, BatchQuoteRequest, BatchQuoteResponse, TopListResponse
from ..models.kline import KLineResponse, KLineQueryParams, BatchKLineRequest, BatchKLineResponse, KLineStats
from ..services.data_source_service import DataSourceService

data_source_router = APIRouter()
service = DataSourceService()


# ========== 股票基础数据 ==========
@data_source_router.get("/stock/list", response_model=APIResponse[StockListResponse])
async def get_stock_list(
    exchange: Optional[str] = Query(None, description="交易所 (SH/SZ)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取股票列表"""
    result = service.get_stock_list(page=page, page_size=page_size, exchange=exchange)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=StockListResponse(**result["data"]),
        message="Stock list retrieved successfully"
    )


@data_source_router.get("/stock/info/{stock_code}", response_model=APIResponse)
async def get_stock_info(stock_code: str = Path(..., description="股票代码")):
    """获取股票详情"""
    result = service.get_stock_info(stock_code)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return APIResponse(data=result["data"], message="Stock info retrieved successfully")


# ========== 行情数据 ==========
@data_source_router.get("/quote/realtime/{stock_code}", response_model=APIResponse[RealtimeQuote])
async def get_realtime_quote(stock_code: str = Path(..., description="股票代码")):
    """获取单股实时行情"""
    quote_data = service.get_realtime_quote(stock_code)
    if not quote_data:
        raise HTTPException(status_code=404, detail=f"Quote not found for {stock_code}")
    return APIResponse(
        data=RealtimeQuote(**quote_data),
        message="Realtime quote retrieved successfully"
    )


@data_source_router.post("/quote/batch", response_model=APIResponse[BatchQuoteResponse])
async def get_batch_quotes(request: BatchQuoteRequest):
    """批量获取行情"""
    quotes_data = service.get_batch_quotes(request.symbols)
    quotes = [RealtimeQuote(**q) for q in quotes_data.values() if q]
    return APIResponse(
        data=BatchQuoteResponse(quotes=quotes, timestamp=datetime.now()),
        message="Batch quotes retrieved successfully"
    )


@data_source_router.get("/quote/top-list", response_model=APIResponse[TopListResponse])
async def get_top_list(
    type: str = Query("gain", description="排行类型 (gain/loss)"),
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)")
):
    """涨跌幅排行"""
    result = service.get_top_list(type=type, date=date)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=TopListResponse(**result["data"]),
        message="Top list retrieved successfully"
    )


# ========== K线数据 ==========
@data_source_router.get("/kline/{stock_code}", response_model=APIResponse[KLineResponse])
async def get_kline(
    stock_code: str = Path(..., description="股票代码"),
    interval: str = Query("1d", description="K线周期"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    limit: int = Query(120, ge=1, le=1000, description="数据条数")
):
    """获取K线数据"""
    klines_data = service.get_kline(stock_code, interval, start_date, end_date, limit)
    if klines_data is None:
        raise HTTPException(status_code=404, detail=f"KLine data not found for {stock_code}")
    return APIResponse(
        data=KLineResponse(
            symbol=stock_code,
            name="",
            interval=interval,
            klines=klines_data,
            total=len(klines_data),
            start_date=start_date,
            end_date=end_date
        ),
        message="KLine data retrieved successfully"
    )


@data_source_router.post("/kline/batch", response_model=APIResponse[BatchKLineResponse])
async def get_batch_klines(request: BatchKLineRequest):
    """批量获取K线"""
    result = service.get_batch_klines(request.symbols, request.interval)
    return APIResponse(
        data=BatchKLineResponse(data=result, timestamp=datetime.now()),
        message="Batch KLine data retrieved successfully"
    )


@data_source_router.get("/kline/stats/{stock_code}", response_model=APIResponse[KLineStats])
async def get_kline_stats(
    stock_code: str = Path(..., description="股票代码"),
    period: str = Query("1y", description="统计周期 (1y/6m/3m/1m)")
):
    """K线统计信息"""
    result = service.get_kline_stats(stock_code, period)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=KLineStats(**result["data"]),
        message="KLine stats retrieved successfully"
    )


# ========== 财务数据 ==========
@data_source_router.get("/financial/indicators/{stock_code}", response_model=APIResponse)
async def get_financial_indicators(stock_code: str = Path(..., description="股票代码")):
    """获取财务指标"""
    result = service.get_financial_indicators(stock_code)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return APIResponse(data=result["data"], message="Financial indicators retrieved successfully")
```

---

## 4. 实现清单

### 4.1 任务列表

- [ ] **T1**: 扩展 `data_sources/aggregator.py` - 新增 `get_stock_list()` 和 `get_stock_detail()` 公共方法
- [ ] **T2**: 扩展 `data_sources/aggregator.py` - 新增 `StockListAPI` 类
- [ ] **T3**: 扩展 `data_sources/aggregator.py` - 新增 `TopListAPI` 类（带缓存）
- [ ] **T4**: 扩展 `data_sources/aggregator.py` - 新增 `KLineStatsAPI` 类
- [ ] **T5**: 扩展 `api_server/services/data_source_service.py` - 新增 6 个方法
- [ ] **T6**: 重写 `api_server/routers/data_source.py` - 连接服务层
- [ ] **T7**: 编写单元测试

### 4.2 依赖关系

```
T1 ─┬──▶ T2 ─┐
    │        │
    ├──▶ T3 ─┼──▶ T5 ──▶ T6 ──▶ T7
    │        │
    └──▶ T4 ─┘
```

---

## 5. 错误处理

### 5.1 服务层错误格式

与现有代码保持一致：

```python
# 成功时返回数据字典
{"success": True, "data": {...}}

# 失败时返回 None 或错误信息
{"success": False, "message": "错误描述"}
```

### 5.2 路由层异常处理

```python
result = service.some_method(...)
if not result.get("success"):
    # 404 用于资源未找到
    # 500 用于服务器错误
    raise HTTPException(status_code=500, detail=result.get("message"))
return APIResponse(data=result["data"], message="Success")
```

---

## 6. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 数据源不可用 | 中 | 高 | 聚合器自动降级机制，依次尝试多个数据源 |
| 性能问题(排行榜) | 中 | 中 | 内存缓存 60 秒 TTL，限制查询 500 只股票 |
| API 频率限制 | 中 | 中 | 缓存机制减少请求；考虑后续添加请求限流 |
| 接口不兼容 | 低 | 低 | 已有抽象层隔离，适配器实现统一接口 |

### 6.1 缓存设计详情

```python
# TopListAPI 内存缓存
_cache: Dict[str, Tuple[List[Dict], float]] = {}
_cache_ttl: int = 60  # 秒

# 缓存键格式
cache_key = f"toplist_{type}_{date}"

# 缓存逻辑
if cache_key in cache and (now - timestamp) < TTL:
    return cached_data
else:
    fetch_new_data()
    update_cache()
```

---

## 7. 验收标准

1. 所有 9 个端点返回真实数据
2. 无 TODO 注释残留
3. 单元测试覆盖率 > 80%
4. 错误场景正确返回错误信息
5. 排行榜接口响应时间 < 2秒（有缓存时 < 100ms）

---

## 8. 变更历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-03-25 | 初版 |
| v2.0 | 2026-03-25 | 修复审核问题：添加财务指标方法、完整实现逻辑、内存缓存设计、公共API使用 |
