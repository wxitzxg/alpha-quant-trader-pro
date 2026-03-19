#!/usr/bin/env python3
"""风险提示路由 - 集成业务逻辑"""

from fastapi import APIRouter, HTTPException, Path, Query, Body, BackgroundTasks
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from ..models.common import APIResponse
from ..models.alerts import AlertsResponse, AlertTrigger
from ..services.data_source_service import DataSourceService
from common.database import DatabaseManager
from stock_market.repositories import KLineRepository
from ..models.kline import KLineQueryParams

alerts_router = APIRouter()

def check_price_alerts(stock_code: str, current_price: float, thresholds: dict) -> List[dict]:
    """检查价格相关预警"""
    alerts = []

    upper_threshold = thresholds.get('upper_threshold')
    lower_threshold = thresholds.get('lower_threshold')
    change_pct_threshold = thresholds.get('change_pct_threshold')

    if upper_threshold and current_price > upper_threshold:
        alerts.append({
            "type": "PRICE_ABOVE_THRESHOLD",
            "stock_code": stock_code,
            "message": f"股价 {current_price:.2f} 已超过设定上限 {upper_threshold:.2f}",
            "severity": "WARNING",
            "current_value": current_price,
            "threshold": upper_threshold
        })

    if lower_threshold and current_price < lower_threshold:
        alerts.append({
            "type": "PRICE_BELOW_THRESHOLD",
            "stock_code": stock_code,
            "message": f"股价 {current_price:.2f} 已低于设定下限 {lower_threshold:.2f}",
            "severity": "WARNING",
            "current_value": current_price,
            "threshold": lower_threshold
        })

    # 检查涨跌幅（需要历史数据）
    klines = DataSourceService.get_kline(
        stock_code=stock_code,
        interval="1d",
        limit=2
    )
    if klines and len(klines) >= 2:
        prev_close = float(klines[1].get('close', 0))
        if prev_close > 0:
            change_pct = (current_price - prev_close) / prev_close
            if change_pct_threshold and abs(change_pct) > change_pct_threshold:
                direction = "上涨" if change_pct > 0 else "下跌"
                alerts.append({
                    "type": "PRICE_CHANGE_EXCEEDED",
                    "stock_code": stock_code,
                    "message": f"股价{direction}{change_pct*100:.2f}%，超过设定阈值{change_pct_threshold*100:.2f}%",
                    "severity": "WARNING" if abs(change_pct) < 0.1 else "CRITICAL",
                    "current_value": change_pct,
                    "threshold": change_pct_threshold
                })

    return alerts

def check_technical_alerts(stock_code: str) -> List[dict]:
    """检查技术指标预警"""
    alerts = []

    try:
        # 获取K线数据
        klines = DataSourceService.get_kline(
            stock_code=stock_code,
            interval="1d",
            limit=50
        )

        if not klines or len(klines) < 20:
            return alerts

        # 提取价格数据
        closes = [float(k.get('close', 0)) for k in klines if k.get('close')]
        highs = [float(k.get('high', 0)) for k in klines if k.get('high')]
        lows = [float(k.get('low', 0)) for k in klines if k.get('low')]

        if len(closes) < 20:
            return alerts

        current_price = closes[-1]
        recent_high = max(closes[-10:])
        recent_low = min(closes[-10:])

        # 检查是否突破近期高点
        if current_price > recent_high * 0.98:  # 接近或突破近期高点
            alerts.append({
                "type": "BREAKOUT_HIGH",
                "stock_code": stock_code,
                "message": f"股价 {current_price:.2f} 接近或突破近期高点 {recent_high:.2f}",
                "severity": "INFO",
                "current_value": current_price,
                "reference_value": recent_high
            })

        # 检查是否跌破近期低点
        if current_price < recent_low * 1.02:  # 接近或跌破近期低点
            alerts.append({
                "type": "BREAKDOWN_LOW",
                "stock_code": stock_code,
                "message": f"股价 {current_price:.2f} 接近或跌破近期低点 {recent_low:.2f}",
                "severity": "WARNING",
                "current_value": current_price,
                "reference_value": recent_low
            })

        # 检查波动率异常
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                returns.append((closes[i] - closes[i-1]) / closes[i-1])

        if returns:
            avg_return = sum(returns) / len(returns)
            volatility = (sum([(r - avg_return) ** 2 for r in returns]) / len(returns)) ** 0.5

            if volatility > 0.05:  # 波动率超过5%
                alerts.append({
                    "type": "HIGH_VOLATILITY",
                    "stock_code": stock_code,
                    "message": f"近期波动率高达 {volatility*100:.2f}%",
                    "severity": "WARNING",
                    "current_value": volatility,
                    "threshold": 0.05
                })

    except Exception as e:
        print(f"Error checking technical alerts for {stock_code}: {e}")

    return alerts

