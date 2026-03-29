# 账户资金计算优化实施计划

## 概述

基于设计文档 `docs/superpowers/specs/2026-03-29-account-capital-design.md` 实施账户资金计算优化。

## 实施阶段

### Phase 1: 数据模型层（基础设施）

**目标**: 建立数据表和 Repository 层

#### Step 1.1: 修改数据库模型
- 文件: `portfolio_manager/database.py`
- 任务:
  - [ ] 修改 `CashBalance` 模型，新增 `initial_capital` 字段
  - [ ] 新增 `CapitalAdjustment` 模型

#### Step 1.2: 新建 Repository
- 文件: `portfolio_manager/repositories/capital_repository.py`（新建）
- 任务:
  - [ ] 创建 `CapitalAdjustmentRepository` 类
  - [ ] 实现 `get_all()`、`add()`、`get_sum()` 方法

#### Step 1.3: 导出 Repository
- 文件: `portfolio_manager/repositories/__init__.py`
- 任务:
  - [ ] 导出 `CapitalAdjustmentRepository`

### Phase 2: Schema 层（数据验证）

**目标**: 定义 API 请求/响应模型

#### Step 2.1: 新建 Capital Schemas
- 文件: `portfolio_manager/schemas/capital_schemas.py`（新建）
- 任务:
  - [ ] 创建 `AdjustmentType` 枚举
  - [ ] 创建 `CapitalAdjustRequest` 请求模型
  - [ ] 创建 `CapitalAdjustResponse` 响应模型
  - [ ] 创建 `CapitalAdjustmentItem` 和 `CapitalAdjustmentHistory` 模型

#### Step 2.2: 导出 Schemas
- 文件: `portfolio_manager/schemas/__init__.py`
- 任务:
  - [ ] 导出 `capital_schemas` 模块

#### Step 2.3: 更新 AccountSummary 模型
- 文件: `portfolio_manager/models.py`
- 任务:
  - [ ] 新增 `initial_capital` 字段
  - [ ] 新增 `total_pl` 字段

### Phase 3: 服务层（业务逻辑）

**目标**: 实现核心业务逻辑

#### Step 3.1: 新建 CapitalService
- 文件: `portfolio_manager/capital_service.py`（新建）
- 任务:
  - [ ] 实现 `adjust_capital()` 方法
  - [ ] 实现 `get_initial_capital()` 方法
  - [ ] 实现 `get_adjustment_history()` 方法
  - [ ] 实现大额操作确认逻辑

#### Step 3.2: 更新 AccountService
- 文件: `portfolio_manager/account_service.py`
- 任务:
  - [ ] 修改 `get_account_summary()` 方法
  - [ ] 集成 `CapitalService` 获取初始资金
  - [ ] 计算总盈亏

### Phase 4: API 层（接口暴露）

**目标**: 暴露 REST API

#### Step 4.1: 更新 API 响应模型
- 文件: `api_server/models/portfolio.py`
- 任务:
  - [ ] 新增 `initial_capital` 字段
  - [ ] 新增 `total_pl` 字段
  - [ ] 新增 `stock_market_value` 字段

#### Step 4.2: 更新 PortfolioService
- 文件: `api_server/services/portfolio_service.py`
- 任务:
  - [ ] 修改 `get_account_summary()` 返回值
  - [ ] 新增 `adjust_capital()` 方法
  - [ ] 新增 `get_capital_history()` 方法

#### Step 4.3: 新增 API 路由
- 文件: `api_server/routers/portfolio.py`
- 任务:
  - [ ] 新增 `POST /account/capital/adjust` 路由
  - [ ] 新增 `GET /account/capital/history` 路由

### Phase 5: 测试

**目标**: 确保功能正确性

#### Step 5.1: 单元测试
- 文件: `tests/portfolio_manager/test_capital.py`（新建）
- 任务:
  - [ ] 测试转入成功
  - [ ] 测试转出成功
  - [ ] 测试转出余额不足
  - [ ] 测试金额验证（0、负数）
  - [ ] 测试初始资金汇总
  - [ ] 测试总盈亏计算

### Phase 6: 迁移脚本

**目标**: 支持现有数据迁移

#### Step 6.1: 迁移脚本
- 文件: `scripts/migrate_capital.py`（新建）
- 任务:
  - [ ] 实现 `migrate()` 函数
  - [ ] 实现 `rollback()` 函数

## 依赖关系

```
Phase 1 (数据模型)
    ↓
Phase 2 (Schema) ←→ Phase 3 (服务层)
    ↓
Phase 4 (API 层)
    ↓
Phase 5 (测试)
    ↓
Phase 6 (迁移脚本)
```

## 执行顺序

1. Phase 1 → Phase 2（可并行）
2. Phase 3（依赖 Phase 1、2）
3. Phase 4（依赖 Phase 3）
4. Phase 5（依赖 Phase 4）
5. Phase 6（可独立执行）

## 预计文件变更

| 操作 | 文件数 |
|------|--------|
| 新建 | 5 |
| 修改 | 8 |
| 总计 | 13 |
