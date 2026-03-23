# 配置目录说明

## 目录结构

```
config/
├── config.yaml              # 统一配置入口（主要配置文件）
├── database.yaml            # 数据库配置（敏感信息为空）
├── app.yaml                 # 应用基础配置
├── api_server.yaml          # API服务器配置
├── portfolio.yaml           # 投资组合配置
├── stock_market.yaml        # 股票市场配置
├── backtest.yaml            # 回测配置
├── simulation.yaml          # 模拟交易配置
├── technical_analysis.yaml  # 技术分析配置
├── data_sources.yaml        # 数据源配置
├── fee.yaml                 # 手续费配置
├── loggin.yaml              # 日志配置
├── .gitignore              # 本地配置文件忽略规则
└── .env.example            # 本地配置示例
```

## 配置文件说明

### 主要配置文件

- **config.yaml**: 统一配置入口，引用其他配置文件
- **database.yaml**: 数据库连接配置（敏感信息通过环境变量设置）
- **\*.yaml**: 各模块独立配置文件

### 环境变量配置

敏感配置（如数据库连接字符串、API密钥等）应通过环境变量设置：

1. **复制模板**: `cp .env.example .env`
2. **编辑配置**: 修改 `.env` 文件，填入实际配置
3. **加载配置**: 应用启动时自动加载 `.env` 文件

详情请参考项目根目录的 `README.env.md`。

## 配置优先级

系统使用以下优先级（从高到低）：

1. **运行时参数** - 代码中直接传入的参数
2. **环境变量** - `.env` 文件或系统环境变量
3. **YAML 配置** - 本目录下的 YAML 文件
4. **默认值** - 配置模型中的默认值

## 安全注意事项

- **永远不要**将包含真实密码的配置文件提交到 Git
- **始终使用** `.env.example` 作为模板
- **敏感信息**应通过环境变量设置

## 本地配置

创建本地配置文件（不提交到 Git）：

```bash
# 开发环境
cp .env.example .env
# 编辑 .env，填入实际配置

# 测试环境  
cp .env.example .env.test
# 修改为测试配置
```

## 验证配置

运行配置检查脚本：

```bash
python3 config/check_config.py
```

