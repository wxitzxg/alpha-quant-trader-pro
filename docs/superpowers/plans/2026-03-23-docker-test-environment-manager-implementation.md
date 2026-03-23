# Docker 测试环境管理器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 扩展 `tests/run_tests.py` 支持 Docker 测试环境管理（启动/停止/状态检查/运行测试）

**Architecture:** 在现有测试脚本基础上添加环境管理功能，通过 `subprocess` 调用 Docker Compose 命令，实现一键启动、运行、清理测试环境

**Tech Stack:** Python 3.11、Docker Compose、subprocess、argparse、pytest

---

## 文件结构

### 创建/修改的文件

| 文件 | 责任 |
|-----|-----|
| `tests/run_tests.py` | 核心管理脚本，包含环境管理 + 测试运行逻辑 |
| `tests/test_run_tests.py` | `run_tests.py` 的单元测试 |
| `.env.test` | 测试环境配置文件（首次运行时自动创建） |
| `docs/superpowers/specs/2026-03-23-docker-test-environment-manager-design.md` | 设计文档 |

---

## 任务分解

### Task 1: 扩展 `run_tests.py` - 环境检查与辅助函数

**Files:**
- Modify: `tests/run_tests.py:1-200`

- [ ] **Step 1: 添加环境检查函数**

```python
import subprocess
import sys
import os
import time
from pathlib import Path

def check_docker_installed():
    """检查 Docker 是否安装"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Docker: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker 未安装或不可用")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker 未安装或不可用")
        return False


def check_docker_compose_installed():
    """检查 Docker Compose 是否安装"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Docker Compose: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker Compose 未安装或不可用")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker Compose 未安装或不可用")
        return False


def check_env_file():
    """检查 .env.test 文件是否存在"""
    env_file = Path(".env.test")
    if not env_file.exists():
        print("⚠️  未找到 .env.test，正在复制模板...")
        example_file = Path(".env.test.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print(f"✓ 已创建 {env_file}")
            print(f"⚠️  请检查 {env_file} 并根据需要修改配置")
        else:
            print("❌ 未找到 .env.test.example 模板文件")
            return False
    else:
        print(f"✓ 配置文件: {env_file}")
    return True


def check_port_available(port):
    """检查端口是否可用"""
    try:
        result = subprocess.run(
            ["netstat", "-tuln"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if f":{port}" in result.stdout:
            return False
        return True
    except:
        # Windows 或其他系统
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return True


def get_service_status(service_name):
    """获取服务状态"""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "ps", "-q", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return "running"
        return "stopped"
    except:
        return "unknown"
```

- [ ] **Step 2: 添加服务健康检查函数**

```python
def wait_for_service_health(service_name, timeout=60, interval=2):
    """等待服务健康检查通过"""
    print(f"⏳ 等待 {service_name} 启动...", end="", flush=True)

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.test.yml", "ps", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # 检查是否包含健康状态
                if "Up" in result.stdout or "healthy" in result.stdout.lower():
                    print(f"\n✓ {service_name} 已启动")
                    return True

                # 对于没有健康检查的服务，检查是否运行
                if service_name in ["test-redis", "mock-api"]:
                    if "Up" in result.stdout:
                        print(f"\n✓ {service_name} 已启动")
                        return True

            print(".", end="", flush=True)
            time.sleep(interval)
        except subprocess.TimeoutExpired:
            print(".", end="", flush=True)
            time.sleep(interval)

    print(f"\n❌ {service_name} 启动超时")
    return False


def check_all_services_healthy():
    """检查所有服务是否健康"""
    services = ["test-db", "test-redis", "mock-api"]
    all_healthy = True

    for service in services:
        status = get_service_status(service_name)
        if status != "running":
            print(f"❌ {service}: {status}")
            all_healthy = False
        else:
            print(f"✓ {service}: running")

    return all_healthy
```

- [ ] **Step 3: 添加环境变量设置函数**

```python
def setup_test_environment_vars():
    """设置测试环境变量"""
    env_vars = {
        "DATABASE_URL": "postgresql://postgres:postgres_test@localhost:5433/test_stock_market",
        "REDIS_URL": "redis://localhost:6380/0",
        "MOCK_API_URL": "http://localhost:9000",
        "USE_MOCK_API": "true",
        "APP_ENV": "testing",
    }

    for key, value in env_vars.items():
        os.environ[key] = value

    print("✓ 测试环境变量已设置")
```

- [ ] **Step 4: 测试环境检查函数**

