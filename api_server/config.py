#!/usr/bin/env python3
"""
API Server 配置
使用 pydantic-settings 管理配置

兼容层：从统一配置系统读取配置
Compatibility layer: reads from unified config system
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from common.config import get_config


class Settings(BaseSettings):
    """API Server 配置"""

    # ========== 兼容层：从统一配置读取 ==========
    # Backward compatibility: read from unified config

    def __init__(self, **kwargs):
        # 从统一配置加载
        unified_config = get_config()
        api_config = unified_config.api_server

        # 设置基础配置
        kwargs.setdefault('API_TITLE', api_config.api_title)
        kwargs.setdefault('API_VERSION', api_config.api_version)
        kwargs.setdefault('API_DESCRIPTION', api_config.api_description)

        # 设置服务器配置
        kwargs.setdefault('HOST', api_config.host)
        kwargs.setdefault('PORT', api_config.port)
        kwargs.setdefault('DEBUG', unified_config.debug)

        # 设置数据库配置（从统一配置的 database 读取）
        kwargs.setdefault('DATABASE_URL', unified_config.database.url)

        # 设置Redis配置
        kwargs.setdefault('REDIS_URL', api_config.redis_url)

        # 设置认证配置
        kwargs.setdefault('API_KEY_SECRET', api_config.api_key_secret)
        kwargs.setdefault('API_KEY_HEADER', api_config.api_key_header)
        kwargs.setdefault('API_SIGNATURE_HEADER', api_config.api_signature_header)
        kwargs.setdefault('API_TIMESTAMP_HEADER', api_config.api_timestamp_header)

        # 设置限流配置
        kwargs.setdefault('RATE_LIMIT_FREE', api_config.rate_limit_free)
        kwargs.setdefault('RATE_LIMIT_STANDARD', api_config.rate_limit_standard)
        kwargs.setdefault('RATE_LIMIT_PREMIUM', api_config.rate_limit_premium)

        # 设置日志配置
        kwargs.setdefault('LOG_LEVEL', unified_config.logging.level)
        kwargs.setdefault('LOG_FILE', "logs/api.log")

        # 调用父类初始化
        super().__init__(**kwargs)

    # ========== 配置字段（保持向后兼容） ==========
    # Configuration fields (backward compatible)

    # 基础配置
    API_TITLE: str
    API_VERSION: str
    API_DESCRIPTION: str

    # 服务器配置
    HOST: str
    PORT: int
    DEBUG: bool

    # 数据库配置
    DATABASE_URL: str

    # Redis 配置（可选）
    REDIS_URL: Optional[str]

    # 认证配置
    API_KEY_SECRET: str
    API_KEY_HEADER: str
    API_SIGNATURE_HEADER: str
    API_TIMESTAMP_HEADER: str

    # 限流配置
    RATE_LIMIT_FREE: int  # 免费用户每分钟 60 次
    RATE_LIMIT_STANDARD: int  # 标准用户每分钟 600 次
    RATE_LIMIT_PREMIUM: int  # 高级用户每分钟 3600 次

    # 日志配置
    LOG_LEVEL: str
    LOG_FILE: str

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
