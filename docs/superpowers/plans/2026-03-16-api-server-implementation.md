# API Server Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将量化交易系统的所有核心能力（数据源、股票市场、持仓管理、技术分析、风险控制、收益统计、风险提示）封装为基于 FastAPI 的 RESTful API 服务，支持 Docker 部署和 API Key 认证。

**Architecture:** 单体应用架构，基于现有模块构建 API 层，使用中间件处理认证、限流和日志，所有数据通过 Pydantic 模型进行验证。

**Tech Stack:** FastAPI, Pydantic, Gunicorn, Docker, PostgreSQL, Redis (可选缓存)

---

## 实施概览

**预计时间:** 17-26 天
**阶段数量:** 10 个阶段
**文件变更:** 约 80+ 个文件（新增 60+，修改 20+）

---

## 阶段 1: 基础框架搭建 (1-2天)

### 任务 1.1: 创建项目结构和依赖

**Files:**
- Create: `api_server/__init__.py`
- Create: `api_server/main.py`
- Create: `api_server/config.py`
- Create: `api_server/models/common.py`
- Create: `requirements.txt` (追加)

#### 步骤 1: 创建 API Server 目录结构

```bash
mkdir -p api_server/{middleware,exception_handlers,routers/models,schemas}
touch api_server/__init__.py
touch api_server/middleware/__init__.py
touch api_server/exception_handlers/__init__.py
touch api_server/routers/__init__.py
touch api_server/models/__init__.py
touch api_server/schemas/__init__.py
```

#### 步骤 2: 安装 FastAPI 依赖

编辑 `requirements.txt`，追加以下内容：

```txt
# API Server Dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
gunicorn==21.2.0
pydantic==2.5.3
pydantic-settings==2.1.0
slowapi==0.1.8
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
```

#### 步骤 3: 创建配置文件

创建 `api_server/config.py`:

