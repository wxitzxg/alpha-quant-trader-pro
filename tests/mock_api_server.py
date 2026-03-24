#!/usr/bin/env python3
"""Mock API Server - 用于模拟外部 API 服务

提供统一的 Mock 接口，模拟 Tushare、Investoday 等外部数据源
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Mock API Server", version="1.0.0")


class MockResponse(BaseModel):
    """统一的 Mock 响应格式"""
    code: int = 200
    msg: str = "success"
    data: Any = None


# ==================== 模拟股票数据 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "mock-api",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stock/{symbol}/quote")
async def get_stock_quote(symbol: str):
    """获取股票实时行情（模拟）"""
    # 模拟一些热门股票的价格
    stock_data = {
        "600519": {
            "symbol": "600519",
            "name": "贵州茅台",
            "price": 1850.0,
            "change": 5.2,
            "change_percent": 0.28,
            "volume": 123456,
            "amount": 2283936000,
            "time": datetime.now().isoformat()
        },
        "000001": {
            "symbol": "000001",
            "name": "平安银行",
            "price": 10.5,
            "change": -0.2,
            "change_percent": -1.87,
            "volume": 45678900,
            "amount": 479628450,
            "time": datetime.now().isoformat()
        },
        "601318": {
            "symbol": "601318",
            "name": "中国平安",
            "price": 45.8,
            "change": 1.2,
            "change_percent": 2.69,
            "volume": 78912300,
            "amount": 3614183340,
            "time": datetime.now().isoformat()
        }
    }

    if symbol not in stock_data:
        return MockResponse(
            code=404,
            msg=f"股票 {symbol} 不存在",
            data=None
        )

    return MockResponse(data=stock_data[symbol])


@app.get("/api/stock/{symbol}/history")
async def get_stock_history(symbol: str, days: int = 30):
    """获取股票历史 K 线数据（模拟）"""
    # 生成模拟的 K 线数据
    history = []
    base_price = 1850.0 if symbol == "600519" else 100.0
    current_price = base_price

    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).date().isoformat()
        open_price = current_price * (0.99 + 0.02 * (i % 3))
        close_price = current_price * (0.98 + 0.04 * (i % 5))
        high_price = max(open_price, close_price) * 1.02
        low_price = min(open_price, close_price) * 0.98
        volume = 1000000 + (i * 10000)

        history.append({
            "date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })

        # 更新价格用于下一天
        current_price = close_price

    return MockResponse(data={
        "symbol": symbol,
        "name": "贵州茅台" if symbol == "600519" else "模拟股票",
        "history": history
    })


@app.get("/api/stock/{symbol}/indicator/macd")
async def get_macd_indicator(symbol: str, days: int = 30):
    """获取 MACD 指标数据（模拟）"""
    # 生成模拟的 MACD 数据
    macd_data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).date().isoformat()
        macd_data.append({
            "date": date,
            "dif": round(0.5 + 0.1 * i, 2),
            "dea": round(0.4 + 0.08 * i, 2),
            "macd": round(0.02 + 0.01 * i, 2)
        })

    return MockResponse(data={
        "symbol": symbol,
        "indicator": "MACD",
        "data": macd_data
    })


# ==================== 模拟新闻数据 ====================

@app.get("/api/news/list")
async def get_news_list(category: str = "stock", page: int = 1, page_size: int = 10):
    """获取新闻列表（模拟）"""
    news_list = [
        {
            "id": f"news_{i}",
            "title": f"【模拟】市场快讯 {i}",
            "summary": f"这是第 {i} 条模拟新闻摘要",
            "url": f"https://example.com/news/{i}",
            "source": "模拟财经",
            "publish_time": (datetime.now() - timedelta(hours=i)).isoformat(),
            "category": category
        }
        for i in range((page - 1) * page_size, page * page_size)
    ]

    return MockResponse(data={
        "list": news_list,
        "total": 100,
        "page": page,
        "page_size": page_size
    })


@app.get("/api/news/{news_id}")
async def get_news_detail(news_id: str):
    """获取新闻详情（模拟）"""
    return MockResponse(data={
        "id": news_id,
        "title": f"【模拟】{news_id} 详细新闻",
        "content": "这是模拟的新闻正文内容...",
        "publish_time": datetime.now().isoformat(),
        "source": "模拟财经"
    })


# ==================== 模拟财务数据 ====================

@app.get("/api/stock/{symbol}/financial")
async def get_financial_data(symbol: str, year: int = 2023):
    """获取财务数据（模拟）"""
    return MockResponse(data={
        "symbol": symbol,
        "year": year,
        "revenue": 1000000000,
        "profit": 200000000,
        "assets": 5000000000,
        "liabilities": 2000000000,
        "equity": 3000000000
    })


# ==================== 模拟资金流向 ====================

@app.get("/api/stock/{symbol}/fundflow")
async def get_fund_flow(symbol: str, days: int = 5):
    """获取资金流向数据（模拟）"""
    fundflow = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).date().isoformat()
        fundflow.append({
            "date": date,
            "inflow": 10000000 + (i * 1000000),
            "outflow": 8000000 + (i * 800000),
            "net": 2000000 + (i * 200000)
        })

    return MockResponse(data={
        "symbol": symbol,
        "fundflow": fundflow
    })


# ==================== 错误处理 ====================

@app.get("/api/error/{error_type}")
async def simulate_error(error_type: str):
    """模拟各种错误情况"""
    error_responses = {
        "404": {"code": 404, "msg": "Not Found", "data": None},
        "400": {"code": 400, "msg": "Bad Request", "data": None},
        "500": {"code": 500, "msg": "Internal Server Error", "data": None},
        "timeout": {"code": 504, "msg": "Gateway Timeout", "data": None},
        "rate_limit": {"code": 429, "msg": "Too Many Requests", "data": None}
    }

    if error_type not in error_responses:
        raise HTTPException(status_code=400, detail="Invalid error type")

    return JSONResponse(
        status_code=error_responses[error_type]["code"],
        content=error_responses[error_type]
    )


# ==================== 通用 Mock 接口 ====================

@app.post("/api/mock/{endpoint}")
async def generic_mock(endpoint: str, request: Dict[str, Any]):
    """通用 Mock 接口 - 返回请求参数"""
    return MockResponse(data={
        "endpoint": endpoint,
        "received": request,
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
