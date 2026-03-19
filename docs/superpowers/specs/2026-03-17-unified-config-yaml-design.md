# 统一配置系统设计方案

**文档版本**: 1.0
**创建日期**: 2026-03-17
**作者**: AI Assistant
**状态**: ✅ 已批准

---

## 一、设计概述

### 1.1 目标

将现有基于JSON的配置系统迁移为**基于YAML的全局统一配置系统**，集中管理所有模块的配置。

### 1.2 设计原则

- ✅ **单文件设计** - 一个 `config.yaml` 包含所有配置
- ✅ **环境分离** - 支持多环境配置文件（development/production/testing）
- ✅ **环境变量优先** - 运行时参数 > 环境变量 > YAML配置 > 默认值
- ✅ **启动时加载** - 应用启动时立即加载，配置错误早期发现
- ✅ **基础验证** - 必需字段检查、类型验证、清晰的错误提示
- ✅ **无热重载** - 配置文件改动少，启动时加载一次即可
- ✅ **Pydantic驱动** - 强大的数据验证和自动生成文档

### 1.3 技术栈

- **YAML解析**: `pyyaml>=6.0`
- **数据验证**: `pydantic>=2.0.0`
- **设置管理**: `pydantic-settings>=2.0.0`

---

## 二、配置文件结构

### 2.1 目录结构

```
config/
├── config.yaml                 # 默认配置（开发环境）
├── config.development.yaml     # 开发环境配置
├── config.production.yaml      # 生产环境配置
├── config.testing.yaml         # 测试环境配置
└── config.example.yaml         # 配置示例（带完整注释）
```

### 2.2 配置文件加载逻辑

```python
# 通过环境变量 APP_ENV 选择配置文件
# APP_ENV=production → 加载 config.production.yaml
# APP_ENV未设置 → 加载 config.yaml（默认为development）

# 配置优先级（从高到低）：
# 1. 运行时参数（代码中直接传入）
# 2. 环境变量（DATABASE_URL, DEBUG 等）
# 3. YAML配置文件
# 4. 代码中的默认值
```

### 2.3 环境变量命名规则

环境变量使用双下划线 `__` 作为嵌套分隔符：

```bash
# 基础配置
APP_NAME="my-app"
DEBUG="true"
ENVIRONMENT="production"

# 嵌套配置
DATABASE__URL="postgresql://user:pass@host:5432/db"
DATABASE__POOL_SIZE="20"

# 运行环境选择
APP_ENV="production"
```

---

## 三、YAML配置文件详细结构

### 3.1 核心配置项（app部分）

```yaml
# ==================== 应用配置 ====================
app:
  # 应用名称
  name: "alpha-quant-trader-pro"

  # 调试模式
  # true: 启用详细日志、开发工具
  # false: 生产环境，性能优化
  debug: false

  # 运行环境
  # development: 开发环境
  # testing: 测试环境
  # staging: 预发布环境
  # production: 生产环境
  environment: "development"

  # 时区设置
  timezone: "Asia/Shanghai"
```

### 3.2 数据库配置（database部分）

```yaml
# ==================== 数据库配置 ====================
database:
  # 数据库连接URL
  # 格式: postgresql://用户名:密码@主机:端口/数据库名
  url: "postgresql://postgres:postgres@localhost:5432/stock_market"

  # 连接池大小
  # 同时保持的数据库连接数量
  # 范围: >= 1
  pool_size: 10

  # 最大溢出连接数
  # 超过pool_size后，额外允许的连接数
  # 范围: >= 0
  max_overflow: 20

  # 连接预检
  # 每次使用连接前检查连接是否有效
  pool_pre_ping: true

  # 连接回收时间（秒）
  # 超过此时间的连接会被回收重建
  # 范围: >= 0
  pool_recycle: 3600

  # 连接超时时间（秒）
  # 数据库连接超时时间
  # 范围: >= 1
  connect_timeout: 30
```

### 3.3 数据源配置（data_sources部分）

```yaml
# ==================== 数据源配置 ====================
data_sources:
  # 默认请求超时（秒）
  # 范围: >= 1
  timeout: 10

  # 最大重试次数
  # 范围: >= 0
  max_retries: 3

  # 重试延迟（秒）
  # 范围: >= 0
  retry_delay: 0.5

  # 是否记录失败日志
  log_failures: true

  # 数据源列表
  sources:
    # ====== 行情数据源 ======
    realtime:
      - name: "sina"           # 源名称
        priority: 10           # 优先级（数字越小优先级越高）
        enabled: true          # 是否启用
        timeout: 3             # 该源的特定超时时间（秒）

      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 5

      - name: "tushare"
        priority: 30
        enabled: true
        timeout: 5

    # ====== K线数据源 ======
    kline:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 10

      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 10

      - name: "sina"
        priority: 30
        enabled: true
        timeout: 5

    # ====== 基本面数据源 ======
    fundamentals:
      - name: "tushare"
        priority: 10
        enabled: true
        timeout: 15

      - name: "akshare"
        priority: 20
        enabled: true
        timeout: 15
```

