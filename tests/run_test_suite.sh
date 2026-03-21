#!/bin/bash
set -e

echo "======================================"
echo "  Alpha Quant Trader Pro - 测试套件"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker 未运行或未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 检查通过${NC}"

# 检查 .env.test 文件
if [ ! -f .env.test ]; then
    if [ -f .env.test.example ]; then
        echo -e "${YELLOW}⚠ 检测到 .env.test.example，正在创建 .env.test...${NC}"
        cp .env.test.example .env.test
        echo -e "${BLUE}💡 提示: .env.test 已创建，当前配置为完全 Mock 模式${NC}"
        echo -e "${BLUE}   如果需要使用真实 API，编辑 .env.test 填入真实密钥${NC}"
    else
        echo -e "${RED}✗ 未找到 .env.test 或 .env.test.example${NC}"
        exit 1
    fi
fi

# 读取环境变量
source .env.test

echo ""
echo -e "${GREEN}✓ 环境检查通过${NC}"
echo ""

# 清理旧容器
echo -e "${BLUE}🔧 清理旧的测试容器...${NC}"
docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true

# 启动测试环境
echo -e "${BLUE}🚀 启动测试环境...${NC}"
docker-compose -f docker-compose.test.yml up -d

# 等待服务健康
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 15

# 检查服务状态
echo -e "${BLUE}🔍 检查服务状态...${NC}"
if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
    echo -e "${RED}✗ 服务启动失败${NC}"
    docker-compose -f docker-compose.test.yml logs
    exit 1
fi

echo -e "${GREEN}✓ 所有服务已启动${NC}"
echo ""

# 检查 Mock API
echo -e "${BLUE}📡 测试 Mock API 连接...${NC}"
if curl -s http://localhost:9000/health >/dev/null; then
    echo -e "${GREEN}✓ Mock API 运行正常${NC}"
else
    echo -e "${YELLOW}⚠ Mock API 未响应（可能不需要）${NC}"
fi

# 运行数据库迁移
echo ""
echo -e "${BLUE}🗄️  运行数据库迁移...${NC}"
if docker-compose -f docker-compose.test.yml exec -T api-server-test alembic upgrade head; then
    echo -e "${GREEN}✓ 数据库迁移完成${NC}"
else
    echo -e "${YELLOW}⚠ 数据库迁移失败或不需要（可能使用单元测试）${NC}"
fi

# 运行测试
echo ""
echo -e "${BLUE}🧪 运行测试...${NC}"
TEST_RESULT=0
docker-compose -f docker-compose.test.yml exec -T api-server-test \
    pytest tests/api_server/ \
        -v \
        --cov=api_server \
        --cov=common \
        --cov=data_sources \
        --cov-report=term-missing \
        --cov-report=html:reports/coverage \
        --junitxml=reports/test-results.xml \
        -n auto \
        || TEST_RESULT=$?

echo ""

# 停止并清理
echo -e "${BLUE}🧹 清理测试环境...${NC}"
docker-compose -f docker-compose.test.yml down -v

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}======================================"
    echo "  ✅ 所有测试通过！"
    echo "======================================${NC}"
    echo ""
    echo -e "${BLUE}📊 覆盖率报告:${NC} file://$(pwd)/reports/coverage/index.html"
    echo -e "${BLUE}📝 测试结果:${NC} $(pwd)/reports/test-results.xml"
    echo ""
    echo -e "${BLUE}💡 快速查看:${NC}"
    echo "   python -m http.server 8080 -d reports/coverage"
    echo "   然后在浏览器打开: http://localhost:8080"
else
    echo -e "${RED}======================================"
    echo "  ❌ 测试失败！"
    echo "======================================${NC}"
    echo ""
    echo -e "${YELLOW}🔍 调试建议:${NC}"
    echo "   1. 查看详细日志: docker-compose -f docker-compose.test.yml logs api-server-test"
    echo "   2. 进入容器调试: docker-compose -f docker-compose.test.yml exec api-server-test bash"
    echo "   3. 运行单个测试: pytest tests/api_server/test_xxx.py -v"
fi

exit $TEST_RESULT
