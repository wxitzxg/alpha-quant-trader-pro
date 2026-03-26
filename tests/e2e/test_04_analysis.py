"""Analysis endpoint tests"""

import pytest


class TestAnalysisEndpoints:
    """Test analysis API endpoints"""

    def test_five_dimension_analysis(self, client):
        """Test POST /api/v1/analysis/five-dimension endpoint"""
        response = client.post(
            "/api/v1/analysis/five-dimension",
            json={"stock_code": "600011", "days": 60}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_strategies_analysis(self, client, default_stock):
        """Test GET /api/v1/analysis/strategies/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/strategies/{default_stock}",
            params={"interval": "1d", "days": 60}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_get_indicator(self, client, default_stock):
        """Test GET /api/v1/analysis/indicator/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/indicator/{default_stock}",
            params={"indicator_name": "macd"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_analysis_report(self, client, default_stock):
        """Test GET /api/v1/analysis/report/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/report/{default_stock}",
            params={"interval": "1d", "days": 60}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_vcp_strategy(self, client, default_stock):
        """Test GET /api/v1/analysis/strategy/vcp/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/strategy/vcp/{default_stock}",
            params={"days": 120}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_td_strategy(self, client, default_stock):
        """Test GET /api/v1/analysis/strategy/td/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/strategy/td/{default_stock}",
            params={"days": 120}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_divergence_strategy(self, client, default_stock):
        """Test GET /api/v1/analysis/strategy/divergence/{stock_code} endpoint"""
        response = client.get(
            f"/api/v1/analysis/strategy/divergence/{default_stock}",
            params={"days": 120}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
