#!/usr/bin/env python3
"""回测系统路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime

from ..models.common import APIResponse
from ..models.backtest import (
    BacktestRequest,
    BacktestResultResponse,
    ReportRequest,
    PerformanceMetrics,
    Trade
)
from common.database import DatabaseManager
from backtest.services import BacktestService
from backtest.config import BacktestConfig
from technical_analysis.services import AnalysisService
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)

def get_db_session() -> Session:
    """获取数据库 session 依赖"""
    db_manager = DatabaseManager()
    with db_manager.get_session() as session:
        yield session

backtest_router = APIRouter()

# 策略映射
STRATEGY_MAP = {
    "five_dimension": FiveDimensionStrategy,
    "vcp": VCPBreakoutStrategy,
    "td_golden_pit": TDGoldenPitStrategy,
    "top_divergence": TopDivergenceStrategy
}

# 内存存储回测结果（生产环境应该用数据库或缓存）
BACKTEST_RESULTS: Dict[str, BacktestResultResponse] = {}


def create_strategy(strategy_name: str, analysis_service=None):
    """创建策略实例"""
    strategy_class = STRATEGY_MAP.get(strategy_name)
    if not strategy_class:
        raise HTTPException(status_code=400, detail=f"无效的策略名称: {strategy_name}")

    if strategy_name == "five_dimension":
        if not analysis_service:
            raise HTTPException(status_code=400, detail="五维共振策略需要 AnalysisService")
        return strategy_class(analysis_service)
    else:
        return strategy_class()


@backtest_router.post("/backtest/single", response_model=APIResponse)
async def run_single_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db_session)
):
    """单股票回测"""
    if not request.symbol:
        raise HTTPException(status_code=400, detail="需要提供股票代码")

    # 创建配置
    config = BacktestConfig(**request.config.dict())

    # 创建服务
    backtest_service = BacktestService(db)
    analysis_service = AnalysisService(db) if request.strategy == "five_dimension" else None

    # 创建策略
    strategy = create_strategy(request.strategy, analysis_service)

    try:
        # 运行回测
        result = backtest_service.run_single_stock_backtest(
            symbol=request.symbol,
            strategy=strategy,
            config=config
        )

        # 生成任务 ID
        task_id = f"bt_{request.symbol}_{int(datetime.now().timestamp())}"

        # 转换结果格式
        response = BacktestResultResponse(
            task_id=task_id,
            symbol=request.symbol,
            strategy=request.strategy,
            config=request.config,
            performance=PerformanceMetrics(
                total_return=result.performance.total_return,
                annual_return=result.performance.annual_return,
                volatility=result.performance.volatility,
                max_drawdown=result.performance.max_drawdown,
                sharpe_ratio=result.performance.sharpe_ratio,
                sortino_ratio=result.performance.sortino_ratio,
                calmar_ratio=result.performance.calmar_ratio,
                total_trades=result.performance.total_trades,
                winning_trades=result.performance.winning_trades,
                losing_trades=result.performance.losing_trades,
                win_rate=result.performance.win_rate,
                profit_factor=result.performance.profit_factor,
                avg_holding_days=result.performance.avg_holding_days
            ),
            trades=[
                Trade(
                    trade_id=i,
                    symbol=request.symbol,
                    date=trade.date,
                    action=trade.action,
                    price=trade.price,
                    quantity=trade.quantity,
                    amount=trade.amount,
                    commission=trade.commission,
                    pnl=trade.pnl
                )
                for i, trade in enumerate(result.trades)
            ],
            equity_curve=result.equity_curve,
            dates=result.dates
        )

        # 保存结果
        BACKTEST_RESULTS[task_id] = response

        return APIResponse(
            data={
                "task_id": task_id,
                "symbol": request.symbol,
                "strategy": request.strategy,
                "status": "completed",
                "result_summary": {
                    "total_return": result.performance.total_return,
                    "annual_return": result.performance.annual_return,
                    "max_drawdown": result.performance.max_drawdown,
                    "sharpe_ratio": result.performance.sharpe_ratio,
                    "win_rate": result.performance.win_rate,
                    "total_trades": result.performance.total_trades
                }
            },
            message="回测完成"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


@backtest_router.post("/backtest/portfolio", response_model=APIResponse)
async def run_portfolio_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db_session)
):
    """多股票组合回测"""
    if not request.symbols:
        raise HTTPException(status_code=400, detail="需要提供股票代码列表")

    config = BacktestConfig(**request.config.dict())
    backtest_service = BacktestService(db)
    analysis_service = AnalysisService(db) if request.strategy == "five_dimension" else None
    strategy = create_strategy(request.strategy, analysis_service)

    try:
        results = backtest_service.run_multi_stock_backtest(
            symbols=request.symbols,
            strategy=strategy,
            config=config
        )

        # 汇总结果
        task_id = f"bt_portfolio_{int(datetime.now().timestamp())}"
        response_data = {
            "task_id": task_id,
            "symbols_count": len(request.symbols),
            "strategy": request.strategy,
            "status": "completed",
            "results": {
                symbol: {
                    "annual_return": result.performance.annual_return,
                    "sharpe_ratio": result.performance.sharpe_ratio,
                    "max_drawdown": result.performance.max_drawdown,
                    "total_return": result.performance.total_return
                }
                for symbol, result in results.items()
            }
        }

        return APIResponse(data=response_data, message="组合回测完成")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"组合回测失败: {str(e)}")


@backtest_router.post("/backtest/compare", response_model=APIResponse)
async def compare_strategies(
    request: BacktestRequest,
    db: Session = Depends(get_db_session)
):
    """策略比较"""
    if not request.symbol:
        raise HTTPException(status_code=400, detail="需要提供股票代码")

    config = BacktestConfig(**request.config.dict())
    backtest_service = BacktestService(db)

    try:
        strategies = [
            create_strategy("five_dimension", AnalysisService(db)),
            create_strategy("vcp"),
            create_strategy("td_golden_pit"),
            create_strategy("top_divergence")
        ]

        results = backtest_service.compare_strategies(
            symbol=request.symbol,
            strategies=strategies,
            config=config
        )

        comparison = {}
        for name, result in results.items():
            comparison[name] = {
                "annual_return": result.performance.annual_return,
                "sharpe_ratio": result.performance.sharpe_ratio,
                "max_drawdown": result.performance.max_drawdown,
                "win_rate": result.performance.win_rate
            }

        # 找出最佳策略
        best_strategy = max(
            comparison.items(),
            key=lambda x: (x[1]["sharpe_ratio"], x[1]["annual_return"])
        )[0]

        return APIResponse(
            data={
                "symbol": request.symbol,
                "comparison": comparison,
                "best_strategy": best_strategy,
                "recommendation": f"{best_strategy} 策略表现最优"
            },
            message="策略比较完成"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略比较失败: {str(e)}")


@backtest_router.get("/backtest/result/{task_id}", response_model=APIResponse)
async def get_backtest_result(task_id: str):
    """获取回测结果"""
    if task_id not in BACKTEST_RESULTS:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    return APIResponse(
        data=BACKTEST_RESULTS[task_id],
        message="回测结果获取成功"
    )


@backtest_router.post("/backtest/report", response_model=APIResponse)
async def generate_backtest_report(
    request: ReportRequest,
    db: Session = Depends(get_db_session)
):
    """生成回测报告"""
    if request.task_id not in BACKTEST_RESULTS:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    report_format = request.format.lower()

    if report_format == "json":
        return APIResponse(
            data={
                "task_id": request.task_id,
                "format": "json",
                "report": BACKTEST_RESULTS[request.task_id].dict()
            },
            message="JSON 报告生成成功"
        )

    elif report_format in ["text", "html"]:
        # 生成文本或 HTML 报告
        backtest_result = BACKTEST_RESULTS[request.task_id]
        report_content = f"""
