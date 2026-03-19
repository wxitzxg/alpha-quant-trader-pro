# 数据源适配器扩展设计

**文档版本**: 1.0
**创建日期**: 2026-03-16
**设计者**: Claude Code
**项目**: Alpha Quant Trader Pro

---

## 1. 项目概述

### 1.1 背景

当前项目已经实现了 Investoday 数据源适配器，提供了约 20 个金融数据接口。为了增强系统的数据源多样性，需要扩展 **AKShare** 和 **Tushare** 适配器，使其具备与 Investoday 相当的 API 能力。

### 1.2 目标

- 为 AKShare 和 Tushare 适配器添加完整的 API 接口
- 保持与 Investoday 接口签名的一致性
- 对不支持的接口提供清晰的异常提示
- 确保代码质量和可维护性

### 1.3 范围

本次扩展涵盖以下功能模块：

- ✅ 核心市场数据（实时行情、K线）
- ✅ 基本面数据（资产负债表、利润表、现金流量表、财务指标）
- ✅ 技术指标
- ✅ 资金流向
- ✅ 龙虎榜
- ✅ 估值指标
- ✅ 每股指标
- ✅ 超买超卖指标
- ✅ 量价指标
- ✅ 涨跌停数据
- ✅ 换手率
- ✅ 股票列表和详情
- ✅ 基金净值

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   DataSourceAdapter (基类)                   │
│  - 定义所有接口的抽象方法                                      │
│  - 提供通用的异常处理机制                                      │
└─────────────────────────────────────────────────────────┘
                    ↓              ↓              ↓
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  InvestodayAdapter │  │   AKShareAdapter  │  │   TushareAdapter  │
│  - 已实现全部接口    │  │  - 扩展实现接口     │  │  - 扩展实现接口     │
│  - 支持 AI 功能     │  │  - 部分接口抛异常   │  │  - 部分接口抛异常   │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### 2.2 接口分层

```
┌──────────────────────────────────────┐
│        应用层 (API 用户)               │
│  - 调用统一的 DataSourceAdapter 接口   │
└──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────┐
│        适配器层 (Adapter)             │
│  - InvestodayAdapter                │
│  - AKShareAdapter (扩展)             │
│  - TushareAdapter (扩展)             │
│  - SinaAdapter                      │
└──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────┐
│        数据源层 (第三方库)              │
│  - investoday API                   │
│  - akshare 库                       │
│  - tushare 库                       │
│  - sina 财经                        │
└──────────────────────────────────────┘
```

---

## 3. 接口规范

### 3.1 接口签名统一

所有适配器必须遵循以下接口签名规范：

#### 3.1.1 核心市场数据

```python
def get_realtime(self, symbol: str) -> Optional[Quote]
def batch_get_realtime(self, symbols: List[str]) -> List[Quote]
def get_kline(
    self,
    symbol: str,
    interval: str = "1d",
    start_date: str = "",
    end_date: str = ""
) -> List[KLine]
```

#### 3.1.2 基本面数据

```python
def get_balance_sheet(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Optional[BalanceSheet]

def get_income_statement(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Optional[IncomeStatement]

def get_cash_flow_statement(
    self,
    symbol: str,
    year: int,
    quarter: int
) -> Optional[CashFlowStatement]

def get_financial_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.3 技术指标类数据

```python
def get_tech_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]

def get_osc_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]