def check_portfolio_risk_alerts() -> List[dict]:
    """检查投资组合风险预警"""
    alerts = []

    try:
        from ..services import PortfolioService
        portfolio_service = PortfolioService()

        # 获取账户汇总
        summary_result = portfolio_service.get_account_summary()
        if summary_result.get("success"):
            summary = summary_result.get("data", {})
            total_profit = summary.get('total_profit', 0)
            total_market_value = summary.get('total_market_value', 0)

            if total_market_value > 0:
                profit_rate = total_profit / total_market_value

                # 检查总盈亏
                if profit_rate < -0.1:  # 亏损超过10%
                    alerts.append({
                        "type": "PORTFOLIO_LOSS",
                        "message": f"账户总亏损达到 {profit_rate*100:.2f}%",
                        "severity": "CRITICAL",
                        "current_value": profit_rate,
                        "threshold": -0.1
                    })
                elif profit_rate < -0.05:  # 亏损超过5%
                    alerts.append({
                        "type": "PORTFOLIO_LOSS",
                        "message": f"账户总亏损达到 {profit_rate*100:.2f}%",
                        "severity": "WARNING",
                        "current_value": profit_rate,
                        "threshold": -0.05
                    })

        # 获取持仓列表
        positions_result = portfolio_service.get_all_positions(page=1, page_size=100)
        if positions_result.get("success"):
            positions = positions_result.get("data", [])
            total_positions = len(positions)

            # 检查持仓集中度
            if total_positions == 0:
                alerts.append({
                    "type": "NO_POSITIONS",
                    "message": "当前没有持仓",
                    "severity": "INFO"
                })
            elif total_positions == 1:
                alerts.append({
                    "type": "CONCENTRATION_RISK",
                    "message": "持仓过于集中，仅持有1只股票",
                    "severity": "WARNING",
                    "current_value": total_positions,
                    "threshold": 3
                })
            elif total_positions < 3:
                alerts.append({
                    "type": "CONCENTRATION_RISK",
                    "message": f"持仓较为集中，仅持有{total_positions}只股票",
                    "severity": "WARNING",
                    "current_value": total_positions,
                    "threshold": 3
                })

            # 检查单个持仓的亏损
            for position in positions:
                floating_pl = position.get('floating_pl', 0)
                market_value = position.get('market_value', 0)
                symbol = position.get('symbol', '')

                if market_value > 0:
                    loss_rate = floating_pl / market_value

                    if loss_rate < -0.15:  # 单只股票亏损超过15%
                        alerts.append({
                            "type": "POSITION_LOSS",
                            "stock_code": symbol,
                            "message": f"持仓 {symbol} 亏损达到 {loss_rate*100:.2f}%",
                            "severity": "WARNING",
                            "current_value": loss_rate,
                            "threshold": -0.15
                        })

    except Exception as e:
        print(f"Error checking portfolio risk alerts: {e}")

    return alerts