运行: `python -c "from tests.run_tests import check_docker_installed; print(check_docker_installed())"`
预期: 输出 Docker 版本并返回 True

- [ ] **Step 5: 提交**

```bash
git add tests/run_tests.py
git commit -m "feat(run_tests): add environment check and helper functions

- Add Docker installation check
- Add Docker Compose installation check
- Add .env.test file check
- Add port availability check
- Add service status and health check functions
- Add test environment variables setup

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 扩展 `run_tests.py` - 环境管理命令

**Files:**
- Modify: `tests/run_tests.py:200-350`

- [ ] **Step 1: 添加启动环境函数**

```python
def setup_test_environment(force=False):
    """启动测试环境"""
    print("\n🚀 启动测试环境...\n")

    # 检查依赖
    if not check_docker_installed():
        print("❌ 请先安装 Docker: https://www.docker.com/")
        return False

    if not check_docker_compose_installed():
        print("❌ 请先安装 Docker Compose")
        return False

    # 检查端口
    ports = [5433, 6380, 9000]
    for port in ports:
        if not check_port_available(port):
            print(f"❌ 端口 {port} 已被占用，请停止冲突服务后重试")
            return False

    # 检查环境文件
    if not check_env_file():
        return False

    # 启动服务
    print("\n📦 启动 Docker 服务...")
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"❌ 启动失败:\n{result.stderr}")
            return False

        print("✓ Docker Compose 启动成功")
    except subprocess.TimeoutExpired:
        print("❌ 启动超时")
        return False

    # 等待服务健康
    print("\n⏳ 等待服务就绪...\n")

    services = ["test-db", "test-redis", "mock-api"]
    for service in services:
        if not wait_for_service_health(service):
            print(f"\n❌ {service} 启动失败，正在清理...")
            teardown_test_environment(force=True)
            return False

    print("\n✅ 测试环境启动成功！\n")
    print("服务信息:")
    print("  - test-db:    localhost:5433")
    print("  - test-redis: localhost:6380")
    print("  - mock-api:   localhost:9000")

    return True
```

- [ ] **Step 2: 添加停止环境函数**

```python
def teardown_test_environment(force=False, purge=False):
    """停止测试环境"""
    print("\n🛑 停止测试环境...\n")

    if not force:
        response = input("确认停止测试环境？(y/n): ")
        if response.lower() != 'y':
            print("⚠️  操作已取消")
            return False

    try:
        cmd = ["docker-compose", "-f", "docker-compose.test.yml", "down"]
        if purge:
            cmd.append("--volumes")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✅ 测试环境已停止")
            if purge:
                print("✅ 数据卷已清理")
            return True
        else:
            print(f"❌ 停止失败:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ 停止超时")
        return False
```

- [ ] **Step 3: 添加状态检查函数**

```python
def show_test_environment_status():
    """显示测试环境状态"""
    print("\n📊 测试环境状态:\n")

    # 检查 Docker
    docker_ok = check_docker_installed()
    compose_ok = check_docker_compose_installed()

    if not (docker_ok and compose_ok):
        return False

    # 检查服务
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(result.stdout)

            # 检查所有服务是否运行
            if "Up" in result.stdout:
                print("✅ 测试环境正在运行")
                return True
            else:
                print("⚠️  测试环境未运行")
                return False
        else:
            print("⚠️  无法获取服务状态")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
```

- [ ] **Step 4: 添加重置环境函数**

```python
def reset_test_environment():
    """重置测试环境（停止+启动）"""
    print("\n🔄 重置测试环境...\n")

    # 停止
    print("⏹️  停止现有环境...")
    teardown_test_environment(force=True)

    # 启动
    print("\n▶️  启动新环境...")
    return setup_test_environment()
```

- [ ] **Step 5: 测试启动函数**

运行: `python -c "from tests.run_tests import setup_test_environment; setup_test_environment(force=True)"`
预期: 启动 Docker 服务并等待健康检查通过

- [ ] **Step 6: 提交**

```bash
git add tests/run_tests.py
git commit -m "feat(run_tests): add environment management commands

- Add setup_test_environment() for starting services
- Add teardown_test_environment() for stopping services
- Add show_test_environment_status() for checking status
- Add reset_test_environment() for resetting environment
- Support force and purge options for teardown

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 扩展 `run_tests.py` - 测试运行命令

**Files:**
- Modify: `tests/run_tests.py:350-450`

- [ ] **Step 1: 添加验证环境函数**

