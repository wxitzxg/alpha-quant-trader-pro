import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime
from portfolio_manager.position_service import PositionService
from portfolio_manager.models import PositionModel
from portfolio_manager.database import Position


class TestPositionService:
    """Unit tests for PositionService.sync_position() method"""

    @pytest.fixture
    def position_repo(self):
        return Mock()

    @pytest.fixture
    def data_source_aggregator(self):
        return Mock()

    @pytest.fixture
    def position_service(self, position_repo, data_source_aggregator):
        return PositionService(repository=position_repo, data_source_aggregator=data_source_aggregator)

    def test_sync_new_position_creates_position(self, position_service, position_repo, data_source_aggregator):
        """Test syncing a new position (create)"""
        # Arrange
        symbol = "AAPL"
        quantity = 100
        cost_price = 150.0

        position_repo.get_by_symbol.return_value = None
        data_source_aggregator.get_realtime.return_value = Mock(price=155.0)

        # Mock the Position creation and calculate_metrics
        mock_position = Mock(spec=Position)
        mock_position.symbol = symbol
        mock_position.quantity = quantity
        mock_position.cost_price = Decimal(str(cost_price))
        mock_position.current_price = Decimal('155.0')
        mock_position.market_value = Decimal('15500.0')
        mock_position.cost_value = Decimal('15000.0')
        mock_position.floating_pl = Decimal('500.0')
        mock_position.last_updated = datetime.now()
        mock_position.id = None

        with patch('portfolio_manager.position_service.Position', return_value=mock_position):
            # Act
            result = position_service.sync_position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price
            )

            # Assert
            position_repo.get_by_symbol.assert_called_once_with(symbol)
            data_source_aggregator.get_realtime.assert_called_once_with(symbol)
            position_repo.add.assert_called_once_with(mock_position)
            mock_position.calculate_metrics.assert_called_once()

            assert isinstance(result, PositionModel)
            assert result.symbol == symbol
            assert result.quantity == quantity
            assert result.cost_price == cost_price
            assert result.current_price == 155.0

    def test_sync_existing_position_updates_position(self, position_service, position_repo, data_source_aggregator):
        """Test syncing an existing position (update)"""
        # Arrange
        symbol = "AAPL"
        quantity = 150  # Updated quantity
        cost_price = 145.0  # Updated cost price

        # Create a real Position object instead of Mock to avoid conversion issues
        existing_position = Position(
            symbol=symbol,
            quantity=100,
            cost_price=Decimal('150.0'),
            current_price=Decimal('155.0')
        )
        existing_position.id = 123
        # Calculate initial metrics
        existing_position.calculate_metrics()

        position_repo.get_by_symbol.return_value = existing_position
        data_source_aggregator.get_realtime.return_value = Mock(price=160.0)

        # Act
        result = position_service.sync_position(
            symbol=symbol,
            quantity=quantity,
            cost_price=cost_price
        )

        # Assert
        position_repo.get_by_symbol.assert_called_once_with(symbol)
        data_source_aggregator.get_realtime.assert_called_once_with(symbol)
        # Should not call add for existing position
        position_repo.add.assert_not_called()

        assert existing_position.quantity == quantity
        assert existing_position.cost_price == Decimal(str(cost_price))
        assert existing_position.current_price == Decimal('160.0')
        assert isinstance(result, PositionModel)
        assert result.symbol == symbol
        assert result.quantity == quantity
        # Verify metrics were recalculated
        assert result.market_value == 150 * 160.0  # quantity * current_price
        assert result.floating_pl == (160.0 - 145.0) * 150  # (current - cost) * quantity

    def test_sync_with_automatic_price_query(self, position_service, position_repo, data_source_aggregator):
        """Test syncing with automatic price query"""
        # Arrange
        symbol = "GOOGL"
        quantity = 50
        cost_price = 2800.0

        position_repo.get_by_symbol.return_value = None
        data_source_aggregator.get_realtime.return_value = Mock(price=2850.0)

        mock_position = Mock(spec=Position)
        mock_position.symbol = symbol
        mock_position.quantity = quantity
        mock_position.cost_price = Decimal(str(cost_price))
        mock_position.current_price = Decimal('2850.0')
        mock_position.market_value = Decimal('142500.0')
        mock_position.cost_value = Decimal('140000.0')
        mock_position.floating_pl = Decimal('2500.0')
        mock_position.last_updated = datetime.now()
        mock_position.id = None

        with patch('portfolio_manager.position_service.Position', return_value=mock_position):
            # Act
            position_service.sync_position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price
            )

            # Assert
            data_source_aggregator.get_realtime.assert_called_once_with(symbol)

    def test_sync_with_provided_price_should_not_query(self, position_service, position_repo, data_source_aggregator):
        """Test syncing with provided price (should not query)"""
        # Arrange
        symbol = "MSFT"
        quantity = 75
        cost_price = 300.0
        provided_price = 305.0

        position_repo.get_by_symbol.return_value = None

        mock_position = Mock(spec=Position)
        mock_position.symbol = symbol
        mock_position.quantity = quantity
        mock_position.cost_price = Decimal(str(cost_price))
        mock_position.current_price = Decimal(str(provided_price))
        mock_position.market_value = Decimal('22875.0')
        mock_position.cost_value = Decimal('22500.0')
        mock_position.floating_pl = Decimal('375.0')
        mock_position.last_updated = datetime.now()
        mock_position.id = None

        with patch('portfolio_manager.position_service.Position', return_value=mock_position):
            # Act
            position_service.sync_position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price,
                current_price=provided_price
            )

            # Assert
            data_source_aggregator.get_realtime.assert_not_called()
            position_repo.add.assert_called_once_with(mock_position)

    def test_metrics_are_calculated(self, position_service, position_repo, data_source_aggregator):
        """Test that metrics are calculated"""
        # Arrange
        symbol = "TSLA"
        quantity = 25
        cost_price = 200.0
        current_price = 220.0

        position_repo.get_by_symbol.return_value = None

        mock_position = Mock(spec=Position)
        mock_position.symbol = symbol
        mock_position.quantity = quantity
        mock_position.cost_price = Decimal(str(cost_price))
        mock_position.current_price = Decimal(str(current_price))
        mock_position.market_value = Decimal('5500.0')  # 25 * 220
        mock_position.cost_value = Decimal('5000.0')   # 25 * 200
        mock_position.floating_pl = Decimal('500.0')   # 5500 - 5000
        mock_position.last_updated = datetime.now()
        mock_position.id = None

        with patch('portfolio_manager.position_service.Position', return_value=mock_position):
            # Act
            result = position_service.sync_position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price,
                current_price=current_price
            )

            # Assert
            mock_position.calculate_metrics.assert_called_once()
            assert result.market_value == 5500.0
            assert result.cost_value == 5000.0
            assert result.floating_pl == 500.0

    def test_with_negative_cost_price_allowed(self, position_service, position_repo, data_source_aggregator):
        """Test with negative cost price (allowed scenario)"""
        # Arrange
        symbol = "SHORT_STOCK"
        quantity = 100
        cost_price = -50.0  # Short position or other scenario
        current_price = 45.0

        position_repo.get_by_symbol.return_value = None

        mock_position = Mock(spec=Position)
        mock_position.symbol = symbol
        mock_position.quantity = quantity
        mock_position.cost_price = Decimal(str(cost_price))
        mock_position.current_price = Decimal(str(current_price))
        mock_position.market_value = Decimal('4500.0')   # 100 * 45
        mock_position.cost_value = Decimal('-5000.0')   # 100 * (-50)
        mock_position.floating_pl = Decimal('9500.0')   # 4500 - (-5000) = 9500
        mock_position.last_updated = datetime.now()
        mock_position.id = None

        with patch('portfolio_manager.position_service.Position', return_value=mock_position):
            # Act
            result = position_service.sync_position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price,
                current_price=current_price
            )

            # Assert
            assert result.cost_price == cost_price
            assert result.current_price == current_price
            assert result.market_value == 4500.0
            assert result.cost_value == -5000.0
            assert result.floating_pl == 9500.0

    def test_quantity_validation(self, position_service, position_repo, data_source_aggregator):
        """Test that quantity validation works"""
        # Arrange
        symbol = "TEST"
        cost_price = 100.0

        # Act & Assert
        with pytest.raises(ValueError, match="Quantity must be > 0"):
            position_service.sync_position(
                symbol=symbol,
                quantity=0,
                cost_price=cost_price
            )

        with pytest.raises(ValueError, match="Quantity must be > 0"):
            position_service.sync_position(
                symbol=symbol,
                quantity=-10,
                cost_price=cost_price
            )