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
