"""Stock Market Router v1 - 兼容旧版本测试"""
from fastapi import APIRouter

stock_market_router = APIRouter(tags=["Stock Market v1"])

@stock_market_router.get("/v1/market/test")
async def test_v1():
    return {"version": "v1", "status": "placeholder"}
