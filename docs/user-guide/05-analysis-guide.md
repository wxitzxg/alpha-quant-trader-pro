# 📊 Technical Analysis Guide

> Complete guide to the technical analysis system and five-dimensional resonance scoring

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Five-Dimensional Resonance Scoring](#five-dimensional-resonance-scoring)
3. [Using the Analysis System](#using-the-analysis-system)
4. [Technical Indicators](#technical-indicators)
5. [Strategy Integration](#strategy-integration)
6. [Interpreting Results](#interpreting-results)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

The technical analysis system provides advanced tools for evaluating stocks and generating trading signals.

### Core Features

- ✅ **Five-Dimensional Resonance Scoring** - Comprehensive stock evaluation
- ✅ **Complete Indicator Library** - 20+ technical indicators
- ✅ **Three Built-in Strategies** - VCP, Nine-Turn, Divergence
- ✅ **Custom Analysis Engine** - Extensible analysis framework
- ✅ **Historical Data Analysis** - Multi-timeframe support

### System Architecture

```
┌─────────────────────────────────────────┐
│         AnalysisService                  │
│  - High-level analysis interface         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Analysis Engine                  │
│  - Scoring Engine                        │
│  - Strategy Engine                       │
│  - Indicator Engine                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Technical Indicators             │
│  - Trend Indicators                      │
│  - Momentum Indicators                   │
│  - Volatility Indicators                 │
│  - Volume Indicators                     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Data Layer (KLine Data)          │
│  - Historical price data                 │
└─────────────────────────────────────────┘
```

---

## 📐 Five-Dimensional Resonance Scoring

### Scoring System Overview

The five-dimensional resonance scoring system evaluates stocks across five key dimensions:

| Dimension | Weight | Max Score | Description |
|-----------|--------|-----------|-------------|
| **Trend** | 20% | 20 points | Overall market trend direction |
| **Pattern** | 20% | 20 points | Chart pattern recognition |
| **Position** | 20% | 20 points | Price position and levels |
| **Momentum** | 20% | 20 points | Price momentum and strength |
| **Trigger** | 20% | 20 points | Entry signal timing |

**Total Score**: 100 points maximum

### Score Interpretation

| Score Range | Rating | Action | Confidence |
|-------------|--------|--------|------------|
| 90-100 | ⭐⭐⭐⭐⭐ | Strong Buy | Very High |
| 80-89 | ⭐⭐⭐⭐ | Buy | High |
| 70-79 | ⭐⭐⭐ | Hold/Consider | Medium |
| 60-69 | ⭐⭐ | Watch | Low |
| 0-59 | ⭐ | Avoid/Sell | Very Low |

---

## 🚀 Using the Analysis System

### Basic Analysis

```python
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService

# Initialize database and analysis service
db = DatabaseManager("postgresql://user:password@localhost:5432/stock_market")
analysis_service = AnalysisService(db.get_session())

# Analyze a stock (e.g., 贵州茅台 600519)
result = analysis_service.analyze_stock("600519", days=120)

print("=" * 60)
print(f"Stock: {result['stock_name']} ({result['symbol']})")
print("=" * 60)
print(f"Total Score: {result['total_score']}/{result['max_score']}")
print(f"Action: {result['action']}")
print(f"Confidence Level: {result['confidence_level']} level")
print("=" * 60)

# Detailed breakdown
print("\nDimension Scores:")
for dimension, score in result['dimension_scores'].items():
    print(f"  {dimension}: {score['score']}/{score['max_score']}")
    print(f"    Reason: {score['reason']}")
```

### Multi-Stock Analysis

```python
# Analyze multiple stocks
stock_symbols = ["600519", "600000", "000001", "601318"]

for symbol in stock_symbols:
    result = analysis_service.analyze_stock(symbol, days=120)

    print(f"\n{result['stock_name']} ({result['symbol']}):")
    print(f"  Score: {result['total_score']}/{result['max_score']}")
    print(f"  Action: {result['action']}")
    print(f"  Confidence: {result['confidence_level']}")

    # Filter for high-scoring stocks
    if result['total_score'] >= 80:
        print("  ⭐ RECOMMENDED")
```

### Historical Analysis

```python
# Analyze stock over different time periods
time_periods = [30, 60, 90, 120]  # days

for days in time_periods:
    result = analysis_service.analyze_stock("600519", days=days)

    print(f"\n{days}-Day Analysis:")
    print(f"  Score: {result['total_score']}/{result['max_score']}")
    print(f"  Trend: {result['dimension_scores']['trend']['score']}/20")
    print(f"  Momentum: {result['dimension_scores']['momentum']['score']}/20")
```

---

## 📈 Technical Indicators

### Trend Indicators

#### Moving Averages (MA)

```python
from technical_analysis.indicators import MovingAverage

# Get moving averages
ma = MovingAverage()
stock_data = get_kline_data("600519", days=120)

# Simple Moving Average
sma_5 = ma.sma(stock_data['close'], period=5)
sma_10 = ma.sma(stock_data['close'], period=10)
sma_20 = ma.sma(stock_data['close'], period=20)
sma_60 = ma.sma(stock_data['close'], period=60)

print(f"SMA 5: {sma_5[-1]:.2f}")
print(f"SMA 10: {sma_10[-1]:.2f}")
print(f"SMA 20: {sma_20[-1]:.2f}")
print(f"SMA 60: {sma_60[-1]:.2f}")

# Check for MA crossover (bullish signal)
if sma_5[-1] > sma_10[-1] > sma_20[-1]:
    print("✅ Bullish MA alignment")
```

#### MACD (Moving Average Convergence Divergence)

```python
from technical_analysis.indicators import MACD

macd = MACD()
macd_values = macd.calculate(stock_data['close'])

print(f"MACD: {macd_values['macd'][-1]:.2f}")
print(f"Signal: {macd_values['signal'][-1]:.2f}")
print(f"Histogram: {macd_values['histogram'][-1]:.2f}")

# Bullish signal
if macd_values['histogram'][-1] > 0 and macd_values['histogram'][-2] <= 0:
    print("✅ MACD Bullish Crossover")
```

### Momentum Indicators

#### RSI (Relative Strength Index)

```python
from technical_analysis.indicators import RSI

rsi = RSI()
rsi_values = rsi.calculate(stock_data['close'], period=14)

current_rsi = rsi_values[-1]
print(f"RSI: {current_rsi:.2f}")

# RSI interpretation
if current_rsi < 30:
    print("⚠️ Oversold (Potential Buy)")
elif current_rsi > 70:
    print("⚠️ Overbought (Potential Sell)")
elif 50 < current_rsi < 70:
    print("📈 Bullish Momentum")
elif 30 < current_rsi < 50:
    print("📉 Bearish Momentum")
```

#### Stochastic Oscillator

```python
from technical_analysis.indicators import Stochastic

stoch = Stochastic()
stoch_values = stoch.calculate(stock_data['high'], stock_data['low'], stock_data['close'])

print(f"K: {stoch_values['k'][-1]:.2f}")
print(f"D: {stoch_values['d'][-1]:.2f}")

# Golden Cross (bullish)
if stoch_values['k'][-1] > stoch_values['d'][-1] and stoch_values['k'][-2] <= stoch_values['d'][-2]:
    if stoch_values['k'][-1] < 80:  # Not overbought
        print("✅ Stochastic Golden Cross")
```

### Volatility Indicators

#### Bollinger Bands

```python
from technical_analysis.indicators import BollingerBands

bb = BollingerBands()
bb_values = bb.calculate(stock_data['close'], period=20, std_dev=2)

print(f"Upper Band: {bb_values['upper'][-1]:.2f}")
print(f"Middle Band (SMA 20): {bb_values['middle'][-1]:.2f}")
print(f"Lower Band: {bb_values['lower'][-1]:.2f}")

current_price = stock_data['close'][-1]

# Price position relative to bands
if current_price > bb_values['upper'][-1]:
    print("⚠️ Price above upper band (Overbought)")
elif current_price < bb_values['lower'][-1]:
    print("⚠️ Price below lower band (Oversold)")
elif current_price < bb_values['middle'][-1]:
    print("📉 Price below middle band (Bearish)")
else:
    print("📈 Price above middle band (Bullish)")
```

### Volume Indicators

#### OBV (On-Balance Volume)

```python
from technical_analysis.indicators import OBV

obv = OBV()
obv_values = obv.calculate(stock_data['close'], stock_data['volume'])

print(f"OBV: {obv_values[-1]:,.0f}")

# OBV trend
if obv_values[-1] > obv_values[-5]:
    print("📈 OBV Rising (Bullish)")
else:
    print("📉 OBV Falling (Bearish)")
```

---

## 🎯 Strategy Integration

### VCP (Volatility Contraction Pattern) Strategy

```python
from technical_analysis.strategies import VCPStrategy

vcp = VCPStrategy()
signal = vcp.analyze("600519", days=120)

print(f"VCP Signal: {signal['action']}")
print(f"Confidence: {signal['confidence']:.2f}")
print(f"Reason: {signal['reason']}")

if signal['action'] == 'buy':
    print("✅ VCP Buy Signal Detected")
    print(f"   Entry Price: {signal['entry_price']:.2f}")
    print(f"   Target Price: {signal['target_price']:.2f}")
    print(f"   Stop Loss: {signal['stop_loss']:.2f}")
```

### Nine-Turn Sequence Strategy

```python
from technical_analysis.strategies import NineTurnStrategy

nine_turn = NineTurnStrategy()
signal = nine_turn.analyze("600519", days=60)

print(f"Nine-Turn Signal: {signal['action']}")
print(f"Sequence Count: {signal['count']}")
print(f"Expected Reversal: {signal['reversal_expected']}")

if signal['action'] == 'buy' and signal['count'] >= 8:
    print("✅ Nine-Turn Buy Signal (Golden Pit)")
```

### Top Divergence Strategy

```python
from technical_analysis.strategies import DivergenceStrategy

divergence = DivergenceStrategy()
signal = divergence.analyze("600519", days=60)

print(f"Divergence Type: {signal['type']}")
print(f"Signal: {signal['action']}")
print(f"Strength: {signal['strength']}")

if signal['action'] == 'sell' and signal['type'] == 'bearish':
    print("⚠️ Top Divergence Sell Signal (Take Profit)")
```

---

## 📊 Interpreting Results

### Reading the Analysis Report

```python
result = analysis_service.analyze_stock("600519", days=120)

# Overall Assessment
print(f"\n{'='*60}")
print(f"OVERALL ASSESSMENT")
print(f"{'='*60}")
print(f"Total Score: {result['total_score']}/{result['max_score']}")
print(f"Rating: {'⭐' * result['confidence_level']}")
print(f"Recommended Action: {result['action']}")
print(f"{'='*60}")

# Trend Analysis
trend_score = result['dimension_scores']['trend']
print(f"\n📈 TREND ({trend_score['score']}/20)")
print(f"   Status: {trend_score['status']}")
print(f"   Strength: {trend_score['strength']}")
print(f"   Reason: {trend_score['reason']}")

# Pattern Analysis
pattern_score = result['dimension_scores']['pattern']
print(f"\n🎯 PATTERN ({pattern_score['score']}/20)")
print(f"   Pattern Type: {pattern_score['pattern_type']}")
print(f"   Completion: {pattern_score['completion']:.0f}%")
print(f"   Reason: {pattern_score['reason']}")

# Position Analysis
position_score = result['dimension_scores']['position']
print(f"\n📍 POSITION ({position_score['score']}/20)")
print(f"   Support Level: {position_score['support']:.2f}")
print(f"   Resistance Level: {position_score['resistance']:.2f}")
print(f"   Distance to Target: {position_score['distance_to_target']:.1f}%")
print(f"   Reason: {position_score['reason']}")

# Momentum Analysis
momentum_score = result['dimension_scores']['momentum']
print(f"\n⚡ MOMENTUM ({momentum_score['score']}/20)")
print(f"   Strength: {momentum_score['strength']}")
print(f"   Indicators: {', '.join(momentum_score['indicators'])}")
print(f"   Reason: {momentum_score['reason']}")

# Trigger Analysis
trigger_score = result['dimension_scores']['trigger']
print(f"\n🔔 TRIGGER ({trigger_score['score']}/20)")
print(f"   Signal Type: {trigger_score['signal_type']}")
print(f"   Timing: {trigger_score['timing']}")
print(f"   Confirmed: {trigger_score['confirmed']}")
print(f"   Reason: {trigger_score['reason']}")

# Trading Recommendations
print(f"\n{'='*60}")
print(f"TRADING RECOMMENDATIONS")
print(f"{'='*60}")

for rec in result['recommendations']:
    print(f"• {rec}")

print(f"{'='*60}")
```

### Score Breakdown Example

```
================================================================================
Stock: 贵州茅台 (600519)
================================================================================
Total Score: 85/100
Action: BUY
Confidence Level: 4 level
================================================================================

Dimension Scores:
  Trend: 18/20
    Reason: Strong uptrend with higher highs and higher lows
  Pattern: 16/20
    Reason: Cup and handle pattern 80% complete
  Position: 19/20
    Reason: Price near support, good risk-reward ratio
  Momentum: 17/20
    Reason: RSI 65, MACD positive, volume increasing
  Trigger: 15/20
    Reason: Breakout signal forming, wait for confirmation

Trading Recommendations:
• Consider buying on breakout above 1800.00
• Set stop-loss at 1700.00 (5% below entry)
• Target price: 2000.00 (11% upside)
• Position size: 10-15% of portfolio
• Hold time: 2-4 weeks
================================================================================
```

---

## 💡 Best Practices

### 1. Use Multiple Timeframes

```python
# Analyze across multiple timeframes
timeframes = [30, 60, 90, 120]

for days in timeframes:
    result = analysis_service.analyze_stock("600519", days=days)

    print(f"\n{days}-Day Analysis:")
    print(f"  Score: {result['total_score']}/100")
    print(f"  Trend Direction: {result['dimension_scores']['trend']['status']}")

# Look for consistency across timeframes
if all(result['total_score'] >= 70 for result in results):
    print("✅ Strong signal across all timeframes")
```

### 2. Combine with Fundamental Analysis

```python
# Get fundamental data
from data_sources import StockAPI
fundamentals = StockAPI.get_fundamentals("600519")

# Technical analysis
technical_result = analysis_service.analyze_stock("600519", days=120)

# Combined assessment
print("Combined Analysis:")
print(f"  Technical Score: {technical_result['total_score']}/100")
print(f"  PE Ratio: {fundamentals['pe_ratio']:.2f}")
print(f"  ROE: {fundamentals['roe']:.2f}%")

if technical_result['total_score'] >= 80 and fundamentals['roe'] > 15:
    print("✅ Strong technical + fundamental signal")
```

### 3. Validate with Backtesting

```python
from backtest import BacktestEngine

# Test the analysis signals
engine = BacktestEngine(db.get_session())

# Run backtest using analysis signals
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="analysis_based",  # Use analysis signals
    analysis_service=analysis_service
)

print(f"Backtest Results:")
print(f"  Win Rate: {results['win_rate']:.2f}%")
print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"  Total Return: {results['total_return']:.2f}%")
```

### 4. Monitor Score Changes

```python
# Track score over time
historical_scores = []

for day_offset in range(0, 30, 5):  # Every 5 days for 30 days
    result = analysis_service.analyze_stock("600519", days=120 - day_offset)
    historical_scores.append({
        'day': day_offset,
        'score': result['total_score'],
        'action': result['action']
    })

# Look for improving trends
if historical_scores[-1]['score'] > historical_scores[0]['score'] + 10:
    print("📈 Score improving over time (bullish)")
```

### 5. Use Score Thresholds

```python
# Define your own thresholds
BUY_THRESHOLD = 80
HOLD_THRESHOLD = 60
SELL_THRESHOLD = 40

result = analysis_service.analyze_stock("600519", days=120)

if result['total_score'] >= BUY_THRESHOLD:
    print("✅ STRONG BUY signal")
elif result['total_score'] >= HOLD_THRESHOLD:
    print("📊 HOLD / WATCH signal")
else:
    print("⚠️ AVOID / SELL signal")
```

---

## 📚 Next Steps

- 📙 [Backtest System Guide](./06-backtest-guide.md) - Test your analysis
- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Strategy details
- 💹 [Trading System Guide](./04-trading-guide.md) - Execute trades
- 📖 [Portfolio Management Guide](./07-portfolio-management.md) - Manage positions

---

**Next Chapter**: [Backtest System Guide →](./06-backtest-guide.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
