# 用户股票管理模块设计文档

**日期：** 2026-03-15
**模块名称：** portfolio_manager
**状态：** ✅ 设计完成，等待评审

---

## 1. 需求概述

### 1.1 业务背景

量化交易系统的上层应用模块，用于管理个人投资组合的持仓、交易和资金数据，依赖底层 `data_sources` 模块获取实时股票数据。

### 1.2 设计目标

- ✅ **数据一致性**：交易、持仓、资金三者实时联动，保证数据准确
- ✅ **简洁易用**：纯 Python 命令行接口，无需界面和券商对接
- ✅ **单用户设计**：个人投资组合管理，使用 PostgreSQL 存储
- ✅ **灵活成本计算**：支持成本价为负数（高位卖出留底仓场景）

### 1.3 核心功能

| 功能模块       | 核心操作        | 说明               |
| ---------- | ----------- | ---------------- |
| **账户资金管理** | 查询总市值、现金、盈亏 | 包括浮动盈亏、持仓盈亏、实际盈亏 |
| **持仓管理**   | 新增、更新、查询、列表 | 支持单股/多股操作，自动计算指标 |
| **交易管理**   | 记录买入、卖出     | 自动联动持仓和资金数据      |
| **手续费管理**  | 配置和计算       | 印花税、交易所费用、券商佣金   |

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              量化交易系统 (alpha-quant-trader-pro)           │
│  ┌──────────────┬──────────────┬──────────────────────────┐  │
│  │  策略引擎     │   回测模块    │   风控模块                │  │
│  └──────┬───────┴──────┬───────┴──────────┬───────────────┘  │
│         │               │                  │                  │
│         └───────────────┼──────────────────┘                  │
│                         │                                     │
│         ┌───────────────▼────────────────────────┐           │
│         │   用户股票管理模块 (portfolio_manager)   │           │
│         │  ┌─────────────────────────────────┐  │           │
│         │  │  统一命令入口 (commands.py)     │  │           │
│         │  │  - add_position()               │  │           │
│         │  │  - update_position()            │  │           │
│         │  │  - record_buy()                 │  │           │
│         │  │  - record_sell()                │  │           │
│         │  │  - get_account_summary()        │  │           │
│         │  └───────────┬─────────────────────┘  │           │
│         │              │                        │           │
│         │  ┌───────────▼───────────┐  ┌────────▼────────┐  │
│         │  │  持仓服务 (Position)  │  │ 交易服务 (Transaction)│
│         │  │  - CRUD 持仓数据      │  │  - 记录交易      │  │
│         │  │  - 计算盈亏/仓位      │  │  - 自动联动      │  │
│         │  └───────────┬───────────┘  └────────┬────────┘  │
│         │              │                       │           │
│         │  ┌───────────▼───────────────────────▼────────┐  │
│         │  │  资金服务 (Account)                        │  │
│         │  │  - 计算总市值、现金、盈亏                 │  │
│         │  │  - 管理手续费配置                        │  │
│         │  └───────────┬───────────────────────────────┘  │
│         │              │                                  │
│         │  ┌───────────▼────────────────────────────────┐ │
│         │  │  数据访问层 (Database)                     │ │
│         │  │  - SQLAlchemy ORM                          │ │
│         │  │  - PostgreSQL                              │ │
│         │  └────────────────────────────────────────────┘ │
│         └─────────────────────────────────────────────────┘
│                         │
│         ┌───────────────▼────────────────────────────────┐
│         │  底层股票数据源 (data_sources)                  │
│         │  - 实时行情 (get_realtime)                      │
│         │  - K线数据 (get_kline)                         │
│         └─────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件                     | 职责     | 关键特性                    |
| ---------------------- | ------ | ----------------------- |
| **Commands**           | 统一命令入口 | 对外提供简洁的 Python API      |
| **PositionService**    | 持仓管理服务 | CRUD + 计算盈亏、仓位比例        |
| **TransactionService** | 交易管理服务 | 记录买卖 + 自动联动持仓和资金        |
| **AccountService**     | 资金管理服务 | 汇总计算所有指标                |
| **Database**           | 数据持久化  | SQLAlchemy + PostgreSQL |
| **FeeCalculator**      | 手续费计算  | 可配置的费用规则                |

