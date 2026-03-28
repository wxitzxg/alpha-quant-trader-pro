# 股票推荐功能实现计划

## 概述

实现股票推荐功能，支持短线和中长线两种策略，基于多维度技术指标和基本面数据进行综合评分。

## 实现步骤

### Phase 1: 基础设施搭建

#### 1.1 创建模块目录结构
- [ ] 创建 `stock_recommendation/` 模块目录
- [ ] 创建子目录: `engines/`, `strategies/`, `services/`, `routers/`
- [ ] 创建各目录的 `__init__.py`

#### 1.2 创建配置文件
- [ ] 创建 `config/recommendation.yaml` 配置文件
- [ ] 更新 `common/config.py` 支持加载推荐配置

#### 1.3 创建数据模型
- [ ] 创建 `stock_recommendation/models.py`
  - `ScanRequest` - 扫描请求模型
  - `ScanResult` - 扫描结果模型
  - `StockRecommendation` - 单只股票推荐结果
  - `AnalysisDetail` - 分析详情模型

### Phase 2: 策略配置模块

#### 2.1 创建策略配置
- [ ] 创建 `stock_recommendation/strategies/strategy_config.py`
  - 短线策略参数 (RSI、KDJ、MACD、布林带等)
  - 中长线策略参数 (趋势、基本面、估值等)
  - 评分权重配置
  - 过滤规则配置

### Phase 3: 选股引擎实现

#### 3.1 创建基类选择器
- [ ] 创建 `stock_recommendation/engines/base_selector.py`
  - `BaseSelector` 抽象基类
  - 公共方法: `_get_rating()`, `_convert_to_json_safe()`, `_calc_trade_points()`
  - 抽象方法: `analyze_single_stock()`

#### 3.2 实现短线选股引擎
- [ ] 创建 `stock_recommendation/engines/short_term_selector.py`
  - `ShortTermSelector` 类
  - RSI评分 (20分)
  - KDJ评分 (20分)
  - MACD评分 (15分)
  - 布林带评分 (15分)
  - 量价异动评分 (15分)
  - 资金流向评分 (15分)
  - 买入/卖出信号生成
  - ATR动态止损止盈

#### 3.3 实现中长线选股引擎
- [ ] 创建 `stock_recommendation/engines/long_term_selector.py`
  - `LongTermSelector` 类
  - 趋势评分 (30分)
  - 基本面评分 (30分): ROE、利润增长、股息率
  - 估值评分 (15分): PEG估值
  - 动量评分 (15分)
  - 量能评分 (15分)
  - DMI评分 (15分)
  - 资金流评分 (10分)
  - 买入/卖出信号生成

### Phase 4: 服务层实现

#### 4.1 创建推荐服务
- [ ] 创建 `stock_recommendation/services/recommendation_service.py`
  - `RecommendationService` 类
  - `scan_stocks()` - 扫描股票池
  - `analyze_stock()` - 分析单只股票
  - `get_stock_pool()` - 获取股票池
  - `apply_filters()` - 应用过滤规则
  - 并行处理优化

### Phase 5: API路由实现

#### 5.1 创建推荐路由
- [ ] 创建 `stock_recommendation/routers/recommendation.py`
  - `POST /api/recommendation/scan` - 扫描推荐
  - `GET /api/recommendation/analyze/{stock_code}` - 分析单只
  - `GET /api/recommendation/strategies` - 获取策略列表
  - `GET /api/recommendation/config` - 获取配置
  - `PUT /api/recommendation/config` - 更新配置

#### 5.2 注册路由
- [ ] 更新 `api_server/routers/__init__.py` 注册新路由
- [ ] 更新 `api_server/main.py` 引入路由

### Phase 6: 数据源集成

#### 6.1 集成资金流向数据
- [ ] 确认 `data_sources/aggregator.py` 资金流向接口
- [ ] 如需扩展，添加资金流向获取方法

#### 6.2 集成基本面数据
- [ ] 确认 `FinancialService` 接口可用
- [ ] 封装基本面数据获取方法

### Phase 7: 测试

#### 7.1 单元测试
- [ ] 创建 `tests/stock_recommendation/` 目录
- [ ] 测试短线选股引擎评分逻辑
- [ ] 测试中长线选股引擎评分逻辑
- [ ] 测试过滤规则

#### 7.2 集成测试
- [ ] 测试API接口
- [ ] 测试完整扫描流程

## 文件清单

| 文件路径 | 说明 |
|----------|------|
| `stock_recommendation/__init__.py` | 模块入口 |
| `stock_recommendation/models.py` | 数据模型 |
| `stock_recommendation/engines/__init__.py` | 引擎模块入口 |
| `stock_recommendation/engines/base_selector.py` | 基类选择器 |
| `stock_recommendation/engines/short_term_selector.py` | 短线选股引擎 |
| `stock_recommendation/engines/long_term_selector.py` | 中长线选股引擎 |
| `stock_recommendation/strategies/__init__.py` | 策略模块入口 |
| `stock_recommendation/strategies/strategy_config.py` | 策略配置 |
| `stock_recommendation/services/__init__.py` | 服务模块入口 |
| `stock_recommendation/services/recommendation_service.py` | 推荐服务 |
| `stock_recommendation/routers/__init__.py` | 路由模块入口 |
| `stock_recommendation/routers/recommendation.py` | 推荐路由 |
| `config/recommendation.yaml` | 配置文件 |

## 依赖复用

| 现有模块 | 复用内容 |
|----------|----------|
| `technical_analysis/indicators/base_indicators.py` | RSI、MACD、布林带、ATR等指标计算 |
| `api_server/services/financial_service.py` | ROE、利润增长、PE等基本面数据 |
| `stock_market/repositories/` | K线数据、股票信息 |
| `data_sources/aggregator.py` | 资金流向数据 |

## 风险点

1. **性能问题**: 全市场扫描3500+股票可能耗时较长，需要并行处理
2. **数据依赖**: 部分股票可能缺少基本面数据，需要优雅降级
3. **API限流**: 数据源可能有请求频率限制，需要控制并发数
