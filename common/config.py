"""
统一的 YAML 配置管理系统

配置优先级：运行时参数 > 环境变量 > YAML配置 > 默认值
Configuration priority: runtime params > env vars > YAML > defaults
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

logger = logging.getLogger(__name__)


# ========== 嵌套配置模型 ==========

class DatabaseConfig(BaseModel):
    """数据库配置 / Database configuration"""
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/stock_market",
        description="数据库连接URL / Database connection URL"
    )
    pool_size: int = Field(default=10, ge=1, description="连接池大小 / Connection pool size")
    max_overflow: int = Field(default=20, ge=0, description="最大溢出连接数 / Max overflow connections")
    pool_pre_ping: bool = Field(default=True, description="连接预检 / Connection pre-ping")
    pool_recycle: int = Field(default=3600, ge=0, description="连接回收时间（秒）/ Connection recycle time (seconds)")
    connect_timeout: int = Field(default=30, ge=1, description="连接超时时间（秒）/ Connection timeout (seconds)")


class DataSourceItem(BaseModel):
    """数据源配置项 / Data source configuration item"""
    name: str = Field(..., description="数据源名称 / Data source name")
    priority: int = Field(100, ge=0, description="优先级，越小越优先 / Priority, smaller is higher")
    enabled: bool = Field(True, description="是否启用 / Enabled")
    timeout: int = Field(5, ge=1, description="超时时间（秒）/ Timeout (seconds)")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        allowed = ['sina', 'akshare', 'tushare', 'investoday']
        if v not in allowed:
            raise ValueError(f"name must be one of {allowed}")
        return v


class DataSourcesConfig(BaseModel):
    """数据源优先级配置 / Data sources priority configuration"""
    realtime: List[DataSourceItem] = Field(default_factory=list, description="实时行情数据源 / Realtime quote sources")
    kline: List[DataSourceItem] = Field(default_factory=list, description="K线数据源 / K-line sources")
    fundamentals: List[DataSourceItem] = Field(default_factory=list, description="基本面数据源 / Fundamentals sources")
    tech_indicators: List[DataSourceItem] = Field(default_factory=list, description="技术指标数据源 / Technical indicators sources")
    fund_flows: List[DataSourceItem] = Field(default_factory=list, description="资金流向数据源 / Fund flows sources")
    dragon_tiger: List[DataSourceItem] = Field(default_factory=list, description="龙虎榜数据源 / Dragon tiger sources")
    valuation: List[DataSourceItem] = Field(default_factory=list, description="估值指标数据源 / Valuation sources")
    per_share_indicators: List[DataSourceItem] = Field(default_factory=list, description="每股指标数据源 / Per share indicators sources")
    osc_indicators: List[DataSourceItem] = Field(default_factory=list, description="超买超卖指标数据源 / Oscillators sources")
    price_vol_ind: List[DataSourceItem] = Field(default_factory=list, description="量价指标数据源 / Price-volume indicators sources")
    limit_up_down: List[DataSourceItem] = Field(default_factory=list, description="涨跌停数据源 / Limit up/down sources")
    turnover_rates: List[DataSourceItem] = Field(default_factory=list, description="换手率数据源 / Turnover rates sources")
    fund_quotes: List[DataSourceItem] = Field(default_factory=list, description="基金净值数据源 / Fund quotes sources")
    dupont_analysis: List[DataSourceItem] = Field(default_factory=list, description="杜邦分析数据源 / Dupont analysis sources")


class DataSourceConfig(BaseModel):
    """数据源配置 / Data source configuration"""
    timeout: int = Field(default=10, ge=1, description="默认请求超时（秒）/ Default timeout (seconds)")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数 / Max retry attempts")
    retry_delay: float = Field(default=0.5, ge=0, description="重试延迟（秒）/ Retry delay (seconds)")
    log_failures: bool = Field(default=True, description="是否记录失败日志 / Log failures")
    sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig, description="数据源列表 / Data sources list")
    fallback: Dict[str, Any] = Field(default_factory=dict, description="降级配置 / Fallback configuration")


class FeeConfig(BaseModel):
    """手续费配置 / Fee configuration"""
    stamp_duty: float = Field(default=0.001, ge=0, le=1, description="印花税 / Stamp duty")
    exchange_fee: float = Field(default=0.00002, ge=0, le=1, description="交易所费用 / Exchange fee")
    broker_commission: float = Field(default=0.0003, ge=0, le=1, description="券商佣金 / Broker commission")
    min_commission: float = Field(default=5.0, ge=0, description="最低佣金（元）/ Minimum commission (CNY)")


class LoggingConfig(BaseModel):
    """日志配置 / Logging configuration"""
    level: str = Field(default="INFO", description="日志级别 / Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式 / Log format"
    )
    file_path: str = Field(default="", description="日志文件路径（可选）/ Log file path (optional)")
    max_file_size: int = Field(default=100, ge=1, description="日志文件大小限制（MB）/ Log file size limit (MB)")
    backup_count: int = Field(default=5, ge=0, description="保留的旧日志文件数量 / Backup count")


class StockMarketConfig(BaseModel):
    """股票市场配置 / Stock market configuration"""
    sync: Dict[str, Any] = Field(default_factory=dict, description="数据同步配置 / Data sync config")
    data_retention: Dict[str, Any] = Field(default_factory=dict, description="数据保留策略 / Data retention")
    trading_hours: Dict[str, str] = Field(default_factory=dict, description="市场交易时间 / Trading hours")


class PortfolioConfig(BaseModel):
    """投资组合配置 / Portfolio configuration"""
    trading: Dict[str, Any] = Field(default_factory=dict, description="交易配置 / Trading config")
    risk: Dict[str, Any] = Field(default_factory=dict, description="风险控制 / Risk control")
    account: Dict[str, Any] = Field(default_factory=dict, description="账户配置 / Account config")


class TechnicalAnalysisConfig(BaseModel):
    """技术分析配置 / Technical analysis configuration"""
    calculation: Dict[str, Any] = Field(default_factory=dict, description="计算配置 / Calculation config")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="指标参数 / Indicator parameters")


class ApiServerConfig(BaseModel):
    """API服务器配置 / API server configuration"""
    # 基础配置
    api_title: str = Field(default="Alpha Quant Trader Pro API", description="API标题 / API title")
    api_version: str = Field(default="2.0.0", description="API版本 / API version")
    api_description: str = Field(default="量化交易系统开放API", description="API描述 / API description")

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机 / Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口 / Server port")

    # Redis配置
    redis_url: Optional[str] = Field(default=None, description="Redis连接URL / Redis connection URL")

    # 认证配置
    api_key_secret: str = Field(default="your-secret-key-change-in-production", description="API密钥密钥 / API key secret")
    api_key_header: str = Field(default="X-API-Key", description="API密钥请求头 / API key header")
    api_signature_header: str = Field(default="X-API-Signature", description="API签名请求头 / API signature header")
    api_timestamp_header: str = Field(default="X-Timestamp", description="时间戳请求头 / Timestamp header")

    # 限流配置
    rate_limit_free: int = Field(default=60, ge=0, description="免费用户限流（每分钟）/ Free tier rate limit (per minute)")
    rate_limit_standard: int = Field(default=600, ge=0, description="标准用户限流（每分钟）/ Standard tier rate limit (per minute)")
    rate_limit_premium: int = Field(default=3600, ge=0, description="高级用户限流（每分钟）/ Premium tier rate limit (per minute)")


class BacktestConfig(BaseModel):
    """回测配置 / Backtest configuration"""
    # 基础配置
    initial_capital: float = Field(default=100000.0, ge=0, description="初始资金 / Initial capital")
    commission_rate: float = Field(default=0.00025, ge=0, le=0.01, description="手续费率 / Commission rate")
    slippage_rate: float = Field(default=0.001, ge=0, le=0.01, description="滑点率 / Slippage rate")
    stamp_duty_rate: float = Field(default=0.001, ge=0, le=0.01, description="印花税率（卖出）/ Stamp duty rate (sell only)")

    # 回测参数
    start_date: str = Field(default="2023-01-01", description="回测开始日期 / Start date")
    end_date: str = Field(default="2024-12-31", description="回测结束日期 / End date")
    interval: str = Field(default="1d", description="K线周期 (1d, 5d, 10d, 1m) / K-line interval")

    # 资金管理
    position_size: float = Field(default=0.1, ge=0, le=1, description="单笔交易仓位 / Position size per trade")
    max_positions: int = Field(default=5, ge=1, description="最大持仓股票数 / Max positions")
    use_dynamic_position: bool = Field(default=True, description="是否动态调整仓位 / Use dynamic position sizing")

    # 风控参数
    stop_loss_pct: float = Field(default=0.08, ge=0, le=1, description="止损比例 / Stop loss percentage")
    take_profit_pct: float = Field(default=0.20, ge=0, le=1, description="止盈比例 / Take profit percentage")
    enable_trailing_stop: bool = Field(default=False, description="启用移动止损 / Enable trailing stop")
    enable_position_control: bool = Field(default=True, description="启用仓位控制 / Enable position control")


class SimulationConfig(BaseModel):
    """模拟交易配置 / Simulation configuration"""
    execution_interval: int = Field(default=300, ge=1, description="执行间隔（秒）/ Execution interval (seconds)")
    check_interval: int = Field(default=60, ge=1, description="健康检查间隔（秒）/ Health check interval (seconds)")
    market_open_time: str = Field(default="09:30", description="市场开盘时间 / Market open time")
    market_close_time: str = Field(default="15:00", description="市场收盘时间 / Market close time")
    log_file: str = Field(default="logs/simulate_trading.log", description="日志文件路径 / Log file path")


# ========== 主配置类 ==========

class Config(BaseSettings):
    """
    统一配置类
    Unified configuration class

    配置优先级：运行时参数 > 环境变量 > YAML配置 > 默认值
    Configuration priority: runtime params > env vars > YAML > defaults
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="allow"  # 允许额外的环境变量
    )

    # ========== 应用配置 ==========
    app_name: str = Field(default="alpha-quant-trader-pro", description="应用名称 / Application name")
    debug: bool = Field(default=False, description="调试模式 / Debug mode")
    environment: str = Field(default="development", description="运行环境 / Environment")
    timezone: str = Field(default="Asia/Shanghai", description="时区设置 / Timezone")

    # ========== 模块配置 ==========
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置 / Database config")
    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig, description="数据源配置 / Data sources config")
    fee: FeeConfig = Field(default_factory=FeeConfig, description="手续费配置 / Fee config")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置 / Logging config")
    stock_market: StockMarketConfig = Field(default_factory=StockMarketConfig, description="股票市场配置 / Stock market config")
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig, description="投资组合配置 / Portfolio config")
    technical_analysis: TechnicalAnalysisConfig = Field(default_factory=TechnicalAnalysisConfig, description="技术分析配置 / Technical analysis config")
    api_server: ApiServerConfig = Field(default_factory=ApiServerConfig, description="API服务器配置 / API server config")
    backtest: BacktestConfig = Field(default_factory=BacktestConfig, description="回测配置 / Backtest config")
    simulation: SimulationConfig = Field(default_factory=SimulationConfig, description="模拟交易配置 / Simulation config")

    # 内部使用
    _config_file: Optional[str] = None

    def __init__(self, config_file: Optional[str] = None, **kwargs):
        """
        初始化配置
        Initialize configuration

        Args:
            config_file: 配置文件路径 / Config file path
            **kwargs: 其他配置参数（运行时参数，优先级最高）/ Other config params (runtime, highest priority)
        """
        # 确定配置文件路径
        if config_file:
            self._config_file = config_file
        else:
            env = os.getenv("APP_ENV", "development")
            if env == "development":
                self._config_file = "config/config.yaml"
            else:
                self._config_file = f"config/config.{env}.yaml"

        # 加载YAML配置
        yaml_config = self._load_yaml_config()

        # 加载 data_sources.yaml 配置
        data_sources_config = self._load_data_sources_config()
        if data_sources_config:
            # 合并数据源配置到 yaml_config
            if 'data_sources' in yaml_config:
                yaml_config['data_sources'].update(data_sources_config)
            else:
                yaml_config['data_sources'] = data_sources_config

        # 合并配置：YAML配置 + 运行时参数
        merged_config = {**yaml_config, **kwargs}

        # 调用父类初始化
        super().__init__(**merged_config)

        logger.info(f"Configuration loaded from {self._config_file}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")

    def _load_yaml_config(self) -> Dict[str, Any]:
        """加载YAML配置文件 / Load YAML config file"""
        if not self._config_file:
            return {}

        config_path = Path(self._config_file)

        if not config_path.exists():
            logger.warning(f"Config file not found: {self._config_file}")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config file {self._config_file}: {e}")
            raise

    def _load_data_sources_config(self) -> Dict[str, Any]:
        """加载数据源专用配置 / Load data sources specific configuration"""
        config_path = Path("config/data_sources.yaml")

        if not config_path.exists():
            logger.warning("config/data_sources.yaml not found, using default configuration")
            # 返回完整的默认配置
            return self._get_default_data_sources_config()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                # 提取 data_sources 内容，直接返回
                return data.get('data_sources', {})
        except Exception as e:
            logger.error(f"Failed to load data_sources.yaml: {e}")
            # 加载失败时返回默认配置
            return self._get_default_data_sources_config()

    def _get_default_data_sources_config(self) -> Dict[str, Any]:
        """获取默认的数据源配置 / Get default data sources configuration"""
        return {
            "timeout": 10,
            "max_retries": 3,
            "retry_delay": 0.5,
            "log_failures": True,
            "sources": {
                "realtime": [
                    {"name": "sina", "priority": 10, "enabled": True, "timeout": 3},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 5},
                    {"name": "tushare", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "kline": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 10},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 10},
                    {"name": "sina", "priority": 30, "enabled": True, "timeout": 5}
                ],
                "fundamentals": [
                    {"name": "tushare", "priority": 10, "enabled": True, "timeout": 15},
                    {"name": "akshare", "priority": 20, "enabled": True, "timeout": 15}
                ],
                "tech_indicators": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "fund_flows": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "dragon_tiger": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "valuation": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "per_share_indicators": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "osc_indicators": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "price_vol_ind": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "limit_up_down": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "turnover_rates": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "fund_quotes": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 10}
                ],
                "dupont_analysis": [
                    {"name": "akshare", "priority": 10, "enabled": True, "timeout": 15}
                ]
            },
            "fallback": {
                "max_retries": 2,
                "retry_delay": 0.5,
                "log_failures": True
            }
        }

    def save_to_file(self, config_file: str):
        """
        保存配置到YAML文件
        Save configuration to YAML file

        Args:
            config_file: 配置文件路径 / Config file path
        """
        config_path = Path(config_file)
        config_dir = config_path.parent

        config_dir.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self.model_dump()
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            logger.info(f"Saved config to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
            raise

    def get_database_url(self) -> str:
        """获取数据库连接字符串 / Get database URL"""
        return self.database.url

    def get_fee_config(self) -> FeeConfig:
        """获取手续费配置 / Get fee configuration"""
        return self.fee


# ========== 配置管理器（单例模式） ==========

class ConfigManager:
    """配置管理器 / Configuration manager"""

    _instance: Optional["ConfigManager"] = None
    _config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = Config()

    def get(self) -> Config:
        """获取配置对象 / Get configuration object"""
        return self._config

    def reload(self):
        """重新加载配置 / Reload configuration"""
        self._config = Config()
        logger.info("Configuration reloaded")

    def save(self, config_file: str = "config/local.yaml"):
        """保存当前配置到文件 / Save current config to file"""
        if self._config:
            self._config.save_to_file(config_file)


# ========== 全局配置 ==========

config_manager = ConfigManager()

# 便捷函数
get_config = config_manager.get
reload_config = config_manager.reload
save_config = config_manager.save
