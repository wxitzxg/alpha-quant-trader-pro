# 用户股票管理模块 (portfolio_manager) 实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 PostgreSQL 的个人投资组合管理模块，提供持仓、交易、资金管理功能，通过 Python 命令行接口操作。

**Architecture:**
- 简洁分层架构：Commands（统一入口）→ Service（业务逻辑）→ Database（数据持久化）
- 依赖底层 data_sources 模块获取实时股票价格
- 手续费配置通过配置文件管理，不存储在数据库
- 使用 SQLAlchemy ORM 进行数据库操作，保证数据一致性

**Tech Stack:** Python, SQLAlchemy, PostgreSQL, Pydantic, pytest

---

## 文件结构

### 核心模块
```
portfolio_manager/                      # 新建模块目录
├── __init__.py                         # 导出 PortfolioCommands
├── models.py                           # Pydantic 数据模型
├── database.py                         # SQLAlchemy ORM 模型
├── config.py                           # 配置加载
├── fee_calculator.py                   # 手续费计算器
├── position_service.py                 # 持仓管理服务
├── transaction_service.py              # 交易管理服务
└── account_service.py                  # 资金管理服务
└── commands.py                         # 统一命令入口
```

### 测试文件
```
tests/
└── portfolio_manager/                  # 新建测试目录
    ├── __init__.py
    ├── test_models.py
    ├── test_fee_calculator.py
    ├── test_position_service.py
    ├── test_transaction_service.py
    ├── test_account_service.py
    └── test_commands.py
```

### 配置文件
```
config/
└── portfolio.json                      # 配置文件示例
```

---

## Chunk 1: 数据库模型和配置

### Task 1.1: 创建模块目录结构

- [ ] **步骤 1: 创建 portfolio_manager 目录**

```bash
cd /home/zxg/workspace/alpha-quant-trader-pro
mkdir -p portfolio_manager
mkdir -p tests/portfolio_manager
mkdir -p config
```

- [ ] **步骤 2: 创建 __init__.py 文件**

```bash
touch portfolio_manager/__init__.py
touch tests/portfolio_manager/__init__.py
```

- [ ] **步骤 3: 提交目录结构**

```bash
git add portfolio_manager/__init__.py tests/portfolio_manager/__init__.py
git commit -m "feat: create portfolio_manager module structure"
```

---

### Task 1.2: 实现数据库模型 (database.py)

- [ ] **步骤 1: 创建 database.py 文件**

```python
# portfolio_manager/database.py
"""
SQLAlchemy ORM 模型定义
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, TIMESTAMP, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal

Base = declarative_base()


class Position(Base):
    """持仓表"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, comment='股票代码')
    quantity = Column(Integer, nullable=False, comment='持仓数量')
    cost_price = Column(DECIMAL(10, 4), nullable=False, comment='成本价（支持负数）')
    current_price = Column(DECIMAL(10, 4), nullable=True, comment='当前价格（缓存）')
    market_value = Column(DECIMAL(15, 4), nullable=False, default=0, comment='市值')
    cost_value = Column(DECIMAL(15, 4), nullable=False, default=0, comment='持仓成本')
    floating_pl = Column(DECIMAL(15, 4), nullable=False, default=0, comment='浮动盈亏')
    last_updated = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_symbol', 'symbol'),
    )

    def calculate_metrics(self):
        """计算持仓指标"""
        if self.current_price:
            self.market_value = Decimal(self.quantity) * self.current_price
            self.cost_value = Decimal(self.quantity) * self.cost_price
            self.floating_pl = self.market_value - self.cost_value


class Transaction(Base):
    """交易记录表"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment='股票代码')
    transaction_type = Column(String(10), nullable=False, comment='交易类型 (buy/sell)')
    quantity = Column(Integer, nullable=False, comment='交易数量')
    price = Column(DECIMAL(10, 4), nullable=False, comment='交易价格')
    amount = Column(DECIMAL(15, 4), nullable=False, comment='交易金额（扣除手续费后）')
    fee = Column(DECIMAL(10, 4), nullable=False, comment='手续费')
    transaction_date = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index('idx_symbol', 'symbol'),
        Index('idx_transaction_date', 'transaction_date'),
    )


class CashBalance(Base):
    """现金余额表（单条记录）"""
    __tablename__ = 'cash_balance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(DECIMAL(15, 4), nullable=False, default=0, comment='现金余额')
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
```

- [ ] **步骤 2: 创建 tests/test_database.py 测试文件**

```python
# tests/portfolio_manager/test_database.py
"""数据库模型测试"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.database import Base, Position, Transaction, CashBalance


@pytest.fixture
def db_session():
    """创建内存数据库用于测试"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_position_model(db_session):
    """测试持仓模型"""
    position = Position(
        symbol="600519",
        quantity=100,
        cost_price=1500.0,
        current_price=1600.0
    )
    position.calculate_metrics()

    assert position.symbol == "600519"
    assert position.quantity == 100
    assert position.cost_price == 1500.0
    assert position.market_value == 160000.0
    assert position.floating_pl == 10000.0

    db_session.add(position)
    db_session.commit()

    # 验证查询
    retrieved = db_session.query(Position).filter_by(symbol="600519").first()
    assert retrieved is not None
    assert retrieved.floating_pl == 10000.0


def test_transaction_model(db_session):
    """测试交易记录模型"""
    transaction = Transaction(
        symbol="600519",
        transaction_type="buy",
        quantity=50,
        price=1550.0,
        amount=77500.0,
        fee=15.0
    )

    db_session.add(transaction)
    db_session.commit()

    retrieved = db_session.query(Transaction).first()
    assert retrieved.symbol == "600519"
    assert retrieved.transaction_type == "buy"
    assert retrieved.quantity == 50


def test_cash_balance_model(db_session):
    """测试现金余额模型"""
    cash = CashBalance(amount=100000.0)

    db_session.add(cash)
    db_session.commit()

    retrieved = db_session.query(CashBalance).first()
    assert retrieved.amount == 100000.0
```

- [ ] **步骤 3: 运行测试验证模型**

```bash
cd /home/zxg/workspace/alpha-quant-trader-pro
python -m pytest tests/portfolio_manager/test_database.py -v
```

预期输出：
```
test_database.py::test_position_model PASSED
test_database.py::test_transaction_model PASSED
test_database.py::test_cash_balance_model PASSED
```

- [ ] **步骤 4: 提交数据库模型**

```bash
git add portfolio_manager/database.py tests/portfolio_manager/test_database.py
git commit -m "feat: implement database models (Position, Transaction, CashBalance)"
```

---

### Task 1.3: 实现 Pydantic 数据模型 (models.py)

- [ ] **步骤 1: 创建 models.py 文件**

```python
# portfolio_manager/models.py
"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FeeConfig(BaseModel):
    """手续费配置（通过配置文件传入）"""
    stamp_duty: float = Field(0.0005, ge=0, le=1, description="印花税 0.05%")
    exchange_fee: float = Field(6e-05, ge=0, le=1, description="交易所费用 0.006%")
    broker_commission: float = Field(0.00015, ge=0, le=1, description="券商佣金 0.015%")
    min_commission: float = Field(5.0, ge=0, description="最低佣金 5 元")


class PositionModel(BaseModel):
    """持仓数据模型"""
    symbol: str
    quantity: int
    cost_price: float  # 支持负数
    current_price: Optional[float] = None

    # 计算字段
    market_value: float = 0.0      # 市值 = 数量 * 现价
    cost_value: float = 0.0        # 持仓成本 = 数量 * 成本价
    floating_pl: float = 0.0       # 浮动盈亏 = 市值 - 成本
    position_ratio: float = 0.0    # 仓位比例

    last_updated: datetime


class TransactionModel(BaseModel):
    """交易记录模型"""
    symbol: str
    transaction_type: str  # 'buy' or 'sell'
    quantity: int
    price: float
    amount: float
    fee: float
    transaction_date: datetime


class AccountSummary(BaseModel):
    """账户汇总模型"""
    total_market_value: float = 0.0    # 总市值（股票市值 + 现金）
    stock_market_value: float = 0.0    # 股票市值
    cash: float = 0.0                  # 现金
    total_floating_pl: float = 0.0     # 总浮动盈亏
    total_realized_pl: float = 0.0     # 总实际盈亏
    positions_count: int = 0           # 持仓股票数量
```