---

## 3. 数据模型设计

### 3.1 数据库表结构

```sql
-- 持仓表
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,  -- 股票代码
    quantity INTEGER NOT NULL,           -- 持仓数量
    cost_price DECIMAL(10, 4) NOT NULL,  -- 成本价（支持负数）
    current_price DECIMAL(10, 4),        -- 当前价格（缓存）
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_symbol (symbol)
);

-- 交易记录表
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,         -- 股票代码
    transaction_type VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
    quantity INTEGER NOT NULL,           -- 交易数量
    price DECIMAL(10, 4) NOT NULL,       -- 交易价格
    amount DECIMAL(12, 4) NOT NULL,      -- 交易金额（含手续费）
    fee DECIMAL(10, 4) NOT NULL,         -- 手续费
    transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_symbol (symbol),
    INDEX idx_date (transaction_date)
);

-- 删除手续费配置表，手续费配置通过配置文件或常量管理
-- 无需存储在数据库中

-- 现金余额表（单条记录）
CREATE TABLE cash_balance (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(15, 4) NOT NULL DEFAULT 0.0,    -- 现金余额
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Pydantic 模型

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ========== 手续费配置 ==========
class FeeConfig(BaseModel):
    stamp_duty: float = Field(0.0005, ge=0, le=1)
    exchange_fee: float = Field(6e-05, ge=0, le=1)
    broker_commission: float = Field(0.00015, ge=0, le=1)
    min_commission: float = Field(0.0, ge=0)

# ========== 持仓数据 ==========
class Position(BaseModel):
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

# ========== 交易记录 ==========
class Transaction(BaseModel):
    symbol: str
    transaction_type: str  # 'buy' or 'sell'
    quantity: int
    price: float
    amount: float
    fee: float
    transaction_date: datetime

# ========== 账户汇总 ==========
class AccountSummary(BaseModel):
    total_market_value: float = 0.0    # 总市值（股票市值 + 现金）
    stock_market_value: float = 0.0    # 股票市值
    cash: float = 0.0                  # 现金
    total_floating_pl: float = 0.0     # 总浮动盈亏
    total_realized_pl: float = 0.0     # 总实际盈亏
    positions_count: int = 0           # 持仓股票数量
```

---

## 4. 详细设计

### 4.1 持仓服务 (PositionService)

