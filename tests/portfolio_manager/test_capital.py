"""
资金调整服务单元测试
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from portfolio_manager.capital_service import CapitalService, LARGE_AMOUNT_THRESHOLD
from portfolio_manager.schemas.capital_schemas import (
    AdjustmentType,
    CapitalAdjustRequest,
    CapitalAdjustResponse
)
from portfolio_manager.database import CapitalAdjustment, CashBalance
from common.exceptions import InsufficientFundsError


class TestCapitalService:
    """资金调整服务测试"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_capital_repo(self):
        """模拟资金调整仓库"""
        return Mock()

    @pytest.fixture
    def mock_cash_repo(self):
        """模拟现金余额仓库"""
        return Mock()

    @pytest.fixture
    def capital_service(self, mock_session, mock_capital_repo, mock_cash_repo):
        """创建资金调整服务实例"""
        return CapitalService(
            session=mock_session,
            capital_repo=mock_capital_repo,
            cash_repo=mock_cash_repo
        )

    def test_deposit_success(self, capital_service, mock_capital_repo, mock_cash_repo, mock_session):
        """测试转入成功"""
        # 设置模拟返回值
        mock_capital_repo.get_sum.return_value = Decimal('100000')
        mock_cash_repo.get_current_balance.return_value = 50000.0

        # 模拟 CashBalance 查询
        mock_cash_balance = Mock(spec=CashBalance)
        mock_cash_balance.amount = Decimal('50000')
        mock_cash_balance.initial_capital = Decimal('100000')

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_cash_balance
        mock_session.execute.return_value = mock_result

        # 模拟 add 方法返回带有 id 的对象
        def add_side_effect(obj):
            obj.id = 1
            return obj
        mock_capital_repo.add.side_effect = add_side_effect

        # 创建请求
        request = CapitalAdjustRequest(
            amount=50000.0,
            adjustment_type=AdjustmentType.DEPOSIT,
            reason="追加投资"
        )

        # 执行调整
        response, confirmation = capital_service.adjust_capital(request)

        # 验证
        assert confirmation is None
        assert response.adjustment_id == 1
        assert response.new_initial_capital == 150000.0
        assert response.adjustment_type == AdjustmentType.DEPOSIT
        assert response.amount == 50000.0
        mock_session.commit.assert_called_once()

    def test_withdraw_success(self, capital_service, mock_capital_repo, mock_cash_repo, mock_session):
        """测试转出成功"""
        # 设置模拟返回值
        mock_capital_repo.get_sum.return_value = Decimal('100000')
        mock_cash_repo.get_current_balance.return_value = 80000.0

        # 模拟 CashBalance 查询
        mock_cash_balance = Mock(spec=CashBalance)
        mock_cash_balance.amount = Decimal('80000')
        mock_cash_balance.initial_capital = Decimal('100000')

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_cash_balance
        mock_session.execute.return_value = mock_result

        # 模拟 add 方法返回带有 id 的对象
        def add_side_effect(obj):
            obj.id = 2
            return obj
        mock_capital_repo.add.side_effect = add_side_effect

        # 创建请求
        request = CapitalAdjustRequest(
            amount=30000.0,
            adjustment_type=AdjustmentType.WITHDRAW,
            reason="部分赎回"
        )

        # 执行调整
        response, confirmation = capital_service.adjust_capital(request)

        # 验证
        assert confirmation is None
        assert response.new_initial_capital == 70000.0
        assert response.adjustment_type == AdjustmentType.WITHDRAW

    def test_withdraw_insufficient_cash(self, capital_service, mock_cash_repo):
        """测试转出余额不足"""
        # 设置模拟返回值
        mock_cash_repo.get_current_balance.return_value = 10000.0

        # 创建请求
        request = CapitalAdjustRequest(
            amount=50000.0,
            adjustment_type=AdjustmentType.WITHDRAW,
            reason="赎回"
        )

        # 验证抛出异常
        with pytest.raises(InsufficientFundsError):
            capital_service.adjust_capital(request)

    def test_deposit_zero_amount(self, capital_service):
        """测试转入金额为0 - Pydantic 验证"""
        # Pydantic 会在请求创建时验证
        with pytest.raises(Exception):  # ValidationError
            CapitalAdjustRequest(
                amount=0.0,
                adjustment_type=AdjustmentType.DEPOSIT,
                reason="测试"
            )

    def test_deposit_negative_amount(self, capital_service):
        """测试转入金额为负数 - Pydantic 验证"""
        # Pydantic 会在请求创建时验证
        with pytest.raises(Exception):  # ValidationError
            CapitalAdjustRequest(
                amount=-1000.0,
                adjustment_type=AdjustmentType.DEPOSIT,
                reason="测试"
            )

    def test_large_amount_requires_confirmation(self, capital_service, mock_capital_repo, mock_cash_repo):
        """测试大额操作需要确认"""
        # 设置模拟返回值
        mock_capital_repo.get_sum.return_value = Decimal('100000')
        mock_cash_repo.get_current_balance.return_value = 500000.0

        # 创建大额请求（不确认）
        request = CapitalAdjustRequest(
            amount=150000.0,  # 大于阈值
            adjustment_type=AdjustmentType.DEPOSIT,
            reason="大额投资",
            confirm=False
        )

        # 执行调整
        response, confirmation = capital_service.adjust_capital(request)

        # 验证需要确认
        assert response is None
        assert confirmation is not None
        assert confirmation.get("require_confirmation") is True

    def test_large_amount_confirmed(self, capital_service, mock_capital_repo, mock_cash_repo, mock_session):
        """测试大额操作确认后执行"""
        # 设置模拟返回值
        mock_capital_repo.get_sum.return_value = Decimal('100000')
        mock_cash_repo.get_current_balance.return_value = 500000.0

        # 模拟 CashBalance 查询
        mock_cash_balance = Mock(spec=CashBalance)
        mock_cash_balance.amount = Decimal('500000')
        mock_cash_balance.initial_capital = Decimal('100000')

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_cash_balance
        mock_session.execute.return_value = mock_result

        # 模拟 add 方法返回带有 id 的对象
        def add_side_effect(obj):
            obj.id = 3
            return obj
        mock_capital_repo.add.side_effect = add_side_effect

        # 创建大额请求（确认）
        request = CapitalAdjustRequest(
            amount=150000.0,
            adjustment_type=AdjustmentType.DEPOSIT,
            reason="大额投资",
            confirm=True
        )

        # 执行调整
        response, confirmation = capital_service.adjust_capital(request)

        # 验证成功执行
        assert confirmation is None
        assert response is not None
        assert response.amount == 150000.0

    def test_get_initial_capital_sum_correctly(self, capital_service, mock_capital_repo):
        """测试初始资金正确汇总"""
        mock_capital_repo.get_sum.return_value = Decimal('150000')

        result = capital_service.get_initial_capital()

        assert result == 150000.0

    def test_new_account_initial_capital_is_zero(self, capital_service, mock_capital_repo):
        """测试新账户初始资金为0"""
        mock_capital_repo.get_sum.return_value = Decimal('0')

        result = capital_service.get_initial_capital()

        assert result == 0.0


class TestAccountSummary:
    """账户汇总测试"""

    def test_total_market_value_calculation(self):
        """测试总市值计算"""
        from portfolio_manager.models import AccountSummary

        summary = AccountSummary(
            total_market_value=105000.0,
            stock_market_value=95000.0,
            cash=10000.0,
            initial_capital=100000.0,
            total_floating_pl=3000.0,
            total_realized_pl=2000.0,
            positions_count=3
        )

        # 验证总市值 = 股票市值 + 现金
        assert summary.total_market_value == summary.stock_market_value + summary.cash
        # 验证初始资金独立记录
        assert summary.initial_capital == 100000.0

    def test_floating_and_realized_pl(self):
        """测试浮动盈亏和实际盈亏"""
        from portfolio_manager.models import AccountSummary

        summary = AccountSummary(
            total_market_value=105000.0,
            stock_market_value=95000.0,
            cash=10000.0,
            initial_capital=100000.0,
            total_floating_pl=-500.0,
            total_realized_pl=1500.0,
            positions_count=3
        )

        # 验证浮动盈亏和实际盈亏独立记录
        assert summary.total_floating_pl == -500.0
        assert summary.total_realized_pl == 1500.0
