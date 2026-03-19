# portfolio_manager/config.py
"""
配置模块 - 简单配置（临时方案）
"""

class PortfolioConfig:
    """投资组合配置"""

    def __init__(self, config_path: str = None):
        """初始化配置"""
        self._config = {}

    def get_database_url(self) -> str:
        """获取数据库连接"""
        return "postgresql://localhost/stock_market"

    def get_fee_config(self):
        """获取手续费配置"""
        from portfolio_manager.models import FeeConfig
        return FeeConfig()