```python
from typing import List, Optional
from decimal import Decimal

class PositionService:
    """持仓管理服务"""

    def __init__(self, db_session, data_source_aggregator):
        self.db = db_session
        self.data_source = data_source_aggregator

    def add_position(
        self,
        symbol: str,
        quantity: int,
        cost_price: float,
        current_price: Optional[float] = None
    ) -> Position:
        """
        新增持仓股

        成本价支持负数：高位卖出留底仓时，盈利收入可能大于成本，
        导致剩余仓位成本为负
        """
        # 如果未提供现价，从数据源获取
        if current_price is None:
            quote = self.data_source.get_realtime(symbol)
            if not quote:
                raise ValueError(f"无法获取 {symbol} 的实时价格")
            current_price = quote.price

        # 创建持仓记录
        position = PositionModel(
            symbol=symbol,
            quantity=quantity,
            cost_price=Decimal(str(cost_price)),
            current_price=Decimal(str(current_price))
        )

        # 计算指标
        position = self._calculate_metrics(position)

        # 保存到数据库
        self.db.add(position)
        self.db.commit()

        return self._to_pydantic(position)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Position:
        """更新持仓股（支持部分字段更新）"""
        position = self.db.query(PositionModel).filter_by(symbol=symbol).first()
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
        position = self._calculate_metrics(position)
        self.db.commit()

        return self._to_pydantic(position)

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取单只持仓股"""
        position = self.db.query(PositionModel).filter_by(symbol=symbol).first()
        if not position:
            return None

        # 刷新现价（可选）
        position.current_price = self._fetch_current_price(symbol)
        position = self._calculate_metrics(position)

        return self._to_pydantic(position)

    def get_all_positions(self) -> List[Position]:
        """获取持仓股列表"""
        positions = self.db.query(PositionModel).all()

        # 批量刷新现价（优化：批量查询）
        symbols = [p.symbol for p in positions]
        quotes = self.data_source.batch_get_realtime(symbols)
        quote_map = {q.symbol: q.price for q in quotes}

        # 计算所有指标
        result = []
        for position in positions:
            position.current_price = Decimal(str(quote_map.get(position.symbol, position.current_price)))
            position = self._calculate_metrics(position)
            result.append(self._to_pydantic(position))

        return result

    def _calculate_metrics(self, position: PositionModel) -> PositionModel:
        """计算持仓指标"""
        # 市值 = 数量 * 现价
        position.market_value = position.quantity * position.current_price

        # 持仓成本 = 数量 * 成本价
        position.cost_value = position.quantity * position.cost_price

        # 浮动盈亏 = 市值 - 成本
        position.floating_pl = position.market_value - position.cost_value

        return position

    def _fetch_current_price(self, symbol: str) -> Decimal:
        """获取当前价格"""
        quote = self.data_source.get_realtime(symbol)
        if quote:
            return Decimal(str(quote.price))
        return Decimal('0')

    def _to_pydantic(self, position: PositionModel) -> Position:
        """转换为 Pydantic 模型"""
        total_market_value = self._get_total_market_value()
        position_ratio = (
            (position.market_value / total_market_value * 100)
            if total_market_value > 0 else 0
        )

        return Position(
            symbol=position.symbol,
            quantity=position.quantity,
            cost_price=float(position.cost_price),
            current_price=float(position.current_price),
            market_value=float(position.market_value),
            cost_value=float(position.cost_value),
            floating_pl=float(position.floating_pl),
            position_ratio=position_ratio,
            last_updated=position.last_updated
        )
```

---

### 4.2 交易服务 (TransactionService)

```python
class TransactionService:
    """交易管理服务 - 记录交易并自动联动持仓和资金"""

    def __init__(self, db_session, position_service, account_service, fee_calculator):
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
    ) -> Transaction:
        """
        记录买入交易

        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新/创建持仓
        4. 扣减现金
        """
        # 计算手续费
        amount = quantity * price
        fee = self.fee_calculator.calculate_buy_fee(amount)
        total_amount = amount + fee

        # 检查现金是否足够
        cash = self.account_service.get_cash_balance()
        if cash < total_amount:
            raise ValueError(
                f"现金不足，需要 {total_amount:.2f}，当前 {cash:.2f}"
            )

        # 创建交易记录
        transaction = TransactionModel(
            symbol=symbol,
            transaction_type='buy',
            quantity=quantity,
            price=Decimal(str(price)),
            amount=Decimal(str(total_amount)),
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

    def record_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_date: Optional[datetime] = None
    ) -> Transaction:
        """
        记录卖出交易

        流程：
        1. 计算手续费和总金额
        2. 创建交易记录
        3. 更新持仓
        4. 增加现金
        """
        # 检查持仓是否足够
        position = self.position_service.get_position(symbol)
        if not position or position.quantity < quantity:
            raise ValueError(
                f"持仓不足，需要 {quantity}，当前 {position.quantity if position else 0}"
            )

        # 计算手续费
        amount = quantity * price
        fee = self.fee_calculator.calculate_sell_fee(amount)
        total_amount = amount - fee  # 卖出后实际到账

        # 创建交易记录
        transaction = TransactionModel(
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

    def _update_position_on_buy(self, symbol: str, quantity: int, price: float):
        """买入后更新持仓"""
        position = self.db.query(PositionModel).filter_by(symbol=symbol).first()

        if position:
            # 已有持仓：加权平均成本
            old_value = position.quantity * position.cost_price
            new_value = quantity * Decimal(str(price))
            total_quantity = position.quantity + quantity
            total_value = old_value + new_value

            position.quantity = total_quantity
            position.cost_price = total_value / total_quantity if total_quantity > 0 else Decimal('0')
        else:
            # 新增持仓
            position = PositionModel(
                symbol=symbol,
                quantity=quantity,
                cost_price=Decimal(str(price))
            )
            self.db.add(position)

    def _update_position_on_sell(self, symbol: str, quantity: int):
        """卖出后更新持仓"""
        position = self.db.query(PositionModel).filter_by(symbol=symbol).first()

        if not position:
            raise ValueError(f"持仓 {symbol} 不存在")

        if position.quantity <= quantity:
            # 全部卖出，删除持仓
            self.db.delete(position)
        else:
            # 部分卖出，更新数量
            position.quantity -= quantity

    def get_transaction_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """获取交易历史"""
        query = self.db.query(TransactionModel)

        if symbol:
            query = query.filter_by(symbol=symbol)
        if start_date:
            query = query.filter(TransactionModel.transaction_date >= start_date)
        if end_date:
            query = query.filter(TransactionModel.transaction_date <= end_date)

        transactions = query.order_by(TransactionModel.transaction_date.desc()).all()
        return [self._to_pydantic(t) for t in transactions]
```