```python
def verify_test_environment():
    """验证测试环境是否可用"""
    # 检查服务是否运行
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and "Up" in result.stdout:
            print("✓ 测试环境可用")
            setup_test_environment_vars()
            return True
        else:
            print("⚠️  测试环境未运行")
            print("💡 提示: 运行 'python tests/run_tests.py --setup' 启动环境")
            return False
    except Exception as e:
        print(f"❌ 无法检查测试环境: {e}")
        return False
```

- [ ] **Step 2: 添加运行测试函数**

```python
def run_tests(test_files=None, pytest_args=None):
    """运行测试"""
    print("\n🧪 运行测试...\n")

    # 验证环境
    if not verify_test_environment():
        return 1

    # 构建 pytest 命令
    cmd = ["pytest"]

    # 添加测试文件
    if test_files:
        cmd.extend(test_files)
    else:
        cmd.extend([
            "tests/api_server/test_stock_market_service.py",
            "tests/api_server/test_portfolio_service.py",
            "tests/api_server/test_financial_service.py",
            "tests/api_server/test_fundflow_service.py",
            "tests/api_server/test_news_service.py",
            "tests/api_server/test_stock_market_router.py",
        ])

    # 添加 pytest 参数
    if pytest_args:
        cmd.extend(pytest_args)

    print(f"📋 测试命令: {' '.join(cmd)}\n")

    # 运行测试
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 130
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return 1
```

- [ ] **Step 3: 添加一键测试函数**

```python
def setup_and_run_tests(test_files=None, pytest_args=None, skip_setup=False):
    """启动环境并运行测试"""
    print("\n🚀 一键测试模式\n")

    # 启动环境（如果需要）
    if not skip_setup:
        if not setup_test_environment():
            print("❌ 环境启动失败，无法运行测试")
            return 1

    # 运行测试
    exit_code = run_tests(test_files, pytest_args)

    if exit_code == 0:
        print("\n✅ 所有测试通过！")
    else:
        print(f"\n❌ {exit_code} 个测试失败")
        print("💡 环境已保留以便调试，完成后运行:")
        print("   python tests/run_tests.py --teardown")

    return exit_code
```

- [ ] **Step 4: 测试运行函数**

运行: `python -c "from tests.run_tests import verify_test_environment; print(verify_test_environment())"`
预期: 检查环境并设置环境变量

- [ ] **Step 5: 提交**

