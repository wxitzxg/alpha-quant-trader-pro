# API 集成实施计划

**日期:** 2026-03-18
**版本:** 1.0.0
**基于设计文档:** [API 集成设计文档](./2026-03-18-api-integration-design.md)

---

## 📋 任务清单

### 阶段 1: 路由集成和启用（预计 1 天）

#### 任务 1.1: 启用现有路由
**文件:** `api_server/main.py`

```python
# 移除路由导入的注释
from .routers import (
    health_router,
    data_source_router,
    stock_market_router,
    portfolio_router,
    analysis_router,      # 启用
    risk_control_router,
    performance_router,   # 启用
    alerts_router
)

# 移除路由注册的注释
app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])
app.include_router(data_source_router, prefix="/api/v1", tags=["数据源聚合"])
app.include_router(stock_market_router, prefix="/api/v1", tags=["股票市场"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["持仓管理"])
app.include_router(analysis_router, prefix="/api/v1", tags=["技术分析"])        # 启用
app.include_router(risk_control_router, prefix="/api/v1", tags=["风险控制"])
app.include_router(performance_router, prefix="/api/v1", tags=["收益统计"])     # 启用
app.include_router(alerts_router, prefix="/api/v1", tags=["风险提示"])
```

**验收标准:**
- [ ] 所有路由正常注册
- [ ] `/docs` 页面可以看到所有端点
- [ ] 健康检查端点正常工作

---

#### 任务 1.2: 完善技术分析路由
**文件:** `api_server/routers/analysis.py`

**需要添加:**
1. 依赖注入（数据库会话）
2. 连接 `AnalysisService`
3. 完善所有端点的实现

**实施步骤:**

```python
# 1. 添加导入
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from common.database import get_db_session
from technical_analysis.services import AnalysisService

# 2. 完善五维共振端点
@analysis_router.post("/analysis/five-dimension", response_model=APIResponse)
async def analyze_five_dimension(
    request: AnalysisRequest,
    db: Session = Depends(get_db_session)
):
    service = AnalysisService(db)
    result = service.analyze_stock(
        symbol=request.stock_code,
        interval="1d",
        days=request.days
    )

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['message'])

    return APIResponse(data=result, message="五维共振分析完成")

# 3. 完善技术指标端点
@analysis_router.get("/analysis/indicator/{stock_code}", response_model=APIResponse)
async def get_indicator(
    stock_code: str,
    indicator_name: str,
    days: int = 60,
    db: Session = Depends(get_db_session)
):
    service = AnalysisService(db)
    result = service.get_technical_indicators(
        symbol=stock_code,
        days=days
    )

    return APIResponse(data=result, message=f"{indicator_name}指标获取成功")

# 4. 添加三大策略分析端点
@analysis_router.get("/analysis/strategies/{stock_code}", response_model=APIResponse)
async def analyze_with_strategies(
    stock_code: str,
    days: int = 120,
    db: Session = Depends(get_db_session)
):
    service = AnalysisService(db)
    result = service.analyze_with_strategies(
        symbol=stock_code,
        days=days
    )

    return APIResponse(data=result, message="策略分析完成")

# 5. 添加完整报告端点
@analysis_router.get("/analysis/report/{stock_code}", response_model=APIResponse)
async def generate_analysis_report(
    stock_code: str,
    days: int = 120,
    db: Session = Depends(get_db_session)
):
    service = AnalysisService(db)
    report = service.generate_analysis_report(
        symbol=stock_code,
        days=days
    )

    return APIResponse(
        data={"symbol": stock_code, "report_type": "text", "content": report},
        message="报告生成成功"
    )
```

**验收标准:**
- [ ] 五维共振分析返回正确结果
- [ ] 技术指标查询正常工作
- [ ] 三大策略分析返回数据
- [ ] 完整报告生成成功
- [ ] 所有端点都有单元测试

---

#### 任务 1.3: 完善收益统计路由
**文件:** `api_server/routers/performance.py`

**需要添加:**
1. 暂时使用模拟数据（阶段 4 再连接真实数据）
2. 完善端点实现

```python
# api_server/routers/performance.py

@performance_router.get("/performance/account/summary", response_model=APIResponse)
async def get_account_performance():
    """账户收益汇总（暂用模拟数据）"""
    return APIResponse(
        data=PerformanceResponse(
            metrics=PerformanceMetrics(
                total_return=15.5,
                total_return_amount=15500,
                annualized_return=28.5,
                max_drawdown=8.2,
                volatility=12.5,
                sharpe_ratio=1.45,
                sortino_ratio=1.85,
                calmar_ratio=3.48,
                win_rate=65.8,
                profit_factor=1.85,
                avg_holding_days=12.5,
                total_trades=45,
                winning_trades=30,
                losing_trades=15
            )
        ),
        message="Account performance retrieved"
    )
```

**验收标准:**
- [ ] 端点返回正确格式
- [ ] 模拟数据合理

---

### 阶段 2: 回测 API 开发（预计 2 天）