```python
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """API Server 配置"""

    # 基础配置
    API_TITLE: str = "Alpha Quant Trader Pro API"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "量化交易系统开放API"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/stock_market")

    # Redis 配置（可选）
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # 认证配置
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "your-secret-key-change-in-production")
    API_KEY_HEADER: str = "X-API-Key"
    API_SIGNATURE_HEADER: str = "X-API-Signature"
    API_TIMESTAMP_HEADER: str = "X-Timestamp"

    # 限流配置
    RATE_LIMIT_FREE: int = 60  # 免费用户每分钟 60 次
    RATE_LIMIT_STANDARD: int = 600  # 标准用户每分钟 600 次
    RATE_LIMIT_PREMIUM: int = 3600  # 高级用户每分钟 3600 次

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/api.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

#### 步骤 4: 创建主应用文件

创建 `api_server/main.py`:

```python
#!/usr/bin/env python3
"""
API Server 主入口
FastAPI 应用初始化和路由注册
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .middleware.api_key_auth import APIKeyAuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.request_logger import RequestLoggerMiddleware
from .exception_handlers.custom_exceptions import register_exception_handlers

# 导入路由
from .routers import (
    data_source_router,
    stock_market_router,
    portfolio_router,
    analysis_router,
    risk_control_router,
    performance_router,
    alerts_router,
    health_router
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("API Server 启动中...")
    logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")
    logger.info(f"数据库: {settings.DATABASE_URL}")

    yield

    # 关闭时
    logger.info("API Server 正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册中间件（顺序很重要）
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(APIKeyAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# 注册异常处理器
register_exception_handlers(app)

# 注册路由
app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])
app.include_router(data_source_router, prefix="/api/v1", tags=["数据源聚合"])
app.include_router(stock_market_router, prefix="/api/v1", tags=["股票市场"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["持仓管理"])
app.include_router(analysis_router, prefix="/api/v1", tags=["技术分析"])
app.include_router(risk_control_router, prefix="/api/v1", tags=["风险控制"])
app.include_router(performance_router, prefix="/api/v1", tags=["收益统计"])
app.include_router(alerts_router, prefix="/api/v1", tags=["风险提示"])


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Alpha Quant Trader Pro API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

#### 步骤 5: 创建通用数据模型

创建 `api_server/models/common.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime


T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = Field(True, description="是否成功")
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[T] = Field(None, description="数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    code: int
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    success: bool = True
    data: List[T]
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class TimeRangeParams(BaseModel):
    """时间范围参数"""
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")


class SortParams(BaseModel):
    """排序参数"""
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序顺序")
```

#### 步骤 6: 创建 .env.example 文件

创建 `.env.example`:

```bash
# API Server 配置
DEBUG=False
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/stock_market

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0

# 认证配置
API_KEY_SECRET=your-secret-key-change-in-production

# 日志配置
LOG_LEVEL=INFO
```

#### 步骤 7: 提交代码

```bash
git add api_server/__init__.py api_server/main.py api_server/config.py api_server/models/common.py requirements.txt .env.example
git commit -m "feat: create API server base structure

- Initialize api_server directory structure
- Add FastAPI main application
- Add configuration management
- Add common Pydantic models
- Add .env.example for environment variables"
```

---

### 任务 1.2: 实现认证中间件

**Files:**
- Create: `api_server/middleware/api_key_auth.py`
- Create: `api_server/middleware/__init__.py`
- Create: `api_server/auth.py`

#### 步骤 1: 创建认证工具类

创建 `api_server/auth.py`:

```python
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
```

#### 步骤 2: 创建 API Key 认证中间件

创建 `api_server/middleware/api_key_auth.py`:

```python
#!/usr/bin/env python3
"""
API Key 认证中间件
验证所有请求的 API Key 和签名
"""

import json
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from ..auth import verify_api_request


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求

        Args:
            request: HTTP 请求
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP 响应
        """
        # 跳过健康检查和文档路径
        skip_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in skip_paths or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            return await call_next(request)

        # 获取请求头
        api_key = request.headers.get("X-API-Key")
        signature = request.headers.get("X-API-Signature")
        timestamp = request.headers.get("X-Timestamp")

        # 读取请求体（用于签名验证）
        body = ""
        if signature and timestamp:
            try:
                body_bytes = await request.body()
                body = body_bytes.decode('utf-8') if body_bytes else ""

                # 重新设置请求体以便后续使用
                receive = request._receive

                async def new_receive():
                    return {'type': 'http.request', 'body': body_bytes, 'more_body': False}

                request._receive = new_receive
            except Exception:
                body = ""

        # 验证 API 请求
        try:
            verify_api_request(
                api_key=api_key,
                signature=signature,
                timestamp=timestamp,
                body=body
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "code": 401,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # 继续处理请求
        response = await call_next(request)
        return response
```

#### 步骤 3: 更新 middleware __init__.py

编辑 `api_server/middleware/__init__.py`:

```python
"""Middleware 模块"""
from .api_key_auth import APIKeyAuthMiddleware

__all__ = [
    "APIKeyAuthMiddleware"
]
```

#### 步骤 4: 测试认证功能

创建临时测试文件 `test_auth.py`:

```python
#!/usr/bin/env python3
"""测试认证功能"""

from api_server.auth import APIAuth

# 测试生成 API Key
api_key, api_secret = APIAuth.generate_api_key(is_test=True)
print(f"API Key: {api_key}")
print(f"API Secret: {api_secret}")

# 测试验证 API Key
print(f"Valid Key: {APIAuth.verify_api_key(api_key)}")

# 测试签名验证
import time
timestamp = str(int(time.time()))
body = '{"test": "data"}'
signature = APIAuth.verify_signature(api_key, "", timestamp, body)
print(f"Signature valid: {signature}")
```

运行测试:

```bash
python test_auth.py
```

#### 步骤 5: 提交代码

```bash
git add api_server/auth.py api_server/middleware/api_key_auth.py api_server/middleware/__init__.py
git commit -m "feat: implement API key authentication middleware

- Add APIAuth class for key and signature verification
- Add APIKeyAuthMiddleware for request authentication
- Support timestamp validation and signature checking
- Skip authentication for health check and docs paths"
```

---

### 任务 1.3: 实现限流中间件

**Files:**
- Create: `api_server/middleware/rate_limit.py`
- Modify: `api_server/middleware/__init__.py`

#### 步骤 1: 创建限流中间件

创建 `api_server/middleware/rate_limit.py`:

```python
#!/usr/bin/env python3
"""
限流中间件
基于 slowapi 实现请求限流
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config import settings


# 创建限流器
limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware:
    """限流中间件包装类"""

    @staticmethod
    def get_limiter():
        """获取限流器实例"""
        return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    限流异常处理器

    Args:
        request: HTTP 请求
        exc: 限流异常
    """
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "code": 429,
            "message": "Too many requests",
            "details": f"Rate limit exceeded. Retry after {exc.limit.limit} seconds.",
            "retry_after": exc.limit.limit,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers={"Retry-After": str(exc.limit.limit)}
    )