---

### 4.3 资金服务 (AccountService)

```python
class AccountService:
    """资金管理服务"""

    def __init__(self, db_session, position_service):
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
        - 总持仓盈亏 = 所有持仓成本之和
        - 总实际盈亏 = 历史卖出交易的盈利之和
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
        """获取现金余额"""
        cash_record = self.db.query(CashBalanceModel).first()
        if not cash_record:
            cash_record = CashBalanceModel(amount=Decimal('0'))
            self.db.add(cash_record)
            self.db.commit()
        return float(cash_record.amount)

    def add_cash(self, amount: float):
        """增加现金"""
        cash_record = self.db.query(CashBalanceModel).first()
        if not cash_record:
            cash_record = CashBalanceModel(amount=Decimal('0'))
            self.db.add(cash_record)

        cash_record.amount += Decimal(str(amount))
        cash_record.updated_at = datetime.now()
        self.db.commit()

    def deduct_cash(self, amount: float):
        """扣减现金"""
        cash_record = self.db.query(CashBalanceModel).first()
        if not cash_record:
            raise ValueError("现金余额未初始化")

        if cash_record.amount < Decimal(str(amount)):
            raise ValueError(f"现金不足，需要 {amount:.2f}")

        cash_record.amount -= Decimal(str(amount))
        cash_record.updated_at = datetime.now()
        self.db.commit()

    def _calculate_realized_pl(self) -> float:
        """计算实际盈亏（历史卖出交易的累计盈利）"""
        # 查询所有卖出交易
        sell_transactions = (
            self.db.query(TransactionModel)
            .filter_by(transaction_type='sell')
            .all()
        )

        # 计算总盈利
        total_profit = Decimal('0')
        for tx in sell_transactions:
            # 卖出收入 - 卖出成本 - 手续费
            # 注意：这里简化处理，实际需要追溯对应买入成本
            total_profit += tx.amount  # amount 已扣除手续费

        return float(total_profit)
```

---

### 4.4 手续费计算器 (FeeCalculator)

