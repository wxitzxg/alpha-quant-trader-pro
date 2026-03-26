# 实时行情同步K线接口设计

## 概述

新增一个API接口，从实时行情数据批量获取多只股票的当日OHLC数据，并将其同步到K线历史数据表中。

## 需求

- **场景**: 盘后更新，收盘后批量更新今日K线数据
- **输入**: 股票代码列表（最大100只）
- **行为**: 覆盖更新，用实时行情数据覆盖已有K线记录
- **日期**: 使用当前自然日作为K线日期，非交易日调用会创建无效记录（由调用方确保盘后调用）

## 方案

扩展 `Quote` 模型增加 OHLC 字段，复用现有实时行情接口获取数据。

## 设计详情

### 1. 数据模型变更

**文件**: `data_sources/models.py`

`Quote` 模型新增 OHLC 字段：

```python
# 在现有 Quote 模型中新增以下字段：
open_price: Optional[float] = None   # 开盘价
high: Optional[float] = None         # 最高价
low: Optional[float] = None          # 最低价
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

### 3. 错误码定义

**文件**: `api_server/models/stock_market.py`

```python
class RealtimeSyncErrorCode(str, Enum):
    """实时同步错误码"""
    STOCK_NOT_FOUND = "stock_not_found"      # 股票代码不存在
    DATA_SOURCE_ERROR = "data_source_error"  # 数据源不可用
    NO_OHLC_DATA = "no_ohlc_data"           # 数据源不支持OHLC
    DB_ERROR = "db_error"                    # 数据库写入失败
    INVALID_PARAMS = "invalid_params"        # 参数校验失败
```

### 4. API 接口

**文件**: `api_server/routers/stock_market.py`

**新增路由**: `POST /market/kline/sync-realtime`

**请求模型**:
```python
class RealtimeKLineSyncParams(BaseModel):
    stock_codes: List[str] = Field(
        ...,
        description="股票代码列表，纯代码格式如 ['600519', '000001']，系统自动识别沪市/深市",
        min_length=1,
        max_length=100
    )
    interval: str = Field(
        default="1d",
        description="周期，仅支持 1d（日线）"
    )
```

**请求示例**:
```json
POST /market/kline/sync-realtime
{
  "stock_codes": ["600519", "000001"],
  "interval": "1d"
}
```

**成功响应示例**:
```json
{
  "success": true,
  "message": "同步完成",
  "data": {
    "total_count": 2,
    "success_count": 2,
    "failed_count": 0,
    "skipped_count": 0,
    "details": [
      {"symbol": "600519", "status": "updated", "reason": null},
      {"symbol": "000001", "status": "updated", "reason": null}
    ]
  }
}
```

**部分失败响应示例**:
```json
{
  "success": true,
  "message": "同步完成",
  "data": {
    "total_count": 3,
    "success_count": 2,
    "failed_count": 1,
    "skipped_count": 0,
    "details": [
      {"symbol": "600519", "status": "updated", "reason": null},
      {"symbol": "000001", "status": "updated", "reason": null},
      {"symbol": "999999", "status": "failed", "reason": "stock_not_found"}
    ]
  }
}
```

**响应模型**（遵循现有 `APIResponse[T]` 包装模式）:
```python
class RealtimeKLineSyncDetail(BaseModel):
    symbol: str
    status: str  # "updated" | "failed" | "skipped"
    reason: Optional[RealtimeSyncErrorCode] = None

class RealtimeKLineSyncData(BaseModel):
    total_count: int       # 总数
    success_count: int     # 成功数
    failed_count: int      # 失败数
    skipped_count: int     # 跳过数
    details: List[RealtimeKLineSyncDetail]

# 实际响应使用 APIResponse 包装
# APIResponse[RealtimeKLineSyncData]
```

**HTTP 状态码**:
- `200 OK`: 请求成功（即使部分股票失败）
- `400 Bad Request`: 参数校验失败（空列表、超过100只、无效interval）
- `500 Internal Server Error`: 服务器内部错误

**参数校验规则**:
| 参数 | 规则 |
|------|------|
| `stock_codes` | 非空列表，长度 1-100 |
| `interval` | 仅支持 "1d" |

### 5. 服务层

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
```

**处理流程**:
1. 调用 `DataSourceAggregator.batch_get_realtime(symbols)`
2. 遍历 Quote 列表
3. 检查 OHLC 数据是否完整
4. 转换为 KLine 记录（见字段映射）
5. 查询当日K线是否存在 → 存在则覆盖更新，不存在则新增
6. 返回处理结果

**Quote → KLine 字段映射**:
```python
# 注意：Pydantic Quote 与 ORM KLine 字段名差异
# stock_id 需通过 stock_repo.get_by_symbol() 获取
stock = stock_repo.get_by_symbol(quote.symbol)
if not stock:
    return {"status": "failed", "reason": "stock_not_found"}

KLine(
    stock_id=stock.id,             # 外键，需从 stocks 表获取
    symbol=quote.symbol,
    date=today,                    # 当前自然日
    interval=interval,
    open=quote.open_price,         # Quote.open_price → KLine.open
    high=quote.high,
    low=quote.low,
    close=quote.price,             # Quote.price → KLine.close
    volume=quote.volume,
    amount=quote.amount,
    sync_time=datetime.now()
)
```

**幂等性说明**: 该接口支持幂等调用，多次调用同一股票会覆盖更新当日K线，不会产生重复记录。

**事务策略**:
- 每只股票使用独立的数据库会话
- 单只股票处理成功后立即提交
- 单只股票失败不回滚其他股票的更新

### 6. 错误处理

| 场景 | 错误码 | 处理方式 |
|------|--------|----------|
| 空列表 | `INVALID_PARAMS` | 返回 400 错误 |
| 超过100只 | `INVALID_PARAMS` | 返回 400 错误 |
| 无效 interval | `INVALID_PARAMS` | 返回 400 错误 |
| 股票代码不存在 | `STOCK_NOT_FOUND` | 记录失败详情，继续处理其他 |
| 数据源不可用 | `DATA_SOURCE_ERROR` | 记录失败详情，继续处理其他 |
| Quote缺少OHLC | `NO_OHLC_DATA` | 跳过，记录详情 |
| 数据库写入失败 | `DB_ERROR` | 记录失败详情，继续处理其他 |

**日志要求**:
- INFO: 同步开始、结束、汇总结果
- WARNING: 单只股票跳过（缺少OHLC）
- ERROR: 数据源错误、数据库错误

## 文件变更清单

| 文件 | 变更类型 |
|------|----------|
| `data_sources/models.py` | 修改 - 扩展 Quote 模型 |
| `data_sources/adapters/sina_adapter.py` | 修改 - 解析 OHLC 字段 |
| `api_server/models/stock_market.py` | 修改 - 新增请求/响应模型、错误码枚举 |
| `api_server/routers/stock_market.py` | 修改 - 新增路由 |
| `stock_market/services/kline_service.py` | 修改 - 新增同步方法 |
| `tests/api_server/test_stock_market_router.py` | 新增 - 路由测试 |

## 测试要点

### 正常场景
1. 单只股票同步成功
2. 多只股票批量同步
3. 当日K线已存在时覆盖更新
4. 当日K线不存在时新增

### 边界场景
5. 空列表返回 400 错误
6. 超过100只返回 400 错误
7. 无效 interval 返回 400 错误

### 异常场景
8. 无效股票代码处理（记录失败详情）
9. 数据源不支持OHLC时跳过
10. 数据库写入失败处理
11. 数据源完全不可用时的全局错误处理
12. 非法股票代码格式验证
