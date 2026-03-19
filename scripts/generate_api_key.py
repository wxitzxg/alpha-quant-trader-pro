#!/usr/bin/env python3
"""
生成 API Key 和 Secret
用于测试和开发环境
"""

import sys
sys.path.insert(0, '.')

from api_server.auth import APIAuth

if __name__ == "__main__":
    # 生成测试环境 API Key
    test_key, test_secret = APIAuth.generate_api_key(is_test=True)
    
    # 生成生产环境 API Key
    live_key, live_secret = APIAuth.generate_api_key(is_test=False)
    
    print("=" * 60)
    print("API Key 生成成功!")
    print("=" * 60)
    print()
    print("🧪 测试环境:")
    print(f"  API Key:    {test_key}")
    print(f"  API Secret: {test_secret}")
    print()
    print("📦 生产环境:")
    print(f"  API Key:    {live_key}")
    print(f"  API Secret: {live_secret}")
    print()
    print("=" * 60)
    print()
    print("💡 使用方法:")
    print("  1. 将 API Secret 配置到 .env.api 文件中:")
    print(f"     API_KEY_SECRET={test_secret}")
    print()
    print("  2. 在 HTTP 请求头中添加:")
    print(f"     X-API-Key: {test_key}")
    print()
    print("  3. 生成签名 (可选):")
    print("     signature = HMAC-SHA256(timestamp + body, API_SECRET)")
    print("     X-API-Signature: <signature>")
    print("     X-Timestamp: <unix_timestamp>")
    print()