```python
from decimal import Decimal
from typing import Optional

class FeeConfig:
    """手续费配置（从配置文件或参数传入）"""
    def __init__(
        self,
        stamp_duty: float = 0.0005,        # 印花税 0.05%
        exchange_fee: float = 0.00006,     # 交易所费用 0.006%
        broker_commission: float = 0.00015, # 券商佣金 0.015%
        min_commission: float = 0.0         # 最低佣金
    ):
        self.stamp_duty = Decimal(str(stamp_duty))
        self.exchange_fee = Decimal(str(exchange_fee))
        self.broker_commission = Decimal(str(broker_commission))
        self.min_commission = Decimal(str(min_commission))


class FeeCalculator:
    """手续费计算器 - 配置通过参数传入，不存储在数据库"""

    def __init__(self, fee_config: Optional[FeeConfig] = None):
        # 使用传入的配置，或默认配置
        self.config = fee_config or FeeConfig()

    @property
    def stamp_duty(self) -> Decimal:
        return self.config.stamp_duty

    @property
    def exchange_fee(self) -> Decimal:
        return self.config.exchange_fee

    @property
    def broker_commission(self) -> Decimal:
        return self.config.broker_commission

    @property
    def min_commission(self) -> Decimal:
        return self.config.min_commission

    def calculate_buy_fee(self, amount: float) -> float:
        """
        计算买入手续费

        买入费用 = 交易所费用 + 券商佣金
        注意：买入不收印花税
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
```

---

### 4.5 统一命令入口 (Commands)

```python
class PortfolioCommands:
    """
    用户股票管理模块 - 统一命令入口

    使用示例：
    >>> from portfolio_manager import PortfolioCommands
    >>> portfolio = PortfolioCommands()

    # 添加持仓
    >>> portfolio.add_position("600519", quantity=100, cost_price=1500)

    # 记录买入
    >>> portfolio.buy("600519", quantity=50, price=1600)

    # 记录卖出
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
        # 初始化数据库连接
        self.db = self._init_database(config_path)

        # 从配置文件加载手续费配置
        fee_config = self._load_fee_config(config_path)

        # 初始化底层数据源
        from data_sources import DataSourceAggregator
        self.data_source = DataSourceAggregator()

        # 初始化服务（FeeCalculator 不依赖数据库）
        self.fee_calculator = FeeCalculator(fee_config)
        self.position_service = PositionService(self.db, self.data_source)
        self.account_service = AccountService(self.db, self.position_service)
        self.transaction_service = TransactionService(
            self.db,
            self.position_service,
            self.account_service,
            self.fee_calculator
        )

    # ========== 持仓管理 ==========

    def add_position(self, symbol: str, quantity: int, cost_price: float) -> Position:
        """新增持仓股"""
        return self.position_service.add_position(symbol, quantity, cost_price)

    def update_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        cost_price: Optional[float] = None
    ) -> Position:
        """更新持仓股"""
        return self.position_service.update_position(symbol, quantity, cost_price)

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取单只持仓股"""
        return self.position_service.get_position(symbol)

    def positions(self) -> List[Position]:
        """获取持仓股列表"""
        return self.position_service.get_all_positions()

    # ========== 交易管理 ==========

    def buy(self, symbol: str, quantity: int, price: float) -> Transaction:
        """记录买入交易"""
        return self.transaction_service.record_buy(symbol, quantity, price)

    def sell(self, symbol: str, quantity: int, price: float) -> Transaction:
        """记录卖出交易"""
        return self.transaction_service.record_sell(symbol, quantity, price)

    def transactions(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """获取交易历史"""
        return self.transaction_service.get_transaction_history(
            symbol, start_date, end_date
        )

    # ========== 账户管理 ==========

    def account_summary(self) -> AccountSummary:
        """获取账户汇总信息"""
        return self.account_service.get_account_summary()

    def cash_balance(self) -> float:
        """获取现金余额"""
        return self.account_service.get_cash_balance()

    def add_cash(self, amount: float):
        """增加现金"""
        self.account_service.add_cash(amount)

    # ========== 手续费管理 ==========

    def fee_config(self) -> FeeConfig:
        """获取手续费配置"""
        return self.fee_calculator.config

    def update_fee_config(
        self,
        stamp_duty: Optional[float] = None,
        exchange_fee: Optional[float] = None,
        broker_commission: Optional[float] = None,
        min_commission: Optional[float] = None
    ):
        """更新手续费配置（直接修改配置对象）"""
        config = self.fee_calculator.config

        if stamp_duty is not None:
            config.stamp_duty = Decimal(str(stamp_duty))
        if exchange_fee is not None:
            config.exchange_fee = Decimal(str(exchange_fee))
        if broker_commission is not None:
            config.broker_commission = Decimal(str(broker_commission))
        if min_commission is not None:
            config.min_commission = Decimal(str(min_commission))

    # ========== 内部方法 ==========

    def _init_database(self, config_path: Optional[str] = None) -> Session:
        """初始化数据库连接"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # 读取数据库配置
        db_url = self._get_db_url(config_path)

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)

        return Session()

    def _get_db_url(self, config_path: Optional[str] = None) -> str:
        """获取数据库连接字符串"""
        # 默认配置
        default_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'portfolio_db',
            'user': 'portfolio_user',
            'password': 'portfolio_password'
        }

        # 如果有配置文件，读取配置
        if config_path:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                default_config.update(config.get('database', {}))

        return (
            f"postgresql://{default_config['user']}:{default_config['password']}"
            f"@{default_config['host']}:{default_config['port']}"
            f"/{default_config['database']}"
        )

    def _load_fee_config(self, config_path: Optional[str] = None) -> FeeConfig:
        """从配置文件加载手续费配置"""
        # 默认配置
        default_config = {
            'stamp_duty': 0.0005,       # 印花税 0.05%
            'exchange_fee': 0.00006,    # 交易所费用 0.006%
            'broker_commission': 0.00015, # 券商佣金 0.015%
            'min_commission': 5.0       # 最低佣金 5 元
        }

        # 如果有配置文件，读取手续费配置
        if config_path:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                fee_config = config.get('fee_config', {})
                default_config.update(fee_config)

        return FeeConfig(
            stamp_duty=default_config['stamp_duty'],
            exchange_fee=default_config['exchange_fee'],
            broker_commission=default_config['broker_commission'],
            min_commission=default_config['min_commission']
        )
```

