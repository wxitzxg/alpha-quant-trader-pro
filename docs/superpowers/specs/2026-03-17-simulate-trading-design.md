# 模拟交易模块设计文档

**日期：** 2026-03-17
**模块名称：** simulate_trading
**状态：** ✅ 设计完成，等待评审
**依赖模块：** data_sources（数据源聚合模块）、portfolio_manager（持仓管理模块）

---

## 1. 需求概述

### 1.1 业务背景

模拟交易模块位于量化交易系统的上层应用，负责：
1. **实时模拟交易** - 基于真实市场行情进行模拟交易，非回测
2. **多策略并行** - 同时运行三种不同风格的交易策略（激进型/稳健型/保守型）
3. **性能对比** - 生成交易日报，对比不同策略的表现

### 1.2 设计目标

- ✅ **三种策略并行** - 激进型、稳健型、保守型独立运行
- ✅ **实时行情集成** - 使用 data_sources 模块获取实时数据
- ✅ **后台持续监控** - 使用独立进程持续运行，定时执行交易决策
- ✅ **数据库持久化** - 使用 PostgreSQL 存储交易记录和日报
- ✅ **YAML 配置管理** - 策略参数通过 YAML 文件配置，支持动态调整
- ✅ **日报生成** - 自动生成每日交易报告，支持策略对比

### 1.3 功能需求

#### 1.3.1 策略管理
- [ ] 三种策略独立配置（初始资金、仓位比例、止盈止损等）
- [ ] 支持策略独立启用/禁用
- [ ] 每种策略独立的账户资金管理

#### 1.3.2 交易执行
- [ ] 实时获取行情数据
- [ ] 自动分析交易机会
- [ ] 自动执行买入/卖出决策
- [ ] 交易记录持久化存储

#### 1.3.3 监控管理
- [ ] 支持启动/停止所有策略
- [ ] 实时状态监控
- [ ] 进程健康检查
- [ ] 异常自动恢复

#### 1.3.4 报告生成
- [ ] 每日交易日报
- [ ] 策略性能对比报告
- [ ] 交易历史查询

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      模拟交易主控制器                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │  启动管理    │  监控面板    │  日报生成    │  策略对比分析    │ │
│  └──────┬──────┴──────┬──────┴──────┬──────┴────────┬────────┘ │
│         │             │             │               │          │
│         ▼             ▼             ▼               ▼          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 激进型策略   │ │ 稳健型策略   │ │ 保守型策略   │  (独立进程)  │
│  │ - 9成仓位    │ │ - 6成仓位    │ │ - 4成仓位    │           │
│  │ - 追涨杀跌   │ │ - 趋势跟踪   │ │ - 价值投资   │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │             │             │                       │
│         └─────────────┼─────────────┘                       │
│                       ▼                                     │
│         ┌─────────────────────────┐                        │
│         │   数据源聚合器           │                        │
│         │   (实时行情获取)         │                        │
│         └───────────┬─────────────┘                        │
│                     │                                      │
│         ┌───────────▼─────────────┐                        │
│         │   PostgreSQL 数据库     │                        │
│         │   - 策略账户表           │                        │
│         │   - 交易记录表           │                        │
│         │   - 每日报告表           │                        │
│         │   - 策略配置表           │                        │
│         └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术架构

**进程架构：**
- 主进程：负责启动管理、状态监控、日报生成
- 工作进程（3个）：每个策略一个独立进程，并行执行
- 进程间通信：通过数据库共享状态，无直接进程通信

**数据流：**
1. 工作进程从数据库读取策略配置
2. 调用 data_sources 获取实时行情
3. 执行交易决策逻辑
4. 将交易记录写入数据库
5. 主进程定期生成日报和对比报告

---

## 3. 模块设计

### 3.1 配置模块

#### 3.1.1 策略配置文件 (`config/strategies.yaml`)

