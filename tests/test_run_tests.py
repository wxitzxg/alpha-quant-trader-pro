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
        if os.path.exists(".env.test"):
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