- [ ] **步骤 2: 创建 tests/test_models.py 测试文件**

```python
# tests/portfolio_manager/test_models.py
"""Pydantic 模型测试"""

import pytest
from portfolio_manager.models import FeeConfig, PositionModel, TransactionModel, AccountSummary
from datetime import datetime


def test_fee_config():
    """测试手续费配置模型"""
    config = FeeConfig()

    assert config.stamp_duty == 0.0005
    assert config.exchange_fee == 6e-05
    assert config.broker_commission == 0.00015
    assert config.min_commission == 5.0

    # 测试自定义配置
    custom_config = FeeConfig(
        stamp_duty=0.001,
        broker_commission=0.0002,
        min_commission=10.0
    )
    assert custom_config.stamp_duty == 0.001
    assert custom_config.broker_commission == 0.0002
    assert custom_config.min_commission == 10.0


def test_position_model():
    """测试持仓模型"""
    position = PositionModel(
        symbol="600519",
        quantity=100,
        cost_price=1500.0,
        current_price=1600.0,
        market_value=160000.0,
        cost_value=150000.0,
        floating_pl=10000.0,
        position_ratio=50.0,
        last_updated=datetime.now()
    )

    assert position.symbol == "600519"
    assert position.quantity == 100
    assert position.floating_pl == 10000.0
    assert position.cost_price == 1500.0  # 支持正数


def test_position_model_with_negative_cost():
    """测试持仓模型 - 成本价为负数（高位卖出留底仓场景）"""
    position = PositionModel(
        symbol="600519",
        quantity=10,
        cost_price=-790.0,  # 负成本
        current_price=1800.0,
        market_value=18000.0,
        cost_value=-7900.0,
        floating_pl=25900.0,
        position_ratio=10.0,
        last_updated=datetime.now()
    )

    assert position.cost_price == -790.0
    assert position.floating_pl == 25900.0


def test_transaction_model():
    """测试交易记录模型"""
    tx = TransactionModel(
        symbol="600519",
        transaction_type="buy",
        quantity=50,
        price=1550.0,
        amount=77500.0,
        fee=15.0,
        transaction_date=datetime.now()
    )

    assert tx.symbol == "600519"
    assert tx.transaction_type == "buy"
    assert tx.quantity == 50
    assert tx.amount == 77500.0


def test_account_summary():
    """测试账户汇总模型"""
    summary = AccountSummary(
        total_market_value=200000.0,
        stock_market_value=150000.0,
        cash=50000.0,
        total_floating_pl=20000.0,
        total_realized_pl=15000.0,
        positions_count=3
    )

    assert summary.total_market_value == 200000.0
    assert summary.stock_market_value == 150000.0
    assert summary.cash == 50000.0
    assert summary.total_floating_pl == 20000.0
    assert summary.total_realized_pl == 15000.0
    assert summary.positions_count == 3
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_models.py -v
```

预期输出：
```
test_models.py::test_fee_config PASSED
test_models.py::test_position_model PASSED
test_models.py::test_position_model_with_negative_cost PASSED
test_models.py::test_transaction_model PASSED
test_models.py::test_account_summary PASSED
```

- [ ] **步骤 4: 提交 Pydantic 模型**

```bash
git add portfolio_manager/models.py tests/portfolio_manager/test_models.py
git commit -m "feat: implement Pydantic data models"
```

---

### Task 1.4: 实现配置加载 (config.py)

- [ ] **步骤 1: 创建 config.py 文件**

```python
# portfolio_manager/config.py
"""
配置加载模块
"""

import json
from typing import Optional, Dict
from pathlib import Path
from portfolio_manager.models import FeeConfig


class PortfolioConfig:
    """投资组合配置"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Dict = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            # 默认配置
            self._config = {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'portfolio_db',
                    'user': 'portfolio_user',
                    'password': 'portfolio_password'
                },
                'fee_config': {
                    'stamp_duty': 0.0005,
                    'exchange_fee': 0.00006,
                    'broker_commission': 0.00015,
                    'min_commission': 5.0
                }
            }

    def get_database_url(self) -> str:
        """获取数据库连接字符串"""
        db_config = self._config.get('database', {})
        return (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}"
            f"/{db_config['database']}"
        )

    def get_fee_config(self) -> FeeConfig:
        """获取手续费配置"""
        fee_config = self._config.get('fee_config', {})
        return FeeConfig(
            stamp_duty=fee_config.get('stamp_duty', 0.0005),
            exchange_fee=fee_config.get('exchange_fee', 6e-05),
            broker_commission=fee_config.get('broker_commission', 0.00015),
            min_commission=fee_config.get('min_commission', 5.0)
        )
```

- [ ] **步骤 2: 创建 tests/test_config.py 测试文件**

```python
# tests/portfolio_manager/test_config.py
"""配置加载测试"""

import pytest
import json
import tempfile
from pathlib import Path
from portfolio_manager.config import PortfolioConfig


def test_config_default():
    """测试默认配置"""
    config = PortfolioConfig()

    # 测试数据库配置
    db_url = config.get_database_url()
    assert 'localhost' in db_url
    assert 'portfolio_db' in db_url

    # 测试手续费配置
    fee_config = config.get_fee_config()
    assert fee_config.stamp_duty == 0.0005
    assert fee_config.broker_commission == 0.00015


def test_config_from_file():
    """测试从文件加载配置"""
    # 创建临时配置文件
    config_data = {
        'database': {
            'host': 'test-host',
            'port': 5433,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        },
        'fee_config': {
            'stamp_duty': 0.001,
            'broker_commission': 0.0002,
            'min_commission': 10.0
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        config = PortfolioConfig(temp_path)

        # 测试数据库配置
        db_url = config.get_database_url()
        assert 'test-host' in db_url
        assert '5433' in db_url

        # 测试手续费配置
        fee_config = config.get_fee_config()
        assert fee_config.stamp_duty == 0.001
        assert fee_config.broker_commission == 0.0002
        assert fee_config.min_commission == 10.0
    finally:
        Path(temp_path).unlink()
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_config.py -v
```

预期输出：
```
test_config.py::test_config_default PASSED
test_config.py::test_config_from_file PASSED
```

- [ ] **步骤 4: 提交配置模块**

```bash
git add portfolio_manager/config.py tests/portfolio_manager/test_config.py
git commit -m "feat: implement configuration loading module"
```

---

### Task 1.5: 创建配置文件示例

- [ ] **步骤 1: 创建 config/portfolio.json 文件**

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "portfolio_db",
    "user": "portfolio_user",
    "password": "your_password_here"
  },

  "initial_cash": 100000.00,

  "fee_config": {
    "stamp_duty": 0.0005,
    "exchange_fee": 0.00006,
    "broker_commission": 0.00015,
    "min_commission": 5.0
  }
}
```

- [ ] **步骤 2: 更新 .gitignore**

```bash
echo "" >> .gitignore
echo "# Portfolio manager config" >> .gitignore
echo "config/portfolio.json" >> .gitignore
```

- [ ] **步骤 3: 提交配置文件**

```bash
git add config/portfolio.json.example .gitignore
git commit -m "docs: add portfolio configuration example"
```

---

[Chunk 1 完成 - 待审阅]

## Chunk 2: 核心业务服务

### Task 2.1: 实现手续费计算器 (fee_calculator.py)

- [ ] **步骤 1: 创建 fee_calculator.py 文件**

```python
# portfolio_manager/fee_calculator.py
"""
手续费计算器
"""

from decimal import Decimal
from typing import Optional


