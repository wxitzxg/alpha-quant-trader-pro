#!/bin/bash
# API Server 部署脚本

set -e

echo "🚀 Starting API Server Deployment..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# 检查环境变量
source .env

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is not set in .env"
    exit 1
fi

if [ -z "$API_KEY_SECRET" ]; then
    echo "❌ API_KEY_SECRET is not set in .env"
    exit 1
fi

echo "✅ Environment variables validated"

# 构建 Docker 镜像
echo "🔨 Building Docker image..."
docker-compose build --no-cache

# 启动服务
echo "🐳 Starting services..."
docker-compose up -d

# 等待服务启动
echo "⏳ Waiting for services to start..."
sleep 10

# 检查服务状态
echo "🔍 Checking service status..."
docker-compose ps

# 测试健康检查
echo "🏥 Testing health check..."
curl -s http://localhost:8000/health | jq .

echo "✅ Deployment completed successfully!"
echo ""
echo "📖 API Documentation:"
echo "   Swagger UI: http://localhost:8000/docs"
echo "   ReDoc:      http://localhost:8000/redoc"