# 回测报告

## 基本信息
- 任务ID: {request.task_id}
- 股票: {backtest_result.symbol}
- 策略: {backtest_result.strategy}
- 回测期间: {backtest_result.config.start_date} ~ {backtest_result.config.end_date}

## 绩效指标
- 总收益率: {backtest_result.performance.total_return:.2f}%
- 年化收益率: {backtest_result.performance.annual_return:.2f}%
- 最大回撤: {backtest_result.performance.max_drawdown:.2f}%
- 夏普比率: {backtest_result.performance.sharpe_ratio:.2f}
- 胜率: {backtest_result.performance.win_rate:.1f}%
- 总交易次数: {backtest_result.performance.total_trades}

## 交易记录
共 {len(backtest_result.trades)} 笔交易
"""

        if report_format == "text":
            return APIResponse(
                data={
                    "task_id": request.task_id,
                    "format": "text",
                    "report_content": report_content
                },
                message="文本报告生成成功"
            )
        else:  # html
            # 构建HTML内容
            html_body = report_content.replace('\\n', '<br>').replace('#', '<h2>').replace('##', '<h3>').replace('-', '&nbsp;&nbsp;-')
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>回测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <h1>📈 回测报告</h1>
    {html_body}
</body>
</html>
"""
            return APIResponse(
                data={
                    "task_id": request.task_id,
                    "format": "html",
                    "report_content": html_content,
                    "download_url": f"/api/v1/backtest/report/download/{request.task_id}.html"
                },
                message="HTML 报告生成成功"
            )

    else:
        raise HTTPException(status_code=400, detail="不支持的报告格式")