```

#### 步骤 2: 更新 middleware __init__.py

编辑 `api_server/middleware/__init__.py`:

```python
"""Middleware 模块"""
from .api_key_auth import APIKeyAuthMiddleware
from .rate_limit import limiter, rate_limit_exceeded_handler

__all__ = [
    "APIKeyAuthMiddleware",
    "limiter",
    "rate_limit_exceeded_handler"
]
```

#### 步骤 3: 更新主应用注册限流异常处理器

编辑 `api_server/main.py`，在 `register_exception_handlers` 中添加:

```python
from slowapi.errors import RateLimitExceeded
from .middleware import rate_limit_exceeded_handler

# 在 register_exception_handlers 函数中添加
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

#### 步骤 4: 提交代码

```bash
git add api_server/middleware/rate_limit.py api_server/middleware/__init__.py
git commit -m "feat: implement rate limiting middleware

- Add SlowAPI-based rate limiting
- Configure rate limits for different user tiers
- Add custom rate limit exceeded handler
- Return proper 429 response with retry-after header"
```

---

### 任务 1.4: 实现请求日志中间件

**Files:**
- Create: `api_server/middleware/request_logger.py`
- Modify: `api_server/middleware/__init__.py`
- Modify: `api_server/main.py`

#### 步骤 1: 创建请求日志中间件

创建 `api_server/middleware/request_logger.py`:

```python
#!/usr/bin/env python3
"""
请求日志中间件
记录所有 API 请求和响应
"""

import time
import json
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """
        记录请求和响应

        Args:
            request: HTTP 请求
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP 响应
        """
        # 记录请求
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        # 读取请求体（仅用于日志，不影响后续处理）
        body = ""
        try:
            body_bytes = await request.body()
            body = body_bytes.decode('utf-8') if body_bytes else ""

            # 重新设置请求体
            async def receive():
                return {'type': 'http.request', 'body': body_bytes, 'more_body': False}

            request._receive = receive
        except Exception:
            pass

        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_host} "
            f"headers={dict(request.headers)} "
            f"body={body[:500]}"  # 限制日志长度
        )

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"from {client_host} "
                f"elapsed={elapsed_time:.3f}s "
                f"error={str(e)}"
            )
            raise

        # 记录响应
        elapsed_time = time.time() - start_time

        # 对于 StreamingResponse，无法直接读取响应体
        if isinstance(response, StreamingResponse):
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"from {client_host} "
                f"status={response.status_code} "
                f"elapsed={elapsed_time:.3f}s"
            )
        else:
            # 读取响应体
            resp_body = b""
            async for chunk in response.body_iterator:
                resp_body += chunk

            # 重新设置响应体
            response.body_iterator = iterate_in_threadpool(iter([resp_body]))

            try:
                resp_text = resp_body.decode('utf-8')
                logger.info(
                    f"Response: {request.method} {request.url.path} "
                    f"from {client_host} "
                    f"status={response.status_code} "
                    f"elapsed={elapsed_time:.3f}s "
                    f"body={resp_text[:500]}"
                )
            except Exception:
                logger.info(
                    f"Response: {request.method} {request.url.path} "
                    f"from {client_host} "
                    f"status={response.status_code} "
                    f"elapsed={elapsed_time:.3f}s"
                )

        return response
```

