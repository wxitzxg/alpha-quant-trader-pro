# 配置系统迁移指南

## 概述

本文档说明如何从旧的分散配置迁移到新的统一配置系统。

## 迁移步骤

### 1. 了解新配置结构

新配置系统包含以下核心文件:

```
config/
├── config.yaml              # 统一配置文件 (YAML)
└── strategies.yaml          # 策略配置 (保持独立)

.env.example                 # 环境变量示例
common/config.py             # 配置核心实现
```

### 2. 配置字段映射

| 旧配置位置 | 新配置位置 | 说明 |
|-----------|-----------|------|
| `api_server/config.py` | `config/api_server` | API服务器配置 |
| `backtest/config.py` | `config/backtest` | 回测配置 |
| `common/config.py` | `config/` (顶层) | 数据库、日志等通用配置 |
| `simulate_trading/config/*.yaml` | `config/simulation` + 独立策略文件 | 模拟交易配置 |

### 3. 向后兼容

现有代码无需立即修改:

```python
# 旧代码仍然可以工作
from api_server.config import settings
print(settings.HOST)  # 自动从统一配置读取

from backtest.config import BacktestConfig
config = BacktestConfig()  # 自动从统一配置读取
```

### 4. 新代码使用方式

```python
# 推荐方式: 直接使用统一配置
from common.config import get_config

config = get_config()
print(config.api_server.host)
print(config.backtest.initial_capital)
print(config.database.url)
```

### 5. 环境变量迁移

旧的环境变量可以直接使用,使用双下划线格式:

```bash
# 旧方式 (仍然支持)
export DATABASE__URL=...

# 新方式 (推荐)
export DATABASE__URL=...
export API_SERVER__PORT=9000
export BACKTEST__INITIAL_CAPITAL=200000
```

## 验证迁移

运行以下命令验证配置加载:

```bash
python3 -c "from common.config import get_config; config = get_config(); print(f'环境: {config.environment}'); print(f'数据库: {config.database.url}')"
```

## 常见问题

### Q: 旧的配置文件需要删除吗?

**A**: 不需要。旧配置文件作为兼容层保留,会自动从统一配置读取。可以逐步迁移代码,最后再删除。

### Q: 如何覆盖特定环境的配置?

**A**: 创建环境特定的配置文件:

```bash
# 测试环境
cp config/config.yaml config/config.testing.yaml
# 修改测试配置...

# 生产环境
cp config/config.yaml config/config.production.yaml
# 修改生产配置...

# 设置环境变量
export APP_ENV=production
```

### Q: YAML 配置和环境变量冲突怎么办?

**A**: 环境变量优先级更高。如果需要强制使用 YAML 配置,删除对应的环境变量。

## 更多信息

- [配置完整指南](./02-configuration.md)
- [配置字段说明](./config-analysis.md)
