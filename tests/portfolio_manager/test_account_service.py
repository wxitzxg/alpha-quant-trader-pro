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
