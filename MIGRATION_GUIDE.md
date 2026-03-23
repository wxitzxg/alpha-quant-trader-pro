# 配置迁移指南

## 概述

本次迁移将数据库配置从 YAML 文件移动到环境变量，提高安全性并支持多环境部署。

## 变更内容

### 1. 配置文件变更

**config/database.yaml**
- 将 `url` 字段改为空字符串
- 添加配置说明注释

**新增文件**
- `.env.example` - 环境变量模板（提交到 Git）
- `.env` - 开发环境配置（不提交）
- `.env.test` - 测试环境配置（不提交）
- `README.env.md` - 环境变量配置指南
- `config/.gitignore` - 配置目录忽略规则
- `config/config.yaml` - 统一配置入口

### 2. .gitignore 更新

添加以下忽略规则：
```
.env
.env.local
.env.*.local
.env.test
.env.production
config/local.yaml
config/config.local.yaml
```

## 迁移步骤

### 开发环境

1. **备份现有配置**（如果需要）
   ```bash
   cp config/database.yaml config/database.yaml.backup
   ```

2. **创建 .env 文件**
   ```bash
   cp .env.example .env
   # 编辑 .env，填入实际的数据库配置
   ```

3. **验证配置**
   ```bash
   python3 -c "from common.config import get_config; print(get_config().database.url)"
   ```

### 测试环境

1. **创建 .env.test 文件**
   ```bash
   cp .env.example .env.test
   # 修改为测试数据库配置
   ```

2. **运行测试**
   ```bash
   python3 -m pytest tests/ -v
   ```

### 生产环境

1. **创建 .env.production 文件**
   ```bash
   cp .env.example .env.production
   # 填入生产环境的真实配置
   ```

2. **部署应用**
   ```bash
   # 确保 .env.production 被正确加载
   ```

## 验证清单

- [ ] `.env.example` 已提交到 Git
- [ ] `.env` 和 `.env.test` 未提交到 Git
- [ ] `config/database.yaml` 中的 URL 字段为空
- [ ] 从 `.env` 能正确加载数据库配置
- [ ] 测试环境使用独立的数据库
- [ ] 所有测试通过

## 常见问题

### Q: 为什么数据库 URL 从 YAML 移除？

A: 数据库连接字符串包含敏感信息（用户名、密码），不应该提交到版本控制。

### Q: 如何在不同环境使用不同配置？

A: 创建不同的 .env 文件（.env.development, .env.production），通过环境变量 APP_ENV 或手动指定。

### Q: 配置优先级是什么？

A: 运行时参数 > 环境变量 > YAML 配置 > 默认值

## 回滚方案

如果需要回滚：

1. 恢复 config/database.yaml
   ```bash
   git checkout config/database.yaml
   ```

2. 删除环境变量文件（如果不需要）
   ```bash
   rm .env .env.test
   ```

3. 恢复 .gitignore
   ```bash
   git checkout .gitignore
   ```