#### 任务 2.1: 创建回测数据模型
**文件:** `api_server/models/backtest.py` (新建)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class BacktestConfigRequest(BaseModel):
    """回测配置请求"""
    initial_capital: float = Field(100000.0, gt=0, description="初始资金")
    commission_rate: float = Field(0.00025, ge=0, le=0.01, description="手续费率")
    slippage_rate: float = Field(0.001, ge=0, le=0.01, description="滑点率")
    stamp_duty_rate: float = Field(0.001, ge=0, le=0.01, description="印花税率")
    start_date: str = Field("2023-01-01", description="回测开始日期")
    end_date: str = Field("2024-12-31", description="回测结束日期")
    interval: str = Field("1d", description="K线周期")
    position_size: float = Field(0.1, gt=0, le=1, description="单笔仓位")
    max_positions: int = Field(5, gt=0, description="最大持仓数")
    stop_loss_pct: float = Field(0.08, gt=0, le=0.5, description="止损比例")
    take_profit_pct: float = Field(0.2, gt=0, le=1.0, description="止盈比例")


class BacktestRequest(BaseModel):
    """回测请求"""
    symbol: Optional[str] = Field(None, description="股票代码（单股票）")
    symbols: Optional[List[str]] = Field(None, description="股票代码列表（组合）")
    strategy: str = Field(..., description="策略名称")
    config: BacktestConfigRequest = Field(default_factory=BacktestConfigRequest)


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    volatility: float = Field(..., description="波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(..., description="索提诺比率")
    calmar_ratio: float = Field(..., description="卡尔玛比率")
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利次数")
    losing_trades: int = Field(..., description="亏损次数")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈亏比")
    avg_holding_days: float = Field(..., description="平均持仓天数")


class Trade(BaseModel):
    """交易记录"""
    trade_id: int
    symbol: str
    date: str
    action: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float] = None


class BacktestResultResponse(BaseModel):
    """回测结果响应"""
    task_id: str
    symbol: Optional[str]
    symbols: Optional[List[str]]
    strategy: str
    config: BacktestConfigRequest
    performance: PerformanceMetrics
    trades: List[Trade]
    equity_curve: List[float]
    dates: List[str]


class ReportRequest(BaseModel):
    """报告请求"""
    task_id: str
    format: str = Field("json", description="报告格式: json, text, html")