```yaml
strategies:
  aggressive:  # 激进型
    name: "激进型"
    description: "高仓位追涨杀跌，短线为主"
    enabled: true
    initial_cash: 80000
    max_position: 0.9
    min_position: 0.5
    stop_loss: -0.08
    take_profit: 0.15
    trade_ratio: 0.5
    chase_threshold: 0.05
    cut_loss_threshold: -0.03

  moderate:  # 稳健型
    name: "稳健型"
    description: "中等仓位趋势跟踪，波段操作"
    enabled: true
    initial_cash: 60000
    max_position: 0.7
    min_position: 0.3
    stop_loss: -0.05
    take_profit: 0.10
    trade_ratio: 0.3
    trend_follow_days: 5

  conservative:  # 保守型
    name: "保守型"
    description: "低仓位价值投资，长期持有"
    enabled: true
    initial_cash: 50000
    max_position: 0.5
    min_position: 0.2
    stop_loss: -0.03
    take_profit: 0.08
    trade_ratio: 0.2
    value_threshold: 0.15
```

#### 3.1.2 模拟交易配置 (`config/simulate_trading.yaml`)

```yaml
trading:
  execution_interval: 300  # 执行间隔（秒），默认5分钟
  check_interval: 60       # 健康检查间隔（秒）
  market_close_time: "15:00"  # 市场收盘时间
  market_open_time: "09:30"   # 市场开盘时间

database:
  url: "${DATABASE_URL}"  # 数据库连接，从环境变量读取
```

### 3.2 数据模型

#### 3.2.1 策略账户表 (`strategy_accounts`)

```python
class StrategyAccount(Base):
    __tablename__ = 'strategy_accounts'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), unique=True, nullable=False)
    initial_cash = Column(DECIMAL(15, 2), nullable=False)
    current_cash = Column(DECIMAL(15, 2), nullable=False)
    total_value = Column(DECIMAL(15, 2), nullable=False)  # 现金 + 持仓市值
    total_profit = Column(DECIMAL(15, 2), nullable=False)
    total_profit_pct = Column(DECIMAL(10, 4), nullable=False)  # 百分比
    position_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 3.2.2 交易记录表 (`strategy_trades`)

```python
class StrategyTrade(Base):
    __tablename__ = 'strategy_trades'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # buy/sell
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    fee = Column(DECIMAL(10, 2), nullable=False)
    reason = Column(String(200))  # 交易理由
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True)
```

#### 3.2.3 每日报告表 (`daily_reports`)

```python
class DailyReport(Base):
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    cash = Column(DECIMAL(15, 2), nullable=False)
    stock_value = Column(DECIMAL(15, 2), nullable=False)
    total_assets = Column(DECIMAL(15, 2), nullable=False)
    profit = Column(DECIMAL(15, 2), nullable=False)
    profit_pct = Column(DECIMAL(10, 4), nullable=False)
    position_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('strategy_name', 'report_date', name='uq_strategy_date'),
    )
```

### 3.3 核心组件

#### 3.3.1 策略基类 (`simulate_trading/strategies/base_strategy.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class StrategyConfig:
    name: str
    description: str
    initial_cash: float
    max_position: float
    min_position: float
    stop_loss: float
    take_profit: float
    trade_ratio: float
    # ... 其他参数

@dataclass
class TradeSignal:
    symbol: str
    action: str  # buy/sell
    quantity: int
    price: float
    reason: str
    confidence: float

@dataclass
class StrategyResult:
    strategy_name: str
    executed_trades: List[TradeSignal]
    skipped_trades: List[TradeSignal]
    total_value: float
    profit: float
    profit_pct: float