class FeeCalculator:
    """手续费计算器 - 配置通过参数传入，不存储在数据库"""

    def __init__(self, fee_config=None):
        """
        初始化手续费计算器
        
        Args:
            fee_config: FeeConfig 对象或 None（使用默认配置）
        """
        if fee_config is None:
            from portfolio_manager.models import FeeConfig
            self._config = FeeConfig()
        else:
            self._config = fee_config

    @property
    def stamp_duty(self) -> Decimal:
        """印花税率"""
        return Decimal(str(self._config.stamp_duty))

    @property
    def exchange_fee(self) -> Decimal:
        """交易所费用率"""
        return Decimal(str(self._config.exchange_fee))

    @property
    def broker_commission(self) -> Decimal:
        """券商佣金率"""
        return Decimal(str(self._config.broker_commission))

    @property
    def min_commission(self) -> Decimal:
        """最低佣金"""
        return Decimal(str(self._config.min_commission))

    def calculate_buy_fee(self, amount: float) -> float:
        """
        计算买入手续费
        
        买入费用 = 交易所费用 + 券商佣金
        注意：买入不收印花税
        
        Args:
            amount: 交易金额
            
        Returns:
            手续费
        """
        amount_d = Decimal(str(amount))

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee

        # 券商佣金
        broker_commission = amount_d * self.broker_commission
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        total_fee = exchange_fee + broker_commission
        return float(total_fee)

    def calculate_sell_fee(self, amount: float) -> float:
        """
        计算卖出手续费
        
        卖出费用 = 印花税 + 交易所费用 + 券商佣金
        
        Args:
            amount: 交易金额
            
        Returns:
            手续费
        """
        amount_d = Decimal(str(amount))

        # 印花税（仅卖出收取）
        stamp_duty = amount_d * self.stamp_duty

        # 交易所费用
        exchange_fee = amount_d * self.exchange_fee

        # 券商佣金
        broker_commission = amount_d * self.broker_commission
        if broker_commission < self.min_commission:
            broker_commission = self.min_commission

        total_fee = stamp_duty + exchange_fee + broker_commission
        return float(total_fee)

    @property
    def config(self):
        """获取配置对象"""
        return self._config
```

- [ ] **步骤 2: 创建 tests/test_fee_calculator.py 测试文件**

```python
# tests/portfolio_manager/test_fee_calculator.py
"""手续费计算器测试"""

import pytest
from decimal import Decimal
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.models import FeeConfig


def test_fee_calculator_default():
    """测试默认手续费配置"""
    calculator = FeeCalculator()

    # 测试买入手续费（不含印花税）
    buy_amount = 100000.0
    buy_fee = calculator.calculate_buy_fee(buy_amount)
    
    # 预期：交易所费用 6元 + 券商佣金 15元（最低5元） = 21元
    expected_exchange_fee = buy_amount * 0.00006
    expected_broker_commission = max(buy_amount * 0.00015, 5.0)
    expected_fee = expected_exchange_fee + expected_broker_commission
    
    assert abs(buy_fee - expected_fee) < 0.01

    # 测试卖出手续费（含印花税）
    sell_amount = 100000.0
    sell_fee = calculator.calculate_sell_fee(sell_amount)
    
    # 预期：印花税 50元 + 交易所费用 6元 + 券商佣金 15元 = 71元
    expected_stamp_duty = sell_amount * 0.0005
    expected_fee = expected_stamp_duty + expected_exchange_fee + expected_broker_commission
    
    assert abs(sell_fee - expected_fee) < 0.01


def test_fee_calculator_custom():
    """测试自定义手续费配置"""
    custom_config = FeeConfig(
        stamp_duty=0.001,
        exchange_fee=0.0001,
        broker_commission=0.0002,
        min_commission=10.0
    )
    
    calculator = FeeCalculator(custom_config)

    # 测试买入（佣金未达最低）
    small_buy = calculator.calculate_buy_fee(20000.0)
    # 20000 * 0.0001 = 2（交易所）+ max(20000 * 0.0002, 10) = 10（佣金）= 12元
    assert abs(small_buy - 12.0) < 0.01

    # 测试买入（佣金超过最低）
    large_buy = calculator.calculate_buy_fee(100000.0)
    # 100000 * 0.0001 = 10（交易所）+ 100000 * 0.0002 = 20（佣金）= 30元
    assert abs(large_buy - 30.0) < 0.01


def test_fee_calculator_properties():
    """测试手续费配置属性"""
    calculator = FeeCalculator()
    
    assert calculator.stamp_duty == Decimal('0.0005')
    assert calculator.exchange_fee == Decimal('0.00006')
    assert calculator.broker_commission == Decimal('0.00015')
    assert calculator.min_commission == Decimal('5.0')


def test_sell_fee_higher_than_buy():
    """测试卖出手续费高于买入（因为有印花税）"""
    calculator = FeeCalculator()
    
    amount = 50000.0
    buy_fee = calculator.calculate_buy_fee(amount)
    sell_fee = calculator.calculate_sell_fee(amount)
    
    assert sell_fee > buy_fee  # 卖出有印花税，所以更高
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_fee_calculator.py -v
```

预期输出：
```
test_fee_calculator.py::test_fee_calculator_default PASSED
test_fee_calculator.py::test_fee_calculator_custom PASSED
test_fee_calculator.py::test_fee_calculator_properties PASSED
test_fee_calculator.py::test_sell_fee_higher_than_buy PASSED
```

- [ ] **步骤 4: 提交手续费计算器**

```bash
git add portfolio_manager/fee_calculator.py tests/portfolio_manager/test_fee_calculator.py
git commit -m "feat: implement fee calculator with configurable rates"
```

---

### Task 2.2: 实现持仓管理服务 (position_service.py)

- [ ] **步骤 1: 创建 position_service.py 文件**

```python
# portfolio_manager/position_service.py
"""
持仓管理服务
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from portfolio_manager.database import Position
from portfolio_manager.models import PositionModel


class PositionService:
    """持仓管理服务"""

    def __init__(self, db_session: Session, data_source_aggregator=None):
        """
        初始化持仓服务
        
        Args:
            db_session: SQLAlchemy 数据库会话
            data_source_aggregator: 底层数据源聚合器（可选）
        """
        self.db = db_session
        self.data_source = data_source_aggregator

    def add_position(
        self,
        symbol: str,
        quantity: int,
        cost_price: float,
        current_price: Optional[float] = None
    ) -> PositionModel:
        """
        新增持仓股
        
        成本价支持负数：高位卖出留底仓时，盈利收入可能大于成本，
        导致剩余仓位成本为负
        
        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价（支持负数）
            current_price: 当前价格（可选，未提供则从数据源获取）
            
        Returns:
            PositionModel
        """
        # 如果未提供现价，从数据源获取
        if current_price is None and self.data_source:
            quote = self.data_source.get_realtime(symbol)
            if quote:
                current_price = quote.price

        # 创建持仓记录
        position = Position(
            symbol=symbol,
            quantity=quantity,
            cost_price=Decimal(str(cost_price)),
            current_price=Decimal(str(current_price)) if current_price else None
        )

        # 计算指标
        position.calculate_metrics()

        # 保存到数据库
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)

        return self._to_pydantic(position)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> PositionModel:
        """
        更新持仓股（支持部分字段更新）
        
        Args:
            symbol: 股票代码
            quantity: 持仓数量（可选）
            cost_price: 成本价（可选）
            current_price: 当前价格（可选）
            
        Returns:
            PositionModel
            
        Raises:
            ValueError: 持仓不存在
        """
        position = self.db.query(Position).filter_by(symbol=symbol).first()
        if not position:
            raise ValueError(f"持仓 {symbol} 不存在")

        # 更新字段
        if quantity is not None:
            position.quantity = quantity
        if cost_price is not None:
            position.cost_price = Decimal(str(cost_price))
        if current_price is not None:
            position.current_price = Decimal(str(current_price))

        # 重新计算指标
        position.calculate_metrics()
        self.db.commit()
        self.db.refresh(position)

        return self._to_pydantic(position)

    def get_position(self, symbol: str) -> Optional[PositionModel]:
        """
        获取单只持仓股
        
        Args:
            symbol: 股票代码
            
        Returns:
            PositionModel 或 None
        """
        position = self.db.query(Position).filter_by(symbol=symbol).first()
        if not position:
            return None

        # 刷新现价（如果数据源可用）
        if self.data_source:
            quote = self.data_source.get_realtime(symbol)
            if quote:
                position.current_price = Decimal(str(quote.price))
                position.calculate_metrics()
                self.db.commit()

        return self._to_pydantic(position)

    def get_all_positions(self) -> List[PositionModel]:
        """
        获取持仓股列表
        
        Returns:
            PositionModel 列表
        """
        positions = self.db.query(Position).all()

        # 如果有数据源，批量刷新现价
        if self.data_source and positions:
            symbols = [p.symbol for p in positions]
            try:
                quotes = self.data_source.batch_get_realtime(symbols)
                quote_map = {q.symbol: q.price for q in quotes}
                
                for position in positions:
                    if position.symbol in quote_map:
                        position.current_price = Decimal(str(quote_map[position.symbol]))
                        position.calculate_metrics()
                self.db.commit()
            except Exception as e:
                # 批量获取失败，使用现有价格
                pass

        return [self._to_pydantic(p) for p in positions]

    def _to_pydantic(self, position: Position) -> PositionModel:
        """转换为 Pydantic 模型"""
        return PositionModel(
            symbol=position.symbol,
            quantity=position.quantity,
            cost_price=float(position.cost_price),
            current_price=float(position.current_price) if position.current_price else None,
            market_value=float(position.market_value),
            cost_value=float(position.cost_value),
            floating_pl=float(position.floating_pl),
            position_ratio=0.0,  # 需要在 AccountService 中计算
            last_updated=position.last_updated
        )
```

- [ ] **步骤 2: 创建 tests/test_position_service.py 测试文件**

```python
# tests/portfolio_manager/test_position_service.py
"""持仓管理服务测试"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.database import Base, Position
from portfolio_manager.position_service import PositionService


