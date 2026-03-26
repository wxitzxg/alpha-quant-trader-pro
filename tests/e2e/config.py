"""E2E 测试配置"""

E2E_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "timeout": 30.0,
    "test_stocks": ["600011", "601611"],  # 华能国际、中国核建
    "default_stock": "600011",
}