@alerts_router.get("/alerts/triggered", response_model=APIResponse)
async def get_triggered_alerts():
    """获取已触发预警"""
    try:
        all_alerts = []

        # 1. 检查投资组合风险预警
        portfolio_alerts = check_portfolio_risk_alerts()
        all_alerts.extend(portfolio_alerts)

        # 2. 检查持仓股票的技术指标预警
        try:
            from ..services import PortfolioService
            portfolio_service = PortfolioService()

            positions_result = portfolio_service.get_all_positions(page=1, page_size=100)
            if positions_result.get("success"):
                positions = positions_result.get("data", [])
                for position in positions:
                    stock_code = position.get('symbol', '')
                    try:
                        technical_alerts = check_technical_alerts(stock_code)
                        all_alerts.extend(technical_alerts)
                    except Exception as e:
                        print(f"Error checking alerts for {stock_code}: {e}")
        except Exception as e:
            print(f"Error getting positions for alerts: {e}")

        # 按严重程度排序
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        all_alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 2))

        return APIResponse(
            data={
                "alerts": all_alerts,
                "total_count": len(all_alerts),
                "critical_count": len([a for a in all_alerts if a.get('severity') == 'CRITICAL']),
                "warning_count": len([a for a in all_alerts if a.get('severity') == 'WARNING']),
                "info_count": len([a for a in all_alerts if a.get('severity') == 'INFO']),
                "check_time": datetime.now().isoformat()
            },
            message="Triggered alerts retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting triggered alerts: {str(e)}")

@alerts_router.get("/alerts/stock/{stock_code}", response_model=APIResponse)
async def get_stock_alerts(
    stock_code: str = Path(..., description="股票代码", example="600519"),
    check_types: str = Query("all", description="检查类型 (price/technical/all)")
):
    """获取单只股票的预警"""
    try:
        all_alerts = []

        # 获取当前价格
        quote = DataSourceService.get_realtime_quote(stock_code)
        if not quote:
            raise HTTPException(status_code=404, detail="Stock quote not found")

        current_price = float(quote.get('current_price', 0))
        if current_price <= 0:
            raise HTTPException(status_code=400, detail="Invalid current price")

        # 检查价格预警
        if check_types in ["price", "all"]:
            price_alerts = check_price_alerts(stock_code, current_price, {
                'upper_threshold': current_price * 1.1,  # 上涨10%
                'lower_threshold': current_price * 0.9,  # 下跌10%
                'change_pct_threshold': 0.05  # 涨跌幅5%
            })
            all_alerts.extend(price_alerts)

        # 检查技术指标预警
        if check_types in ["technical", "all"]:
            technical_alerts = check_technical_alerts(stock_code)
            all_alerts.extend(technical_alerts)

        return APIResponse(
            data={
                "stock_code": stock_code,
                "current_price": current_price,
                "alerts": all_alerts,
                "total_count": len(all_alerts),
                "check_time": datetime.now().isoformat()
            },
            message=f"Alerts for {stock_code} retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stock alerts: {str(e)}")

@alerts_router.post("/alerts/portfolio/monitor", response_model=APIResponse)
async def monitor_portfolio_risks():
    """监控投资组合风险"""
    try:
        alerts = check_portfolio_risk_alerts()

        # 按严重程度排序
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        alerts.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 2))

        summary = {
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.get('severity') == 'CRITICAL']),
            "warning_alerts": len([a for a in alerts if a.get('severity') == 'WARNING']),
            "info_alerts": len([a for a in alerts if a.get('severity') == 'INFO']),
            "check_time": datetime.now().isoformat()
        }

        # 生成建议
        recommendations = []
        if summary["critical_alerts"] > 0:
            recommendations.append("⚠️ 发现严重风险，请立即关注")
        if summary["warning_alerts"] > 0:
            recommendations.append("⚠️ 建议检查投资组合配置")
        if summary["total_alerts"] == 0:
            recommendations.append("✅ 投资组合风险状况良好")

        summary["recommendations"] = recommendations

        return APIResponse(
            data={
                "alerts": alerts,
                "summary": summary
            },
            message="Portfolio risk monitoring completed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error monitoring portfolio risks: {str(e)}")
