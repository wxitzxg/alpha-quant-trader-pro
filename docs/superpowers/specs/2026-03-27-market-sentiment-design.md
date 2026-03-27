# Market Sentiment Feature Design

**Goal:** 在技术分析模块实现市场情绪评分功能，支持 API 接口、选股策略和告警系统。

**Author:** Claude
**Date:** 2026-03-27

---

## 1. Overview

### 1.1 Background

参考 `a-stock-monitor` 项目的 7 维度市场情绪评分实现，在 `alpha-quant-trader-pro` 的技术分析模块中实现相同功能。

### 1.2 Scope

- 新增 `MarketSentimentService` 服务层
- 新增 `MarketSentimentCalculator` 评分计算器
- 新增 REST API 端点
- 集成到选股策略作为筛选条件

---

## 2. Architecture

### 2.1 Module Structure

```
technical_analysis/
├── services/
│   ├── __init__.py                   # 新增导出
│   ├── analysis_service.py           # 现有，不变
│   └── market_sentiment_service.py   # 新增
├── indicators/
│   ├── __init__.py                   # 新增导出
│   └── market_sentiment.py           # 新增：评分计算器
└── schemas/                          # 新建目录
    ├── __init__.py                   # 新增导出
    └── market_sentiment.py           # 新增：数据结构
```

> **注意**: `schemas/` 是新建目录，用于存放数据结构定义，与其他模块保持一致的架构模式。

### 2.2 Data Flow

```
API Request
    ↓
MarketSentimentService
    ├─→ DataAggregator.batch_get_realtime() [优先]
    └─→ KLineRepository.get_all_latest_klines() [备选，新增方法]
    ↓
MarketSentimentCalculator.calculate()
    ↓
MarketSentimentResult
```

### 2.3 Core Components

| 组件 | 职责 |
|------|------|
| `MarketSentimentService` | 服务层入口，协调数据获取和评分计算 |
| `MarketSentimentCalculator` | 7 维度评分算法实现 |
| `MarketSentimentResult` | 输出数据结构 |
| `MarketStats` | 统计数据结构 |

---

## 3. Data Source Strategy

### 3.1 Priority

1. **实时行情** (优先): 调用 `DataAggregator.batch_get_realtime()` 获取全市场实时数据
2. **K线数据** (备选): 从 `klines` 表查询最新一日数据

### 3.2 Batch Processing

- 单次获取股票数量限制: 每批 500 只
- 分批查询避免超时
- **批量限制原因**: 新浪财经 API 单次请求最多支持约 50 只股票，akshare 内部有分页机制，500 只是性能与效率的平衡点

### 3.3 Dependencies

- `DataAggregator.batch_get_realtime()` (data_sources 模块) - 实时行情批量获取
- `KLineRepository.get_all_latest_klines()` (stock_market 模块) - **新增方法**，获取所有股票最新 K 线
- `StockRepository.get_active()` (stock_market 模块) - 获取上市股票列表

### 3.4 New Repository Method

需要在 `KLineRepository` 中新增方法:

```python
def get_all_latest_klines(
    self,
    interval: str = "1d",
    limit: int = 5000
) -> List[KLine]:
    """
    获取所有股票的最新K线数据

    Args:
        interval: K线周期
        limit: 最大返回数量

    Returns:
        每只股票最新一天K线数据的列表
    """
    # 使用子查询获取每只股票的最新日期
    # 然后关联获取完整K线数据
```

---

## 4. Scoring Algorithm

### 4.1 7-Dimension System (Base Score: 50)

| 维度 | 权重 | 计算逻辑 | 分值范围 |
|------|------|----------|----------|
| 涨跌家数比 | 20% | 涨股占比 >70%: +10, >60%: +7, >50%: +4, >40%: 0, >30%: -4, ≤30%: -10 | ±10 |
| 平均涨幅 | 20% | 均涨 >3%: +10, >1.5%: +7, >0.5%: +4, >-0.5%: 0, >-1.5%: -4, >-3%: -7, ≤-3%: -10 | ±10 |
| 涨跌停比 | 15% | (涨停数-跌停数) ≥10: +8, ≥5: +5, ≥1: +2, ≥-1: 0, ≥-5: -2, ≥-10: -5, <-10: -8 | ±8 |
| 强势股占比 | 15% | 涨幅>5%占比 >30%: +8, >20%: +5, >10%: +2; 跌幅>5%占比高则扣分 | ±8 |
| 成交活跃度 | 10% | 均换手 >5%: +5, >3%: +3, >2%: +1, >1%: 0, ≤1%: -5 | ±5 |
| 波动率 | 10% | 均振幅 3-5%: +5, >5%: +2, >8%: -3, ≤2%: -3 | ±5 |
| 趋势强度 | 10% | **暂不实现**: 当前数据不支持 MA20 批量计算，该维度得分固定为 0 | 0 |

> **注意**: 趋势强度维度由于需要全市场股票的 MA20 数据，当前实现暂固定为 0 分。未来可在 K 线数据同步时预计算 MA20 后启用该维度。

### 4.2 Rating Levels

| 分数范围 | 等级 | Emoji | 描述 |
|----------|------|-------|------|
| ≥80 | 极度乐观 | 🔥 | 市场情绪极度亢奋，注意追高风险 |
| 65-79 | 乐观 | 📈 | 市场情绪积极，趋势向上 |
| 55-64 | 偏乐观 | 🟢 | 市场偏强，情绪稳定 |
| 45-54 | 中性 | 😐 | 市场平稳，多空平衡 |
| 35-44 | 偏悲观 | 🔻 | 市场偏弱，观望为主 |
| 20-34 | 悲观 | 📉 | 市场情绪低迷，谨慎操作 |
| <20 | 极度悲观 | ❄️ | 市场情绪极度低迷，恐慌情绪蔓延 |

