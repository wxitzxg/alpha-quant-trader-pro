# ==================== 阶段 1: 构建依赖 ====================
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 配置 pip 阿里镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --user --no-cache-dir -r requirements.txt


# ==================== 阶段 2: 运行时镜像 ====================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖（从 builder 阶段）
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["gunicorn", "-c", "gunicorn.conf.py", "api_server.main:app"]