### 3.4 手续费配置（fee部分）

```yaml
# ==================== 手续费配置 ====================
fee:
  # 印花税
  # 卖出时收取，买入不收
  # 范围: 0-1
  stamp_duty: 0.001  # 0.1%

  # 交易所费用
  # 买卖双向收取
  # 范围: 0-1
  exchange_fee: 0.00002  # 0.002%

  # 券商佣金
  # 买卖双向收取
  # 范围: 0-1
  broker_commission: 0.0003  # 0.03%

  # 最低佣金
  # 单笔交易佣金低于此值时，按此值收取
  # 范围: >= 0
  min_commission: 5.0  # 5元
```

### 3.5 日志配置（logging部分）

```yaml
# ==================== 日志配置 ====================
logging:
  # 日志级别
  # DEBUG: 详细调试信息
  # INFO: 一般信息
  # WARNING: 警告信息
  # ERROR: 错误信息
  # CRITICAL: 严重错误
  level: "INFO"

  # 日志格式
  # %(asctime)s: 时间戳
  # %(name)s: 记录器名称
  # %(levelname)s: 日志级别
  # %(message)s: 日志消息
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

  # 日志文件路径（可选）
  # 留空则输出到控制台
  file_path: ""

  # 日志文件大小限制（MB）
  # 范围: >= 1
  max_file_size: 100

  # 保留的旧日志文件数量
  # 范围: >= 0
  backup_count: 5
```

### 3.6 股票市场配置（stock_market部分）

```yaml
# ==================== 股票市场配置 ====================
stock_market:
  # 数据同步配置
  sync:
    # 是否启用增量同步
    incremental: true

    # 并发同步数量
    # 同时同步的股票数量
    # 范围: >= 1
    concurrency: 5

    # 同步批次大小
    batch_size: 100

    # 同步间隔（秒）
    interval: 60

  # 数据保留策略
  data_retention:
    # K线数据保留天数
    # 0表示永久保留
    # 范围: >= 0
    kline_days: 365

    # 基本面数据保留天数
    fundamentals_days: 1825  # 5年

  # 市场交易时间
  trading_hours:
    # A股开盘时间（上午）
    morning_open: "09:30"

    # A股收盘时间（上午）
    morning_close: "11:30"

    # A股开盘时间（下午）
    afternoon_open: "13:00"

    # A股收盘时间（下午）
    afternoon_close: "15:00"
```

### 3.7 投资组合配置（portfolio部分）

```yaml
# ==================== 投资组合配置 ====================
portfolio:
  # 交易配置
  trading:
    # 默认交易金额（元）
    default_amount: 10000

    # 最小交易金额（元）
    min_amount: 1000

    # 单笔最大持仓比例（0-1）
    max_position_ratio: 0.3  # 30%

  # 风险控制
  risk:
    # 单笔最大亏损比例（0-1）
    max_loss_ratio: 0.05  # 5%

    # 总资产最大回撤比例（0-1）
    max_drawdown_ratio: 0.15  # 15%

  # 账户配置
  account:
    # 初始资金（元）
    initial_capital: 1000000

    # 可用资金比例（0-1）
    available_ratio: 0.9  # 90%
```

### 3.8 技术分析配置（technical_analysis部分）

```yaml
# ==================== 技术分析配置 ====================
technical_analysis:
  # 计算配置
  calculation:
    # 并发计算数量
    concurrency: 4

    # 缓存有效期（秒）
    cache_ttl: 3600  # 1小时

  # 指标参数
  indicators:
    # 移动平均线
    ma:
      periods: [5, 10, 20, 60]  # 周期列表

    # 相对强弱指标
    rsi:
      period: 14  # 计算周期

    # 随机指标
    kdj:
      fast_k: 9   # 快速K周期
      slow_k: 3   # 慢速K周期
      slow_d: 3   # 慢速D周期

    # 布林带
    bollinger:
      period: 20      # 计算周期
      std_dev: 2.0    # 标准差倍数

    # 量价通道（VCP）
    vcp:
      consolidation_periods: 5  # 盘整期数
      breakout_threshold: 0.05   # 突破阈值（5%）

    # TD序列
    td_sequential:
      setup_period: 9      # 建仓周期
      countdown_period: 13  # 倒计时周期
```

---

## 四、配置系统代码实现

### 4.1 依赖要求

在 `requirements.txt` 中添加：

```txt
pyyaml>=6.0                  # YAML解析
pydantic>=2.0.0              # 数据验证和设置管理
pydantic-settings>=2.0.0     # Pydantic设置管理
```

### 4.2 配置类代码

详见 `common/config.py` 实现。

### 4.3 使用示例