---

## 5. 使用示例

### 5.1 初始化模块

```python
from portfolio_manager import PortfolioCommands

# 创建命令对象（单例模式）
portfolio = PortfolioCommands(config_path="config/portfolio.json")
```

### 5.2 资金管理

```python
# 增加初始资金
portfolio.add_cash(100000)

# 查看账户汇总
summary = portfolio.account_summary()
print(f"总市值: {summary.total_market_value:.2f} 元")
print(f"股票市值: {summary.stock_market_value:.2f} 元")
print(f"现金: {summary.cash:.2f} 元")
print(f"浮动盈亏: {summary.total_floating_pl:.2f} 元")
```

### 5.3 持仓管理

```python
# 新增持仓（假设之前已手动买入）
portfolio.add_position("600519", quantity=100, cost_price=1500)

# 更新持仓（修改成本价）
portfolio.update_position("600519", cost_price=1450)

# 获取单只持仓详情
position = portfolio.get_position("600519")
print(f"{position.symbol}: {position.quantity} 股")
print(f"成本价: {position.cost_price:.2f}, 现价: {position.current_price:.2f}")
print(f"浮动盈亏: {position.floating_pl:.2f}, 仓位: {position.position_ratio:.1f}%")

# 获取所有持仓
positions = portfolio.positions()
for p in positions:
    print(f"{p.symbol}: {p.quantity} 股, 盈亏: {p.floating_pl:.2f}")
```

### 5.4 交易管理

```python
# 记录买入交易
buy_tx = portfolio.buy("600519", quantity=50, price=1600)
print(f"买入 {buy_tx.quantity} 股，价格 {buy_tx.price:.2f}，手续费 {buy_tx.fee:.2f}")

# 记录卖出交易
sell_tx = portfolio.sell("600519", quantity=30, price=1800)
print(f"卖出 {sell_tx.quantity} 股，价格 {sell_tx.price:.2f}，手续费 {sell_tx.fee:.2f}")

# 查看交易历史
history = portfolio.transactions(symbol="600519")
for tx in history:
    print(f"{tx.transaction_date}: {tx.transaction_type} {tx.quantity} 股 @ {tx.price:.2f}")
```

### 5.5 手续费管理

