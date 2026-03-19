#!/usr/bin/env python3
"""
API 认证工具
提供 API Key 验证和签名验证功能
"""

import hmac
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from .config import settings


class APIAuth:
    """API 认证类"""

    @staticmethod
    def verify_api_key(api_key: str) -> bool:
        """
        验证 API Key

        Args:
            api_key: API Key

        Returns:
            是否有效
        """
        # 简单验证：检查是否以 sk_ 开头
        if not api_key or not api_key.startswith("sk_"):
            return False

        # TODO: 从数据库查询 API Key 信息
        # 这里暂时使用环境变量验证
        valid_keys = [
            f"sk_test_{settings.API_KEY_SECRET}",
            f"sk_live_{settings.API_KEY_SECRET}"
        ]

        return api_key in valid_keys

    @staticmethod
    def verify_signature(
        api_key: str,
        signature: str,
        timestamp: str,
        body: str = ""
    ) -> bool:
        """
        验证请求签名

        Args:
            api_key: API Key
            signature: 签名
            timestamp: 时间戳
            body: 请求体

        Returns:
            是否有效
        """
        # 检查时间戳是否过期（5分钟）
        try:
            request_time = datetime.fromtimestamp(int(timestamp))
            current_time = datetime.now()
            time_diff = current_time - request_time

            if time_diff > timedelta(minutes=5):
                return False
        except (ValueError, TypeError):
            return False

        # 生成预期签名
        message = f"{timestamp}{body}"
        expected_signature = hmac.new(
            settings.API_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 安全比较
        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def generate_api_key(is_test: bool = True) -> Tuple[str, str]:
        """
        生成 API Key 和 Secret

        Args:
            is_test: 是否为测试环境

        Returns:
            (api_key, api_secret)
        """
        import secrets
        import string

        # 生成随机字符串
        chars = string.ascii_letters + string.digits
        random_str = ''.join(secrets.choice(chars) for _ in range(32))

        prefix = "sk_test_" if is_test else "sk_live_"
        api_key = f"{prefix}{random_str}"
        api_secret = secrets.token_hex(32)

        return api_key, api_secret


def verify_api_request(
    api_key: Optional[str],
    signature: Optional[str] = None,
    timestamp: Optional[str] = None,
    body: str = ""
) -> None:
    """
    验证 API 请求

    Args:
        api_key: API Key
        signature: 签名
        timestamp: 时间戳
        body: 请求体

    Raises:
        HTTPException: 认证失败
    """
    # 检查 API Key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not APIAuth.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 如果提供了签名，验证签名
    if signature and timestamp:
        if not APIAuth.verify_signature(api_key, signature, timestamp, body):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
                headers={"WWW-Authenticate": "Bearer"}
            )
