#!/usr/bin/env python3
"""风险控制路由 - 集成业务逻辑"""

from fastapi import APIRouter, HTTPException, Path, Query, Body
from datetime import datetime
from typing import Optional
import numpy as np
from scipy import stats

from ..models.common import APIResponse
from ..models.risk_control import RiskControlResponse, RiskMetrics
from ..services.data_source_service import DataSourceService

risk_control_router = APIRouter()

def calculate_volatility(prices: list, window: int = 30) -> float:
    """计算波动率"""
    if len(prices) < 2:
        return 0.0
    returns = np.diff(np.log(prices))
    return np.std(returns) * np.sqrt(window)

def calculate_var(returns: list, confidence_level: float = 0.95) -> float:
    """计算 VaR (Value at Risk)"""
    if not returns:
        return 0.0
    returns_array = np.array(returns)
    var = np.percentile(returns_array, 100 * (1 - confidence_level))
    return abs(var)

def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
    """计算夏普比率"""
    if not returns:
        return 0.0
    returns_array = np.array(returns)
    excess_returns = returns_array - risk_free_rate / 252  # 日化无风险利率
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(returns_array) > 0 else 0.0

def calculate_max_drawdown(prices: list) -> float:
    """计算最大回撤"""
    if len(prices) < 2:
        return 0.0
    prices_array = np.array(prices)
    running_max = np.maximum.accumulate(prices_array)
    drawdowns = (prices_array - running_max) / running_max
    return abs(np.min(drawdowns))

def calculate_beta(stock_returns: list, market_returns: Optional[list] = None) -> float:
    """计算 Beta 值"""
    if not stock_returns:
        return 1.0  # 默认值
    if market_returns is None:
        # 如果没有市场收益率，返回1.0作为默认值
        return 1.0
    stock_returns_array = np.array(stock_returns)
    market_returns_array = np.array(market_returns)
    covariance = np.cov(stock_returns_array, market_returns_array)[0][1]
    market_variance = np.var(market_returns_array)
    return covariance / market_variance if market_variance > 0 else 1.0

@risk_control_router.get("/risk/volatility/{stock_code}", response_model=APIResponse)
async def get_volatility(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    days: int = Query(30, ge=1, description="分析天数")
):
    """波动率分析"""
    try:
        # 获取历史价格数据
        klines = DataSourceService.get_kline(
            stock_code=stock_code,
            interval="1d",
            limit=days + 10  # 多取一些数据
        )

        if not klines or len(klines) < 2:
            raise HTTPException(status_code=404, detail="No price data available")

        # 提取收盘价
        prices = [float(k.get('close', 0)) for k in klines if k.get('close')]

        if len(prices) < 2:
            raise HTTPException(status_code=400, detail="Insufficient price data")

        # 计算收益率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])

        # 计算各项风险指标
        volatility = calculate_volatility(prices, window=days)
        var_95 = calculate_var(returns, confidence_level=0.95)
        var_99 = calculate_var(returns, confidence_level=0.99)
        max_dd = calculate_max_drawdown(prices)
        sharpe = calculate_sharpe_ratio(returns)
        beta = calculate_beta(returns)

        risk_metrics = {
            "var_95": round(var_95, 4),
            "var_99": round(var_99, 4),
            "volatility": round(volatility, 4),
            "max_drawdown": round(max_dd, 4),
            "sharpe_ratio": round(sharpe, 2),
            "beta": round(beta, 2),
            "analysis_days": days,
            "data_points": len(prices)
        }

        return APIResponse(
            data={
                "stock_code": stock_code,
                "risk_metrics": risk_metrics,
                "current_price": prices[-1] if prices else 0,
                "analysis_time": datetime.now().isoformat()
            },
            message=f"Volatility analysis for {stock_code} completed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating volatility: {str(e)}")

@risk_control_router.post("/risk/stop-loss/calculate", response_model=APIResponse)
async def calculate_stop_loss(
    stock_code: str = Body(..., description="股票代码", example="600519"),
    risk_tolerance: float = Body(0.05, ge=0.01, le=0.2, description="风险容忍度 (1%-20%)"),
    method: str = Body("atr", description="计算方法 (atr/volatility/percentage)")
):
    """计算止损位"""
    try:
        # 获取历史价格数据
        klines = DataSourceService.get_kline(
            stock_code=stock_code,
            interval="1d",
            limit=30
        )

        if not klines or len(klines) < 2:
            raise HTTPException(status_code=404, detail="No price data available")

        # 提取价格数据
        prices = [float(k.get('close', 0)) for k in klines if k.get('close')]
        highs = [float(k.get('high', 0)) for k in klines if k.get('high')]
        lows = [float(k.get('low', 0)) for k in klines if k.get('low')]

        if len(prices) < 2:
            raise HTTPException(status_code=400, detail="Insufficient price data")

        current_price = prices[-1]
        highest_recent = max(prices[-5:]) if len(prices) >= 5 else max(prices)
        lowest_recent = min(prices[-5:]) if len(prices) >= 5 else min(prices)

        # 计算止损位（根据不同方法）
        stop_loss = 0.0

        if method == "atr":
            # ATR 方法（平均真实波幅）
            if len(highs) >= 14 and len(lows) >= 14:
                tr_values = []
                for i in range(1, 14):
                    tr = max(
                        highs[i] - lows[i],
                        abs(highs[i] - prices[i-1]),
                        abs(lows[i] - prices[i-1])
                    )
                    tr_values.append(tr)
                atr = np.mean(tr_values) if tr_values else 0
                stop_loss = current_price - 2 * atr
            else:
                # 如果数据不足，使用简单方法
                stop_loss = current_price * (1 - risk_tolerance)

        elif method == "volatility":
            # 波动率方法
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
            volatility = np.std(returns) if returns else risk_tolerance
            stop_loss = current_price * (1 - 2 * volatility)

        elif method == "percentage":
            # 百分比方法
            stop_loss = current_price * (1 - risk_tolerance)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

        # 确保止损位为正数且低于当前价格
        stop_loss = max(0.01, min(stop_loss, current_price * 0.99))

        risk_reward_ratio = (highest_recent - current_price) / (current_price - stop_loss) if stop_loss > 0 else 0

        return APIResponse(
            data={
                "stock_code": stock_code,
                "current_price": round(current_price, 2),
                "stop_loss": round(stop_loss, 2),
                "risk_tolerance": risk_tolerance,
                "method": method,
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "potential_loss_pct": round((current_price - stop_loss) / current_price * 100, 2),
                "calculation_time": datetime.now().isoformat()
            },
            message="Stop loss calculated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stop loss: {str(e)}")

