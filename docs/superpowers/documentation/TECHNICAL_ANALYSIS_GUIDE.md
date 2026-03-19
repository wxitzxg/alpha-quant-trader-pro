# 技术分析模块使用指南

## 📊 模块概述

`technical_analysis` 模块提供完整的股票技术分析功能，包括：

- **五维共振总控引擎** - 整合趋势、形态、位置、动能、触发五个维度评分
- **三大交易策略** - VCP 爆发突击、九转黄金坑、顶部背离止盈
- **完整指标体系** - 趋势、动量、波动率、成交量指标

## 🏗️ 架构设计

```
technical_analysis/
├── indicators/              # 技术指标层
│   ├── base_indicators.py   # 基础指标 (MA、MACD、RSI、布林带等)
│   ├── td_sequential.py     # 神奇九转
│   ├── vcp_detector.py      # VCP 形态识别
│   ├── divergence_check.py  # MACD 背离检测
│   └── zigzag.py            # ZigZag 之字转向
│
├── strategies/              # 策略层
│   ├── vcp_breakout.py      # VCP 爆发突击策略
│   ├── td_golden_pit.py     # 九转黄金坑策略
│   └── top_divergence.py    # 顶部背离止盈策略
│
├── engines/                 # 引擎层
│   └── ultimate_engine.py   # 五维共振总控引擎
│
└── services/                # 服务层
    └── analysis_service.py  # 技术分析服务
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install ta numpy
```

### 2. 基本使用

```python
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService

# 初始化
db = DatabaseManager("postgresql://...")
with db.get_session() as session:
    analysis_service = AnalysisService(session)

    # 五维共振分析
    result = analysis_service.analyze_stock(
        symbol="600519",
        interval="1d",
        days=120
    )

    print(f"总分: {result['total_score']}/{result['max_score']}")
    print(f"决策: {result['action']}")
    print(f"置信度: {result['confidence_level']} 级")
    print(f"建议仓位: {result['position_suggestion'] * 100:.0f}%")
```

## 📈 核心功能

### 1. 五维共振分析

五维评分系统 (0-100分):

- **D1 趋势维 (20分)**: EMA50/200 多头排列 + ZigZag 趋势
- **D2 形态维 (30分)**: VCP 形态 + 布林带收口
- **D3 位置维 (20分)**: 布林带位置 + RSI
- **D4 动能维 (10分)**: MACD 背离 + 成交量
- **D5 触发维 (20分)**: 神奇九转 + 枢轴突破

决策阈值:
- **S 级 (≥85分)**: STRONG_BUY - 满仓 20%
- **A 级 (≥65分)**: BUY - 半仓 10%
- **B 级 (≥40分)**: HOLD - 轻仓 5%
- **C 级 (<40分)**: WAIT - 观望

### 2. 三大策略

#### VCP 爆发突击策略

```python
result = analysis_service.analyze_with_strategies(
    symbol="600519",
    interval="1d",
    days=120
)

vcp_signal = result['strategies']['vcp_breakout']['signal']  # BUY/WATCH/HOLD
vcp_score = result['strategies']['vcp_breakout']['score']    # 0-100
```

**策略逻辑:**
1. 识别 VCP 形态 (波动收缩)
2. 等待突破枢轴点
3. 成交量确认 (>1.5 倍均量)
4. 结合趋势和位置确认

#### 九转黄金坑策略

```python
td_signal = result['strategies']['td_golden_pit']['signal']  # BUY/HOLD
td_score = result['strategies']['td_golden_pit']['score']    # 0-100
```

**策略逻辑:**
1. 等待神奇九转低九信号
2. 确认趋势向上 (EMA 多头排列)
3. 确认位置超卖 (RSI < 30)
4. 有效低九买入

#### 顶部背离止盈策略

```python
div_signal = result['strategies']['top_divergence']['signal']  # SELL/WATCH/HOLD
div_score = result['strategies']['top_divergence']['score']    # 0-100
risk_level = result['strategies']['top_divergence']['risk_level']  # HIGH/MEDIUM/LOW
```

**策略逻辑:**
1. 检测顶背离信号 (价格新高，指标未新高)
2. 确认超买状态 (RSI > 70)
3. 提供止盈建议

### 3. 生成分析报告

```python
report = analysis_service.generate_analysis_report(
    symbol="600519",
    interval="1d",
    days=120
)

print(report)
```

**报告内容:**
- 五维共振总分和决策
- 各维度详细评分
- 三大策略信号概要
- 当前价格和分析日期

### 4. 获取技术指标

```python
indicators = analysis_service.get_technical_indicators(
    symbol="600519",
    interval="1d",
    days=60
)

print(f"均线趋势: {indicators['latest_signals']['ma_trend']}")
print(f"MACD 信号: {indicators['latest_signals']['macd_signal']}")
print(f"RSI 状态: {indicators['latest_signals']['rsi_condition']}")
print(f"布林带位置: {indicators['latest_signals']['bb_position']}")
print(f"成交量状态: {indicators['latest_signals']['volume_condition']}")
```

## 📋 API 参考

### AnalysisService

#### `analyze_stock(symbol, interval="1d", start_date=None, end_date=None, days=120)`

完整五维共振分析

**返回值:**
```python
{
    'total_score': 75,              # 总分
    'max_score': 100,               # 满分
    'score_percentage': 75.0,       # 得分百分比
    'action': 'BUY',                # 决策: STRONG_BUY/BUY/HOLD/WAIT
    'position_suggestion': 0.10,    # 建议仓位 (0-1)
    'confidence_level': 'A',        # 置信度: S/A/B/C
    'dimension_scores': {           # 各维度得分
        'D1': 15,
        'D2': 25,
        'D3': 18,
        'D4': 8,
        'D5': 15
    },
    'dimension_details': {...},     # 各维度详情
    'symbol': '600519',
    'interval': '1d',
    'data_points': 120,
    'analysis_date': '2026-03-16'
}
```

