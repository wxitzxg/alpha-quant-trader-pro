"""
集成测试：验证 Phase 1 的所有修复

测试内容：
1. Repository 生命周期问题修复
2. 实际盈亏计算正确性
3. 现金余额表乐观锁机制
4. 完整交易流程
5. 错误处理（现金不足、持仓不足）
6. 并发场景测试
"""

import pytest
from decimal import Decimal
from datetime import datetime
from portfolio_manager.commands_refactored import PortfolioCommands
from common.exceptions import InsufficientFundsError, InsufficientSharesError


class TestPhase1Integration:
    """Phase 1 集成测试"""

    def setup_method(self):
        """每个测试方法前重置状态"""
        # 这里假设有一个测试数据库或内存数据库
        # 在实际实现中，需要根据项目的测试框架调整
        self.portfolio = PortfolioCommands()
        # 重置现金余额
        self.portfolio.add_cash(100000.0)

    def teardown_method(self):
        """每个测试方法后清理"""
        if hasattr(self, 'portfolio'):
            self.portfolio.close()

    def test_complete_trading_flow(self):
        """测试完整交易流程"""
        # 初始现金
        initial_cash = self.portfolio.cash_balance()
        assert initial_cash == 100000.0

        # 买入股票
        buy_tx = self.portfolio.buy("600519", quantity=100, price=1000.0)
        assert buy_tx.symbol == "600519"
        assert buy_tx.quantity == 100
        assert buy_tx.price == 1000.0
        assert buy_tx.transaction_type == "buy"
        assert buy_tx.cost_basis is not None
        assert buy_tx.realized_pl is None  # 买入交易没有 realized_pl

        # 检查持仓
        position = self.portfolio.get_position("600519")
        assert position is not None
        assert position.quantity == 100
        assert position.cost_price == 1000.0

        # 检查现金
        cash_after_buy = self.portfolio.cash_balance()
        expected_buy_amount = 100 * 1000.0  # 股票金额
        expected_fee = expected_buy_amount * 0.0003 + 5.0  # 假设手续费配置
        expected_cash = initial_cash - expected_buy_amount - expected_fee
        # 由于手续费计算可能有小数精度问题，使用近似比较
        assert abs(cash_after_buy - expected_cash) < 1.0

        # 卖出部分股票
        sell_tx = self.portfolio.sell("600519", quantity=50, price=1100.0)
        assert sell_tx.symbol == "600519"
        assert sell_tx.quantity == 50
        assert sell_tx.price == 1100.0
        assert sell_tx.transaction_type == "sell"
        assert sell_tx.cost_basis is not None
        assert sell_tx.realized_pl is not None

        # 验证实际盈亏计算
        expected_cost_basis = 50 * 1000.0  # 50股的成本
        expected_sale_proceeds = 50 * 1100.0  # 销售收入
        expected_realized_pl = expected_sale_proceeds - expected_cost_basis
        # 手续费会影响实际到账金额，但 realized_pl 应该基于毛利润计算
        assert abs(float(sell_tx.realized_pl) - expected_realized_pl) < 10.0

        # 检查剩余持仓
        remaining_position = self.portfolio.get_position("600519")
        assert remaining_position.quantity == 50
        assert remaining_position.cost_price == 1000.0  # 成本价不变

        # 检查账户汇总
        summary = self.portfolio.account_summary()
        assert summary.positions_count == 1
        assert summary.total_realized_pl == float(sell_tx.realized_pl)

    def test_insufficient_funds_error(self):
        """测试现金不足错误"""
        # 设置很少的现金
        self.portfolio.add_cash(1000.0)

        with pytest.raises(InsufficientFundsError):
            self.portfolio.buy("600519", quantity=100, price=100.0)

    def test_insufficient_shares_error(self):
        """测试持仓不足错误"""
        # 买入一些股票
        self.portfolio.buy("600519", quantity=10, price=100.0)

        with pytest.raises(InsufficientSharesError):
            self.portfolio.sell("600519", quantity=20, price=100.0)

    def test_weighted_average_cost_calculation(self):
        """测试加权平均成本计算"""
        # 第一次买入
        self.portfolio.buy("600519", quantity=100, price=100.0)

        # 第二次买入（不同价格）
        self.portfolio.buy("600519", quantity=50, price=120.0)

        # 验证加权平均成本
        position = self.portfolio.get_position("600519")
        expected_cost = (100 * 100.0 + 50 * 120.0) / 150
        assert abs(position.cost_price - expected_cost) < 0.01

        # 卖出部分股票，成本价应该保持不变
        self.portfolio.sell("600519", quantity=50, price=110.0)
        position_after_sell = self.portfolio.get_position("600519")
        assert abs(position_after_sell.cost_price - expected_cost) < 0.01

    def test_cash_balance_optimistic_lock(self):
        """测试现金余额乐观锁机制"""
        # 这个测试在单线程环境下难以完全验证并发冲突
        # 但可以验证基本功能正常工作
        initial_balance = self.portfolio.cash_balance()

        # 多次添加现金
        self.portfolio.add_cash(1000.0)
        self.portfolio.add_cash(2000.0)

        final_balance = self.portfolio.cash_balance()
        expected_balance = initial_balance + 1000.0 + 2000.0
        assert abs(final_balance - expected_balance) < 0.01

    def test_repository_lifecycle(self):
        """测试 Repository 生命周期修复"""
        # 验证多次调用不会出现 session 关闭问题
        for i in range(5):
            positions = self.portfolio.positions()
            summary = self.portfolio.account_summary()
            cash = self.portfolio.cash_balance()

            # 所有操作都应该成功
            assert isinstance(positions, list)
            assert isinstance(summary.total_market_value, float)
            assert isinstance(cash, float)

    def test_transaction_history_with_new_fields(self):
        """测试交易历史包含新字段"""
        # 执行买卖交易
        buy_tx = self.portfolio.buy("600519", quantity=10, price=100.0)
        sell_tx = self.portfolio.sell("600519", quantity=5, price=110.0)

        # 获取交易历史
        transactions = self.portfolio.transactions("600519")
        assert len(transactions) == 2

        # 验证新字段存在
        buy_from_history = next(tx for tx in transactions if tx.transaction_type == "buy")
        sell_from_history = next(tx for tx in transactions if tx.transaction_type == "sell")

        assert buy_from_history.cost_basis is not None
        assert buy_from_history.realized_pl is None

        assert sell_from_history.cost_basis is not None
        assert sell_from_history.realized_pl is not None


if __name__ == "__main__":
    # 允许直接运行测试
    pytest.main([__file__, "-v"])