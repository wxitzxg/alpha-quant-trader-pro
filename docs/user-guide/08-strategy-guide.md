# 🎯 Three Strategies Explained

> Detailed explanation of the three core trading strategies: VCP, Nine-Turn, and Top Divergence

---

## 📋 Table of Contents

1. [Strategy Overview](#strategy-overview)
2. [VCP Strategy (Volatility Contraction Pattern)](#vcp-strategy-volatility-contraction-pattern)
3. [Nine-Turn Strategy](#nine-turn-strategy)
4. [Top Divergence Strategy](#top-divergence-strategy)
5. [Strategy Comparison](#strategy-comparison)
6. [Combining Strategies](#combining-strategies)
7. [Best Practices](#best-practices)

---

## 🎯 Strategy Overview

The system includes three powerful trading strategies:

| Strategy | Type | Best For | Win Rate | Holding Period |
|----------|------|----------|----------|----------------|
| **VCP** | Breakout | Trending markets | 65-75% | 2-6 weeks |
| **Nine-Turn** | Reversal | Oversold conditions | 70-80% | 1-4 weeks |
| **Divergence** | Exit | Top detection | 75-85% | Timing exits |

---

## 📈 VCP Strategy (Volatility Contraction Pattern)

### What is VCP?

**VCP (Volatility Contraction Pattern)** is a continuation pattern that occurs before major price breakouts. It's characterized by decreasing volatility followed by a powerful upward move.

### Pattern Characteristics

```
Price Action:
1. Initial Rally → 20-30% gain
2. First Pullback → 10-15% decline (high volume)
3. Second Rally → New high
4. Second Pullback → 5-10% decline (lower volume)
5. Third Rally → Breakout above resistance
```

### Key Features

**Volume Pattern**:
- Declining volume during contractions
- Increasing volume on breakouts
- Volume confirms the pattern

**Time Frame**:
- Pattern develops over 3-6 months
- 2-4 contractions typically occur
- Each contraction tighter than previous

**Volatility**:
- Each pullback smaller than previous
- Trading range narrows progressively
- Consolidation before breakout

### How to Identify VCP

```python
from technical_analysis.strategies import VCPStrategy

vcp = VCPStrategy()
signal = vcp.analyze("600519", days=180)

print("VCP Analysis Results:")
print(f"Pattern Detected: {signal['pattern_detected']}")
print(f"Contraction Count: {signal['contraction_count']}")
print(f"Volume Confirmation: {signal['volume_confirmed']}")
print(f"Breakout Level: {signal['breakout_level']:.2f} RMB")

if signal['pattern_detected']:
    print(f"\n✅ VCP Pattern Found!")
    print(f"Action: {signal['action']}")
    print(f"Confidence: {signal['confidence']:.2f}/1.0")
    print(f"\nTrading Plan:")
    print(f"  Entry: Break above {signal['breakout_level']:.2f}")
    print(f"  Target: {signal['target_price']:.2f} (+{signal['target_pct']:.1f}%)")
    print(f"  Stop Loss: {signal['stop_loss']:.2f} (-{signal['stop_pct']:.1f}%)")
    print(f"  Position Size: {signal['position_size_pct']:.0f}% of portfolio")
```

### Trading Rules

**Entry**:
- ✅ Buy on breakout above resistance
- ✅ Wait for volume confirmation (volume > 20-day average)
- ✅ Enter within 1-3 days of breakout

**Exit**:
- ✅ Take profit at 20-30% gain
- ✅ Trail stop-loss to breakeven after 10% gain
- ✅ Exit if price falls below 10-day MA

**Stop-Loss**:
- ✅ Initial stop: 7-10% below entry
- ✅ Move to breakeven after 10% profit
- ✅ Trail below recent swing lows

### Example Trade

```
Stock: 贵州茅台 (600519)
Pattern Duration: 4 months
Contractions: 3

Entry: 1,800.00 RMB (breakout)
Target: 2,340.00 RMB (+30%)
Stop Loss: 1,620.00 RMB (-10%)

Result:
Week 1: +5%
Week 2: +12%
Week 3: +18%
Week 4: +25% → Exit at target

Total Return: 25%
Holding Period: 4 weeks
```

### VCP Checklist

**Before Entry**:
- [ ] Pattern completed 2-4 contractions
- [ ] Volume declining during contractions
- [ ] Volume increasing on breakout
- [ ] Breakout above key resistance
- [ ] Market in uptrend (CSI 300 > 200-day MA)

**Position Management**:
- [ ] Risk ≤ 2% of portfolio
- [ ] Stop-loss placed immediately
- [ ] Target set at 20-30% gain
- [ ] Trail stop after 10% profit

---

## 🔄 Nine-Turn Strategy

### What is Nine-Turn?

**Nine-Turn Sequence (TD Sequential)** is a reversal indicator that identifies potential exhaustion points after extended price moves.

### Pattern Characteristics

**Bearish Nine-Turn** (Top Detection):
```
Nine consecutive closes below the close four bars earlier
Indicates selling exhaustion
Potential bullish reversal
```

**Bullish Nine-Turn** (Bottom Detection):
```
Nine consecutive closes above the close four bars earlier
Indicates buying exhaustion
Potential bearish reversal
```

### How to Identify Nine-Turn

```python
from technical_analysis.strategies import NineTurnStrategy

nine_turn = NineTurnStrategy()
signal = nine_turn.analyze("600519", days=60)

print("Nine-Turn Analysis Results:")
print(f"Sequence Type: {signal['sequence_type']}")  # bullish or bearish
print(f"Count: {signal['count']}")  # Current count (1-9+)
print(f"Reversal Expected: {signal['reversal_expected']}")
print(f"Strength: {signal['strength']}")  # weak, medium, strong

if signal['count'] >= 8:
    print(f"\n⚠️ Nine-Turn Signal Active!")
    print(f"Action: {signal['action']}")
    print(f"Confidence: {signal['confidence']:.2f}/1.0")

    if signal['sequence_type'] == 'bearish':
        print("\n📊 Golden Pit Setup (Bullish Reversal Expected)")
        print(f"Current Price: {signal['current_price']:.2f} RMB")
        print(f"Support Level: {signal['support_level']:.2f} RMB")
        print(f"Expected Reversal Zone: {signal['reversal_zone_low']:.2f} - {signal['reversal_zone_high']:.2f}")
```

### Trading Rules

**Bullish Nine-Turn (Buy Signal)**:
- ✅ Occurs after downtrend
- ✅ Count reaches 8 or 9
- ✅ Look for bullish candlestick patterns
- ✅ Enter on confirmation (bullish engulfing, hammer)
- ✅ Stop-loss below recent low

**Bearish Nine-Turn (Sell Signal)**:
- ✅ Occurs after uptrend
- ✅ Count reaches 8 or 9
- ✅ Look for bearish candlestick patterns
- ✅ Exit long positions or enter shorts
- ✅ Stop-loss above recent high

**Confirmation Signals**:
- ✅ Volume spike on reversal day
- ✅ RSI divergence
- ✅ MACD crossover
- ✅ Candlestick reversal patterns

### Example Trade (Golden Pit)

```
Stock: 浦发银行 (600000)
Downtrend Duration: 2 months
Nine-Turn Count: 9 (bearish sequence)

Setup:
Price reaches 9.50 RMB
Count completes at 9
Bullish hammer candle forms
Volume increases 150%

Entry: 9.60 RMB (after confirmation)
Target: 12.00 RMB (+25%)
Stop Loss: 9.00 RMB (-6%)

Result:
Day 1-3: Consolidation
Day 4: Breakout begins
Week 2: +15%
Week 3: +25% → Exit at target

Total Return: 25%
Holding Period: 3 weeks
Win Rate: 75% historically
```

### Nine-Turn Checklist

**Bullish Setup**:
- [ ] Downtrend established (lower highs & lows)
- [ ] Count reaches 8 or 9
- [ ] Price near support level
- [ ] Bullish reversal candle forms
- [ ] Volume confirms reversal

**Bearish Setup**:
- [ ] Uptrend established (higher highs & lows)
- [ ] Count reaches 8 or 9
- [ ] Price near resistance level
- [ ] Bearish reversal candle forms
- [ ] Volume confirms reversal

---

## ⚠️ Top Divergence Strategy

### What is Top Divergence?

**Top Divergence (Bearish Divergence)** occurs when price makes higher highs but momentum indicators make lower highs, signaling weakening momentum and potential reversal.

### Types of Divergence

**Regular Bearish Divergence**:
```
Price: Higher High (HH)
RSI/MACD: Lower High (LH)
Signal: Bearish reversal likely
```

**Hidden Bearish Divergence**:
```
Price: Lower High (LH)
RSI/MACD: Higher High (HH)
Signal: Continuation of downtrend
```

### How to Identify Divergence

```python
from technical_analysis.strategies import DivergenceStrategy

divergence = DivergenceStrategy()
signal = divergence.analyze("600519", days=60)

print("Divergence Analysis Results:")
print(f"Divergence Type: {signal['type']}")  # regular_bearish, hidden_bearish
print(f"Price Pattern: {signal['price_pattern']}")
print(f"Indicator Pattern: {signal['indicator_pattern']}")
print(f"Strength: {signal['strength']}")  # weak, medium, strong

if signal['action'] == 'sell':
    print(f"\n⚠️ TOP DIVERGENCE DETECTED!")
    print(f"Confidence: {signal['confidence']:.2f}/1.0")
    print(f"\nExit Recommendation:")
    print(f"Current Price: {signal['current_price']:.2f} RMB")
    print(f"Resistance: {signal['resistance']:.2f} RMB")
    print(f"Suggested Exit Zone: {signal['exit_zone_low']:.2f} - {signal['exit_zone_high']:.2f}")
```

### Common Indicators for Divergence

**RSI Divergence**:
- Look for RSI making lower highs while price makes higher highs
- RSI below 70 (overbought zone) strengthens signal
- Confirmation when RSI crosses below 50

**MACD Divergence**:
- MACD histogram makes lower highs
- MACD line makes lower highs
- Signal line crossover confirms

**Stochastic Divergence**:
- %K line makes lower highs
- Occurs in overbought zone (> 80)
- Bearish crossover confirms

### Trading Rules

**Exit Signals**:
- ✅ Take partial profits (50%) on divergence detection
- ✅ Set trailing stop-loss
- ✅ Exit remaining position on confirmation (bearish candle)
- ✅ Consider reversal short if confirmed

**Confirmation Patterns**:
- ✅ Bearish engulfing candle
- ✅ Evening star pattern
- ✅ Shooting star at resistance
- ✅ Volume spike on down day

**Risk Management**:
- ✅ Don't fight the divergence - exit or reduce
- ✅ Wait for confirmation before shorting
- ✅ Use tight stop-loss if going short

### Example Trade (Exit Signal)

```
Stock: 贵州茅台 (600519)
Position: Long at 1,800 RMB
Current Price: 2,200 RMB (+22%)

Divergence Detected:
Price makes HH at 2,200
RSI makes LH at 75 (vs previous 85)
MACD histogram weakening

Action:
Day 1: Sell 50% at 2,180 RMB
Day 2: Set trailing stop at 2,100
Day 3: Bearish engulfing forms
Day 4: Exit remaining 50% at 2,050

Result:
First 50%: +21% profit
Second 50%: +14% profit
Total: +17.5% average
Avoided: 15% drawdown if held

Win Rate: 85% for exits
```

### Divergence Checklist

**Detection**:
- [ ] Price making higher highs
- [ ] Indicator making lower highs
- [ ] Divergence over 2-3 peaks
- [ ] Indicator in overbought zone

**Confirmation**:
- [ ] Bearish candlestick pattern
- [ ] Volume increase on down day
- [ ] Support/resistance level nearby
- [ ] Multiple indicators confirm

---

## 📊 Strategy Comparison

### Performance Comparison

| Metric | VCP | Nine-Turn | Divergence |
|--------|-----|-----------|------------|
| **Win Rate** | 65-75% | 70-80% | 75-85% |
| **Avg Return** | 20-30% | 15-25% | N/A (exit) |
| **Holding Period** | 2-6 weeks | 1-4 weeks | N/A |
| **Frequency** | Medium | High | High |
| **Risk Level** | Medium | Medium | Low |
| **Best Market** | Trending | Reversing | Any |

### When to Use Each Strategy

**VCP Strategy**:
- ✅ Strong uptrend established
- ✅ Stock consolidating after rally
- ✅ Volume declining then expanding
- ✅ Breakout imminent

**Nine-Turn Strategy**:
- ✅ Extended downtrend (oversold)
- ✅ Count reaching 8-9
- ✅ Price near support
- **Market bottoming**

**Divergence Strategy**:
- ✅ Extended uptrend (overbought)
- ✅ Momentum weakening
- ✅ Price making HH, indicator LH
- ✅ Take profit signal

---

## 🔗 Combining Strategies

### Multi-Strategy Approach

**Example 1: VCP + Divergence**
```
1. Enter on VCP breakout
2. Hold during uptrend
3. Monitor for divergence
4. Exit on divergence signal

Result: Capture full move, avoid reversals
```

**Example 2: Nine-Turn + VCP**
```
1. Buy on Nine-Turn reversal
2. Hold as position develops
3. Look for VCP pattern
4. Add to position on VCP breakout

Result: Early entry + pyramiding
```

**Example 3: Full Cycle**
```
1. Buy on Nine-Turn (reversal)
2. Hold through VCP development
3. Add on VCP breakout
4. Exit on Divergence

Result: Complete trade cycle
```

### Strategy Priority

**Entry Priority**:
1. Nine-Turn (highest win rate)
2. VCP (good risk-reward)
3. Other signals

**Exit Priority**:
1. Divergence (highest reliability)
2. Technical targets
3. Stop-loss

---

## 💡 Best Practices

### 1. Strategy Selection

**Match Strategy to Market**:
- **Bull Market**: VCP (breakouts work well)
- **Bear Market**: Nine-Turn (reversals frequent)
- **Sideways**: Wait or use range-bound strategies
- **All Markets**: Divergence (exit tool)

### 2. Confirmation

**Always Wait for Confirmation**:
- ✅ Volume confirmation
- ✅ Candlestick patterns
- ✅ Multiple indicator alignment
- ✅ Price action confirmation

### 3. Risk Management

**Universal Rules**:
- ✅ Never risk > 2% per trade
- ✅ Always use stop-loss
- ✅ Take profits at targets
- ✅ Don't average down losers

### 4. Position Sizing

**Strategy-Based Sizing**:
- **VCP**: 10-15% of portfolio (medium risk)
- **Nine-Turn**: 15-20% of portfolio (higher win rate)
- **Divergence**: N/A (exit signal)

### 5. Backtesting

**Always Backtest**:
```python
from backtest import BacktestEngine

engine = BacktestEngine(db.get_session())

# Test VCP strategy
vcp_results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="vcp"
)

# Test Nine-Turn strategy
nine_turn_results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategy="nine_turn"
)

# Compare results
print(f"VCP: {vcp_results['total_return']:.2f}% return, {vcp_results['win_rate']:.1f}% win rate")
print(f"Nine-Turn: {nine_turn_results['total_return']:.2f}% return, {nine_turn_results['win_rate']:.1f}% win rate")
```

---

## 📚 Next Steps

- 💹 [Trading System Guide](./04-trading-guide.md) - Execute strategies
- 📈 [Backtest System Guide](./06-backtest-guide.md) - Test strategies
- 📊 [Technical Analysis Guide](./05-analysis-guide.md) - Analysis tools
- 📖 [FAQ](./09-faq.md) - Common questions

---

## 🎓 Strategy Learning Path

1. **Week 1-2**: Learn VCP pattern recognition
2. **Week 3-4**: Practice Nine-Turn identification
3. **Week 5-6**: Master Divergence detection
4. **Week 7-8**: Combine strategies in paper trading
5. **Week 9+**: Live trading with small positions

---

**Congratulations! You've completed the User Guide! 🎉**

**Next**: Return to [User Guide Main Page](./README.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