#### 步骤 2: 更新 middleware __init__.py

编辑 `api_server/middleware/__init__.py`:

```python
"""Middleware 模块"""
from .api_key_auth import APIKeyAuthMiddleware
from .rate_limit import limiter, rate_limit_exceeded_handler
from .request_logger import RequestLoggerMiddleware

__all__ = [
    "APIKeyAuthMiddleware",
    "limiter",
    "rate_limit_exceeded_handler",
    "RequestLoggerMiddleware"
]
```

#### 步骤 3: 提交代码

```bash
git add api_server/middleware/request_logger.py api_server/middleware/__init__.py
git commit -m "feat: implement request logging middleware

- Add comprehensive request/response logging
- Log request method, path, client, headers, and body
- Log response status, elapsed time, and body
- Handle StreamingResponse properly
- Include error logging with stack traces"
```

---

### 任务 1.5: 实现异常处理

**Files:**
- Create: `api_server/exception_handlers/custom_exceptions.py`
- Create: `api_server/exception_handlers/__init__.py`

#### 步骤 1: 创建自定义异常

创建 `api_server/exception_handlers/custom_exceptions.py`:

```python
#!/usr/bin/env python3
"""
自定义异常和异常处理器
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from common.exceptions import StockTraderException

from ..models.common import ErrorResponse
from ..config import settings

import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """注册所有异常处理器"""

    # Pydantic 验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Validation error",
                details=str(exc.errors())
            ).model_dump()
        )

    # Pydantic 模型验证错误
    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
        logger.error(f"Pydantic validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Data validation error",
                details=str(exc.errors())
            ).model_dump()
        )

    # SQLAlchemy 错误
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Database error",
                details="Internal database error occurred"
            ).model_dump()
        )

    # 通用异常（生产环境不泄露详细信息）
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        error_msg = str(exc)
        logger.error(f"Unhandled exception: {error_msg}", exc_info=True)

        # 生产环境隐藏详细错误
        details = error_msg if settings.DEBUG else "Internal server error"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Internal server error",
                details=details
            ).model_dump()
        )


class APIException(Exception):
    """API 自定义异常基类"""

    def __init__(self, message: str, code: int = 400, details: Optional[str] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundException(APIException):
    """未找到异常"""

    def __init__(self, message: str = "Resource not found", details: Optional[str] = None):
        super().__init__(message, 404, details)


class BadRequestException(APIException):
    """请求错误异常"""

    def __init__(self, message: str = "Bad request", details: Optional[str] = None):
        super().__init__(message, 400, details)


class UnauthorizedException(APIException):
    """未授权异常"""

    def __init__(self, message: str = "Unauthorized", details: Optional[str] = None):
        super().__init__(message, 401, details)


class ForbiddenException(APIException):
    """禁止访问异常"""

    def __init__(self, message: str = "Forbidden", details: Optional[str] = None):
        super().__init__(message, 403, details)
```

#### 步骤 2: 更新 exception_handlers __init__.py

编辑 `api_server/exception_handlers/__init__.py`:

```python
"""Exception Handlers 模块"""
from .custom_exceptions import register_exception_handlers, APIException, NotFoundException, BadRequestException, UnauthorizedException, ForbiddenException

__all__ = [
    "register_exception_handlers",
    "APIException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException"
]
```

#### 步骤 3: 提交代码

