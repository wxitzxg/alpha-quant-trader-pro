# 🚀 5-Minute Quick Start

> Get started with Alpha Quant Trader Pro in just 5 minutes

---

## 📋 What You'll Learn

In this quick start guide, you will:
- ✅ Install the system
- ✅ Set up your first account
- ✅ Execute your first trade
- ✅ Run your first technical analysis
- ✅ Test your first strategy with backtesting

**Time Required**: 5 minutes
**Difficulty**: Beginner
**Prerequisites**: Basic Python knowledge, PostgreSQL installed

---

## 🎯 Step 1: Installation (1 minute)

### 1.1 Clone the Repository

```bash
git clone https://github.com/your-org/alpha-quant-trader-pro.git
cd alpha-quant-trader-pro
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.3 Configure Environment

```bash
cp .env.example .env
# Edit .env file with your database settings
```

**Required Settings in `.env`**:
```bash
DATABASE__URL=postgresql://user:password@localhost/stock_market
TUSHARE_TOKEN=your_tushare_token_here
```

### 1.4 Initialize Database

```bash
# Create database
createdb stock_market

# Tables are auto-created when API server starts
# Start the server to initialize tables:
python -m api_server.main
# You should see: "数据库表同步完成"
```

---

## 🎯 Step 2: First Trade (2 minutes)

### 2.1 Initialize Your Account

```python
from portfolio_manager import PortfolioCommands

# Create portfolio manager instance
portfolio = PortfolioCommands()
portfolio.add_cash(100000)  # Add 100,000 initial capital
```

### 2.2 Buy Your First Stock

```python
# Buy 100 shares of 浦发银行 (600000) at 10.0 price
portfolio.buy(
    symbol="600000",
    quantity=100,
    price=10.0
)

print("✅ First buy order executed!")
```

### 2.3 Check Your Position

```python
# View your positions
positions = portfolio.get_positions()
for pos in positions:
    print(f"Stock: {pos.stock_name} ({pos.symbol})")
    print(f"Quantity: {pos.quantity}")
    print(f"Average Cost: {pos.average_cost:.2f}")
    print("---")

# View account summary
summary = portfolio.account_summary()
print(f"Total Cash: {summary.cash:.2f}")
print(f"Total Market Value: {summary.total_market_value:.2f}")
print(f"Total Assets: {summary.total_assets:.2f}")
```

### 2.4 Sell Some Shares

```python
# Sell 50 shares at 12.0 price
portfolio.sell(
    symbol="600000",
    quantity=50,
    price=12.0
)

print("✅ First sell order executed!")
```

---

## 🎯 Step 3: Technical Analysis (1 minute)

### 3.1 Analyze a Stock

```python
from common.database import DatabaseManager
from technical_analysis.services import AnalysisService

# Initialize database and analysis service
db = DatabaseManager("postgresql://user:password@localhost/stock_market")
analysis_service = AnalysisService(db.get_session())

# Analyze 贵州茅台 (600519)
result = analysis_service.analyze_stock("600519", days=120)

print(f"{'='*50}")
print(f"Stock: {result['stock_name']} ({result['symbol']})")
print(f"{'='*50}")
print(f"Total Score: {result['total_score']}/{result['max_score']}")
print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence_level']} level")
print(f"{'='*50}")

# Detailed breakdown
print("\nDetailed Scores:")
for dimension, score in result['dimension_scores'].items():
    print(f"  {dimension}: {score['score']}/{score['max_score']}")
    print(f"    Reason: {score['reason']}")
```

### 3.2 Understand the Scoring

The **Five-Dimensional Resonance Scoring System** evaluates:
- 📈 **Trend**: Overall market trend
- 🎯 **Pattern**: Chart patterns
- 📍 **Position**: Price position
- ⚡ **Momentum**: Price momentum
- 🔔 **Trigger**: Entry signals

Each dimension scores 0-20 points, total 100 points maximum.

---

## 🎯 Step 4: Backtest a Strategy (1 minute)

### 4.1 Run a Simple Backtest

```python
from backtest import BacktestEngine
from common.database import DatabaseManager

db = DatabaseManager("postgresql://user:password@localhost/stock_market")

# Initialize backtest engine
engine = BacktestEngine(db.get_session())

# Run backtest on 贵州茅台
results = engine.run_backtest(
    symbol="600519",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=100000,
    strategy="vcp"  # VCP breakout strategy
)

# View results
print(f"{'='*50}")
print(f"Backtest Results: 贵州茅台 (600519)")
print(f"{'='*50}")
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Annual Return: {results['annual_return']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"{'='*50}")
```

### 4.2 Export Backtest Report

```python
from backtest import ReportGenerator

report_gen = ReportGenerator()
report = report_gen.generate_report(results)

# Save to file
with open("backtest_report.html", "w") as f:
    f.write(report)

print("✅ Backtest report saved to backtest_report.html")
```

---

## 🎉 Congratulations! You're Ready

You've just completed the 5-minute quick start! You now know how to:
- ✅ Install and configure the system
- ✅ Execute buy and sell orders
- ✅ Manage your portfolio
- ✅ Run technical analysis
- ✅ Backtest trading strategies

---

## 📚 Next Steps

### Learn More About:
- 📘 [Trading System Guide](./04-trading-guide.md) - Complete trading guide
- 📗 [Technical Analysis Guide](./05-analysis-guide.md) - Deep dive into analysis
- 📙 [Backtest System Guide](./06-backtest-guide.md) - Advanced backtesting
- 🎯 [Three Strategies Guide](./08-strategy-guide.md) - Strategy details

### Practice:
1. **Try different stocks** - Test with other stock codes
2. **Experiment with strategies** - Try VCP, Nine-Turn, and Divergence
3. **Run longer backtests** - Test 1-year, 3-year periods
4. **Build your portfolio** - Add multiple positions

---

## ❓ Common Issues

### Database Connection Failed
**Solution**: Check your `DATABASE__URL` in `.env` file and ensure PostgreSQL is running.

### Tushare API Error
**Solution**: Get a free token from [Tushare](https://tushare.pro/) and update `TUSHARE_TOKEN` in `.env`.

### Module Import Error
**Solution**: Run `pip install -r requirements.txt` to install all dependencies.

---

## 💡 Tips for Beginners

1. **Start Small**: Use small amounts for your first trades
2. **Paper Trade First**: Always backtest before real trading
3. **Learn One Strategy**: Master one strategy before trying others
4. **Track Your Trades**: Keep a trading journal
5. **Risk Management**: Never risk more than 2% per trade

---

## 🆘 Need Help?

- 📖 Check the [FAQ](./09-faq.md)
- 📚 Read the [Glossary](./10-glossary.md)
- 📧 Contact support: support@alphaquant.com

---

**Next Chapter**: [Installation Guide →](./02-installation.md)

---

**Version**: v2.0.0
**Last Updated**: 2026-03-18