---

## 5. Data Structures

### 5.1 Output Schema

```python
@dataclass
class MarketSentimentResult:
    score: float              # 情绪评分 (0-100)
    level: str                # 等级
    emoji: str                # 表情符号
    description: str          # 描述
    stats: 'MarketStats'      # 统计数据
    data_source: str          # 数据来源: realtime/kline
    update_time: str          # 计算时间

@dataclass
class MarketStats:
    total: int                # 总股票数
    gainers: int              # 上涨数
    losers: int               # 下跌数
    neutral: int              # 平盘数
    limit_up: int             # 涨停数 (≥9.8%)
    limit_down: int           # 跌停数 (≤-9.8%)
    strong_stocks: int        # 强势股数 (涨>5%)
    weak_stocks: int          # 弱势股数 (跌>5%)
    avg_change: float         # 平均涨幅%
    avg_turnover: float       # 平均换手率%
    avg_volatility: float     # 平均振幅%
```

### 5.2 Input Schema

```python
@dataclass
class MarketStockData:
    """单只股票的市场数据"""
    symbol: str
    name: str
    price: float
    change_pct: float         # 涨跌幅% (由 Quote.percent * 100 转换)
    turnover: float           # 换手率% (默认 0，K线数据可能无此字段)
    amplitude: float          # 振幅% (计算公式: (high - low) / pre_close * 100)
```

**数据转换说明**:
- `change_pct`: `Quote.percent` 是小数格式 (0.05 = 5%)，需要乘以 100 转换为百分比
- `amplitude`: 从 Quote 的 high/low/pre_close 计算，公式: `((high - low) / pre_close) * 100`
- `turnover`: 换手率字段可选，实时数据可能不包含，默认值为 0

---

## 6. Service Interface

### 6.1 MarketSentimentService

```python
class MarketSentimentService:
    def __init__(self, session: Session):
        pass

    def get_market_sentiment(
        self,
        use_realtime: bool = True,
        stock_filter: Optional[Dict] = None
    ) -> MarketSentimentResult:
        """
        获取市场情绪评分

        Args:
            use_realtime: 是否优先使用实时数据
            stock_filter: 可选的股票过滤条件

        Returns:
            市场情绪评分结果
        """

    def get_sentiment_for_stocks(
        self,
        symbols: List[str],
        use_realtime: bool = True
    ) -> MarketSentimentResult:
        """
        计算指定股票池的市场情绪
        """
```

### 6.2 Calculator Interface

```python
class MarketSentimentCalculator:
    def calculate(
        self,
        stocks: List[MarketStockData]
    ) -> MarketSentimentResult:
        """
        计算市场情绪评分

        Args:
            stocks: 股票市场数据列表

        Returns:
            市场情绪评分结果
        """
```

---

## 7. REST API

### 7.1 Endpoints

```
GET /api/market/sentiment
    - 获取全市场情绪评分
    - Query params: use_realtime (default: true)
    - 返回 MarketSentimentResult

GET /api/market/sentiment/stats
    - 获取详细统计数据
    - 返回 MarketStats
```

### 7.2 Response Example

```json
{
    "score": 57.0,
    "level": "偏乐观",
    "emoji": "🟢",
    "description": "市场偏强，情绪稳定",
    "stats": {
        "total": 5000,
        "gainers": 2460,
        "losers": 2534,
        "neutral": 6,
        "limit_up": 15,
        "limit_down": 3,
        "strong_stocks": 500,
        "weak_stocks": 400,
        "avg_change": 0.52,
        "avg_turnover": 3.5,
        "avg_volatility": 2.1
    },
    "data_source": "realtime",
    "update_time": "2026-03-27 14:30:00"
}
```

---

## 8. Integration Points

### 8.1 Selection Strategy Filter

```python
def filter_by_sentiment(
    candidates: List[Dict],
    min_score: float = 45
) -> List[Dict]:
    """根据市场情绪过滤候选股票"""
    sentiment = sentiment_service.get_market_sentiment()
    if sentiment.score < min_score:
        return []
    return candidates
```

### 8.2 Alert System

- 当 score < 30 或 score > 75 时触发告警
- 通过 WebSocket 推送给订阅客户端

---

## 9. Error Handling

| 场景 | 处理方式 |
|------|----------|
| 无股票数据 | 返回中性评分(50分)，description="暂无数据" |
| 实时数据获取失败 | 自动降级到 K 线数据，记录日志 |
| K 线数据不足 | 返回中性评分，description="数据不足" |
| 部分股票数据缺失 | 跳过缺失数据，用有效数据计算 |
| 计算异常 | 捕获异常，返回中性评分，记录错误日志 |

---

## 10. Testing Strategy

### 10.1 Test File

```
tests/
└── technical_analysis/
    └── test_market_sentiment.py
```

### 10.2 Test Cases

1. `test_calculate_with_normal_data` - 正常数据计算
2. `test_calculate_with_empty_data` - 空数据返回中性
3. `test_calculate_dimension_boundaries` - 各维度边界值
4. `test_rating_level_mapping` - 评分等级映射
5. `test_service_fallback_to_kline` - 实时数据降级
6. `test_api_endpoint` - API 集成测试

---

## 11. Implementation Notes

1. 不存储计算结果，每次请求实时计算
2. 参考 `a-stock-monitor/scripts/market_sentiment.py` 的算法实现
3. 遵循现有 Repository-Service 架构模式
4. 使用 dataclasses 定义数据结构
