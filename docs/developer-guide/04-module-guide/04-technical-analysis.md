# 📊 Technical Analysis Module Guide

> Guide for the Technical Analysis module

## Overview

Provides technical indicators, scoring, and trading strategies.

## Key Components

- **AnalysisService**: Main analysis interface
- **IndicatorEngine**: Calculate technical indicators
- **ScoringEngine**: Five-dimension scoring system
- **StrategyEngine**: Trading strategy execution
- **Indicators**: MA, MACD, RSI, Bollinger Bands, Stochastic

## Usage Examples

```python
from technical_analysis import AnalysisService

service = AnalysisService()

# Analyze stock
analysis = service.analyze_stock("600519", days=120)
print(f"Score: {analysis['overall_score']}")
print(f"Recommendation: {analysis['recommendation']}")

# Get signals
signals = service.get_strategy_signals("vcp")
for signal in signals:
    print(f"{signal['symbol']}: {signal['signal_type']}")
```

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