```python
# 方式1：获取全局配置
from common.config import get_config

config = get_config()
print(f"App: {config.app_name}")
print(f"DB: {config.database.url}")

# 方式2：环境变量覆盖
import os
os.environ["DEBUG"] = "true"
from common.config import reload_config
reload_config()
config = get_config()
print(f"Debug: {config.debug}")  # True

# 方式3：运行时参数覆盖
from common.config import Config
config = Config(debug=True, app_name="custom-app")

# 方式4：保存配置到文件
config.save_to_file("config/custom.yaml")
```

---

## 五、迁移路径

### 5.1 迁移步骤

#### 阶段1：创建YAML配置系统（第1天）
1. 创建新的 `common/config.py`（YAML版本）
2. 添加 `pyyaml` 依赖到 `requirements.txt`
3. 创建 `config.example.yaml` 示例文件
4. 创建 `config.yaml` 默认配置文件

#### 阶段2：平滑迁移（第2-3天）
1. 保留现有 `common/config.py`（JSON版本），重命名为 `common/config_legacy.py`
2. 新代码使用新的YAML配置系统
3. 旧代码继续使用JSON配置系统（向后兼容）
4. 提供配置转换工具：`scripts/convert_config.py`

#### 阶段3：全面切换（第4-5天）
1. 将所有旧代码迁移到新的YAML配置系统
2. 删除 `common/config_legacy.py`
3. 删除旧的JSON配置文件（`config/default.json`, `config/sources.json`）

#### 阶段4：清理和文档（第6天）
1. 从 `requirements.txt` 中移除不再需要的依赖
2. 更新文档：`docs/CONFIG_GUIDE.md`
3. 更新示例代码：`examples/config_example.py`

### 5.2 配置转换工具

```python
# scripts/convert_config.py
"""
将JSON配置文件转换为YAML格式
"""

import json
import yaml
from pathlib import Path

def convert_json_to_yaml(json_file: str, yaml_file: str):
    """转换JSON配置到YAML"""
    # 读取JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 写入YAML
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"✓ 转换完成: {json_file} → {yaml_file}")
```

---

## 六、测试方案

### 6.1 单元测试

覆盖以下场景：
- ✅ 加载默认配置
- ✅ 加载自定义配置文件
- ✅ 环境变量覆盖
- ✅ 运行时参数覆盖
- ✅ 配置验证（必需字段、类型检查）
- ✅ 配置保存
- ✅ 配置管理器单例模式

### 6.2 集成测试

- ✅ 配置与数据库集成
- ✅ 配置与数据源集成
- ✅ 配置与日志系统集成

### 6.3 验收测试

完整的配置工作流测试，包括加载、覆盖、保存、重载等操作。

---

## 七、交付物清单

| 序号 | 文件/组件 | 说明 | 优先级 |
|-----|----------|------|--------|
| 1 | `common/config.py` | 配置系统核心代码 | 🔴 高 |
| 2 | `requirements.txt` | 添加 pyyaml 依赖 | 🔴 高 |
| 3 | `config/config.yaml` | 默认配置文件 | 🔴 高 |
| 4 | `config/config.production.yaml` | 生产环境配置 | 🟡 中 |
| 5 | `config/config.example.yaml` | 完整示例配置（带注释） | 🟡 中 |
| 6 | `tests/test_config.py` | 单元测试 | 🔴 高 |
| 7 | `docs/CONFIG_GUIDE.md` | 配置指南文档 | 🟡 中 |
| 8 | `scripts/convert_config.py` | JSON转YAML工具 | 🟢 低 |
| 9 | `examples/config_example.py` | 使用示例 | 🟡 中 |

---

## 八、风险评估和缓解措施

### 8.1 风险点

| 风险 | 严重性 | 概率 | 缓解措施 |
|-----|--------|------|----------|
| 旧代码兼容性问题 | 高 | 中 | 保留旧配置系统并行运行 |
| 配置文件格式错误 | 中 | 低 | Pydantic强验证 + 单元测试 |
| 环境变量冲突 | 低 | 低 | 清晰的命名规范和文档 |
| 性能影响 | 低 | 低 | 启动时加载，无运行时开销 |

### 8.2 回滚方案

如果迁移过程中遇到问题：
1. 恢复 `common/config_legacy.py`
2. 切换回JSON配置文件
3. 旧代码无需修改即可正常运行

---

## 九、后续优化方向

1. **配置加密** - 敏感字段加密存储（可选）
2. **配置热重载** - 支持运行时重载（可选）
3. **配置UI** - Web界面管理配置（远期）
4. **配置审计** - 配置变更日志（远期）

---

## 十、审批记录

| 日期 | 审批人 | 状态 | 备注 |
|-----|--------|------|------|
| 2026-03-17 | 用户确认 | ✅ 批准 | 设计方案已确认 |

---

**文档结束**
