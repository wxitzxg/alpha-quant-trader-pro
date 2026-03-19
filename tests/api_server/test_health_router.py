#!/usr/bin/env python3
"""测试健康检查 API 路由器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
from fastapi.testclient import TestClient


from api_server.main import app


class TestHealthAPI:
    """健康检查 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        client = TestClient(app)
        client.headers["X-API-Key"] = "sk_test_your-secret-key-change-in-production"
        return client

    def test_health_check_success(self, client):
        """测试健康检查 - 成功"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"
        assert "Service is healthy" in data["message"]

    def test_health_check_data_structure(self, client):
        """测试健康检查 - 数据结构"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