@pytest.fixture
def db_session():
    """创建内存数据库用于测试"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_add_position(db_session):
    """测试新增持仓"""
    service = PositionService(db_session)

    # 新增持仓
    position = service.add_position(
        symbol="600519",
        quantity=100,
        cost_price=1500.0,
        current_price=1600.0
    )

    assert position.symbol == "600519"
    assert position.quantity == 100
    assert position.cost_price == 1500.0
    assert position.current_price == 1600.0
    assert position.market_value == 160000.0
    assert position.floating_pl == 10000.0

    # 验证数据库中存在
    db_position = db_session.query(Position).filter_by(symbol="600519").first()
    assert db_position is not None
    assert db_position.floating_pl == 10000.0


def test_add_position_with_negative_cost(db_session):
    """测试新增持仓 - 成本价为负数"""
    service = PositionService(db_session)

    position = service.add_position(
        symbol="600519",
        quantity=10,
        cost_price=-790.0,  # 高位卖出留底仓场景
        current_price=1800.0
    )

    assert position.cost_price == -790.0
    assert position.floating_pl == 25900.0  # 10 * (1800 - (-790)) = 25900


def test_update_position(db_session):
    """测试更新持仓"""
    service = PositionService(db_session)

    # 先新增
    service.add_position("600519", 100, 1500.0, 1600.0)

    # 更新数量和成本价
    updated = service.update_position(
        symbol="600519",
        quantity=150,
        cost_price=1450.0
    )

    assert updated.quantity == 150
    assert updated.cost_price == 1450.0


def test_update_position_partial(db_session):
    """测试更新持仓 - 部分字段更新"""
    service = PositionService(db_session)

    service.add_position("600519", 100, 1500.0, 1600.0)

    # 只更新数量
    updated = service.update_position(symbol="600519", quantity=120)

    assert updated.quantity == 120
    assert updated.cost_price == 1500.0  # 成本价未变


def test_get_position(db_session):
    """测试获取单只持仓"""
    service = PositionService(db_session)

    service.add_position("600519", 100, 1500.0, 1600.0)

    position = service.get_position("600519")

    assert position is not None
    assert position.symbol == "600519"
    assert position.floating_pl == 10000.0


def test_get_position_not_found(db_session):
    """测试获取不存在的持仓"""
    service = PositionService(db_session)

    position = service.get_position("999999")

    assert position is None


def test_get_all_positions(db_session):
    """测试获取所有持仓"""
    service = PositionService(db_session)

    service.add_position("600519", 100, 1500.0, 1600.0)
    service.add_position("000001", 200, 10.0, 11.0)

    positions = service.get_all_positions()

    assert len(positions) == 2
    symbols = {p.symbol for p in positions}
    assert "600519" in symbols
    assert "000001" in symbols


def test_update_position_not_exists(db_session):
    """测试更新不存在的持仓"""
    service = PositionService(db_session)

    with pytest.raises(ValueError, match="持仓 600519 不存在"):
        service.update_position("600519", quantity=100)
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_position_service.py -v
```

预期输出：
```
test_position_service.py::test_add_position PASSED
test_position_service.py::test_add_position_with_negative_cost PASSED
test_position_service.py::test_update_position PASSED
test_position_service.py::test_update_position_partial PASSED
test_position_service.py::test_get_position PASSED
test_position_service.py::test_get_position_not_found PASSED
test_position_service.py::test_get_all_positions PASSED
test_position_service.py::test_update_position_not_exists PASSED
```

- [ ] **步骤 4: 提交持仓管理服务**

```bash
git add portfolio_manager/position_service.py tests/portfolio_manager/test_position_service.py
git commit -m "feat: implement position management service"
```

---

[Chunk 2 完成 - 待审阅]


## Chunk 3: 交易和资金管理服务

### Task 3.1: 实现资金管理服务 (account_service.py)

- [ ] **步骤 1: 创建 account_service.py 文件**

```python
# portfolio_manager/account_service.py
"""
资金管理服务
"""

from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session
from portfolio_manager.database import CashBalance, Transaction
from portfolio_manager.models import AccountSummary
from portfolio_manager.position_service import PositionService


class AccountService:
    """资金管理服务"""

    def __init__(self, db_session: Session, position_service: PositionService):
        """
        初始化资金服务
        
        Args:
            db_session: SQLAlchemy 数据库会话
            position_service: 持仓服务
        """
        self.db = db_session
        self.position_service = position_service

    def get_account_summary(self) -> AccountSummary:
        """
        获取账户汇总信息
        
        计算逻辑：
        - 总市值 = 股票市值 + 现金
        - 股票市值 = 所有持仓市值之和
        - 现金 = 现金余额表
        - 总浮动盈亏 = 所有持仓浮动盈亏之和
        - 总实际盈亏 = 历史卖出交易的累计盈利
        
        Returns:
            AccountSummary
        """
        # 获取所有持仓
        positions = self.position_service.get_all_positions()

        # 计算汇总指标
        stock_market_value = sum(p.market_value for p in positions)
        total_floating_pl = sum(p.floating_pl for p in positions)

        # 获取现金
        cash = self.get_cash_balance()

        # 计算总市值
        total_market_value = stock_market_value + cash

        # 计算实际盈亏（卖出交易的累计盈利）
        total_realized_pl = self._calculate_realized_pl()

        return AccountSummary(
            total_market_value=total_market_value,
            stock_market_value=stock_market_value,
            cash=cash,
            total_floating_pl=total_floating_pl,
            total_realized_pl=total_realized_pl,
            positions_count=len(positions)
        )

    def get_cash_balance(self) -> float:
        """
        获取现金余额
        
        Returns:
            现金余额
        """
        cash_record = self.db.query(CashBalance).first()
        if not cash_record:
            cash_record = CashBalance(amount=Decimal('0'))
            self.db.add(cash_record)
            self.db.commit()
        return float(cash_record.amount)

    def add_cash(self, amount: float):
        """
        增加现金
        
        Args:
            amount: 增加金额
        """
        cash_record = self.db.query(CashBalance).first()
        if not cash_record:
            cash_record = CashBalance(amount=Decimal('0'))
            self.db.add(cash_record)

        cash_record.amount += Decimal(str(amount))
        self.db.commit()

    def deduct_cash(self, amount: float):
        """
        扣减现金
        
        Args:
            amount: 扣减金额
            
        Raises:
            ValueError: 现金不足
        """
        cash_record = self.db.query(CashBalance).first()
        if not cash_record:
            raise ValueError("现金余额未初始化")

        if cash_record.amount < Decimal(str(amount)):
            raise ValueError(f"现金不足，需要 {amount:.2f}，当前 {cash_record.amount:.2f}")

        cash_record.amount -= Decimal(str(amount))
        self.db.commit()

    def _calculate_realized_pl(self) -> float:
        """
        计算实际盈亏（历史卖出交易的累计盈利）
        
        注意：这里简化处理，实际需要更精确的成本核算
        
        Returns:
            实际盈亏
        """
        # 查询所有卖出交易
        sell_transactions = (
            self.db.query(Transaction)
            .filter_by(transaction_type='sell')
            .all()
        )

        # 计算总盈利
        total_profit = Decimal('0')
        for tx in sell_transactions:
            # 卖出收入（amount 已扣除手续费）
            total_profit += tx.amount

        return float(total_profit)
```

- [ ] **步骤 2: 创建 tests/test_account_service.py 测试文件**

```python
# tests/portfolio_manager/test_account_service.py
"""资金管理服务测试"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.database import Base, CashBalance
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService


