#!/usr/bin/env python3
"""
将JSON配置文件转换为YAML格式
Convert JSON config files to YAML format

使用方法 / Usage:
    python scripts/convert_config.py config/default.json config/config.yaml
"""

import json
import yaml
from pathlib import Path
import sys


def convert_json_to_yaml(json_file: str, yaml_file: str):
    """
    转换JSON配置到YAML
    Convert JSON config to YAML

    Args:
        json_file: JSON配置文件路径 / JSON config file path
        yaml_file: YAML配置文件路径 / YAML config file path
    """
    json_path = Path(json_file)
    yaml_path = Path(yaml_file)

    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_file}")
        print(f"Error: JSON file not found: {json_file}")
        return False

    try:
        # 读取JSON / Read JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 创建输出目录 / Create output directory
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入YAML / Write YAML
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"✓ 转换完成: {json_file} → {yaml_file}")
        print(f"✓ Conversion complete: {json_file} → {yaml_file}")
        return True

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        print(f"✗ Conversion failed: {e}")
        return False


def main():
    """主函数 / Main function"""
    if len(sys.argv) != 3:
        print("使用方法 / Usage: python scripts/convert_config.py <input.json> <output.yaml>")
        print("\n示例 / Example:")
        print("  python scripts/convert_config.py config/default.json config/config.yaml")
        sys.exit(1)

    json_file = sys.argv[1]
    yaml_file = sys.argv[2]

    success = convert_json_to_yaml(json_file, yaml_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
