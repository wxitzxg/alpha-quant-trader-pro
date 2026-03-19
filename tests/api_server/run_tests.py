#!/usr/bin/env python3
"""API 服务层测试运行器"""

import sys
import os
sys.path.insert(0, '.')

import pytest
import argparse


def run_tests():
    """运行所有 API 服务层测试"""
    parser = argparse.ArgumentParser(description="Run API server tests")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-k",
        type=str,
        help="Run only tests that match the expression"
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Enable coverage reporting"
    )
    args = parser.parse_args()

    # 测试文件列表
    test_files = [
        "tests/api_server/test_stock_market_service.py",
        "tests/api_server/test_portfolio_service.py",
        "tests/api_server/test_financial_service.py",
        "tests/api_server/test_fundflow_service.py",
        "tests/api_server/test_news_service.py",
        "tests/api_server/test_stock_market_router.py",
    ]

    # 构建 pytest 参数
    pytest_args = test_files.copy()

    if args.verbose:
        pytest_args.insert(0, "-v")

    if args.k:
        pytest_args.extend(["-k", args.k])

    if args.cov:
        pytest_args.extend([
            "--cov=api_server/services",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])

    print(f"Running API server tests with args: {pytest_args}")
    print("=" * 80)

    # 运行测试
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {exit_code} test(s) failed")

    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests()