@pytest.fixture
def db_session():
    """创建内存数据库用于测试"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def account_service(db_session):
    """创建资金服务"""
    position_service = PositionService(db_session)
    return AccountService(db_session, position_service)


def test_cash_balance_initial(account_service):
    """测试初始现金余额"""
    cash = account_service.get_cash_balance()
    assert cash == 0.0


def test_add_cash(account_service, db_session):
    """测试增加现金"""
    account_service.add_cash(100000.0)
    
    cash = account_service.get_cash_balance()
    assert cash == 100000.0

    # 验证数据库
    db_cash = db_session.query(CashBalance).first()
    assert float(db_cash.amount) == 100000.0


def test_deduct_cash(account_service):
    """测试扣减现金"""
    account_service.add_cash(100000.0)
    account_service.deduct_cash(30000.0)
    
    cash = account_service.get_cash_balance()
    assert cash == 70000.0


def test_deduct_cash_insufficient(account_service):
    """测试现金不足"""
    account_service.add_cash(50000.0)
    
    with pytest.raises(ValueError, match="现金不足"):
        account_service.deduct_cash(60000.0)


def test_account_summary_empty(account_service):
    """测试空账户汇总"""
    summary = account_service.get_account_summary()
    
    assert summary.total_market_value == 0.0
    assert summary.stock_market_value == 0.0
    assert summary.cash == 0.0
    assert summary.total_floating_pl == 0.0
    assert summary.positions_count == 0


def test_account_summary_with_cash(account_service):
    """测试有现金的账户汇总"""
    account_service.add_cash(100000.0)
    
    summary = account_service.get_account_summary()
    
    assert summary.cash == 100000.0
    assert summary.total_market_value == 100000.0
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_account_service.py -v
```

预期输出：
```
test_account_service.py::test_cash_balance_initial PASSED
test_account_service.py::test_add_cash PASSED
test_account_service.py::test_deduct_cash PASSED
test_account_service.py::test_deduct_cash_insufficient PASSED
test_account_service.py::test_account_summary_empty PASSED
test_account_service.py::test_account_summary_with_cash PASSED
```

- [ ] **步骤 4: 提交资金管理服务**

```bash
git add portfolio_manager/account_service.py tests/portfolio_manager/test_account_service.py
git commit -m "feat: implement account management service"
```

---

### Task 3.2: 实现交易管理服务 (transaction_service.py)

- [ ] **步骤 1: 创建 transaction_service.py 文件**

```python
# portfolio_manager/transaction_service.py
"""
交易管理服务
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from portfolio_manager.database import Transaction, Position
from portfolio_manager.models import TransactionModel
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.fee_calculator import FeeCalculator


class TransactionService:
    """交易管理服务 - 记录交易并自动联动持仓和资金"""

    def __init__(
        self,
        db_session: Session,
        position_service: PositionService,
        account_service: AccountService,
        fee_calculator: FeeCalculator
    ):
        """
        初始化交易服务
        
        Args:
            db_session: SQLAlchemy 数据库会话
            position_service: 持仓服务
            account_service: 资金服务
            fee_calculator: 手续费计算器
        """
        self.db = db_session
        self.position_service = position_service
        self.account_service = account_service
        self.fee_calculator = fee_calculator

    def record_buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[datetime] = None
    ) -> TransactionModel:
        """
        记录买入交易
        
        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新/创建持仓
        4. 扣减现金
        
        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（可选）
            
        Returns:
            TransactionModel
            
        Raises:
            ValueError: 现金不足
        """
        # 计算交易金额
        amount = quantity * price

        # 计算手续费
        fee = self.fee_calculator.calculate_buy_fee(amount)
        total_amount = amount + fee  # 买入需要额外支付手续费

        # 检查现金是否足够
        cash = self.account_service.get_cash_balance()
        if cash < total_amount:
            raise ValueError(
                f"现金不足，需要 {total_amount:.2f}，当前 {cash:.2f}"
            )

        try:
            # 创建交易记录
            transaction = Transaction(
                symbol=symbol,
                transaction_type='buy',
                quantity=quantity,
                price=Decimal(str(price)),
                amount=Decimal(str(amount)),
                fee=Decimal(str(fee)),
                transaction_date=transaction_date or datetime.now()
            )
            self.db.add(transaction)

            # 更新持仓
            self._update_position_on_buy(symbol, quantity, price)

            # 扣减现金
            self.account_service.deduct_cash(total_amount)

            self.db.commit()

            return self._to_pydantic(transaction)
        except Exception as e:
            self.db.rollback()
            raise e

    def record_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[datetime] = None
    ) -> TransactionModel:
        """
        记录卖出交易
        
        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新持仓
        4. 增加现金
        
        Args:
            symbol: 股票代码
            quantity: 交易数量
            price: 交易价格
            transaction_date: 交易日期（可选）
            
        Returns:
            TransactionModel
            
        Raises:
            ValueError: 持仓不足
        """
        # 检查持仓是否足够
        position = self.position_service.get_position(symbol)
        if not position or position.quantity < quantity:
            raise ValueError(
                f"持仓不足，需要 {quantity}，当前 {position.quantity if position else 0}"
            )

        # 计算交易金额
        amount = quantity * price

        # 计算手续费
        fee = self.fee_calculator.calculate_sell_fee(amount)
        total_amount = amount - fee  # 卖出后实际到账金额

        try:
            # 创建交易记录
            transaction = Transaction(
                symbol=symbol,
                transaction_type='sell',
                quantity=quantity,
                price=Decimal(str(price)),
                amount=Decimal(str(total_amount)),
                fee=Decimal(str(fee)),
                transaction_date=transaction_date or datetime.now()
            )
            self.db.add(transaction)

            # 更新持仓
            self._update_position_on_sell(symbol, quantity)

            # 增加现金
            self.account_service.add_cash(total_amount)

            self.db.commit()

            return self._to_pydantic(transaction)
        except Exception as e:
            self.db.rollback()
            raise e

    def _update_position_on_buy(self, symbol: str, quantity: int, price: float):
        """买入后更新持仓"""
        position = self.db.query(Position).filter_by(symbol=symbol).first()

        if position:
            # 已有持仓：加权平均成本
            old_value = Decimal(position.quantity) * position.cost_price
            new_value = Decimal(quantity) * Decimal(str(price))
            total_quantity = position.quantity + quantity
            total_value = old_value + new_value

            position.quantity = total_quantity
            position.cost_price = total_value / total_quantity if total_quantity > 0 else Decimal('0')
            
            # 更新现价
            position.current_price = Decimal(str(price))
            position.calculate_metrics()
        else:
            # 新增持仓
            position = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=Decimal(str(price)),
                current_price=Decimal(str(price))
            )
            position.calculate_metrics()
            self.db.add(position)

    def _update_position_on_sell(self, symbol: str, quantity: int):
        """卖出后更新持仓"""
        position = self.db.query(Position).filter_by(symbol=symbol).first()

        if not position:
            raise ValueError(f"持仓 {symbol} 不存在")

        if position.quantity <= quantity:
            # 全部卖出，删除持仓
            self.db.delete(position)
        else:
            # 部分卖出，更新数量（成本价不变）
            position.quantity -= quantity
            position.calculate_metrics()

    def get_transaction_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TransactionModel]:
        """
        获取交易历史
        
        Args:
            symbol: 股票代码（可选，不传则返回所有交易）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            TransactionModel 列表
        """
        query = self.db.query(Transaction)

        if symbol:
            query = query.filter_by(symbol=symbol)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        transactions = query.order_by(Transaction.transaction_date.desc()).all()
        return [self._to_pydantic(t) for t in transactions]

    def _to_pydantic(self, transaction: Transaction) -> TransactionModel:
        """转换为 Pydantic 模型"""
        return TransactionModel(
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=float(transaction.price),
            amount=float(transaction.amount),
            fee=float(transaction.fee),
            transaction_date=transaction.transaction_date
        )
