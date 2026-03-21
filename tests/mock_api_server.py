"""
Mock API Server for external dependencies
模拟外部 API 服务，用于测试

支持的 Mock 端点:
- /tushare/stock/basic - Tushare 基础数据
- /tushare/stock/kline - Tushare K线数据
- /investoday/stock/quote - Investoday 行情
- /investoday/stock/kline - Investoday K线
- /health - 健康检查
"""
from flask import Flask, jsonify, request
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock 数据
MOCK_STOCK_DATA = {
    "600519": {
        "ts_code": "600519.SH",
        "name": "贵州茅台",
        "price": 1850.0,
        "open": 1840.0,
        "high": 1860.0,
        "low": 1835.0,
        "close": 1850.0,
        "volume": 10000,
        "amount": 185000000,
        "change_pct": 1.5,
        "turnover_rate": 0.5
    },
    "000001": {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "price": 15.5,
        "open": 15.3,
        "high": 15.7,
        "low": 15.2,
        "close": 15.5,
        "volume": 500000,
        "amount": 7750000,
        "change_pct": 1.2,
        "turnover_rate": 0.3
    }
}

MOCK_KLINE_DATA = {
    "600519": [
        {
            "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y%m%d"),
            "open": 1840.0 + i * 0.5,
            "high": 1860.0 + i * 0.5,
            "low": 1835.0 + i * 0.5,
            "close": 1850.0 + i * 0.5,
            "volume": 10000 + i * 100,
            "amount": 185000000 + i * 1000000
        }
        for i in range(30)
    ]
}


@app.route('/tushare/stock/basic', methods=['GET'])
def mock_tushare_basic():
    """Mock Tushare 基础数据接口"""
    ts_code = request.args.get('ts_code')
    logger.info(f"Mock Tushare request: ts_code={ts_code}")

    # 提取股票代码（去掉后缀）
    stock_code = ts_code.split('.')[0] if ts_code else "600519"

    if stock_code in MOCK_STOCK_DATA:
        return jsonify({
            "code": 0,
            "msg": "success",
            "data": MOCK_STOCK_DATA[stock_code]
        })
    return jsonify({"code": -1, "msg": "stock not found"}), 404


@app.route('/tushare/stock/kline', methods=['GET'])
def mock_tushare_kline():
    """Mock Tushare K线数据接口"""
    ts_code = request.args.get('ts_code')
    logger.info(f"Mock Tushare kline request: ts_code={ts_code}")

    stock_code = ts_code.split('.')[0] if ts_code else "600519"

    if stock_code in MOCK_KLINE_DATA:
        return jsonify({
            "code": 0,
            "msg": "success",
            "data": MOCK_KLINE_DATA[stock_code]
        })
    return jsonify({"code": -1, "msg": "kline data not found"}), 404


@app.route('/investoday/stock/quote', methods=['GET'])
def mock_investoday_quote():
    """Mock Investoday 行情接口"""
    symbol = request.args.get('symbol')
    logger.info(f"Mock Investoday quote request: symbol={symbol}")

    stock_code = symbol if symbol else "600519"

    if stock_code in MOCK_STOCK_DATA:
        return jsonify({
            "status": "success",
            "code": 200,
            "data": MOCK_STOCK_DATA[stock_code]
        })
    return jsonify({"status": "error", "code": 404, "message": "stock not found"}), 404


@app.route('/investoday/stock/kline', methods=['GET'])
def mock_investoday_kline():
    """Mock Investoday K线接口"""
    symbol = request.args.get('symbol')
    logger.info(f"Mock Investoday kline request: symbol={symbol}")

    stock_code = symbol if symbol else "600519"

    if stock_code in MOCK_KLINE_DATA:
        return jsonify({
            "status": "success",
            "code": 200,
            "data": MOCK_KLINE_DATA[stock_code]
        })
    return jsonify({"status": "error", "code": 404, "message": "kline data not found"}), 404


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "mock-api-server",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/stats', methods=['GET'])
def stats():
    """统计信息"""
    return jsonify({
        "total_requests": 0,  # TODO: 实现请求计数
        "mocked_stocks": list(MOCK_STOCK_DATA.keys()),
        "available_endpoints": [
            "/tushare/stock/basic",
            "/tushare/stock/kline",
            "/investoday/stock/quote",
            "/investoday/stock/kline"
        ]
    })


if __name__ == '__main__':
    logger.info("Mock API Server starting on port 9000...")
    app.run(host='0.0.0.0', port=9000, debug=True)