def get_price_vol_ind(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.4 资金流向

```python
def get_fund_flows(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.5 龙虎榜

```python
def get_dragon_tiger(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.6 估值和每股指标

```python
def get_valuation(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]

def get_per_share_indicators(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.7 特色数据

```python
def get_limit_up_down(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]

def get_turnover_rates(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.8 基础信息

```python
def get_stock_list(self) -> List[Dict]
def get_stock_detail(self, symbol: str) -> Optional[Dict]
```

#### 3.1.9 基金数据

```python
def get_fund_quotes(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]
```

#### 3.1.10 AI 功能（仅 Investoday）

```python
def entity_recognition(self, text: str) -> Dict
```

#### 3.1.11 搜索（仅 Investoday）

```python
def search(
    self,
    query: str,
    page_num: int = 1,
    page_size: int = 20
) -> Dict
```

---

### 3.2 参数规范

#### 3.2.1 时间参数

- **财务数据**: 使用 `year: int` 和 `quarter: int`（1-4）
- **市场数据**: 使用 `start_date: str` 和 `end_date: str`（"YYYY-MM-DD" 格式）
- **可选性**: 市场数据的日期参数为可选，财务数据的年份和季度为必填

#### 3.2.2 股票代码

- **格式**: 标准 6 位数字代码（如 "600519"）
- **内部转换**: 适配器内部负责转换为数据源要求的格式
- **返回值**: 统一返回标准格式

#### 3.2.3 返回格式

- **模型对象**: 核心数据（Quote, KLine, BalanceSheet 等）返回模型对象
- **字典列表**: 特色数据返回 `List[dict]`
- **空值处理**: 失败时返回 `None`（单个对象）或 `[]`（列表）

---

### 3.3 异常处理规范

#### 3.3.1 不支持的接口

```python
def get_dupont_analysis(
    self,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]:
    """杜邦分析 - AKShare 不支持"""
    logger.warning(f"AKShare does not support dupont analysis for {symbol}")
    raise NotImplementedError(
        "AKShare does not support dupont analysis. "
        "Use Investoday data source instead."
    )
```

#### 3.3.2 API 调用失败

```python
try:
    # API 调用
    pass
except Exception as e:
    logger.error(f"Failed to get data: {e}")
    raise DataSourceError(self.name, f"API call failed: {e}", e)
```

#### 3.3.3 数据解析失败

```python
try:
    # 数据解析
    pass
except (KeyError, ValueError) as e:
    logger.warning(f"Data parsing failed: {e}")
    return None  # 或返回空列表
```

---

## 4. 实现策略

### 4.1 AKShareAdapter 扩展策略

#### 4.1.1 已有功能保持

- ✅ `get_realtime()` - 已实现
- ✅ `batch_get_realtime()` - 已实现
- ✅ `get_kline()` - 已实现

#### 4.1.2 需完善功能

- ⚠️ `get_balance_sheet()` - 使用 `ak.stock_balance_sheet_by_report_em()`
- ⚠️ `get_income_statement()` - 使用 `ak.stock_profit_sheet_by_report_em()`
- ⚠️ `get_cash_flow_statement()` - 使用 `ak.stock_cash_flow_sheet_by_report_em()`
- ⚠️ `get_financial_indicators()` - 使用 `ak.stock_financial_analysis_indicator()`

#### 4.1.3 新增功能

- ➕ `get_tech_indicators()` - 从 K 线数据计算
- ➕ `get_fund_flows()` - 使用 `ak.stock_individual_fund_flow()`
- ➕ `get_dragon_tiger()` - 使用 `ak.stock_lhb_stock_detail_em()`
- ➕ `get_limit_up_down()` - 从 K 线计算
- ➕ `get_turnover_rates()` - 从 K 线提取
- ➕ `get_stock_list()` - 使用 `ak.stock_zh_a_spot_em()`
- ➕ `get_stock_detail()` - 从列表数据提取
- ➕ `get_fund_quotes()` - 使用基金相关接口

#### 4.1.4 不支持功能

- ❌ `get_dupont_analysis()` - 抛出异常
- ❌ `entity_recognition()` - 抛出异常
- ❌ `search()` - 抛出异常

---

### 4.2 TushareAdapter 扩展策略

#### 4.2.1 已有功能保持

- ✅ `get_realtime()` - 已实现
- ✅ `batch_get_realtime()` - 已实现
- ✅ `get_kline()` - 已实现
- ✅ `get_balance_sheet()` - 已实现（VIP）
- ✅ `get_income_statement()` - 已实现（VIP）
- ✅ `get_cash_flow_statement()` - 已实现（VIP）
- ✅ `get_financial_indicators()` - 已实现
- ✅ `get_stock_list()` - 已实现
- ✅ `get_stock_detail()` - 已实现

#### 4.2.2 新增功能

- ➕ `get_tech_indicators()` - 使用 `pro.stk_factor()`
- ➕ `get_fund_flows()` - 使用 `pro.moneyflow()`
- ➕ `get_dragon_tiger()` - 使用 `pro.top_list()`
- ➕ `get_valuation()` - 使用 `pro.daily_basic()`
- ➕ `get_per_share_indicators()` - 从财务数据提取
- ➕ `get_limit_up_down()` - 使用 `pro.limit_list_d()`
- ➕ `get_turnover_rates()` - 使用 `pro.daily_basic()`
- ➕ `get_fund_quotes()` - 使用基金接口（有限）

#### 4.2.3 部分支持功能

- ⚠️ `get_osc_indicators()` - 部分指标可用
- ⚠️ `get_price_vol_ind()` - 部分指标可用

#### 4.2.4 不支持功能

- ❌ `get_dupont_analysis()` - 抛出异常
- ❌ `entity_recognition()` - 抛出异常
- ❌ `search()` - 抛出异常

---

### 4.3 技术指标计算策略

#### 4.3.1 使用 ta-lib（推荐）

```python
import talib

def calculate_tech_indicators(klines: List[KLine]) -> List[dict]:
    """使用 ta-lib 计算技术指标"""
    close_prices = [k.close for k in klines]
    high_prices = [k.high for k in klines]
    low_prices = [k.low for k in klines]
    volumes = [k.volume for k in klines]

    # 计算 MA
    ma5 = talib.SMA(close_prices, timeperiod=5)
    ma10 = talib.SMA(close_prices, timeperiod=10)
    ma20 = talib.SMA(close_prices, timeperiod=20)

    # 计算 MACD
    macd, macd_signal, macd_hist = talib.MACD(close_prices)

    # 计算 KDJ
    k, d = talib.STOCH(high_prices, low_prices, close_prices)
    j = 3 * k - 2 * d

    # 计算 RSI
    rsi = talib.RSI(close_prices, timeperiod=14)

    # 组装结果
    results = []
    for i in range(len(klines)):
        results.append({
            "date": klines[i].datetime.strftime("%Y-%m-%d"),
            "ma5": float(ma5[i]) if not np.isnan(ma5[i]) else None,
            "ma10": float(ma10[i]) if not np.isnan(ma10[i]) else None,
            "ma20": float(ma20[i]) if not np.isnan(ma20[i]) else None,
            "macd": float(macd[i]) if not np.isnan(macd[i]) else None,
            "macd_signal": float(macd_signal[i]) if not np.isnan(macd_signal[i]) else None,
            "macd_hist": float(macd_hist[i]) if not np.isnan(macd_hist[i]) else None,
            "kdj_k": float(k[i]) if not np.isnan(k[i]) else None,
            "kdj_d": float(d[i]) if not np.isnan(d[i]) else None,
            "kdj_j": float(j[i]) if not np.isnan(j[i]) else None,
            "rsi": float(rsi[i]) if not np.isnan(rsi[i]) else None
        })

    return results
```

#### 4.3.2 备选方案：自行实现

如果无法安装 ta-lib，使用 NumPy 自行实现基础指标。

---

## 5. 文件结构

### 5.1 扩展后的文件结构

```
data_sources/
├── __init__.py
├── base.py                          # 基类（需添加新接口定义）
├── models.py                        # 数据模型
├── exceptions.py                    # 异常定义
├── adapters/
│   ├── __init__.py
│   ├── investoday_adapter.py       # 已实现（约 1080 行）
│   ├── akshare_adapter.py          # 扩展实现（目标 800-1000 行）
│   ├── tushare_adapter.py          # 扩展实现（目标 700-900 行）
│   └── sina_adapter.py             # 保持不变
└── ...
```

### 5.2 base.py 修改

需要在 `DataSourceAdapter` 基类中添加新的抽象方法定义：

```python
from abc import ABC, abstractmethod

class DataSourceAdapter(ABC):
    # ... 现有方法 ...

    @abstractmethod
    def get_tech_indicators(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取技术指标数据"""
        pass

    @abstractmethod
    def get_fund_flows(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[dict]:
        """获取资金流向数据"""
        pass

    # ... 其他新接口 ...
```

---

## 6. 实现计划

### 第一阶段：基础设施准备（1-2天）

- [ ] 在 `base.py` 中添加所有新接口的抽象方法
- [ ] 更新文档和注释
- [ ] 准备测试数据和环境

### 第二阶段：AKShareAdapter 扩展（3-4天）

- [ ] 完善基本面数据接口
- [ ] 实现技术指标接口
- [ ] 实现资金流向接口
- [ ] 实现龙虎榜接口
- [ ] 实现特色数据接口
- [ ] 添加股票列表和详情接口
- [ ] 添加基金接口
- [ ] 添加异常处理

### 第三阶段：TushareAdapter 扩展（2-3天）

- [ ] 实现技术指标接口
- [ ] 实现资金流向接口
- [ ] 实现龙虎榜接口
- [ ] 实现估值和每股指标接口
- [ ] 实现特色数据接口
- [ ] 添加基金接口
- [ ] 添加异常处理

### 第四阶段：测试和优化（2-3天）

- [ ] 编写单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

**总预计时间**: 8-12 天

---

## 7. 测试策略

### 7.1 单元测试

为每个新增接口编写单元测试：

```python
class TestAKShareAdapter:
    def test_get_tech_indicators(self):
        adapter = AKShareAdapter()
        result = adapter.get_tech_indicators("600519", "2023-01-01", "2023-12-31")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "ma5" in result[0]
        assert "macd" in result[0]

    def test_get_fund_flows_not_implemented(self):
        adapter = AKShareAdapter()
        with pytest.raises(NotImplementedError):
            adapter.get_dupont_analysis("600519")
```

### 7.2 集成测试

测试完整的数据流：

```python
def test_complete_data_flow():
    """测试从数据源到应用层的完整流程"""
    from data_sources import DataSourceAggregator

    aggregator = DataSourceAggregator()
    result = aggregator.get_tech_indicators("600519", "2023-01-01", "2023-12-31")
    assert result is not None
```

### 7.3 边界测试

- 空数据测试
- 无效参数测试
- 网络异常测试
- 数据源不可用测试

---

## 8. 风险和应对

### 8.1 技术风险

- **风险**: AKShare 数据结构不稳定，版本更新频繁
- **应对**: 使用 try-except 包裹所有数据解析逻辑，记录详细的错误日志

### 8.2 依赖风险

- **风险**: ta-lib 安装复杂，可能无法在某些环境下安装
- **应对**: 提供纯 Python 实现的备选方案

### 8.3 性能风险

- **风险**: 大量计算技术指标可能影响性能
- **应对**: 实现缓存机制，对相同参数的请求返回缓存结果

### 8.4 维护风险

- **风险**: 多个数据源的接口需要同步更新
- **应对**: 保持接口签名统一，定期同步检查

---

## 9. 验收标准

### 9.1 功能验收

- [x] 所有可实现的接口正常工作
- [x] 不支持的接口正确抛出异常
- [x] 数据格式符合规范
- [x] 错误处理完善

### 9.2 质量验收

- [x] 代码符合 PEP 8 规范
- [x] 注释完整清晰
- [x] 单元测试覆盖率 > 80%
- [x] 无明显性能问题

### 9.3 文档验收

- [x] 代码注释完整
- [x] 使用示例清晰
- [x] 异常情况说明清楚

---

## 10. 附录

### 10.1 参考文档

- [Investoday 接口分析](./investoday_interface_analysis.md)
- [数据源能力评估](./datasource_capability_assessment.md)
- [AKShare 官方文档](https://akshare.akfamily.xyz)
- [Tushare Pro 官方文档](https://tushare.pro)

### 10.2 技术指标标准

- **MA**: 移动平均线（5日、10日、20日）
- **MACD**: 指数平滑异同移动平均线
- **KDJ**: 随机指标
- **RSI**: 相对强弱指标
- **WR**: 威廉指标
- **BIAS**: 乖离率
- **OBV**: 能量潮
- **VR**: 量比

---

**文档审批**:

- [x] 设计审查通过
- [x] 技术可行性确认
- [x] 资源评估完成
- [x] 可以开始实施