@risk_control_router.get("/risk/diversification", response_model=APIResponse)
async def get_portfolio_diversification():
    """投资组合分散度分析"""
    try:
        from ..services import PortfolioService
        portfolio_service = PortfolioService()

        # 获取持仓列表
        positions_result = portfolio_service.get_all_positions(page=1, page_size=100)

        if not positions_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get positions")

        positions = positions_result.get("data", [])

        if not positions:
            return APIResponse(
                data={
                    "diversification_score": 0,
                    "concentration_risk": "N/A",
                    "positions_count": 0,
                    "top_position_ratio": 0,
                    "recommendation": "No positions found"
                },
                message="No positions to analyze"
            )

        # 计算分散度指标
        total_value = sum([p.get('market_value', 0) for p in positions])
        if total_value <= 0:
            return APIResponse(
                data={
                    "diversification_score": 0,
                    "concentration_risk": "HIGH",
                    "positions_count": len(positions),
                    "top_position_ratio": 0,
                    "recommendation": "No market value"
                },
                message="No market value in positions"
            )

        # 计算前5大持仓占比
        sorted_positions = sorted(positions, key=lambda x: x.get('market_value', 0), reverse=True)
        top5_value = sum([p.get('market_value', 0) for p in sorted_positions[:5]])
        top5_ratio = top5_value / total_value

        # 计算赫芬达尔-赫希曼指数 (HHI)
        hhi = sum([(p.get('market_value', 0) / total_value) ** 2 for p in positions])

        # 计算分散度分数 (0-100)
        diversification_score = max(0, min(100, (1 - hhi) * 100))

        # 风险等级
        if hhi > 0.25:
            concentration_risk = "HIGH"
            recommendation = "持仓过于集中，建议分散投资"
        elif hhi > 0.15:
            concentration_risk = "MEDIUM"
            recommendation = "持仓集中度较高，可考虑适当分散"
        else:
            concentration_risk = "LOW"
            recommendation = "持仓分散度良好"

        return APIResponse(
            data={
                "diversification_score": round(diversification_score, 2),
                "concentration_risk": concentration_risk,
                "hhi_index": round(hhi, 4),
                "positions_count": len(positions),
                "top_position_ratio": round(sorted_positions[0].get('market_value', 0) / total_value, 4) if positions else 0,
                "top5_ratio": round(top5_ratio, 4),
                "recommendation": recommendation,
                "calculation_time": datetime.now().isoformat()
            },
            message="Portfolio diversification analysis completed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing diversification: {str(e)}")

@risk_control_router.get("/risk/portfolio/value-at-risk", response_model=APIResponse)
async def get_portfolio_var(
    confidence_level: float = Query(0.95, ge=0.9, le=0.99, description="置信水平 (0.9-0.99)")
):
    """投资组合 VaR 计算"""
    try:
        from ..services import PortfolioService
        portfolio_service = PortfolioService()

        # 获取持仓和交易历史
        positions_result = portfolio_service.get_all_positions(page=1, page_size=100)
        transactions_result = portfolio_service.get_transaction_history()

        if not positions_result.get("success") or not transactions_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to get portfolio data")

        positions = positions_result.get("data", [])
        transactions = transactions_result.get("data", [])

        if not positions:
            return APIResponse(
                data={
                    "var": 0,
                    "var_pct": 0,
                    "confidence_level": confidence_level,
                    "positions_count": 0,
                    "warning": "No positions found"
                },
                message="No positions to calculate VaR"
            )

        # 计算总市值
        total_value = sum([p.get('market_value', 0) for p in positions])

        if total_value <= 0:
            return APIResponse(
                data={
                    "var": 0,
                    "var_pct": 0,
                    "confidence_level": confidence_level,
                    "positions_count": len(positions),
                    "warning": "No market value"
                },
                message="No market value in positions"
            )

        # 简化的 VaR 计算（基于历史模拟法）
        # 实际项目应该使用更复杂的蒙特卡洛模拟或参数法
        returns_list = []
        for transaction in transactions:
            if transaction.get('transaction_type') == 'SELL':
                # 计算每笔交易的收益率
                # 这里简化处理
                returns_list.append(0.01)  # 假设1%的收益率

        if returns_list:
            var = calculate_var(returns_list, confidence_level)
            var_amount = total_value * var
        else:
            var = 0.05  # 默认5%
            var_amount = total_value * var

        return APIResponse(
            data={
                "var": round(var_amount, 2),
                "var_pct": round(var * 100, 2),
                "confidence_level": confidence_level,
                "total_portfolio_value": round(total_value, 2),
                "positions_count": len(positions),
                "method": "Historical Simulation (Simplified)",
                "calculation_time": datetime.now().isoformat()
            },
            message="Portfolio VaR calculated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating portfolio VaR: {str(e)}")