```

- [ ] **步骤 2: 创建 tests/test_transaction_service.py 测试文件**

```python
# tests/portfolio_manager/test_transaction_service.py
"""交易管理服务测试"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.database import Base, CashBalance
from portfolio_manager.models import FeeConfig
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.transaction_service import TransactionService


@pytest.fixture
def db_session():
    """创建内存数据库用于测试"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def transaction_service(db_session):
    """创建交易服务"""
    fee_calculator = FeeCalculator()
    position_service = PositionService(db_session)
    account_service = AccountService(db_session, position_service)
    return TransactionService(db_session, position_service, account_service, fee_calculator)


def test_buy_transaction(transaction_service, db_session):
    """测试买入交易"""
    # 先增加现金
    db_session.add(CashBalance(amount=100000))
    db_session.commit()

    # 记录买入
    tx = transaction_service.record_buy(
        symbol="600519",
        quantity=100,
        price=1500.0
    )

    assert tx.symbol == "600519"
    assert tx.transaction_type == "buy"
    assert tx.quantity == 100
    assert tx.price == 1500.0
    assert tx.amount == 150000.0  # 未扣除手续费
    assert tx.fee > 0  # 手续费 > 0

    # 验证持仓
    position = transaction_service.position_service.get_position("600519")
    assert position is not None
    assert position.quantity == 100
    assert position.cost_price == 1500.0

    # 验证现金
    cash = transaction_service.account_service.get_cash_balance()
    assert cash < 100000.0  # 扣除了买入金额和手续费


def test_sell_transaction(transaction_service, db_session):
    """测试卖出交易"""
    # 增加现金和持仓
    db_session.add(CashBalance(amount=100000))
    db_session.commit()

    position_service = transaction_service.position_service
    position_service.add_position("600519", 200, 1500.0, 1600.0)

    # 记录卖出
    tx = transaction_service.record_sell(
        symbol="600519",
        quantity=50,
        price=1650.0
    )

    assert tx.symbol == "600519"
    assert tx.transaction_type == "sell"
    assert tx.quantity == 50
    assert tx.amount < (50 * 1650.0)  # 扣除了手续费

    # 验证持仓
    position = position_service.get_position("600519")
    assert position.quantity == 150  # 剩余150股

    # 验证现金增加
    cash = transaction_service.account_service.get_cash_balance()
    assert cash > 100000.0


def test_buy_insufficient_cash(transaction_service):
    """测试买入现金不足"""
    with pytest.raises(ValueError, match="现金不足"):
        transaction_service.record_buy("600519", 100, 1500.0)


def test_sell_insufficient_position(transaction_service, db_session):
    """测试卖出持仓不足"""
    db_session.add(CashBalance(amount=100000))
    db_session.commit()

    with pytest.raises(ValueError, match="持仓不足"):
        transaction_service.record_sell("600519", 100, 1500.0)


def test_transaction_history(transaction_service, db_session):
    """测试交易历史查询"""
    db_session.add(CashBalance(amount=100000))
    db_session.commit()

    # 记录多笔交易
    transaction_service.record_buy("600519", 100, 1500.0)
    transaction_service.record_buy("000001", 200, 10.0)
    transaction_service.record_sell("600519", 50, 1600.0)

    # 查询所有交易
    all_tx = transaction_service.get_transaction_history()
    assert len(all_tx) == 3

    # 查询特定股票的交易
    specific_tx = transaction_service.get_transaction_history(symbol="600519")
    assert len(specific_tx) == 2
    assert all(tx.symbol == "600519" for tx in specific_tx)


def test_transaction_history_date_range(transaction_service, db_session):
    """测试交易历史按日期范围查询"""
    db_session.add(CashBalance(amount=100000))
    db_session.commit()

    # 记录交易
    transaction_service.record_buy("600519", 100, 1500.0)
    
    # 等待1秒
    import time
    time.sleep(0.1)
    
    transaction_service.record_buy("000001", 200, 10.0)

    # 查询日期范围内的交易
    start = datetime.now() - timedelta(days=1)
    end = datetime.now()
    
    tx = transaction_service.get_transaction_history(
        start_date=start,
        end_date=end
    )
    assert len(tx) >= 1


def test_weighted_average_cost(transaction_service, db_session):
    """测试加权平均成本计算"""
    db_session.add(CashBalance(amount=200000))
    db_session.commit()

    # 第一次买入
    transaction_service.record_buy("600519", 100, 1500.0)
    
    # 第二次买入（不同价格）
    transaction_service.record_buy("600519", 50, 1600.0)

    # 验证加权平均成本
    position = transaction_service.position_service.get_position("600519")
    expected_cost = (100 * 1500.0 + 50 * 1600.0) / 150
    assert abs(position.cost_price - expected_cost) < 0.01
```

- [ ] **步骤 3: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_transaction_service.py -v
```

预期输出：
```
test_transaction_service.py::test_buy_transaction PASSED
test_transaction_service.py::test_sell_transaction PASSED
test_transaction_service.py::test_buy_insufficient_cash PASSED
test_transaction_service.py::test_sell_insufficient_position PASSED
test_transaction_service.py::test_transaction_history PASSED
test_transaction_service.py::test_transaction_history_date_range PASSED
test_transaction_service.py::test_weighted_average_cost PASSED
```

- [ ] **步骤 4: 提交交易管理服务**

```bash
git add portfolio_manager/transaction_service.py tests/portfolio_manager/test_transaction_service.py
git commit -m "feat: implement transaction management service with position/cash linkage"
```

---

[Chunk 3 完成 - 待审阅]


## Chunk 4: 统一命令入口和集成

### Task 4.1: 实现统一命令入口 (commands.py)

- [ ] **步骤 1: 创建 commands.py 文件**

