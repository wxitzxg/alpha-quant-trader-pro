# 实时行情同步K线接口设计

## 概述

新增一个API接口，从实时行情数据批量获取多只股票的当日OHLC数据，并将其同步到K线历史数据表中。

## 需求

- **场景**: 盘后更新，收盘后批量更新今日K线数据
- **输入**: 股票代码列表
- **行为**: 覆盖更新，用实时行情数据覆盖已有K线记录

## 方案

扩展 `Quote` 模型增加 OHLC 字段，复用现有实时行情接口获取数据。

## 设计详情

### 1. 数据模型变更

**文件**: `data_sources/models.py`

扩展 `Quote` 模型：

```python
class Quote(BaseModel):
    """实时行情数据模型"""
    symbol: str
    price: float
    change: float
    percent: float
    volume: int
    amount: float
    # 新增 OHLC 字段
    open_price: Optional[float] = None   # 开盘价
    high: Optional[float] = None         # 最高价
    low: Optional[float] = None          # 最低价
    # 原有字段
    bid_price: List[float] = Field(default_factory=list)
    bid_volume: List[int] = Field(default_factory=list)
    ask_price: List[float] = Field(default_factory=list)
    ask_volume: List[int] = Field(default_factory=list)
    timestamp: datetime
```

### 2. 数据源适配器修改

**文件**: `data_sources/adapters/sina_adapter.py`

修改 `get_realtime()` 和 `batch_get_realtime()` 方法，在构建 Quote 时传入 OHLC 字段：

```python
# 现有解析代码已获取 OHLC
open_price = float(values[1])
current = float(values[3])
high = float(values[4])
low = float(values[5])

return Quote(
    symbol=symbol,
    price=current,
    open_price=open_price,  # 新增
    high=high,              # 新增
    low=low,                # 新增
    # ... 其他字段
)
```

**注意**: `InvestodayAdapter` 暂不返回 OHLC（API限制），保持字段为 `None`。

### 3. API 接口

**文件**: `api_server/routers/stock_market.py`

**新增路由**: `POST /market/kline/sync-realtime`

**请求模型**:
```python
class RealtimeKLineSyncParams(BaseModel):
    stock_codes: List[str] = Field(..., description="股票代码列表")
    interval: str = Field(default="1d", description="周期，默认日线")
```

**响应模型**:
```python
class RealtimeKLineSyncDetail(BaseModel):
    symbol: str
    status: str  # "updated" | "failed" | "skipped"
    reason: Optional[str] = None

class RealtimeKLineSyncResponse(BaseModel):
    total: int      # 总数
    success: int    # 成功数
    failed: int     # 失败数
    skipped: int    # 跳过数
    details: List[RealtimeKLineSyncDetail]
```

### 4. 服务层

**文件**: `stock_market/services/kline_service.py`

**新增方法**: `sync_realtime_to_kline()`

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
        interval: 周期

    Returns:
        {"total": 10, "success": 8, "failed": 2, "details": [...]}
    """
```

**处理流程**:
1. 调用 `DataSourceAggregator.batch_get_realtime(symbols)`
2. 遍历 Quote 列表
3. 检查 OHLC 数据是否完整
4. 转换为 KLine 记录
5. 查询当日K线是否存在 → 存在则覆盖更新，不存在则新增
6. 返回处理结果

### 5. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 股票代码不存在 | 返回 `status: "failed", reason: "stock_not_found"` |
| 数据源不可用 | 返回 `status: "failed", reason: "data_source_error"` |
| Quote缺少OHLC | 返回 `status: "skipped", reason: "no_ohlc_data"` |
| 数据库写入失败 | 返回 `status: "failed", reason: "db_error"` |

## 文件变更清单

| 文件 | 变更类型 |
|------|----------|
| `data_sources/models.py` | 修改 - 扩展 Quote 模型 |
| `data_sources/adapters/sina_adapter.py` | 修改 - 解析 OHLC 字段 |
| `api_server/models/stock_market.py` | 修改 - 新增请求/响应模型 |
| `api_server/routers/stock_market.py` | 修改 - 新增路由 |
| `stock_market/services/kline_service.py` | 修改 - 新增同步方法 |

## 测试要点

1. 单只股票同步成功
2. 多只股票批量同步
3. 当日K线已存在时覆盖更新
4. 当日K线不存在时新增
5. 无效股票代码处理
6. 数据源不支持OHLC时跳过
