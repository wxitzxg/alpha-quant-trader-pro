#!/usr/bin/env python3
"""测试持仓同步 API"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api_server.main import app
from .test_utils import (
    TEST_STOCK_CODE,
    TEST_STOCK_NAME,
    TEST_QUANTITY,
    TEST_PRICE_COST,
    assert_success_response,
    assert_error_response
)


class TestPortfolioSyncAPI:
    """持仓同步 API 测试"""

    @pytest.fixture
    def client(self) -> TestClient:
        """创建测试客户端"""
        test_client = TestClient(app)
        test_client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return test_client

    def test_sync_new_position(self, client: TestClient) -> None:
        """Test syncing a new position via API"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.sync_position.return_value = {
                "success": True,
                "data": {
                    "symbol": TEST_STOCK_CODE,
                    "name": TEST_STOCK_NAME,
                    "quantity": TEST_QUANTITY,
                    "cost_price": TEST_PRICE_COST,
                    "current_price": 155.25,
                    "market_value": TEST_QUANTITY * 155.25,
                    "profit": (155.25 - TEST_PRICE_COST) * TEST_QUANTITY,
                    "profit_rate": (155.25 - TEST_PRICE_COST) / TEST_PRICE_COST
                },
                "message": "Position synced successfully"
            }

            response = client.post(
                "/api/v1/portfolio/positions/sync",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY,
                    "cost_price": TEST_PRICE_COST,
                    "current_price": 155.25
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == TEST_STOCK_CODE
            assert data["data"]["quantity"] == TEST_QUANTITY
            assert data["data"]["cost_price"] == TEST_PRICE_COST
            assert data["data"]["current_price"] == 155.25

    def test_sync_existing_position(self, client: TestClient) -> None:
        """Test syncing an existing position via API"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            # Updated position with new values
            updated_position = {
                "symbol": TEST_STOCK_CODE,
                "name": TEST_STOCK_NAME,
                "quantity": TEST_QUANTITY + 50,
                "cost_price": TEST_PRICE_COST + 25.50,
                "current_price": 2900.00,
                "market_value": (TEST_QUANTITY + 50) * 2900.00,
                "profit": (2900.00 - (TEST_PRICE_COST + 25.50)) * (TEST_QUANTITY + 50),
                "profit_rate": (2900.00 - (TEST_PRICE_COST + 25.50)) / (TEST_PRICE_COST + 25.50)
            }

            mock_service.sync_position.return_value = {
                "success": True,
                "data": updated_position,
                "message": "Position synced successfully"
            }

            response = client.post(
                "/api/v1/portfolio/positions/sync",
                json={
                    "stock_code": TEST_STOCK_CODE,
                    "quantity": TEST_QUANTITY + 50,
                    "cost_price": TEST_PRICE_COST + 25.50,
                    "current_price": 2900.00
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["symbol"] == TEST_STOCK_CODE
            assert data["data"]["quantity"] == TEST_QUANTITY + 50
            assert data["data"]["cost_price"] == TEST_PRICE_COST + 25.50
            assert data["data"]["current_price"] == 2900.00

    def test_sync_with_provided_current_price(self, client: TestClient) -> None:
        """Test syncing with provided current price"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.sync_position.return_value = {
                "success": True,
                "data": {
                    "symbol": "MSFT",
                    "name": "Microsoft",
                    "quantity": 50,
                    "cost_price": 300.00,
                    "current_price": 315.75,
                    "market_value": 50 * 315.75,
                    "profit": (315.75 - 300.00) * 50,
                    "profit_rate": (315.75 - 300.00) / 300.00
                },
                "message": "Position synced successfully"
            }

            response = client.post(
                "/api/v1/portfolio/positions/sync",
                json={
                    "stock_code": "MSFT",
                    "quantity": 50,
                    "cost_price": 300.00,
                    "current_price": 315.75
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["current_price"] == 315.75
            expected_market_value = 50 * 315.75
            assert abs(data["data"]["market_value"] - expected_market_value) < 0.01

    def test_sync_with_invalid_quantity(self, client: TestClient) -> None:
        """Test syncing with invalid quantity"""
        # Test with negative quantity
        response = client.post(
            "/api/v1/portfolio/positions/sync",
            json={
                "stock_code": "TSLA",
                "quantity": -10,  # Invalid negative quantity
                "cost_price": 200.00,
                "current_price": 210.50
            }
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_sync_with_missing_required_field(self, client: TestClient) -> None:
        """Test syncing with missing required field"""
        # Test missing quantity field
        response = client.post(
            "/api/v1/portfolio/positions/sync",
            json={
                "stock_code": "AMZN",
                # Missing quantity field
                "cost_price": 180.00,
                "current_price": 185.25
            }
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_sync_with_zero_quantity(self, client: TestClient) -> None:
        """Test syncing with zero quantity (should be valid)"""
        with patch('api_server.routers.portfolio.service') as mock_service:
            mock_service.sync_position.return_value = {
                "success": True,
                "data": {
                    "symbol": "AAPL",
                    "name": "Apple",
                    "quantity": 0,
                    "cost_price": 150.00,
                    "current_price": 155.00,
                    "market_value": 0.0,
                    "profit": 0.0,
                    "profit_rate": 0.0
                },
                "message": "Position synced successfully"
            }

            response = client.post(
                "/api/v1/portfolio/positions/sync",
                json={
                    "stock_code": "AAPL",
                    "quantity": 0,  # Zero quantity should be valid
                    "cost_price": 150.00,
                    "current_price": 155.00
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert data["data"]["quantity"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])