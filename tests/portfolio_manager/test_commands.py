# tests/portfolio_manager/test_commands.py
"""统一命令入口测试"""

import pytest
from datetime import datetime
from portfolio_manager import PortfolioCommands


def test_commands_initialization():
    """测试命令对象初始化"""
    # 使用默认配置（SQLite）
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