#### `analyze_with_strategies(symbol, interval="1d", start_date=None, end_date=None, days=120)`

三大策略分析

**返回值:**
```python
{
    'symbol': '600519',
    'strategies': {
        'vcp_breakout': {
            'signal': 'BUY',        # 信号: BUY/WATCH/HOLD
            'score': 65,            # 得分
            'confidence': 'medium', # 置信度: high/medium/low
            'entry_price': 1500.0,  # 建议入场价
            'stop_loss': 1450.0,    # 止损价
            'take_profit': 1600.0,  # 止盈价
            'recommendation': '...' # 建议文字
        },
        'td_golden_pit': {...},
        'top_divergence': {...}
    }
}
```

#### `generate_analysis_report(symbol, interval="1d", start_date=None, end_date=None, days=120)`

生成完整分析报告

**返回值:** 格式化的文本报告

#### `get_technical_indicators(symbol, interval="1d", start_date=None, end_date=None, days=60)`

获取技术指标数据

**返回值:**
```python
{
    'symbol': '600519',
    'current_price': 1500.0,
    'latest_signals': {
        'ma_trend': 'strong_uptrend',
        'macd_signal': 'bullish',
        'rsi_condition': 'neutral',
        'bb_position': 'lower_half',
        'volume_condition': 'normal',
        ...
    },
    'data_points': 60
}
```

## 🎯 使用场景

### 场景 1: 股票筛选

```python
# 批量分析多只股票
symbols = ["600519", "000001", "300750", "600036"]

for symbol in symbols:
    result = analysis_service.analyze_stock(symbol, days=120)

    if result.get('action') in ['STRONG_BUY', 'BUY']:
        print(f"✅ {symbol}: {result['action']} ({result['total_score']}分)")
    else:
        print(f"❌ {symbol}: {result['action']}")
```

### 场景 2: 策略回测

```python
# 获取历史信号
from technical_analysis.indicators import VCPDetector
import pandas as pd

# 加载历史数据
df = load_historical_data("600519")

# 检测 VCP 形态
vcp = VCPDetector(df)
vcp_result = vcp.detect_vcp()

if vcp_result['breakout_detected']:
    print("发现 VCP 突破信号!")
    # 执行买入逻辑
```

### 场景 3: 风险控制

```python
# 检查顶部风险
result = analysis_service.analyze_with_strategies("600519")

divergence = result['strategies']['top_divergence']
if divergence['risk_level'] == 'HIGH':
    print("⚠️ 高风险警告: 发现顶部背离信号")
    # 执行减仓或止盈逻辑
```

## 📚 技术指标说明

### 趋势指标

- **MA (移动平均线)**: MA5/MA10/MA20/MA50/MA200
- **EMA (指数移动平均)**: EMA12/EMA26/EMA50/EMA200
- **MACD**: 快线(12)、慢线(26)、信号线(9)
- **ADX**: 趋势强度指标 (14周期)

### 动量指标

- **RSI**: 相对强弱指标 (14周期)
- **Stochastic**: 随机指标 (14周期, 平滑3)
- **CCI**: 商品通道指数 (20周期)
- **Williams %R**: 威廉指标 (14周期)

### 波动率指标

- **布林带**: 中轨(20周期)、上下轨(2标准差)
- **ATR**: 平均真实波幅 (14周期)
- **标准差**: 20周期标准差

### 成交量指标

- **OBV**: 能量潮指标
- **量比**: 当前成交量 / 5日均量

### 高级指标

- **TD Sequential**: 神奇九转 (9周期, 比较4周期)
- **VCP**: 波动收缩形态 (2-4次回调)
- **Divergence**: MACD 背离检测
- **ZigZag**: 之字转向 (5% 阈值)

## ⚠️ 注意事项

1. **数据要求**: 至少需要 30 条 K 线数据才能进行有效分析
2. **同步数据**: 使用前请确保已通过 `stock_market` 模块同步 K 线数据
3. **策略组合**: 建议结合多个策略信号进行决策，不要仅依赖单一指标
4. **风险控制**: 所有策略都应配合止损和仓位管理
5. **仅供参考**: 技术分析不能保证 100% 准确，请结合基本面分析

## 🧪 测试

运行测试:

```bash
pytest tests/technical_analysis/ -v
```

## 📖 相关文档

- [股票市场模块文档](../stock_market/README.md)
- [持仓管理模块文档](../portfolio_manager/README.md)
- [数据源聚合模块文档](../data_sources/README.md)

## 🆘 常见问题

### Q1: 数据不足错误

**错误信息**: `需要至少 30 条 K 线数据，当前只有 XX 条`

**解决方法**:
```python
# 先同步 K 线数据
from stock_market.services import KLineService
from common.database import DatabaseManager

db = DatabaseManager("...")
with db.get_session() as session:
    kline_service = KLineService(session)
    kline_service.sync_single_kline("600519", "1d", "2023-01-01")
```

### Q2: 依赖安装失败

**错误信息**: `No module named 'ta'`

**解决方法**:
```bash
pip install ta numpy pandas sqlalchemy
```

### Q3: 分析结果不准确

**可能原因**:
1. 数据质量问题 (缺失、异常值)
2. K 线周期选择不当
3. 回溯天数不足

**建议**:
- 使用至少 120 天数据
- 检查数据完整性
- 尝试不同周期 (1d/5d/10d)

## 📞 技术支持

如有问题，请查看:
- [项目 README](../README.md)
- [测试示例](../examples/technical_analysis_example.py)
- [单元测试](../tests/technical_analysis/)