```bash
git add api_server/exception_handlers/custom_exceptions.py api_server/exception_handlers/__init__.py
git commit -m "feat: implement comprehensive exception handling

- Add custom exception classes for API errors
- Register handlers for validation errors
- Register handlers for database errors
- Add generic exception handler with debug/prod mode
- Return standardized error responses"
```

---

### 任务 1.6: 配置 Docker 和部署

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `gunicorn.conf.py`
- Create: `.dockerignore`

#### 步骤 1: 创建 Dockerfile

创建 `Dockerfile`:

```dockerfile
# ==================== 阶段 1: 构建依赖 ====================
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

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
```

#### 步骤 2: 创建 docker-compose.yml

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: alpha-quant-api
    ports:
      - "8000:8000"
    environment:
      - DEBUG=${DEBUG:-False}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - API_KEY_SECRET=${API_KEY_SECRET}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
      - ./api_server:/app/api_server
    restart: unless-stopped
    networks:
      - alpha-quant-network

  db:
    image: postgres:15-alpine
    container_name: alpha-quant-db
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-stock_market}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - alpha-quant-network

  redis:
    image: redis:7-alpine
    container_name: alpha-quant-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - alpha-quant-network

volumes:
  db_data:
  redis_data:

networks:
  alpha-quant-network:
    driver: bridge
```

#### 步骤 3: 创建 Gunicorn 配置

创建 `gunicorn.conf.py`:

```python
#!/usr/bin/env python3
"""
Gunicorn 配置文件
用于生产环境部署
"""

import multiprocessing
import os


# ==================== 基础配置 ====================
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
threads = 2

# ==================== 超时配置 ====================
timeout = 120
keepalive = 5
graceful_timeout = 30

# ==================== 安全配置 ====================
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 8190

# ==================== 日志配置 ====================
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ==================== 进程管理 ====================
daemon = False
pidfile = "/app/logs/gunicorn.pid"
umask = 0o027

# ==================== 性能优化 ====================
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# ==================== SSL 配置（可选）====================
# keyfile = "/app/certs/key.pem"
# certfile = "/app/certs/cert.pem"
```

#### 步骤 4: 创建 .dockerignore

创建 `.dockerignore`:

```gitignore
# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Test
test_*.py
tests/
.pytest_cache/
.coverage
htmlcov/