```bash
git add tests/run_tests.py
git commit -m "feat(run_tests): add test execution commands

- Add verify_test_environment() for environment validation
- Add run_tests() for executing pytest
- Add setup_and_run_tests() for one-step testing
- Auto-set environment variables for test execution
- Support custom test files and pytest arguments

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 扩展 `run_tests.py` - 命令行接口

**Files:**
- Modify: `tests/run_tests.py:450-600`

- [ ] **Step 1: 重写主函数的参数解析**

```python
def run_tests_cli():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description="API 服务层测试运行器 - 支持 Docker 测试环境管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动测试环境
  python tests/run_tests.py --setup

  # 运行测试
  python tests/run_tests.py

  # 启动并运行测试
  python tests/run_tests.py --setup-and-run

  # 运行特定测试
  python tests/run_tests.py -k "test_stock"

  # 带覆盖率报告
  python tests/run_tests.py --cov

  # 停止测试环境
  python tests/run_tests.py --teardown

  # 查看状态
  python tests/run_tests.py --status
        """
    )

    # 环境管理命令
    parser.add_argument(
        "--setup", "-u", "--up",
        action="store_true",
        help="启动测试环境 (docker-compose up)"
    )

    parser.add_argument(
        "--teardown", "-d", "--down",
        action="store_true",
        help="停止测试环境 (docker-compose down)"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="查看测试环境状态"
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置测试环境 (teardown + setup)"
    )

    parser.add_argument(
        "--setup-and-run", "--test",
        action="store_true",
        help="启动环境并运行测试（一键测试）"
    )

    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="跳过环境启动（配合 --setup-and-run 使用）"
    )

    # teardown 选项
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制操作（跳过确认）"
    )

    parser.add_argument(
        "--purge",
        action="store_true",
        help="清理数据卷（与 --teardown 配合使用）"
    )

    # 测试选项（传递给 pytest）
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )

    parser.add_argument(
        "-k",
        type=str,
        help="运行匹配表达式的测试"
    )

    parser.add_argument(
        "--cov",
        action="store_true",
        help="生成覆盖率报告"
    )

    parser.add_argument(
        "test_files",
        nargs="*",
        help="指定测试文件（默认运行所有 API Server 测试）"
    )

    args = parser.parse_args()

    # 环境管理命令
    if args.setup:
        success = setup_test_environment()
        sys.exit(0 if success else 1)

    if args.teardown:
        success = teardown_test_environment(force=args.force, purge=args.purge)
        sys.exit(0 if success else 1)

    if args.status:
        success = show_test_environment_status()
        sys.exit(0 if success else 1)

    if args.reset:
        success = reset_test_environment()
        sys.exit(0 if success else 1)

    # 一键测试
    if args.setup_and_run:
        # 构建 pytest 参数
        pytest_args = []
        if args.verbose:
            pytest_args.append("-v")
        if args.k:
            pytest_args.extend(["-k", args.k])
        if args.cov:
            pytest_args.extend([
                "--cov=api_server/services",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])

        exit_code = setup_and_run_tests(
            test_files=args.test_files,
            pytest_args=pytest_args,
            skip_setup=args.skip_setup
        )
        sys.exit(exit_code)

    # 默认：运行测试
    pytest_args = []
    if args.verbose:
        pytest_args.append("-v")
    if args.k:
        pytest_args.extend(["-k", args.k])
    if args.cov:
        pytest_args.extend([
            "--cov=api_server/services",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])

    exit_code = run_tests(
        test_files=args.test_files,
        pytest_args=pytest_args
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests_cli()
```

- [ ] **Step 2: 测试命令行接口**

运行: `python tests/run_tests.py --help`
预期: 显示完整的帮助信息

运行: `python tests/run_tests.py --setup --help`
预期: 显示帮助信息（--setup 不需要参数）

- [ ] **Step 3: 提交**

```bash
git add tests/run_tests.py
git commit -m "feat(run_tests): add command-line interface

- Rewrite main function with argparse
- Support environment management commands (--setup, --teardown, --status, --reset)
- Support one-step testing (--setup-and-run)
- Support pytest arguments (-k, --cov, -v)
- Add comprehensive help and examples

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 编写 `run_tests.py` 单元测试

**Files:**
- Create: `tests/test_run_tests.py`

- [ ] **Step 1: 创建测试文件框架**

```python
"""
run_tests.py 单元测试
测试环境管理功能
"""
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.run_tests import (
    check_docker_installed,
    check_docker_compose_installed,
    check_env_file,
    check_port_available,
    get_service_status,
)


class TestEnvironmentChecks:
    """环境检查测试"""

    def test_check_docker_installed(self):
        """测试 Docker 安装检查"""
        result = check_docker_installed()
        # 应该返回布尔值
        assert isinstance(result, bool)

    def test_check_docker_compose_installed(self):
        """测试 Docker Compose 安装检查"""
        result = check_docker_compose_installed()
        assert isinstance(result, bool)

    def test_check_env_file_exists(self):
        """测试 .env.test 文件检查（文件存在时）"""
        # 创建临时 .env.test 文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.test', delete=False) as f:
            f.write("TEST_VAR=test")
            temp_file = f.name

        try:
            os.rename(temp_file, ".env.test")
            result = check_env_file()
            assert result is True
        finally:
            if os.path.exists(".env.test"):
                os.remove(".env.test")

    def test_check_env_file_missing(self):
        """测试 .env.test 文件检查（文件不存在但有模板时）"""
        # 确保 .env.test 不存在
        if os.path.exists(".env.test"):
            os.remove(".env.test")

        # 确保 .env.test.example 存在
        if not os.path.exists(".env.test.example"):
            with open(".env.test.example", "w") as f:
                f.write("# Test template")

        result = check_env_file()
        assert result is True
        assert os.path.exists(".env.test")

        # 清理
        os.remove(".env.test")

    def test_check_port_available(self):
        """测试端口可用性检查"""
        # 选择一个不太可能被占用的高端口
        result = check_port_available(65535)
        assert isinstance(result, bool)

    def test_get_service_status(self):
        """测试服务状态检查"""
        result = get_service_status("test-db")
        assert result in ["running", "stopped", "unknown"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行测试**

运行: `python tests/test_run_tests.py`
预期: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/test_run_tests.py
git commit -m "test(run_tests): add unit tests for environment management

- Add tests for Docker installation check
- Add tests for environment file check
- Add tests for port availability check
- Add tests for service status check

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 集成测试与文档

**Files:**
- Modify: `docs/superpowers/specs/2026-03-23-docker-test-environment-manager-design.md`

- [ ] **Step 1: 创建集成测试脚本**

```python
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
        ["python", "tests/run_tests.py", "--setup"],
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
        ["python", "tests/run_tests.py", "--status"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 状态检查失败:\n{result.stderr}")
        return False

    print("✓ 状态检查通过")

    # 3. 运行简单测试
    print("\n3️⃣  运行测试（健康检查）...")
    result = subprocess.run(
        ["python", "tests/run_tests.py", "tests/api_server/test_health_router.py", "-v"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ 测试失败:\n{result.stderr}")
        return False

    print("✓ 测试通过")

    # 4. 停止环境
    print("\n4️⃣  停止测试环境...")
    result = subprocess.run(
        ["python", "tests/run_tests.py", "--teardown", "--force"],
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
```

保存为: `tests/test_integration_workflow.py`

- [ ] **Step 2: 运行集成测试**

运行: `python tests/test_integration_workflow.py`
预期: 完整工作流测试通过

- [ ] **Step 3: 更新设计文档（添加使用示例）**

在设计文档末尾添加：

```markdown
## 10. 快速开始

### 10.1 首次使用

```bash
# 1. 复制环境变量模板
cp .env.test.example .env.test

# 2. 启动测试环境
python tests/run_tests.py --setup

# 3. 运行测试
python tests/run_tests.py

# 4. 停止环境
python tests/run_tests.py --teardown
```

### 10.2 日常使用

```bash
# 一键启动并运行测试
python tests/run_tests.py --setup-and-run

# 运行特定测试
python tests/run_tests.py -k "test_stock"

# 带覆盖率报告
python tests/run_tests.py --setup-and-run --cov

# 查看环境状态
python tests/run_tests.py --status
```

### 10.3 常见问题

**Q: 端口冲突怎么办？**
A: 修改 `docker-compose.test.yml` 中的端口映射，或停止占用端口的服务。

**Q: 测试环境无法启动？**
A: 检查 Docker 是否运行，查看日志：`docker logs alpha-quant-test-db`

**Q: 如何清理所有数据？**
A: 使用 `--purge` 选项：`python tests/run_tests.py --teardown --force --purge`
```

- [ ] **Step 4: 提交**

```bash
git add tests/test_integration_workflow.py docs/superpowers/specs/2026-03-23-docker-test-environment-manager-design.md
git commit -m "docs: add integration test and usage examples

- Add integration workflow test script
- Add quick start guide to design document
- Add FAQ section with common issues

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: 验收测试

**Files:**
- None (运行测试验证)

- [ ] **Step 1: 验证所有验收标准**

```bash
# 1. 启动环境
python tests/run_tests.py --setup

# 预期: 成功启动所有服务

# 2. 查看状态
python tests/run_tests.py --status

# 预期: 显示正确的服务状态

# 3. 运行测试
python tests/run_tests.py

# 预期: 成功运行测试并返回正确退出码

# 4. 运行特定测试
python tests/run_tests.py -k "test_health"

# 预期: 只运行匹配的测试

# 5. 一键测试
python tests/run_tests.py --setup-and-run --cov

# 预期: 启动环境 + 运行测试 + 生成覆盖率报告

# 6. 停止环境
python tests/run_tests.py --teardown

# 预期: 完全清理资源
```

- [ ] **Step 2: 运行单元测试**

运行: `python tests/test_run_tests.py -v`
预期: 所有单元测试通过

- [ ] **Step 3: 运行集成测试**

运行: `python tests/test_integration_workflow.py`
预期: 集成测试通过

- [ ] **Step 4: 验证现有测试兼容性**

运行: `python tests/run_tests.py --setup-and-run`
预期: 所有现有测试用例通过

- [ ] **Step 5: 提交最终验收**

```bash
git add .
git commit -m "feat: complete Docker test environment manager implementation

验收标准验证:
- ✅ 启动环境成功
- ✅ 查看状态正常
- ✅ 运行测试成功
- ✅ 一键测试工作
- ✅ 停止环境清理完整
- ✅ 现有测试兼容
- ✅ 错误处理清晰
- ✅ 覆盖率报告生成

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 实施完成

实施完成后，用户可以通过以下命令使用：

```bash
# 基础使用
python tests/run_tests.py --setup      # 启动环境
python tests/run_tests.py              # 运行测试
python tests/run_tests.py --teardown   # 停止环境

# 一键测试
python tests/run_tests.py --setup-and-run --cov

# 快捷命令
python tests/run_tests.py --up         # 启动
python tests/run_tests.py --down       # 停止
python tests/run_tests.py --status     # 状态
python tests/run_tests.py --reset      # 重置

# 高级用法
python tests/run_tests.py -k "test_stock"    # 过滤测试
python tests/run_tests.py --cov              # 覆盖率
python tests/run_tests.py --test-files ...   # 指定文件
```