class BaseStrategy(ABC):
    def __init__(self, config: StrategyConfig, db_session):
        self.config = config
        self.db = db_session
        self.logger = logging.getLogger(f"strategy.{config.name}")

        # 依赖注入
        from simulate_trading.services import TradingDataService
        self.data_service = TradingDataService(db_session)

    @abstractmethod
    def execute(self) -> StrategyResult:
        """
        执行策略核心逻辑

        流程：
        1. 获取实时行情
        2. 计算当前持仓市值
        3. 分析交易机会
        4. 执行交易决策
        5. 更新账户状态

        Returns:
            StrategyResult
        """
        pass

    @abstractmethod
    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        分析交易机会

        Returns:
            交易信号列表
        """
        pass

    def get_account_summary(self):
        """获取账户汇总信息"""
        pass

    def calculate_position_ratio(self) -> float:
        """计算当前仓位比例"""
        pass

    def generate_daily_report(self, report_date: datetime) -> dict:
        """生成每日报告"""
        pass
```

#### 3.3.2 激进型策略 (`simulate_trading/strategies/aggressive_strategy.py`)

```python
class AggressiveStrategy(BaseStrategy):
    """
    激进型策略：高仓位追涨杀跌，短线为主

    特点：
    - 高仓位（最高9成）
    - 追涨：涨幅>5%且未持仓，建议买入
    - 杀跌：跌幅>3%且持仓亏损，建议卖出
    - 快进快出，短线操作
    """

    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        激进型机会分析：
        1. 追涨机会：热门股涨幅>5%且无持仓
        2. 杀跌机会：持仓股跌幅>3%且亏损
        3. 止盈机会：持仓股涨幅>15%
        4. 止损机会：持仓股跌幅>8%
        """
        pass

    def execute(self) -> StrategyResult:
        """执行激进型策略"""
        pass