```python
# 查看当前手续费配置
config = portfolio.fee_config()
print(f"印花税: {config.stamp_duty:.4%}")
print(f"交易所费用: {config.exchange_fee:.4%}")
print(f"券商佣金: {config.broker_commission:.4%}")

# 更新手续费配置
portfolio.update_fee_config(
    broker_commission=0.0002,  # 调整佣金率
    min_commission=5.0         # 调整最低佣金
)
```

---

## 6. 目录结构

```
portfolio_manager/
├── __init__.py              # 对外导出 PortfolioCommands
├── models.py                # Pydantic 数据模型
├── database.py              # SQLAlchemy 模型定义
├── config.py                # 配置管理
├── fee_calculator.py        # 手续费计算器
├── position_service.py      # 持仓管理服务
├── transaction_service.py   # 交易管理服务
├── account_service.py       # 资金管理服务
└── commands.py              # 统一命令入口

tests/
├── test_models.py
├── test_fee_calculator.py
├── test_position_service.py
├── test_transaction_service.py
├── test_account_service.py
└── test_commands.py

config/
└── portfolio.json           # 配置文件示例

docs/
└── README.md                # 使用文档
```

---

## 7. 测试策略

### 7.1 单元测试覆盖

| 模块                     | 测试要点              | 覆盖率目标 |
| ---------------------- | ----------------- | ----- |
| **FeeCalculator**      | 买入/卖出手续费计算、配置更新   | 90%+  |
| **PositionService**    | CRUD 持仓、盈亏计算、仓位比例 | 85%+  |
| **TransactionService** | 买入/卖出交易、持仓联动、资金联动 | 95%+  |
| **AccountService**     | 汇总计算、现金管理         | 90%+  |
| **Commands**           | 集成测试、端到端流程        | 100%+ |

### 7.2 测试场景

#### 持仓管理测试

- ✅ 新增持仓，验证成本价支持负数
- ✅ 更新持仓，验证部分字段更新
- ✅ 获取单只持仓，验证计算指标正确
- ✅ 获取持仓列表，验证批量查询性能

#### 交易管理测试

- ✅ 买入交易，验证持仓增加和现金扣减
- ✅ 卖出交易，验证持仓减少和现金增加
- ✅ 现金不足时的错误处理
- ✅ 持仓不足时的错误处理
- ✅ 交易历史查询（按股票、按日期范围）

#### 资金管理测试

- ✅ 总市值计算（股票市值 + 现金）
- ✅ 浮动盈亏汇总
- ✅ 实际盈亏计算（卖出交易累计）

#### 手续费测试

- ✅ 买入手续费（不含印花税）
- ✅ 卖出手续费（含印花税）
- ✅ 最低佣金限制
- ✅ 配置更新后重新计算

### 7.3 测试覆盖率目标

- **目标：** 80%+ 代码覆盖率
- **关键路径：** 交易联动逻辑、盈亏计算、手续费计算
- **工具：** pytest + pytest-cov

---

## 8. 成本价为负数的场景说明

### 8.1 业务场景

**高位卖出留底仓**：投资者在股价高位时卖出大部分仓位，实现盈利，但保留少量底仓继续观察。

**示例：**

- 初始买入：100 股 @ 100 元，总成本 10,000 元
- 高位卖出：90 股 @ 200 元，收入 18,000 元（扣除手续费后约 17,900 元）
- 剩余持仓：10 股
- 计算剩余持仓成本：
  - 初始成本：10,000 元
  - 卖出收入：17,900 元
  - 净盈利：7,900 元
  - 剩余 10 股的"成本"：-790 元/股（负成本）

### 8.2 系统支持

```python
# 支持成本价为负数
portfolio.add_position("600519", quantity=10, cost_price=-790)

# 系统正常计算盈亏
position = portfolio.get_position("600519")
# 如果现价 180 元，浮动盈亏 = 10 * (180 - (-790)) = 9,700 元
```

### 8.3 数据模型

```python
class PositionModel(Base):
    cost_price = Column(DECIMAL(10, 4), nullable=False)  # 支持负数
```