```

**验收标准:**
- [ ] 所有模型创建完成
- [ ] 字段验证正确
- [ ] 导出到 `api_server/models/__init__.py`

---

#### 任务 2.2: 创建回测路由
**文件:** `api_server/routers/backtest.py` (新建)

```python
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
from common.database import get_db_session
from backtest.services import BacktestService
from backtest.config import BacktestConfig
from technical_analysis.services import AnalysisService
from backtest.strategies.prebuilt import (
    FiveDimensionStrategy,
    VCPBreakoutStrategy,
    TDGoldenPitStrategy,
    TopDivergenceStrategy
)

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

    backtest_service = BacktestService(db)
    result = BACKTEST_RESULTS[request.task_id]

    # 这里需要将 BacktestResultResponse 转换回 backtest.models.BacktestResult
    # 为了简化，我们直接返回存储的结果
    report_format = request.format.lower()

    if report_format == "json":
        return APIResponse(
            data={
                "task_id": request.task_id,
                "format": "json",
                "report": result.dict()
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
    {report_content.replace('\n', '<br>').replace('#', '<h2>').replace('##', '<h3>').replace('-', '&nbsp;&nbsp;-')}
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
```

**验收标准:**
- [ ] 单股票回测正常工作
- [ ] 多股票组合回测正常工作
- [ ] 策略比较正常工作
- [ ] 结果查询正常工作
- [ ] 报告生成支持 JSON/文本/HTML
- [ ] 所有端点都有错误处理
- [ ] 所有端点都有单元测试

---

#### 任务 2.3: 注册回测路由
**文件:** `api_server/routers/__init__.py`

```python
# 添加导入
from .backtest import backtest_router

# 添加到 __all__
__all__ = [
    "health_router",
    "data_source_router",
    "stock_market_router",
    "portfolio_router",
    "analysis_router",
    "risk_control_router",
    "performance_router",
    "alerts_router",
    "backtest_router"  # 新增
]
```

**文件:** `api_server/main.py`

```python
# 添加导入
from .routers import backtest_router

# 注册路由
app.include_router(backtest_router, prefix="/api/v1", tags=["回测系统"])
```

**验收标准:**
- [ ] 路由成功注册
- [ ] `/docs` 页面可以看到回测端点

---

### 阶段 3: 模拟交易开发（预计 2 天）

#### 任务 3.1: 创建模拟交易数据模型
**文件:** `api_server/models/simulation.py` (新建)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SimulationAccountCreate(BaseModel):
    """创建账户请求"""
    account_name: str = Field(..., min_length=1, max_length=50, description="账户名称")
    initial_capital: float = Field(100000.0, gt=0, description="初始资金")
    commission_rate: float = Field(0.00025, ge=0, le=0.01, description="手续费率")


class Position(BaseModel):
    """持仓信息"""
    symbol: str
    quantity: int
    cost_price: float
    market_price: float
    market_value: float
    floating_pl: float
    floating_pl_pct: float
    entry_date: str


class PositionsResponse(BaseModel):
    """持仓列表响应"""
    account_id: str
    positions: List[Position]
    total_market_value: float
    total_floating_pl: float
    total_floating_pl_pct: float


class TradeOrder(BaseModel):
    """交易订单"""
    account_id: str
    symbol: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    order_type: str = Field("market", description="订单类型: market, limit")


class Trade(BaseModel):
    """交易记录"""
    trade_id: str
    account_id: str
    symbol: str
    action: str  # buy, sell
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float] = None
    total_cost: Optional[float] = None
    total_revenue: Optional[float] = None
    timestamp: datetime


class TradeResult(BaseModel):
    """交易结果"""
    trade_id: str
    account_id: str
    symbol: str
    action: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: Optional[float]
    total_cost: Optional[float]
    total_revenue: Optional[float]
    timestamp: datetime
    account_balance: float


class SimulationAccount(BaseModel):
    """模拟账户"""
    account_id: str
    account_name: str
    initial_capital: float
    current_balance: float
    available_cash: float
    total_value: float
    floating_pl: float
    total_return: float
    positions_count: int
    commission_rate: float
    created_at: datetime
    updated_at: datetime
```

**验收标准:**
- [ ] 所有模型创建完成
- [ ] 字段验证正确
- [ ] 导出到 `api_server/models/__init__.py`

---

#### 任务 3.2: 创建模拟交易服务
**文件:** `api_server/services/simulation_service.py` (新建)

```python
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from ..models.simulation import SimulationAccount as AccountModel


class Position:
    """持仓类"""

    def __init__(self, symbol: str, quantity: int, cost_price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.cost_price = cost_price
        self.entry_date = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self, market_price: float):
        """转换为字典"""
        market_value = market_price * self.quantity
        floating_pl = (market_price - self.cost_price) * self.quantity
        floating_pl_pct = (floating_pl / (self.cost_price * self.quantity)) * 100 if self.quantity > 0 else 0

        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "cost_price": self.cost_price,
            "market_price": market_price,
            "market_value": market_value,
            "floating_pl": floating_pl,
            "floating_pl_pct": floating_pl_pct,
            "entry_date": self.entry_date
        }


class Trade:
    """交易类"""

    def __init__(
        self,
        account_id: str,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        commission: float,
        pnl: Optional[float] = None
    ):
        self.trade_id = f"trade_{uuid.uuid4().hex[:8]}"
        self.account_id = account_id
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.amount = price * quantity
        self.commission = commission
        self.pnl = pnl
        self.timestamp = datetime.now()

    def to_dict(self):
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "account_id": self.account_id,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "amount": self.amount,
            "commission": self.commission,
            "pnl": self.pnl,
            "timestamp": self.timestamp.isoformat()
        }


class SimulationAccount:
    """模拟账户类"""

    def __init__(
        self,
        account_name: str,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025
    ):
        self.account_id = f"sim_{int(datetime.now().timestamp())}"
        self.account_name = account_name
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.available_cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def buy(self, symbol: str, price: float, quantity: int) -> Trade:
        """买入"""
        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_cost = total_amount + commission

        if self.available_cash < total_cost:
            raise ValueError(
                f"余额不足，需要 {total_cost:.2f}，当前可用 {self.available_cash:.2f}"
            )

        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_cost_price = (pos.cost_price * pos.quantity + total_amount) / new_quantity
            pos.quantity = new_quantity
            pos.cost_price = new_cost_price
        else:
            self.positions[symbol] = Position(symbol, quantity, price)

        # 更新账户
        self.available_cash -= total_cost
        self.current_balance -= total_cost

        # 记录交易
        trade = Trade(self.account_id, symbol, "buy", price, quantity, commission)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

    def sell(self, symbol: str, price: float, quantity: int) -> Trade:
        """卖出"""
        if symbol not in self.positions:
            raise ValueError(f"没有持仓 {symbol}")

        pos = self.positions[symbol]
        if pos.quantity < quantity:
            raise ValueError(f"持仓不足，当前 {pos.quantity}，卖出 {quantity}")

        total_amount = price * quantity
        commission = total_amount * self.commission_rate
        total_revenue = total_amount - commission

        # 计算盈亏
        pnl = (price - pos.cost_price) * quantity

        # 更新持仓
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]

        # 更新账户
        self.available_cash += total_revenue
        self.current_balance += total_revenue

        # 记录交易
        trade = Trade(self.account_id, symbol, "sell", price, quantity, commission, pnl)
        self.trades.append(trade)
        self.updated_at = datetime.now()

        return trade

    def get_positions(self, market_prices: Dict[str, float]) -> dict:
        """获取持仓列表"""
        positions = []
        total_market_value = 0
        total_floating_pl = 0

        for symbol, pos in self.positions.items():
            market_price = market_prices.get(symbol, pos.cost_price)
            pos_dict = pos.to_dict(market_price)
            positions.append(pos_dict)
            total_market_value += pos_dict["market_value"]
            total_floating_pl += pos_dict["floating_pl"]

        total_floating_pl_pct = (
            (total_floating_pl / self.initial_capital) * 100
            if self.initial_capital > 0 else 0
        )

        return {
            "account_id": self.account_id,
            "positions": positions,
            "total_market_value": total_market_value,
            "total_floating_pl": total_floating_pl,
            "total_floating_pl_pct": total_floating_pl_pct
        }

    def to_dict(self, market_prices: Dict[str, float] = None) -> dict:
        """转换为字典"""
        # 计算总市值和浮动盈亏
        total_market_value = 0
        total_floating_pl = 0

        if market_prices:
            for symbol, pos in self.positions.items():
                market_price = market_prices.get(symbol, pos.cost_price)
                market_value = market_price * pos.quantity
                floating_pl = (market_price - pos.cost_price) * pos.quantity
                total_market_value += market_value
                total_floating_pl += floating_pl

        total_value = self.available_cash + total_market_value
        floating_pl = total_floating_pl
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100

        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "initial_capital": self.initial_capital,
            "current_balance": self.current_balance,
            "available_cash": self.available_cash,
            "total_value": total_value,
            "floating_pl": floating_pl,
            "total_return": total_return,
            "positions_count": len(self.positions),
            "commission_rate": self.commission_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SimulationService:
    """模拟交易服务"""

    def __init__(self):
        self.accounts: Dict[str, SimulationAccount] = {}
        # 模拟市场价格（实际应该从数据源获取）
        self.market_prices: Dict[str, float] = {}

    def set_market_price(self, symbol: str, price: float):
        """设置市场价格（测试用）"""
        self.market_prices[symbol] = price

    def create_account(
        self,
        account_name: str,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025
    ) -> SimulationAccount:
        """创建账户"""
        account = SimulationAccount(account_name, initial_capital, commission_rate)
        self.accounts[account.account_id] = account
        return account

    def get_account(self, account_id: str) -> SimulationAccount:
        """获取账户"""
        if account_id not in self.accounts:
            raise ValueError(f"账户 {account_id} 不存在")
        return self.accounts[account_id]

    def list_accounts(self) -> List[SimulationAccount]:
        """获取所有账户"""
        return list(self.accounts.values())

    def delete_account(self, account_id: str):
        """删除账户"""
        if account_id in self.accounts:
            del self.accounts[account_id]

    def buy(
        self,
        account_id: str,
        symbol: str,
        price: float,
        quantity: int
    ) -> Trade:
        """买入"""
        account = self.get_account(account_id)
        # 如果没有设置市场价格，使用交易价格
        if symbol not in self.market_prices:
            self.market_prices[symbol] = price
        return account.buy(symbol, price, quantity)

    def sell(
        self,
        account_id: str,
        symbol: str,
        price: float,
        quantity: int
    ) -> Trade:
        """卖出"""
        account = self.get_account(account_id)
        if symbol not in self.market_prices:
            self.market_prices[symbol] = price
        return account.sell(symbol, price, quantity)

    def get_positions(self, account_id: str) -> dict:
        """获取持仓"""
        account = self.get_account(account_id)
        return account.get_positions(self.market_prices)

    def get_trades(self, account_id: str, limit: int = 20) -> dict:
        """获取交易历史"""
        account = self.get_account(account_id)
        trades = [t.to_dict() for t in account.trades[-limit:]]

        # 统计
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losing_trades = sum(1 for t in trades if t.get("pnl", 0) < 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)

        return {
            "account_id": account_id,
            "trades": trades,
            "total_count": len(account.trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_pnl": total_pnl
        }
```

**验收标准:**
- [ ] 账户创建正常
- [ ] 买入交易正常
- [ ] 卖出交易正常
- [ ] 持仓计算正确
- [ ] 交易历史记录正确
- [ ] 有完整的单元测试

---

#### 任务 3.3: 创建模拟交易路由
**文件:** `api_server/routers/simulation.py` (新建)

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from ..models.common import APIResponse
from ..models.simulation import (
    SimulationAccountCreate,
    TradeOrder,
    SimulationAccount,
    PositionsResponse,
    TradeResult
)
from ..services.simulation_service import SimulationService

simulation_router = APIRouter()

# 全局服务实例（生产环境应该用依赖注入）
SIMULATION_SERVICE = SimulationService()


@simulation_router.post("/simulation/account", response_model=APIResponse)
async def create_simulation_account(request: SimulationAccountCreate):
    """创建模拟账户"""
    try:
        account = SIMULATION_SERVICE.create_account(
            account_name=request.account_name,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )

        return APIResponse(
            data=account.to_dict(),
            message="账户创建成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建账户失败: {str(e)}")


@simulation_router.get("/simulation/account/{account_id}", response_model=APIResponse)
async def get_simulation_account(account_id: str):
    """获取账户信息"""
    try:
        account = SIMULATION_SERVICE.get_account(account_id)
        return APIResponse(
            data=account.to_dict(SIMULATION_SERVICE.market_prices),
            message="账户信息获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@simulation_router.get("/simulation/accounts", response_model=APIResponse)
async def list_simulation_accounts():
    """获取所有账户"""
    try:
        accounts = SIMULATION_SERVICE.list_accounts()
        return APIResponse(
            data=[acc.to_dict(SIMULATION_SERVICE.market_prices) for acc in accounts],
            message="账户列表获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")


@simulation_router.post("/simulation/buy", response_model=APIResponse)
async def buy_stock(request: TradeOrder):
    """买入股票"""
    try:
        trade = SIMULATION_SERVICE.buy(
            account_id=request.account_id,
            symbol=request.symbol,
            price=request.price,
            quantity=request.quantity
        )

        account = SIMULATION_SERVICE.get_account(request.account_id)

        return APIResponse(
            data=TradeResult(
                trade_id=trade.trade_id,
                account_id=request.account_id,
                symbol=request.symbol,
                action="buy",
                price=request.price,
                quantity=request.quantity,
                amount=trade.amount,
                commission=trade.commission,
                total_cost=trade.amount + trade.commission,
                timestamp=trade.timestamp,
                account_balance=account.current_balance
            ),
            message="买入成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"买入失败: {str(e)}")


@simulation_router.post("/simulation/sell", response_model=APIResponse)
async def sell_stock(request: TradeOrder):
    """卖出股票"""
    try:
        trade = SIMULATION_SERVICE.sell(
            account_id=request.account_id,
            symbol=request.symbol,
            price=request.price,
            quantity=request.quantity
        )

        account = SIMULATION_SERVICE.get_account(request.account_id)

        return APIResponse(
            data=TradeResult(
                trade_id=trade.trade_id,
                account_id=request.account_id,
                symbol=request.symbol,
                action="sell",
                price=request.price,
                quantity=request.quantity,
                amount=trade.amount,
                commission=trade.commission,
                pnl=trade.pnl,
                total_revenue=trade.amount - trade.commission,
                timestamp=trade.timestamp,
                account_balance=account.current_balance
            ),
            message="卖出成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卖出失败: {str(e)}")


@simulation_router.get("/simulation/positions/{account_id}", response_model=APIResponse)
async def get_positions(account_id: str):
    """获取持仓列表"""
    try:
        positions_data = SIMULATION_SERVICE.get_positions(account_id)
        return APIResponse(
            data=positions_data,
            message="持仓列表获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@simulation_router.get("/simulation/trades/{account_id}", response_model=APIResponse)
async def get_trades(account_id: str, limit: int = 20):
    """获取交易历史"""
    try:
        trades_data = SIMULATION_SERVICE.get_trades(account_id, limit=limit)
        return APIResponse(
            data=trades_data,
            message="交易历史获取成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易历史失败: {str(e)}")


@simulation_router.delete("/simulation/account/{account_id}", response_model=APIResponse)
async def delete_simulation_account(account_id: str):
    """删除账户"""
    try:
        SIMULATION_SERVICE.delete_account(account_id)
        return APIResponse(
            data={"account_id": account_id, "deleted_at": datetime.now().isoformat()},
            message="账户删除成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除账户失败: {str(e)}")
```

**验收标准:**
- [ ] 账户创建正常
- [ ] 账户查询正常
- [ ] 买入交易正常
- [ ] 卖出交易正常
- [ ] 持仓查询正常
- [ ] 交易历史查询正常
- [ ] 账户删除正常
- [ ] 所有端点都有错误处理
- [ ] 所有端点都有单元测试

---

#### 任务 3.4: 注册模拟交易路由
**文件:** `api_server/routers/__init__.py`

```python
# 添加导入
from .simulation import simulation_router

# 添加到 __all__
__all__ = [
    "health_router",
    "data_source_router",
    "stock_market_router",
    "portfolio_router",
    "analysis_router",
    "risk_control_router",
    "performance_router",
    "alerts_router",
    "backtest_router",
    "simulation_router"  # 新增
]
```

**文件:** `api_server/main.py`

```python
# 添加导入
from .routers import simulation_router

# 注册路由
app.include_router(simulation_router, prefix="/api/v1", tags=["模拟交易"])
```

**验收标准:**
- [ ] 路由成功注册
- [ ] `/docs` 页面可以看到模拟交易端点

---

### 阶段 4: 收益统计完善（预计 1 天）

#### 任务 4.1: 创建收益统计服务
**文件:** `api_server/services/performance_service.py` (新建)

```python
from typing import Dict, List
from datetime import datetime
from ..services.simulation_service import SimulationAccount, SimulationService


class PerformanceService:
    """收益统计服务"""

    def __init__(self, simulation_service: SimulationService):
        self.simulation_service = simulation_service

    def calculate_metrics(self, account: SimulationAccount) -> Dict:
        """计算绩效指标"""
        # 总收益
        total_return = account.current_balance - account.initial_capital
        total_return_pct = (total_return / account.initial_capital) * 100 if account.initial_capital > 0 else 0

        # 年化收益
        days = (datetime.now() - account.created_at).days
        if days < 1:
            days = 1  # 避免除零
        annualized_return = total_return_pct * (365 / days)

        # 交易统计
        sell_trades = [t for t in account.trades if t.action == "sell"]
        total_trades = len(sell_trades)

        winning_trades = sum(1 for t in sell_trades if t.pnl and t.pnl > 0)
        losing_trades = sum(1 for t in sell_trades if t.pnl and t.pnl < 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 盈亏比
        profits = [t.pnl for t in sell_trades if t.pnl and t.pnl > 0]
        losses = [abs(t.pnl) for t in sell_trades if t.pnl and t.pnl < 0]
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = avg_profit / avg_loss if avg_loss > 0 else 0

        # 持仓市值和浮动盈亏
        market_prices = self.simulation_service.market_prices
        total_market_value = 0
        total_floating_pl = 0

        for symbol, pos in account.positions.items():
            market_price = market_prices.get(symbol, pos.cost_price)
            market_value = market_price * pos.quantity
            floating_pl = (market_price - pos.cost_price) * pos.quantity
            total_market_value += market_value
            total_floating_pl += floating_pl

        total_value = account.available_cash + total_market_value

        return {
            "total_return": total_return_pct,
            "total_return_amount": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": 0.0,  # 需要历史数据计算
            "volatility": 0.0,     # 需要历史数据计算
            "sharpe_ratio": 0.0,   # 需要历史数据计算
            "sortino_ratio": 0.0,  # 需要历史数据计算
            "calmar_ratio": 0.0,   # 需要历史数据计算
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_holding_days": 0.0,  # 需要持仓历史计算
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_value": total_value,
            "total_market_value": total_market_value,
            "total_floating_pl": total_floating_pl
        }

    def get_account_performance(self, account_id: str) -> Dict:
        """获取账户收益汇总"""
        try:
            account = self.simulation_service.get_account(account_id)
            metrics = self.calculate_metrics(account)

            return {
                "account_id": account_id,
                "metrics": metrics,
                "time_period": {
                    "start_date": account.created_at.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "days": (datetime.now() - account.created_at).days
                }
            }
        except ValueError as e:
            raise ValueError(f"获取账户失败: {str(e)}")

    def get_positions_performance(self, account_id: str) -> Dict:
        """获取持仓收益分析"""
        try:
            account = self.simulation_service.get_account(account_id)
            market_prices = self.simulation_service.market_prices

            positions_analysis = []
            total_cost_basis = 0
            total_current_value = 0

            for symbol, pos in account.positions.items():
                market_price = market_prices.get(symbol, pos.cost_price)
                cost_basis = pos.cost_price * pos.quantity
                current_value = market_price * pos.quantity
                unrealized_pl = (market_price - pos.cost_price) * pos.quantity
                unrealized_pl_pct = (unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0
                days_held = (datetime.now() - datetime.fromisoformat(pos.entry_date)).days or 1
                annualized_return = unrealized_pl_pct * (365 / days_held)

                positions_analysis.append({
                    "symbol": symbol,
                    "quantity": pos.quantity,
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "unrealized_pl": unrealized_pl,
                    "unrealized_pl_pct": unrealized_pl_pct,
                    "days_held": days_held,
                    "annualized_return": annualized_return
                })

                total_cost_basis += cost_basis
                total_current_value += current_value

            total_unrealized_pl = total_current_value - total_cost_basis
            total_unrealized_pl_pct = (total_unrealized_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0

            return {
                "account_id": account_id,
                "positions_analysis": positions_analysis,
                "summary": {
                    "total_cost_basis": total_cost_basis,
                    "total_current_value": total_current_value,
                    "total_unrealized_pl": total_unrealized_pl,
                    "total_unrealized_pl_pct": total_unrealized_pl_pct
                }
            }
        except ValueError as e:
            raise ValueError(f"获取持仓分析失败: {str(e)}")

    def get_trades_performance(self, account_id: str) -> Dict:
        """获取交易绩效分析"""
        try:
            account = self.simulation_service.get_account(account_id)
            sell_trades = [t for t in account.trades if t.action == "sell"]

            if not sell_trades:
                return {
                    "account_id": account_id,
                    "trade_analysis": {
                        "total_trades": 0,
                        "buy_trades": len([t for t in account.trades if t.action == "buy"]),
                        "sell_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0.0,
                        "avg_win": 0.0,
                        "avg_loss": 0.0,
                        "profit_factor": 0.0,
                        "largest_win": 0.0,
                        "largest_loss": 0.0,
                        "avg_holding_days": 0.0,
                        "total_commission": sum(t.commission for t in account.trades)
                    },
                    "realized_pl": 0.0,
                    "commission_paid": sum(t.commission for t in account.trades),
                    "net_profit": 0.0
                }

            # 统计
            winning_trades = [t for t in sell_trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in sell_trades if t.pnl and t.pnl < 0]

            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(abs(t.pnl) for t in losing_trades) / len(losing_trades) if losing_trades else 0
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

            largest_win = max((t.pnl for t in sell_trades if t.pnl), default=0)
            largest_loss = min((t.pnl for t in sell_trades if t.pnl), default=0)

            total_commission = sum(t.commission for t in account.trades)
            realized_pl = sum(t.pnl for t in sell_trades if t.pnl)
            net_profit = realized_pl - total_commission

            return {
                "account_id": account_id,
                "trade_analysis": {
                    "total_trades": len(sell_trades),
                    "buy_trades": len([t for t in account.trades if t.action == "buy"]),
                    "sell_trades": len(sell_trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(losing_trades),
                    "win_rate": (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss,
                    "profit_factor": profit_factor,
                    "largest_win": largest_win,
                    "largest_loss": largest_loss,
                    "avg_holding_days": 0.0,  # 需要更复杂的逻辑
                    "total_commission": total_commission
                },
                "realized_pl": realized_pl,
                "commission_paid": total_commission,
                "net_profit": net_profit
            }
        except ValueError as e:
            raise ValueError(f"获取交易分析失败: {str(e)}")
```

**验收标准:**
- [ ] 收益指标计算正确
- [ ] 持仓分析正确
- [ ] 交易分析正确
- [ ] 有完整的单元测试

---

#### 任务 4.2: 完善收益统计路由
**文件:** `api_server/routers/performance.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.common import APIResponse
from ..models.performance import PerformanceResponse, PerformanceMetrics
from ..services.performance_service import PerformanceService
from ..services.simulation_service import SIMULATION_SERVICE

performance_router = APIRouter()

# 创建服务实例
PERFORMANCE_SERVICE = PerformanceService(SIMULATION_SERVICE)


@performance_router.get("/performance/account/{account_id}", response_model=APIResponse)
async def get_account_performance(account_id: str):
    """账户收益汇总"""
    try:
        result = PERFORMANCE_SERVICE.get_account_performance(account_id)
        return APIResponse(data=result, message="收益汇总获取成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收益汇总失败: {str(e)}")


@performance_router.get("/performance/positions/{account_id}", response_model=APIResponse)
async def get_positions_performance(account_id: str):
    """持仓收益分析"""
    try:
        result = PERFORMANCE_SERVICE.get_positions_performance(account_id)
        return APIResponse(data=result, message="持仓收益分析完成")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓分析失败: {str(e)}")


@performance_router.get("/performance/trades/{account_id}", response_model=APIResponse)
async def get_trades_performance(account_id: str):
    """交易绩效分析"""
    try:
        result = PERFORMANCE_SERVICE.get_trades_performance(account_id)
        return APIResponse(data=result, message="交易绩效分析完成")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易分析失败: {str(e)}")
```

**验收标准:**
- [ ] 收益汇总正常工作
- [ ] 持仓分析正常工作
- [ ] 交易分析正常工作
- [ ] 所有端点都有错误处理
- [ ] 所有端点都有单元测试

---

### 阶段 5: 集成测试和文档（预计 1 天）

#### 任务 5.1: 端到端测试

创建集成测试文件 `tests/api_server/test_integration.py`:

```python
import pytest
from fastapi.testclient import TestClient
from api_server.main import app

client = TestClient(app)


def test_complete_workflow():
    """完整工作流测试：创建账户 -> 买入 -> 卖出 -> 查看收益"""

    # 1. 创建模拟账户
    response = client.post(
        "/api/v1/simulation/account",
        json={"account_name": "测试账户", "initial_capital": 100000}
    )
    assert response.status_code == 200
    account_id = response.json()["data"]["account_id"]

    # 2. 买入股票
    response = client.post(
        "/api/v1/simulation/buy",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1850.0,
            "quantity": 10
        }
    )
    assert response.status_code == 200

    # 3. 卖出股票
    response = client.post(
        "/api/v1/simulation/sell",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1900.0,
            "quantity": 5
        }
    )
    assert response.status_code == 200

    # 4. 查看账户信息
    response = client.get(f"/api/v1/simulation/account/{account_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_return"] > 0

    # 5. 查看收益统计
    response = client.get(f"/api/v1/performance/account/{account_id}")
    assert response.status_code == 200

    # 6. 删除账户
    response = client.delete(f"/api/v1/simulation/account/{account_id}")
    assert response.status_code == 200


def test_backtest_workflow():
    """回测工作流测试"""

    # 1. 运行单股票回测
    response = client.post(
        "/api/v1/backtest/single",
        json={
            "symbol": "600519",
            "strategy": "vcp",
            "config": {
                "initial_capital": 100000,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        }
    )
    assert response.status_code == 200
    task_id = response.json()["data"]["task_id"]

    # 2. 获取回测结果
    response = client.get(f"/api/v1/backtest/result/{task_id}")
    assert response.status_code == 200

    # 3. 生成报告
    response = client.post(
        "/api/v1/backtest/report",
        json={"task_id": task_id, "format": "json"}
    )
    assert response.status_code == 200


def test_analysis_workflow():
    """技术分析工作流测试"""

    # 1. 五维共振分析
    response = client.post(
        "/api/v1/analysis/five-dimension",
        json={"symbol": "600519", "days": 120}
    )
    # 注意：这个测试需要数据库连接，可能需要 mock

    # 2. 策略分析
    response = client.get("/api/v1/analysis/strategies/600519?days=120")
    # 同样需要数据库

    # 3. 技术指标
    response = client.get("/api/v1/analysis/indicators/600519?indicator=macd&days=60")
    # 同样需要数据库
```

**验收标准:**
- [ ] 完整工作流测试通过
- [ ] 回测工作流测试通过
- [ ] 技术分析工作流测试通过（可能需要 mock 数据库）

---

#### 任务 5.2: 更新 API 文档

创建 `docs/API_REFERENCE.md`:

```markdown
# API 参考文档

## 基础信息

- **Base URL:** `http://localhost:8000/api/v1`
- **文档:** `http://localhost:8000/docs`
- **认证:** 无（全部公开）

## 目录

1. [技术分析 API](#技术分析-api)
2. [回测系统 API](#回测系统-api)
3. [模拟交易 API](#模拟交易-api)
4. [收益统计 API](#收益统计-api)

...（详细文档，参考设计文档）
```

**验收标准:**
- [ ] API 文档完整
- [ ] 包含所有端点
- [ ] 包含请求/响应示例

---

#### 任务 5.3: 编写使用示例

创建 `examples/api_usage.py`:

```python
"""
API 使用示例
演示如何使用所有 API 功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"


def example_simulation_trading():
    """模拟交易示例"""
    print("=== 模拟交易示例 ===")

    # 1. 创建账户
    response = requests.post(
        f"{BASE_URL}/simulation/account",
        json={"account_name": "示例账户", "initial_capital": 100000}
    )
    account_id = response.json()["data"]["account_id"]
    print(f"✅ 账户创建成功: {account_id}")

    # 2. 买入
    response = requests.post(
        f"{BASE_URL}/simulation/buy",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1850.0,
            "quantity": 10
        }
    )
    print("✅ 买入成功")

    # 3. 查看持仓
    response = requests.get(f"{BASE_URL}/simulation/positions/{account_id}")
    print(f"📊 持仓: {response.json()['data']}")

    # 4. 卖出
    response = requests.post(
        f"{BASE_URL}/simulation/sell",
        json={
            "account_id": account_id,
            "symbol": "600519",
            "price": 1900.0,
            "quantity": 5
        }
    )
    print("✅ 卖出成功")

    # 5. 查看收益
    response = requests.get(f"{BASE_URL}/performance/account/{account_id}")
    print(f"💰 收益: {response.json()['data']}")

    # 6. 删除账户
    requests.delete(f"{BASE_URL}/simulation/account/{account_id}")
    print("✅ 账户删除成功")


def example_backtest():
    """回测示例"""
    print("\n=== 回测示例 ===")

    # 运行回测
    response = requests.post(
        f"{BASE_URL}/backtest/single",
        json={
            "symbol": "600519",
            "strategy": "vcp",
            "config": {
                "initial_capital": 100000,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        }
    )
    task_id = response.json()["data"]["task_id"]
    print(f"✅ 回测任务创建: {task_id}")

    # 获取结果
    response = requests.get(f"{BASE_URL}/backtest/result/{task_id}")
    result = response.json()["data"]
    print(f"📈 年化收益: {result['performance']['annual_return']:.2f}%")


def example_technical_analysis():
    """技术分析示例"""
    print("\n=== 技术分析示例 ===")

    # 五维共振分析
    response = requests.post(
        f"{BASE_URL}/analysis/five-dimension",
        json={"symbol": "600519", "days": 120}
    )
    result = response.json()["data"]
    print(f"🎯 五维共振评分: {result['total_score']}/100")


if __name__ == "__main__":
    example_simulation_trading()
    example_backtest()
    example_technical_analysis()
```

**验收标准:**
- [ ] 示例代码可运行
- [ ] 涵盖所有主要功能
- [ ] 代码注释清晰

---

## 📊 验收标准总览

### 功能完整性
- [ ] 所有路由正常注册
- [ ] 所有端点返回正确格式
- [ ] 错误处理完善
- [ ] 数据验证正确

### 代码质量
- [ ] 符合 PEP 8 规范
- [ ] 函数单一职责
- [ ] 适当的注释和文档字符串
- [ ] 无重复代码

### 测试覆盖
- [ ] 单元测试覆盖所有服务
- [ ] 路由测试覆盖所有端点
- [ ] 集成测试覆盖主要工作流
- [ ] 测试覆盖率 >= 80%

### 文档
- [ ] API 参考文档完整
- [ ] 使用示例可运行
- [ ] 代码注释清晰

---

## 🚀 交付物

1. **代码文件**
   - `api_server/routers/backtest.py`
   - `api_server/routers/simulation.py`
   - `api_server/services/simulation_service.py`
   - `api_server/services/performance_service.py`
   - `api_server/models/backtest.py`
   - `api_server/models/simulation.py`

2. **测试文件**
   - `tests/api_server/test_backtest_router.py`
   - `tests/api_server/test_simulation_router.py`
   - `tests/api_server/test_simulation_service.py`
   - `tests/api_server/test_performance_service.py`
   - `tests/api_server/test_integration.py`

3. **文档文件**
   - `docs/API_REFERENCE.md`
   - `examples/api_usage.py`

4. **修改文件**
   - `api_server/main.py`
   - `api_server/routers/__init__.py`
   - `api_server/routers/analysis.py`
   - `api_server/routers/performance.py`

---

**实施计划完成 ✅**

请审核此实施计划，确认后我将开始编写代码！