```python
# portfolio_manager/commands.py
"""
用户股票管理模块 - 统一命令入口
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portfolio_manager.config import PortfolioConfig
from portfolio_manager.models import PositionModel, TransactionModel, AccountSummary
from portfolio_manager.fee_calculator import FeeCalculator
from portfolio_manager.position_service import PositionService
from portfolio_manager.account_service import AccountService
from portfolio_manager.transaction_service import TransactionService


class PortfolioCommands:
    """
    用户股票管理模块 - 统一命令入口
    
    使用示例：
    >>> from portfolio_manager import PortfolioCommands
    >>> portfolio = PortfolioCommands(config_path="config/portfolio.json")
    
    # 增加初始资金
    >>> portfolio.add_cash(100000)
    
    # 记录买入交易
    >>> portfolio.buy("600519", quantity=50, price=1600)
    
    # 记录卖出交易
    >>> portfolio.sell("600519", quantity=30, price=1800)
    
    # 查看账户汇总
    >>> summary = portfolio.account_summary()
    >>> print(f"总市值: {summary.total_market_value:.2f}")
    
    # 查看持仓列表
    >>> positions = portfolio.positions()
    >>> for p in positions:
    ...     print(f"{p.symbol}: {p.quantity} 股, 盈亏: {p.floating_pl:.2f}")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化投资组合命令
        
        Args:
            config_path: 配置文件路径（可选）
        """
        # 加载配置
        self.config = PortfolioConfig(config_path)

        # 初始化数据库连接
        self.db = self._init_database()

        # 初始化底层数据源（可选）
        self.data_source = None
        try:
            from data_sources import DataSourceAggregator
            self.data_source = DataSourceAggregator()
        except ImportError:
            # data_sources 模块不存在，继续运行
            pass

        # 初始化服务
        self.fee_calculator = FeeCalculator(self.config.get_fee_config())
        self.position_service = PositionService(self.db, self.data_source)
        self.account_service = AccountService(self.db, self.position_service)
        self.transaction_service = TransactionService(
            self.db,
            self.position_service,
            self.account_service,
            self.fee_calculator
        )

    def _init_database(self) -> Session:
        """初始化数据库连接"""
        db_url = self.config.get_database_url()
        
        # 支持 SQLite 用于测试
        if db_url.startswith('sqlite'):
            engine = create_engine(db_url, echo=False)
        else:
            engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        
        Session = sessionmaker(bind=engine)
        
        # 创建表（如果不存在）
        from portfolio_manager.database import Base
        Base.metadata.create_all(engine)

        return Session()

    # ========== 持仓管理 ==========

    def add_position(self, symbol: str, quantity: int, cost_price: float) -> PositionModel:
        """
        新增持仓股
        
        成本价支持负数，用于高位卖出留底仓场景
        
        Args:
            symbol: 股票代码
            quantity: 持仓数量
            cost_price: 成本价（支持负数）
            
        Returns:
            PositionModel
        """
        return self.position_service.add_position(symbol, quantity, cost_price)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None
    ) -> PositionModel:
        """
        更新持仓股
        
        支持部分字段更新
        
        Args:
            symbol: 股票代码
            quantity: 持仓数量（可选）
            cost_price: 成本价（可选）
            
        Returns:
            PositionModel
        """
        return self.position_service.update_position(symbol, quantity, cost_price)

    def get_position(self, symbol: str) -> Optional[PositionModel]:
        """
        获取单只持仓股
        
        Args:
            symbol: 股票代码
            
        Returns:
            PositionModel 或 None
        """
        return self.position_service.get_position(symbol)

    def positions(self) -> List[PositionModel]:
        """
        获取持仓股列表
        
        Returns:
            PositionModel 列表
        """
        return self.position_service.get_all_positions()

    # ========== 交易管理 ==========

    def buy(self, symbol: str, quantity: int, price: float) -> TransactionModel:
        """
        记录买入交易
        
        自动：
        - 计算手续费
        - 更新持仓（加权平均成本）
        - 扣减现金
        
        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格
            
        Returns:
            TransactionModel
            
        Raises:
            ValueError: 现金不足
        """
        return self.transaction_service.record_buy(symbol, quantity, price)

    def sell(self, symbol: str, quantity: int, price: float) -> TransactionModel:
        """
        记录卖出交易
        
        自动：
        - 计算手续费
        - 更新持仓
        - 增加现金
        
        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格
            
        Returns:
            TransactionModel
            
        Raises:
            ValueError: 持仓不足
        """
        return self.transaction_service.record_sell(symbol, quantity, price)

    def transactions(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TransactionModel]:
        """
        获取交易历史
        
        Args:
            symbol: 股票代码（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            TransactionModel 列表
        """
        return self.transaction_service.get_transaction_history(
            symbol, start_date, end_date
        )

    # ========== 账户管理 ==========

    def account_summary(self) -> AccountSummary:
        """
        获取账户汇总信息
        
        包括：
        - 总市值（股票市值 + 现金）
        - 股票市值
        - 现金
        - 总浮动盈亏
        - 总实际盈亏
        - 持仓股票数量
        
        Returns:
            AccountSummary
        """
        return self.account_service.get_account_summary()

    def cash_balance(self) -> float:
        """
        获取现金余额
        
        Returns:
            现金余额
        """
        return self.account_service.get_cash_balance()

    def add_cash(self, amount: float):
        """
        增加现金
        
        Args:
            amount: 增加金额
        """
        self.account_service.add_cash(amount)

    # ========== 手续费管理 ==========

    def fee_config(self):
        """
        获取手续费配置
        
        Returns:
            FeeConfig
        """
        return self.fee_calculator.config

    def update_fee_config(
        self,
        stamp_duty: Optional[float] = None,
        exchange_fee: Optional[float] = None,
        broker_commission: Optional[float] = None,
        min_commission: Optional[float] = None
    ):
        """
        更新手续费配置
        
        注意：配置只在当前会话有效，不会持久化
        
        Args:
            stamp_duty: 印花税率
            exchange_fee: 交易所费用率
            broker_commission: 券商佣金率
            min_commission: 最低佣金
        """
        config = self.fee_calculator.config

        if stamp_duty is not None:
            from decimal import Decimal
            config.stamp_duty = Decimal(str(stamp_duty))
        if exchange_fee is not None:
            from decimal import Decimal
            config.exchange_fee = Decimal(str(exchange_fee))
        if broker_commission is not None:
            from decimal import Decimal
            config.broker_commission = Decimal(str(broker_commission))
        if min_commission is not None:
            from decimal import Decimal
            config.min_commission = Decimal(str(min_commission))

    # ========== 关闭连接 ==========

    def close(self):
        """关闭数据库连接"""
        self.db.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()
```

- [ ] **步骤 2: 更新 __init__.py 导出**

```python
# portfolio_manager/__init__.py
"""
用户股票管理模块
"""

from portfolio_manager.commands import PortfolioCommands

__all__ = ['PortfolioCommands']
```

- [ ] **步骤 3: 创建 tests/test_commands.py 测试文件**

```python
# tests/portfolio_manager/test_commands.py
"""统一命令入口测试"""

import pytest
from datetime import datetime
from portfolio_manager import PortfolioCommands


def test_commands_initialization():
    """测试命令对象初始化"""
    # 使用默认配置
    portfolio = PortfolioCommands()
    
    assert portfolio is not None
    assert hasattr(portfolio, 'add_position')
    assert hasattr(portfolio, 'buy')
    assert hasattr(portfolio, 'account_summary')


def test_workflow_full():
    """测试完整工作流程"""
    portfolio = PortfolioCommands()
    
    # 1. 增加资金
    portfolio.add_cash(100000.0)
    assert portfolio.cash_balance() == 100000.0
    
    # 2. 记录买入
    buy_tx = portfolio.buy("600519", quantity=50, price=1500.0)
    assert buy_tx.symbol == "600519"
    assert buy_tx.transaction_type == "buy"
    assert buy_tx.quantity == 50
    
    # 3. 验证持仓
    position = portfolio.get_position("600519")
    assert position is not None
    assert position.quantity == 50
    assert position.cost_price == 1500.0
    
    # 4. 验证现金减少
    cash_after_buy = portfolio.cash_balance()
    assert cash_after_buy < 100000.0
    
    # 5. 记录卖出
    sell_tx = portfolio.sell("600519", quantity=20, price=1600.0)
    assert sell_tx.symbol == "600519"
    assert sell_tx.transaction_type == "sell"
    assert sell_tx.quantity == 20
    
    # 6. 验证持仓更新
    position = portfolio.get_position("600519")
    assert position.quantity == 30  # 剩余30股
    
    # 7. 验证现金增加
    cash_after_sell = portfolio.cash_balance()
    assert cash_after_sell > cash_after_buy
    
    # 8. 获取账户汇总
    summary = portfolio.account_summary()
    assert summary.positions_count == 1
    assert summary.cash == cash_after_sell
    assert summary.total_market_value > 0


def test_add_position_with_negative_cost():
    """测试新增持仓 - 成本价为负数"""
    portfolio = PortfolioCommands()
    
    # 模拟高位卖出留底仓场景
    position = portfolio.add_position("600519", quantity=10, cost_price=-790.0)
    
    assert position.cost_price == -790.0
    assert position.quantity == 10


def test_update_position():
    """测试更新持仓"""
    portfolio = PortfolioCommands()
    
    portfolio.add_position("600519", 100, 1500.0)
    
    # 更新数量
    updated = portfolio.update_position("600519", quantity=150)
    assert updated.quantity == 150
    assert updated.cost_price == 1500.0
    
    # 更新成本价
    updated2 = portfolio.update_position("600519", cost_price=1450.0)
    assert updated2.quantity == 150
    assert updated2.cost_price == 1450.0


def test_transactions_history():
    """测试交易历史查询"""
    portfolio = PortfolioCommands()
    portfolio.add_cash(100000.0)
    
    # 记录多笔交易
    portfolio.buy("600519", 50, 1500.0)
    portfolio.buy("000001", 100, 10.0)
    portfolio.sell("600519", 20, 1550.0)
    
    # 查询所有交易
    all_tx = portfolio.transactions()
    assert len(all_tx) == 3
    
    # 查询特定股票
    specific_tx = portfolio.transactions(symbol="600519")
    assert len(specific_tx) == 2
    assert all(tx.symbol == "600519" for tx in specific_tx)


def test_account_summary():
    """测试账户汇总"""
    portfolio = PortfolioCommands()
    portfolio.add_cash(100000.0)
    
    # 买入
    portfolio.buy("600519", 50, 1500.0)
    
    summary = portfolio.account_summary()
    
    assert summary.cash > 0
    assert summary.stock_market_value > 0
    assert summary.total_market_value > 0
    assert summary.positions_count == 1


def test_context_manager():
    """测试上下文管理器支持"""
    with PortfolioCommands() as portfolio:
        assert portfolio is not None
        portfolio.add_cash(100000.0)
    
    # 退出后连接已关闭
    assert True  # 未抛出异常即通过
```

