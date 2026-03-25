# 数据源路由 TODO 实现设计

> **日期**: 2026-03-25
> **状态**: 待审核
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
│   - FundamentalsAPI.*                                       │
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
                                                  └──────────────────┘
```

### 2.2 改动范围

| 文件 | 改动类型 | 改动量 |
|------|----------|--------|
| `data_sources/aggregator.py` | 扩展 | +80行 |
| `api_server/services/data_source_service.py` | 扩展 | +120行 |
| `api_server/routers/data_source.py` | 重写 | ~180行 |

---

## 3. 详细设计

### 3.1 聚合层扩展 (`data_sources/aggregator.py`)

新增 3 个简化调用 API 类：

```python
class StockListAPI:
    """股票列表 API"""

    @staticmethod
    def get(exchange: Optional[str] = None) -> List[Dict]:
        aggregator = DataSourceAggregator()
        adapters = aggregator._get_sorted_adapters('realtime')
        # 调用 adapter.get_stock_list()
        ...

class TopListAPI:
    """涨跌排行 API"""

    @staticmethod
    def get(type: str, date: Optional[str] = None) -> List[Dict]:
        # 从全市场实时行情计算排行
        aggregator = DataSourceAggregator()
        all_quotes = aggregator.batch_get_realtime(
            aggregator.get_all_symbols()
        )
        # 按 change_pct 排序
        ...

class KLineStatsAPI:
    """K线统计 API"""

    @staticmethod
    def get(symbol: str, period: str = "1y") -> Dict:
        aggregator = DataSourceAggregator()
        # 获取K线数据后计算统计
        klines = aggregator.get_kline(symbol, "1d", ...)
        return {
            "symbol": symbol,
            "period": period,
            "total_trading_days": len(klines),
            "price_range": {...},
            "volume_stats": {...},
            "volatility": ...,
            "highest_price": {...},
            "lowest_price": {...}
        }
```

### 3.2 服务层扩展 (`api_server/services/data_source_service.py`)

新增方法：

```python
class DataSourceService:
    # 现有方法保持不变...

    @staticmethod
    def get_stock_list(
        page: int = 1,
        page_size: int = 20,
        exchange: Optional[str] = None
    ) -> Dict:
        """获取股票列表（分页）"""
        all_stocks = StockListAPI.get(exchange=exchange)
        # 分页处理
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

    @staticmethod
    def get_stock_info(stock_code: str) -> Dict:
        """获取股票详情"""
        aggregator = DataSourceAggregator()
        detail = aggregator._get_sorted_adapters('realtime')[0].get_stock_detail(stock_code)
        if detail:
            return {"success": True, "data": detail}
        return {"success": False, "message": f"Stock {stock_code} not found"}

    @staticmethod
    def get_top_list(type: str, date: Optional[str] = None) -> Dict:
        """获取涨跌排行"""
        items = TopListAPI.get(type=type, date=date)
        return {
            "success": True,
            "data": {
                "type": type,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "items": items[:100],  # Top 100
                "total": len(items)
            }
        }

    @staticmethod
    def get_kline_stats(symbol: str, period: str = "1y") -> Dict:
        """获取K线统计"""
        stats = KLineStatsAPI.get(symbol=symbol, period=period)
        return {"success": True, "data": stats}
```

### 3.3 路由层重写 (`api_server/routers/data_source.py`)

```python
from ..services.data_source_service import DataSourceService

data_source_router = APIRouter()
service = DataSourceService()

@data_source_router.get("/stock/list", response_model=APIResponse[StockListResponse])
async def get_stock_list(
    params: StockFilterParams = Query(...),
    pagination: PaginationParams = Query(...)
):
    """获取股票列表"""
    result = service.get_stock_list(
        page=pagination.page,
        page_size=pagination.page_size,
        exchange=params.exchange
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(
        data=StockListResponse(**result["data"]),
        message="Stock list retrieved successfully"
    )

# ... 其他端点类似模式
```

---

## 4. 实现清单

### 4.1 任务列表

- [ ] **T1**: 扩展 `data_sources/aggregator.py` - 新增 `StockListAPI`
- [ ] **T2**: 扩展 `data_sources/aggregator.py` - 新增 `TopListAPI`
- [ ] **T3**: 扩展 `data_sources/aggregator.py` - 新增 `KLineStatsAPI`
- [ ] **T4**: 扩展 `api_server/services/data_source_service.py` - 新增 5 个方法
- [ ] **T5**: 重写 `api_server/routers/data_source.py` - 连接服务层
- [ ] **T6**: 编写单元测试

### 4.2 依赖关系

```
T1 ─┐
T2 ─┼──▶ T4 ──▶ T5 ──▶ T6
T3 ─┘
```

---

## 5. 错误处理

### 5.1 服务层错误格式

```python
{
    "success": False,
    "error": "具体的错误信息",
    "message": "用户友好的错误描述"
}
```

### 5.2 路由层异常处理

```python
try:
    result = service.some_method(...)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return APIResponse(data=result["data"], message="Success")
except HTTPException:
    raise
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

---

## 6. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 数据源不可用 | 中 | 高 | 聚合器自动降级机制 |
| 性能问题(排行榜) | 中 | 中 | 缓存全市场行情 |
| 接口不兼容 | 低 | 低 | 已有抽象层隔离 |

---

## 7. 验收标准

1. 所有 9 个端点返回真实数据
2. 无 TODO 注释残留
3. 单元测试覆盖率 > 80%
4. 错误场景正确返回错误信息
