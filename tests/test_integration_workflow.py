#!/usr/bin/env python3
"""
集成测试：验证完整的测试环境工作流
"""
import subprocess
import sys
import time


def test_full_workflow():
    """测试完整工作流"""
    print("🧪 集成测试：完整工作流\n")

    # 1. 启动环境
    print("1️⃣  启动测试环境...")
    result = subprocess.run(
        ["python3", "tests/run_tests.py", "--setup"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 启动失败:\n{result.stderr}")
        return False

    print("✓ 环境启动成功")
    time.sleep(2)

    # 2. 检查状态
    print("\n2️⃣  检查环境状态...")
    result = subprocess.run(
        ["python3", "tests/run_tests.py", "--status"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 状态检查失败:\n{result.stderr}")
        return False

    print("✓ 状态检查通过")

    # 3. 停止环境
    print("\n3️⃣  停止测试环境...")
    result = subprocess.run(
        ["python3", "tests/run_tests.py", "--teardown", "--force"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 停止失败:\n{result.stderr}")
        return False

    print("✓ 环境停止成功")

    print("\n✅ 集成测试通过！")
    return True


if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