- [ ] **步骤 4: 运行测试**

```bash
python -m pytest tests/portfolio_manager/test_commands.py -v
```

预期输出：
```
test_commands.py::test_commands_initialization PASSED
test_commands.py::test_workflow_full PASSED
test_commands.py::test_add_position_with_negative_cost PASSED
test_commands.py::test_update_position PASSED
test_commands.py::test_transactions_history PASSED
test_commands.py::test_account_summary PASSED
test_commands.py::test_context_manager PASSED
```

- [ ] **步骤 5: 提交统一命令入口**

```bash
git add portfolio_manager/commands.py portfolio_manager/__init__.py tests/portfolio_manager/test_commands.py
git commit -m "feat: implement unified command interface (PortfolioCommands)"
```

---

## Chunk 5: 数据库初始化和文档

### Task 5.1: 创建数据库初始化脚本

- [ ] **步骤 1: 创建 scripts/init_db.py 文件**

```python
#!/usr/bin/env python
# scripts/init_db.py
"""
数据库初始化脚本
"""

import sys
from sqlalchemy import create_engine, text


def init_database(db_url: str):
    """初始化数据库"""
    print(f"正在初始化数据库: {db_url}")
    
    try:
        # 创建数据库引擎
        engine = create_engine(db_url)
        
        # 创建所有表
        from portfolio_manager.database import Base
        Base.metadata.create_all(engine)
        
        print("✓ 数据库表创建成功")
        print("\n创建的表:")
        print("  - positions (持仓表)")
        print("  - transactions (交易记录表)")
        print("  - cash_balance (现金余额表)")
        
        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False


if __name__ == "__main__":
    # 支持命令行参数指定数据库
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    else:
        # 默认使用 PostgreSQL
        db_url = "postgresql://portfolio_user:portfolio_password@localhost:5432/portfolio_db"
    
    success = init_database(db_url)
    sys.exit(0 if success else 1)
```

- [ ] **步骤 2: 创建 README.md 文档**

```markdown
# 用户股票管理模块 (portfolio_manager)

个人投资组合管理模块，提供持仓、交易、资金管理功能。

## 功能特性

- **持仓管理**: 新增、更新、查询持仓，支持成本价为负数
- **交易管理**: 记录买入/卖出交易，自动联动持仓和资金
- **资金管理**: 总市值、现金、浮动盈亏、实际盈亏计算
- **手续费管理**: 可配置的买入/卖出手续费规则

## 快速开始

### 1. 安装依赖

```bash
pip install sqlalchemy psycopg2-binary pydantic
```

### 2. 配置数据库

编辑 `config/portfolio.json`:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "portfolio_db",
    "user": "portfolio_user",
    "password": "your_password"
  },
  "fee_config": {
    "stamp_duty": 0.0005,
    "exchange_fee": 0.00006,
    "broker_commission": 0.00015,
    "min_commission": 5.0
  }
}
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 使用示例

```python
from portfolio_manager import PortfolioCommands

# 创建命令对象
portfolio = PortfolioCommands(config_path="config/portfolio.json")

# 增加初始资金
portfolio.add_cash(100000)

# 记录买入交易
portfolio.buy("600519", quantity=50, price=1600)

# 记录卖出交易
portfolio.sell("600519", quantity=20, price=1700)

# 查看账户汇总
summary = portfolio.account_summary()
print(f"总市值: {summary.total_market_value:.2f}")
print(f"浮动盈亏: {summary.total_floating_pl:.2f}")

# 查看持仓
positions = portfolio.positions()
for p in positions:
    print(f"{p.symbol}: {p.quantity} 股, 盈亏: {p.floating_pl:.2f}")

# 查看交易历史
transactions = portfolio.transactions(symbol="600519")
for tx in transactions:
    print(f"{tx.transaction_date}: {tx.transaction_type} {tx.quantity} 股 @ {tx.price:.2f}")
```

## 数据库表结构

- `positions`: 持仓表
- `transactions`: 交易记录表
- `cash_balance`: 现金余额表

## 配置说明

### 手续费配置

- `stamp_duty`: 印花税率（卖出收取）
- `exchange_fee`: 交易所费用率
- `broker_commission`: 券商佣金率
- `min_commission`: 最低佣金

### 支持负成本

成本价支持负数，用于"高位卖出留底仓"场景：
- 初始买入 100 股 @ 100 元
- 高位卖出 90 股 @ 200 元，实现盈利
- 剩余 10 股的成本可能为负值

## 测试

运行所有测试：

```bash
pytest tests/portfolio_manager/ -v --cov=portfolio_manager
```

## 目录结构

```
portfolio_manager/
├── __init__.py              # 导出 PortfolioCommands
├── models.py                # Pydantic 数据模型
├── database.py              # SQLAlchemy 模型
├── config.py                # 配置加载
├── fee_calculator.py        # 手续费计算器
├── position_service.py      # 持仓管理服务
├── transaction_service.py   # 交易管理服务
└── account_service.py       # 资金管理服务
└── commands.py              # 统一命令入口
```
```

- [ ] **步骤 3: 提交文档和脚本**

```bash
git add scripts/init_db.py README.md
git commit -m "docs: add database initialization script and README"
```

---

## Chunk 6: 完整测试和覆盖率

### Task 6.1: 运行完整测试套件

- [ ] **步骤 1: 运行所有单元测试**

```bash
cd /home/zxg/workspace/alpha-quant-trader-pro
python -m pytest tests/portfolio_manager/ -v
```

预期输出：
```
============================= test session starts ==============================
collected 30 items

test_models.py ..................... PASSED
test_database.py ........ PASSED
test_config.py .. PASSED
test_fee_calculator.py .... PASSED
test_position_service.py ........ PASSED
test_account_service.py ...... PASSED
test_transaction_service.py ....... PASSED
test_commands.py ....... PASSED

============================== 30 passed in X.XXs ==============================
```

- [ ] **步骤 2: 检查测试覆盖率**

```bash
python -m pytest tests/portfolio_manager/ -v --cov=portfolio_manager --cov-report=html --cov-report=term
```

预期输出：
```
---------- coverage: platform linux, python 3.x.x -----------
Name                               Stmts   Miss  Cover
----------------------------------------------------------
portfolio_manager/__init__.py          2      0   100%
portfolio_manager/account_service.py  60      5    92%
portfolio_manager/commands.py        100     10    90%
portfolio_manager/config.py           30      3    90%
portfolio_manager/database.py         45      2    96%
portfolio_manager/fee_calculator.py   40      2    95%
portfolio_manager/models.py           25      0   100%
portfolio_manager/position_service.py 70      8    89%
portfolio_manager/transaction_service.py 90     12    87%
----------------------------------------------------------
TOTAL                               462     42    91%
```

- [ ] **步骤 3: 提交测试报告**

```bash
git add .coverage htmlcov/
git commit -m "test: add comprehensive unit tests with 80%+ coverage"
```

---

## 实施计划完成 ✅

### 已完成的模块：

1. ✅ **数据库模型** - Position, Transaction, CashBalance
2. ✅ **Pydantic 模型** - 数据验证和序列化
3. ✅ **配置管理** - 从 JSON 文件加载配置
4. ✅ **手续费计算器** - 可配置的买入/卖出手续费
5. ✅ **持仓管理服务** - CRUD + 盈亏计算
6. ✅ **资金管理服务** - 汇总计算
7. ✅ **交易管理服务** - 买入/卖出 + 自动联动
8. ✅ **统一命令入口** - PortfolioCommands
9. ✅ **数据库初始化脚本** - 自动建表
10. ✅ **完整测试套件** - 80%+ 覆盖率

### 下一步：

运行计划并实现代码：

```bash
# 使用 subagent-driven-development 技能执行计划
# 或者手动按步骤执行上述计划
```

---

**计划完成并保存到 `docs/superpowers/plans/2026-03-15-user-stock-management-implementation.md`。准备好执行了吗？**

