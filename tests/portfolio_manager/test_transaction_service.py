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
    # 先增加现金（需要更多以支付手续费）
    db_session.add(CashBalance(amount=200000))
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
    db_session.add(CashBalance(amount=300000))
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
    db_session.add(CashBalance(amount=200000))
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
    db_session.add(CashBalance(amount=300000))
    db_session.commit()

    # 第一次买入
    transaction_service.record_buy("600519", 100, 1500.0)

    # 第二次买入（不同价格）
    transaction_service.record_buy("600519", 50, 1600.0)

    # 验证加权平均成本
    position = transaction_service.position_service.get_position("600519")
    expected_cost = (100 * 1500.0 + 50 * 1600.0) / 150
    assert abs(position.cost_price - expected_cost) < 0.01
