"""
配置加载模块
"""
import json
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(__file__).parent / "database.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