# Logs
logs/*.log
logs/*.json

# Environment
.env

# Documentation
docs/
README.md

# Other
.DS_Store
```

#### 步骤 5: 创建部署脚本

创建 `scripts/deploy.sh`:

```bash
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
```

#### 步骤 6: 提交代码

```bash
git add Dockerfile docker-compose.yml gunicorn.conf.py .dockerignore scripts/deploy.sh
git commit -m "feat: add Docker deployment configuration

- Add multi-stage Dockerfile for optimized image size
- Add docker-compose.yml for local development
- Add Gunicorn configuration for production
- Add .dockerignore to reduce image size
- Add deployment script with health checks
- Configure PostgreSQL and Redis services"
```

---

### 任务 1.7: 测试基础框架

**Files:**
- Create: `tests/test_api/test_basic.py`
- Create: `tests/test_api/__init__.py`

#### 步骤 1: 创建基础测试

创建 `tests/test_api/test_basic.py`:

```python
#!/usr/bin/env python3
"""基础 API 测试"""

import pytest
from fastapi.testclient import TestClient
from api_server.main import app


client = TestClient(app)


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Alpha Quant Trader Pro API"
    assert "docs" in data
    assert "redoc" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_docs_endpoint():
    """测试 Swagger 文档"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """测试 ReDoc 文档"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_json():
    """测试 OpenAPI JSON"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"]
    assert data["info"]["title"] == "Alpha Quant Trader Pro API"
```

#### 步骤 2: 运行测试

```bash
pytest tests/test_api/test_basic.py -v
```

#### 步骤 3: 启动本地服务测试

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 启动服务
python api_server/main.py
```

访问:
- http://localhost:8000 - 根路径
- http://localhost:8000/health - 健康检查
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

#### 步骤 4: 提交代码

```bash
git add tests/test_api/test_basic.py tests/test_api/__init__.py
git commit -m "test: add basic API framework tests

- Test root endpoint
- Test health check endpoint
- Test documentation endpoints
- Test OpenAPI schema generation"
```

---

## 阶段 1 完成总结

已完成:
- ✅ 项目结构创建
- ✅ FastAPI 应用初始化
- ✅ 认证中间件
- ✅ 限流中间件
- ✅ 请求日志中间件
- ✅ 异常处理
- ✅ Docker 部署配置
- ✅ 基础测试

接下来: 阶段 2 - 数据源 API 实现

---

## 阶段 2: 数据源 API 实现 (2-3天)

### 任务 2.1: 创建数据源模型

**Files:**
- Create: `api_server/models/data_source.py`
- Create: `api_server/schemas/data_source.py`

(详细步骤省略 - 包含股票、K线、财务数据等Pydantic模型)

### 任务 2.2: 实现行情数据API

**Files:**
- Create: `api_server/routers/data_source.py`
- Create: `tests/test_api/test_data_source.py`

(实现单股行情、批量行情、指数行情、板块行情等API端点)

### 任务 2.3: 实现K线数据API

**Files:**
- Modify: `api_server/routers/data_source.py`
- Modify: `tests/test_api/test_data_source.py`

(实现K线查询、批量K线、K线统计等端点)

### 任务 2.4: 实现财务数据API

**Files:**
- Modify: `api_server/routers/data_source.py`
- Modify: `tests/test_api/test_data_source.py`

(实现三张表、财务指标、业绩预告等端点)

---

## 阶段 3: 股票市场 API 实现 (1-2天)

### 任务 3.1: 创建股票市场模型

**Files:**
- Create: `api_server/models/stock_market.py`
- Create: `api_server/schemas/stock_market.py`

### 任务 3.2: 实现股票同步API

**Files:**
- Create: `api_server/routers/stock_market.py`
- Create: `tests/test_api/test_stock_market.py`

(实现股票列表、同步状态、K线同步等端点)

---

## 阶段 4: 持仓管理 API 实现 (2-3天)

### 任务 4.1: 创建持仓模型

**Files:**
- Create: `api_server/models/portfolio.py`
- Create: `api_server/schemas/portfolio.py`

### 任务 4.2: 实现账户管理API

**Files:**
- Create: `api_server/routers/portfolio.py`
- Create: `tests/test_api/test_portfolio.py`

(实现账户汇总、充值提现、持仓查询、交易记录等端点)

---

## 阶段 5: 技术分析 API 实现 (3-4天)

### 任务 5.1: 创建技术分析模型

**Files:**
- Create: `api_server/models/analysis.py`
- Create: `api_server/schemas/analysis.py`

### 任务 5.2: 实现基础指标API

**Files:**
- Create: `api_server/routers/analysis.py`
- Create: `tests/test_api/test_analysis.py`

(实现MA、MACD、RSI、布林带等50+个技术指标端点)

### 任务 5.3: 实现策略引擎API

**Files:**
- Modify: `api_server/routers/analysis.py`
- Modify: `tests/test_api/test_analysis.py`

(实现五维共振、VCP、TD九转、背离策略等端点)

---

## 阶段 6: 风险控制模块 (2-3天)

### 任务 6.1: 创建风险控制引擎

**Files:**
- Create: `core/risk_control/__init__.py`
- Create: `core/risk_control/risk_calculator.py`
- Create: `core/risk_control/stop_loss_engine.py`
- Create: `core/risk_control/volatility_analyzer.py`
- Create: `core/risk_control/var_calculator.py`
- Create: `core/risk_control/position_controller.py`

### 任务 6.2: 创建风险控制模型

**Files:**
- Create: `api_server/models/risk_control.py`
- Create: `api_server/schemas/risk_control.py`

### 任务 6.3: 实现风险控制API

**Files:**
- Create: `api_server/routers/risk_control.py`
- Create: `tests/test_api/test_risk_control.py`

(实现VaR计算、波动率分析、止损位计算、仓位检查等端点)

---

## 阶段 7: 收益统计模块 (2-3天)

### 任务 7.1: 创建收益统计引擎

**Files:**
- Create: `core/performance/__init__.py`
- Create: `core/performance/performance_calculator.py`
- Create: `core/performance/metrics.py`
- Create: `core/performance/benchmark_comparator.py`

### 任务 7.2: 创建收益统计模型

**Files:**
- Create: `api_server/models/performance.py`
- Create: `api_server/schemas/performance.py`

### 任务 7.3: 实现收益统计API

**Files:**
- Create: `api_server/routers/performance.py`
- Create: `tests/test_api/test_performance.py`

(实现账户收益、个股收益、时段收益、胜率统计、基准对比等端点)

---

## 阶段 8: 风险提示模块 (2-3天)

### 任务 8.1: 创建风险提示引擎

**Files:**
- Create: `core/alerts/__init__.py`
- Create: `core/alerts/price_alerts.py`
- Create: `core/alerts/technical_alerts.py`
- Create: `core/alerts/risk_alerts.py`
- Create: `core/alerts/alert_manager.py`

### 任务 8.2: 创建风险提示模型

**Files:**
- Create: `api_server/models/alerts.py`
- Create: `api_server/schemas/alerts.py`

### 任务 8.3: 实现风险提示API

**Files:**
- Create: `api_server/routers/alerts.py`
- Create: `tests/test_api/test_alerts.py`

(实现价格预警、技术预警、风险预警、批量检查等端点)

---

## 阶段 9: 文档和集成测试 (2-3天)

### 任务 9.1: 完善API文档

**Files:**
- Create: `docs/api/API_OVERVIEW.md`
- Create: `docs/api/AUTHENTICATION.md`
- Create: `docs/api/DATA_SOURCE_API.md`
- Create: `docs/api/PORTFOLIO_API.md`
- Create: `docs/api/ANALYSIS_API.md`
- Create: `docs/api/RISK_CONTROL_API.md`
- Create: `docs/api/PERFORMANCE_API.md`

### 任务 9.2: 编写集成测试

**Files:**
- Create: `tests/test_integration/test_full_workflow.py`
- Create: `tests/test_integration/test_performance.py`
- Create: `tests/test_integration/test_security.py`

### 任务 9.3: 性能测试

**Files:**
- Create: `scripts/performance_test.py`

---

## 阶段 10: 部署上线 (1-2天)

### 任务 10.1: 配置生产环境

**Files:**
- Create: `scripts/generate_api_key.py`
- Modify: `docker-compose.yml` (生产环境配置)
- Create: `nginx/nginx.conf` (反向代理)

### 任务 10.2: 部署到服务器

**Steps:**
- 配置服务器环境
- 部署Docker容器
- 配置监控和日志
- 运行健康检查

### 任务 10.3: 生成SDK示例

**Files:**
- Create: `examples/python_sdk_example.py`
- Create: `examples/curl_examples.sh`

---

## 实施要点

### 1. 依赖注入
- 使用 `common/di_container.py` 中的 DI 容器
- 在每个路由中注入所需的服务

### 2. 数据验证
- 所有输入使用 Pydantic 模型验证
- 所有输出使用 Pydantic 模型序列化

### 3. 错误处理
- 使用自定义异常类
- 返回统一的错误响应格式

### 4. 测试驱动开发
- 先写测试，再写实现
- 每个端点至少有3个测试用例
- 目标覆盖率: 80%+

### 5. 文档注释
- 所有函数添加 docstring
- 所有模型字段添加 description
- API 端点添加 summary 和 description

---

## 文件统计

**新增文件:** ~60个
**修改文件:** ~20个
**总代码行数:** ~8000-10000行

---

**实施计划完成!** 

准备好开始实施了吗?

