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
