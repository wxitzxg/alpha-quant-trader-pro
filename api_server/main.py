#!/usr/bin/env python3
"""
API Server 主入口
FastAPI 应用初始化和路由注册
"""

import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .exception_handlers.custom_exceptions import register_exception_handlers
from .middleware.request_logger import RequestLoggerMiddleware

# 导入路由
from .routers import (
    health_router,
    data_source_router,
    stock_market_router,
    portfolio_router,
    analysis_router,
    risk_control_router,
    performance_router,
    alerts_router,
    backtest_router,
    simulation_router,
    base_indicators_router,
    divergence_router,
    td_sequential_router,
    vcp_router,
    zigzag_router,
    fundflow_router,
    news_router,
    financial_router,
    market_sentiment_router
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

    # ✅ 初始化数据库管理器并同步表
    from common.database import DatabaseManager
    from common.config import get_config

    # ✅ 导入所有模型模块，确保它们注册到 Base.metadata
    import stock_market.models  # Stock, KLine, SyncRecord
    import portfolio_manager.database  # Position, Transaction, CashBalance
    import simulate_trading.models  # StrategyAccount, StrategyTrade, DailyReport

    config = get_config()
    db_url = config.get_database_url()

    db_manager = DatabaseManager(db_url)

    # ✅ 自动创建所有表 (如果不存在)
    logger.info("正在同步数据库表...")
    db_manager.create_all()
    logger.info("数据库表同步完成")

    # 存储到 app.state 供其他地方使用
    app.state.db_manager = db_manager

    yield

    # 关闭时
    logger.info("API Server 正在关闭...")
    db_manager.dispose()


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
app.include_router(backtest_router, prefix="/api/v1", tags=["回测系统"])
app.include_router(simulation_router, prefix="/api/v1", tags=["模拟交易"])

# 新增路由：技术指标
app.include_router(base_indicators_router, prefix="/api/v1", tags=["基础指标"])
app.include_router(divergence_router, prefix="/api/v1", tags=["背离检测"])
app.include_router(td_sequential_router, prefix="/api/v1", tags=["TD序列"])
app.include_router(vcp_router, prefix="/api/v1", tags=["VCP形态"])
app.include_router(zigzag_router, prefix="/api/v1", tags=["ZigZag"])

# 新增路由：其他数据服务
app.include_router(fundflow_router, prefix="/api/v1", tags=["资金流向"])
app.include_router(news_router, prefix="/api/v1", tags=["新闻资讯"])
app.include_router(financial_router, prefix="/api/v1", tags=["财务数据"])
app.include_router(market_sentiment_router, prefix="/api/v1", tags=["市场情绪"])


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