```

#### 3.3.3 稳健型策略 (`simulate_trading/strategies/moderate_strategy.py`)

```python
class ModerateStrategy(BaseStrategy):
    """
    稳健型策略：中等仓位趋势跟踪，波段操作

    特点：
    - 中等仓位（最高7成）
    - 趋势跟踪：连续上涨/下跌趋势
    - 波段操作：持有数天至数周
    - 严格止盈止损
    """

    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        稳健型机会分析：
        1. 趋势确认：连续N天上涨
        2. 回调买入：上涨趋势中的回调
        3. 止盈卖出：达到目标收益
        4. 止损卖出：触及止损线
        """
        pass

    def execute(self) -> StrategyResult:
        """执行稳健型策略"""
        pass
```

#### 3.3.4 保守型策略 (`simulate_trading/strategies/conservative_strategy.py`)

```python
class ConservativeStrategy(BaseStrategy):
    """
    保守型策略：低仓位价值投资，长期持有

    特点：
    - 低仓位（最高5成）
    - 价值投资：低估时买入
    - 长期持有：数月至数年
    - 极低换手率
    """

    def analyze_opportunities(self) -> List[TradeSignal]:
        """
        保守型机会分析：
        1. 价值低估：市盈率/市净率低于历史平均
        2. 长期持有：不轻易卖出
        3. 分批建仓：逐步买入
        4. 极限止损：仅在极端情况止损
        """
        pass

    def execute(self) -> StrategyResult:
        """执行保守型策略"""
        pass
```

#### 3.3.5 交易数据服务 (`simulate_trading/services/data_service.py`)

```python
class TradingDataService:
    """
    交易数据服务 - 封装数据源和数据库操作
    """

    def __init__(self, db_session):
        self.db = db_session
        self.data_source = DataSourceAggregator()

    def get_realtime_price(self, symbol: str) -> Optional[dict]:
        """
        获取实时价格

        Args:
            symbol: 股票代码

        Returns:
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "price": 1600.0,
                "change_percent": 2.5,
                "volume": 10000,
                "amount": 16000000
            }
        """
        pass

    def get_kline_data(self, symbol: str, interval: str = "1d", days: int = 30):
        """获取K线数据"""
        pass

    def get_hot_stocks(self) -> List[tuple]:
        """获取热门股票池"""
        pass
```

#### 3.3.6 交易执行器 (`simulate_trading/services/trade_executor.py`)

```python
class TradeExecutor:
    """
    交易执行器 - 执行买入/卖出操作
    """

    def __init__(self, db_session, strategy_name: str):
        self.db = db_session
        self.strategy_name = strategy_name

    def execute_buy(self, symbol: str, quantity: int, price: float, reason: str):
        """
        执行买入

        流程：
        1. 计算手续费
        2. 检查现金是否足够
        3. 创建交易记录
        4. 更新策略账户
        """
        pass

    def execute_sell(self, symbol: str, quantity: int, price: float, reason: str):
        """
        执行卖出

        流程：
        1. 计算手续费
        2. 检查持仓是否足够
        3. 创建交易记录
        4. 更新策略账户
        """
        pass

    def update_account_summary(self):
        """更新账户汇总信息"""
        pass
```

#### 3.3.7 报告生成器 (`simulate_trading/services/report_generator.py`)

```python
class ReportGenerator:
    """
    报告生成器 - 生成日报和对比报告
    """

    def __init__(self, db_session):
        self.db = db_session

    def generate_daily_report(self, strategy_name: str, report_date: date):
        """生成单个策略的日报"""
        pass

    def generate_comparison_report(self, date_range: tuple = None):
        """
        生成策略对比报告

        包括：
        - 收益率对比
        - 波动率对比
        - 交易次数对比
        - 胜率对比
        """
        pass

    def export_report_to_file(self, report_data: dict, format: str = "txt"):
        """导出报告到文件"""
        pass
```

#### 3.3.8 进程管理器 (`simulate_trading/processes/process_manager.py`)

```python
from multiprocessing import Process, Queue
import signal

class StrategyProcessManager:
    """
    策略进程管理器 - 管理多个策略进程
    """

    def __init__(self):
        self.processes = {}  # {strategy_name: Process}
        self.running = False

    def start_strategy(self, strategy_name: str, config: dict):
        """
        启动单个策略进程

        Args:
            strategy_name: 策略名称
            config: 策略配置
        """
        pass

    def start_all_strategies(self):
        """启动所有启用的策略"""
        pass

    def stop_strategy(self, strategy_name: str):
        """停止单个策略"""
        pass

    def stop_all_strategies(self):
        """停止所有策略"""
        pass

    def monitor_processes(self):
        """监控进程健康状态"""
        pass

    def restart_failed_processes(self):
        """重启失败的进程"""
        pass
```

#### 3.3.9 策略工作进程 (`simulate_trading/processes/strategy_worker.py`)

```python
class StrategyWorker:
    """
    策略工作进程 - 独立进程执行单个策略
    """

    def __init__(self, strategy_name: str, config: dict):
        self.strategy_name = strategy_name
        self.config = config
        self.strategy = self._create_strategy()
        self.interval = config.get('execution_interval', 300)

    def _create_strategy(self):
        """创建策略实例"""
        if self.strategy_name == 'aggressive':
            return AggressiveStrategy(self.config)
        elif self.strategy_name == 'moderate':
            return ModerateStrategy(self.config)
        elif self.strategy_name == 'conservative':
            return ConservativeStrategy(self.config)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy_name}")

    def run(self):
        """
        运行策略主循环

        循环执行：
        1. 执行策略逻辑
        2. 生成日报（收盘后）
        3. 等待下次执行
        """
        while True:
            try:
                # 执行策略
                result = self.strategy.execute()

                # 日志记录
                self.logger.info(f"Strategy {self.strategy_name} executed: {result}")

                # 等待下次执行
                time.sleep(self.interval)

            except Exception as e:
                self.logger.error(f"Strategy {self.strategy_name} error: {e}")
                time.sleep(60)  # 错误后等待1分钟重试
```

#### 3.3.10 主控制器 (`simulate_trading/controller.py`)

```python
class TradingController:
    """
    模拟交易主控制器 - 统一管理入口
    """

    def __init__(self):
        self.process_manager = StrategyProcessManager()
        self.config = self._load_config()

    def start(self):
        """启动所有策略"""
        self.process_manager.start_all_strategies()
        self._start_monitoring()

    def stop(self):
        """停止所有策略"""
        self.process_manager.stop_all_strategies()

    def status(self) -> dict:
        """获取当前状态"""
        return self.process_manager.get_status()

    def generate_report(self, strategy_name: str = None):
        """生成报告"""
        if strategy_name:
            return self._generate_single_report(strategy_name)
        else:
            return self._generate_comparison_report()

    def reset(self):
        """重置所有策略账户"""
        pass

    def _start_monitoring(self):
        """启动监控循环"""
        pass
```

#### 3.3.11 命令行接口 (`simulate_trading/cli.py`)

```python
def main():
    """
    命令行入口

    用法：
        python -m simulate_trading start     # 启动所有策略
        python -m simulate_trading stop      # 停止所有策略
        python -m simulate_trading status    # 查看状态
        python -m simulate_trading report    # 生成报告
        python -m simulate_trading reset     # 重置账户
    """
    controller = TradingController()

    if len(sys.argv) < 2:
        print("用法: python -m simulate_trading [start|stop|status|report|reset]")
        return

    command = sys.argv[1]

    if command == 'start':
        controller.start()
    elif command == 'stop':
        controller.stop()
    elif command == 'status':
        status = controller.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif command == 'report':
        report = controller.generate_report()
        print(report)
    elif command == 'reset':
        controller.reset()
    else:
        print(f"未知命令: {command}")
```

---

## 4. 数据库设计

### 4.1 表结构

#### 4.1.1 策略账户表

```sql
CREATE TABLE strategy_accounts (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) UNIQUE NOT NULL,
    initial_cash DECIMAL(15, 2) NOT NULL,
    current_cash DECIMAL(15, 2) NOT NULL,
    total_value DECIMAL(15, 2) NOT NULL,
    total_profit DECIMAL(15, 2) NOT NULL,
    total_profit_pct DECIMAL(10, 4) NOT NULL,
    position_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.2 交易记录表

```sql
CREATE TABLE strategy_trades (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    fee DECIMAL(10, 2) NOT NULL,
    reason VARCHAR(200),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy (strategy_name),
    INDEX idx_symbol (symbol),
    INDEX idx_date (transaction_date)
);
```

#### 4.1.3 每日报告表

```sql
CREATE TABLE daily_reports (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    report_date DATE NOT NULL,
    cash DECIMAL(15, 2) NOT NULL,
    stock_value DECIMAL(15, 2) NOT NULL,
    total_assets DECIMAL(15, 2) NOT NULL,
    profit DECIMAL(15, 2) NOT NULL,
    profit_pct DECIMAL(10, 4) NOT NULL,
    position_count INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_strategy_date (strategy_name, report_date),
    INDEX idx_strategy (strategy_name),
    INDEX idx_date (report_date)
);
```

### 4.2 数据库迁移

使用 Alembic 管理数据库表结构变更：

```bash
# 初始化迁移
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "add simulate trading tables"

# 执行迁移
alembic upgrade head
```

---

## 5. 交易流程设计

### 5.1 单次执行流程（每5分钟）

```
开始
  │
  ▼
1. 获取实时行情数据
  │  - 调用 data_sources 获取热门股票池
  │  - 获取每只股票的实时价格
  │
  ▼
2. 计算当前账户状态
  │  - 获取当前持仓
  │  - 计算持仓市值
  │  - 计算总仓位比例
  │
  ▼
3. 分析交易机会
  │  - 根据策略规则分析买入/卖出机会
  │  - 生成交易信号列表
  │
  ▼
4. 过滤交易信号
  │  - 检查仓位限制
  │  - 检查现金/持仓是否足够
  │  - 检查是否符合策略规则
  │
  ▼
5. 执行交易
  │  - 买入：扣减现金，增加持仓
  │  - 卖出：增加现金，减少持仓
  │  - 记录交易到数据库
  │
  ▼
6. 更新账户状态
  │  - 更新策略账户表
  │  - 计算新的总市值和收益率
  │
  ▼
7. 日志记录
  │  - 记录执行结果
  │  - 记录交易详情
  │
  ▼
结束
```

### 5.2 每日收盘流程（15:00）

```
开始
  │
  ▼
1. 执行最后一次交易决策
  │
  ▼
2. 生成每日交易报告
  │  - 统计当日交易次数
  │  - 计算当日收益
  │  - 统计胜率
  │
  ▼
3. 保存日报到数据库
  │
  ▼
4. 输出日报到控制台
  │
  ▼
5. 等待市场开盘
  │
  ▼
结束
```

---

## 6. 目录结构

```
alpha-quant-trader-pro/
├── simulate_trading/                    # 模拟交易模块
│   ├── __init__.py
│   ├── config/                          # 配置文件
│   │   └── strategies.yaml
│   ├── strategies/                      # 策略实现
│   │   ├── __init__.py
│   │   ├── base_strategy.py            # 策略基类
│   │   ├── aggressive_strategy.py      # 激进型
│   │   ├── moderate_strategy.py        # 稳健型
│   │   └── conservative_strategy.py    # 保守型
│   ├── models/                          # 数据模型
│   │   ├── __init__.py
│   │   ├── strategy_account.py
│   │   ├── strategy_trade.py
│   │   └── daily_report.py
│   ├── repositories/                    # 数据仓库
│   │   ├── __init__.py
│   │   ├── strategy_account_repo.py
│   │   ├── strategy_trade_repo.py
│   │   └── daily_report_repo.py
│   ├── services/                        # 业务服务
│   │   ├── __init__.py
│   │   ├── data_service.py             # 行情数据服务
│   │   ├── trade_executor.py           # 交易执行器
│   │   └── report_generator.py         # 报告生成器
│   ├── processes/                       # 进程管理
│   │   ├── __init__.py
│   │   ├── process_manager.py          # 进程管理器
│   │   └── strategy_worker.py          # 策略工作进程
│   ├── controller.py                    # 主控制器
│   ├── cli.py                           # 命令行接口
│   ├── schemas/                         # Pydantic 模型
│   │   └── __init__.py
│   ├── exceptions.py                    # 异常定义
│   └── utils/                           # 工具函数
│       └── __init__.py
├── config/                              # 配置目录
│   ├── strategies.yaml                  # 策略配置
│   └── simulate_trading.yaml            # 模拟交易配置
├── scripts/                             # 脚本
│   └── run_simulate_trading.py          # 启动脚本
├── migrations/                          # 数据库迁移
│   └── versions/                        # 迁移版本
└── tests/                               # 测试
    └── simulate_trading/                # 模拟交易测试
```

---

## 7. 关键功能

### 7.1 命令行接口

```bash
# 启动所有策略
python -m simulate_trading start

# 停止所有策略
python -m simulate_trading stop

# 查看实时状态
python -m simulate_trading status

# 生成对比报告
python -m simulate_trading report

# 重置所有策略
python -m simulate_trading reset
```

### 7.2 交易日报示例

```
==================================================
📈 模拟交易日报 - 2026-03-17
==================================================

📊 激进型策略:
  初始资金: 80,000元
  当前现金: 12,500元
  持仓市值: 78,300元 (5只)
  总资产: 90,800元
  总收益: +10,800元 (+13.50%)
  今日操作: 买入2笔，卖出1笔
  交易次数: 15笔 (胜率: 60%)

📊 稳健型策略:
  初始资金: 60,000元
  当前现金: 18,200元
  持仓市值: 45,600元 (3只)
  总资产: 63,800元
  总收益: +3,800元 (+6.33%)
  今日操作: 买入1笔
  交易次数: 8笔 (胜率: 62.5%)

📊 保守型策略:
  初始资金: 50,000元
  当前现金: 32,500元
  持仓市值: 19,800元 (2只)
  总资产: 52,300元
  总收益: +2,300元 (+4.60%)
  今日操作: 无
  交易次数: 3笔 (胜率: 66.7%)

🏆 策略对比:
  收益率排名: 激进型(13.50%) > 稳健型(6.33%) > 保守型(4.60%)
  波动率排名: 激进型 > 稳健型 > 保守型
  交易活跃度: 激进型(15笔) > 稳健型(8笔) > 保守型(3笔)
  胜率排名: 保守型(66.7%) > 稳健型(62.5%) > 激进型(60%)

💡 分析建议:
  近期市场强势，激进型策略表现最佳
  稳健型策略平衡收益与风险，适合大多数投资者
  保守型策略波动最小，适合风险厌恶者
==================================================
```

---

## 8. 技术实现要点

### 8.1 进程管理

- 使用 `multiprocessing.Process` 创建独立进程
- 每个策略一个进程，并行执行
- 主进程负责监控和管理

### 8.2 异常处理

- 每个进程独立的异常捕获
- 数据库操作使用事务保证一致性
- 网络请求设置超时和重试机制

### 8.3 日志记录

```python
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulate_trading.log'),
        logging.StreamHandler()
    ]
)
```

### 8.4 配置热加载

```python
class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.last_modified = 0

    def load(self) -> dict:
        """加载配置，支持热更新"""
        current_mtime = os.path.getmtime(self.config_path)
        if current_mtime > self.last_modified:
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)
            self.last_modified = current_mtime
        return self.config
```

### 8.5 健康检查

```python
class HealthChecker:
    def check_process_health(self, process: Process) -> bool:
        """检查进程是否存活"""
        return process.is_alive()

    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        try:
            db.execute("SELECT 1")
            return True
        except:
            return False
```

---

## 9. 测试计划

### 9.1 单元测试

- 策略决策逻辑测试
- 手续费计算测试
- 仓位管理测试
- 数据源集成测试

### 9.2 集成测试

- 数据库读写测试
- 进程启动/停止测试
- 多策略并行测试

### 9.3 端到端测试

- 完整交易流程模拟
- 日报生成测试
- 对比报告测试

### 9.4 性能测试

- 并发策略执行性能
- 大数据量处理能力
- 长时间运行稳定性

---

## 10. 风险与应对

### 10.1 风险点

1. **数据源不稳定** - 实时行情API可能失败或延迟
2. **进程崩溃** - 策略进程可能因异常退出
3. **数据库锁** - 多进程同时写入可能产生锁竞争
4. **配置错误** - YAML配置格式错误导致启动失败

### 10.2 应对措施

1. **数据源容错** - 多数据源备用，失败自动切换
2. **进程监控** - 主进程监控子进程，异常自动重启
3. **数据库事务** - 使用事务保证数据一致性
4. **配置验证** - 启动时验证配置格式和参数范围

---

## 11. 后续扩展

### 11.1 短期（1-2周）

- [ ] 添加技术分析指标支持（MA、MACD、RSI）
- [ ] 优化交易决策逻辑
- [ ] 添加更多热门股票池

### 11.2 中期（1个月）

- [ ] 支持自定义策略
- [ ] 添加策略参数调优
- [ ] 实现策略组合（多种策略混合）

### 11.3 长期（2-3个月）

- [ ] Web 管理界面
- [ ] 实时推送通知（邮件/微信）
- [ ] 策略回测功能
- [ ] 机器学习优化策略参数

---

## 12. 参考资料

- [data_sources 模块文档](../../data_sources/README.md)
- [portfolio_manager 模块文档](../../portfolio_manager/README.md)
- [参考项目 simulate_trading.py](/home/zxg/workspace/stock-trader/scripts/simulate_trading.py)

---

**文档版本：** v1.0
**最后更新：** 2026-03-17
**作者：** AI Assistant
**审核状态：** ✅ 用户已批准
