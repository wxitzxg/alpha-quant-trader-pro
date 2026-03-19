# API Server 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境

```bash
cp .env.api.example .env.api
# 编辑 .env.api 配置数据库和密钥
```

## 3. 运行测试

```bash
pytest tests/test_api/test_basic.py -v
```

## 4. 启动服务

```bash
python api_server/main.py
```

## 5. 访问 API

- 根路径: http://localhost:8000
- 健康检查: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 6. Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f api-server
```
