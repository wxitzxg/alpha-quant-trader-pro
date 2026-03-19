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