---

## 9. 数据一致性保障

### 9.1 交易原子性

使用数据库事务保证交易的原子性：

```python
def record_buy(self, symbol, quantity, price):
    try:
        # 1. 创建交易记录
        transaction = TransactionModel(...)
        self.db.add(transaction)

        # 2. 更新持仓
        self._update_position_on_buy(...)

        # 3. 扣减现金
        self.account_service.deduct_cash(...)

        # 4. 提交事务（原子操作）
        self.db.commit()
    except Exception as e:
        # 任何步骤失败，回滚所有操作
        self.db.rollback()
        raise e
```

### 9.2 业务规则校验

- **买入校验：** 现金是否足够
- **卖出校验：** 持仓是否足够
- **成本价校验：** 支持负数（特殊场景）

### 9.3 实时数据同步

- **持仓现价：** 每次查询时从 `data_sources` 获取最新价格
- **批量优化：** 查询持仓列表时批量获取价格，减少 API 调用

---

## 10. 配置文件示例

### 10.1 portfolio.json

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "portfolio_db",
    "user": "portfolio_user",
    "password": "your_password"
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

### 10.2 数据库初始化脚本

```sql
-- 创建数据库
CREATE DATABASE portfolio_db;

-- 创建用户
CREATE USER portfolio_user WITH PASSWORD 'your_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;
```

---

## 11. 风险与应对

| 风险          | 影响  | 应对措施                      |
| ----------- | --- | ------------------------- |
| **数据源失效**   | 中   | 依赖 `data_sources` 的自动降级机制 |
| **价格延迟**    | 低   | 接受分钟级延迟，实时性要求不高           |
| **数据不一致**   | 高   | 数据库事务 + 业务规则校验            |
| **手续费计算错误** | 高   | 单元测试覆盖所有计算场景              |
| **负成本理解困难** | 低   | 文档说明 + 使用示例               |

---

## 12. 扩展性设计

### 12.1 新增功能

- **支持分红记录**：在 `transactions` 表增加 `dividend` 类型
- **支持配股/送股**：增加相应交易类型和处理逻辑
- **支持多个投资组合**：增加 `portfolio_id` 字段

### 12.2 性能优化

- **价格缓存**：缓存实时价格 1-3 分钟，减少 API 调用
- **查询优化**：添加数据库索引，优化复杂查询
- **批量操作**：支持批量买入/卖出

---

## 13. 下一步计划

### Phase 1 - 基础框架 (2-3天)

- [ ] 数据库表结构设计和创建
- [ ] SQLAlchemy 模型定义
- [ ] Pydantic 数据模型
- [ ] 配置文件加载

### Phase 2 - 核心服务 (3-4天)

- [ ] FeeCalculator（手续费计算器）
- [ ] PositionService（持仓管理）
- [ ] AccountService（资金管理）
- [ ] TransactionService（交易管理）

### Phase 3 - 统一入口 (1天)

- [ ] PortfolioCommands（统一命令入口）
- [ ] 集成测试

### Phase 4 - 测试与文档 (2-3天)

- [ ] 单元测试（80%+ 覆盖率）
- [ ] 集成测试
- [ ] 使用文档
- [ ] 示例代码

---

## 14. 设计审批

- [x] 架构设计 ✓
- [x] 接口设计 ✓
- [x] 数据模型设计 ✓
- [x] 业务逻辑设计 ✓
- [x] 测试策略 ✓

**审批人：** _________张新光________
**日期：** _________20260315________

---

## 附录：关键决策记录

### 决策 1：简洁架构（方案 A）

**原因：** 需求明确简单，不需要过度设计，快速开发，易于维护。

### 决策 2：PostgreSQL 数据库

**原因：** 单用户但需要可靠的数据持久化，支持复杂查询和事务。

### 决策 3：纯 Python 命令行接口

**原因：** 无需界面和券商对接，符合个人使用场景。

### 决策 4：支持成本价为负数

**原因：** 适配高位卖出留底仓的盈利场景。
