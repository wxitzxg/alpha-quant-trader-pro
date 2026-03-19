#!/usr/bin/env python3
"""
API Server 配置
使用 pydantic-settings 管理配置
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """API Server 配置"""

    # 基础配置
    API_TITLE: str = "Alpha Quant Trader Pro API"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "量化交易系统开放API"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/stock_market")

    # Redis 配置（可选）
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # 认证配置
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "your-secret-key-change-in-production")
    API_KEY_HEADER: str = "X-API-Key"
    API_SIGNATURE_HEADER: str = "X-API-Signature"
    API_TIMESTAMP_HEADER: str = "X-Timestamp"

    # 限流配置
    RATE_LIMIT_FREE: int = 60  # 免费用户每分钟 60 次
    RATE_LIMIT_STANDARD: int = 600  # 标准用户每分钟 600 次
    RATE_LIMIT_PREMIUM: int = 3600  # 高级用户每分钟 3600 次

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/api.log"

    model_config = SettingsConfigDict(
        env_file=".env.api",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
