"""
适配器注册表模块

自动发现和管理所有数据源适配器
"""

import importlib
import os
import logging
from typing import Dict, Type, List, Optional
from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    适配器注册表

    负责自动发现、注册和管理所有数据源适配器
    """

    def __init__(self):
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._adapter_classes: Dict[str, Type[DataSourceAdapter]] = {}

    def auto_discover(self, package: str = "data_sources.adapters"):
        """
        自动发现适配器

        扫描 adapters 目录，自动导入所有适配器类

        Args:
            package: 适配器包路径
        """
        # 获取适配器目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        adapter_dir = os.path.join(current_dir, "adapters")

        if not os.path.exists(adapter_dir):
            logger.warning(f"Adapter directory not found: {adapter_dir}")
            return

        # 遍历目录中的所有文件
        for filename in os.listdir(adapter_dir):
            # 只处理以 _adapter.py 结尾的文件，排除 __init__.py
            if (filename.endswith("_adapter.py") and
                not filename.startswith("__")):

                module_name = filename[:-3]  # 去掉 .py 后缀
                module_path = f"{package}.{module_name}"

                try:
                    logger.info(f"Loading adapter module: {module_name}")
                    module = importlib.import_module(module_path)

                    # 查找继承自 DataSourceAdapter 的类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, DataSourceAdapter) and
                            attr != DataSourceAdapter):

                            self.register_class(attr)
                            logger.info(f"  Registered adapter class: {attr_name}")

                except Exception as e:
                    logger.error(f"Failed to load adapter {module_name}: {e}", exc_info=True)

    def register_class(self, adapter_class: Type[DataSourceAdapter]):
        """
        注册适配器类

        Args:
            adapter_class: 适配器类
        """
        # 通过约定的命名规则获取适配器名称
        # 优先使用类的 name 属性（如果是 property，则会在此处访问）
        # 如果无法获取，则使用类名转换

        # 方法1: 尝试直接访问 name 属性（不实例化）
        adapter_name = None
        try:
            # 检查是否有 name 类属性或 property
            if hasattr(adapter_class, 'name'):
                name_attr = getattr(adapter_class, 'name')
                if isinstance(name_attr, property):
                    # 是 property，使用类名作为默认值
                    adapter_name = adapter_class.__name__.lower().replace('adapter', '')
                else:
                    adapter_name = str(name_attr)
        except:
            pass

        # 方法2: 如果还是获取不到，使用类名转换
        if not adapter_name:
            adapter_name = adapter_class.__name__.lower().replace('adapter', '')

        if adapter_name in self._adapter_classes:
            logger.warning(f"Adapter {adapter_name} already registered, overwriting")

        self._adapter_classes[adapter_name] = adapter_class
        logger.debug(f"Registered adapter class: {adapter_name}")

    def create_adapter(self, name: str, **kwargs) -> DataSourceAdapter:
        """
        创建适配器实例

        Args:
            name: 适配器名称
            **kwargs: 传递给适配器构造函数的参数

        Returns:
            适配器实例

        Raises:
            ValueError: 适配器类不存在
        """
        if name not in self._adapter_classes:
            raise ValueError(f"Adapter class '{name}' not found. "
                           f"Available: {list(self._adapter_classes.keys())}")

        adapter_class = self._adapter_classes[name]
        adapter = adapter_class(**kwargs)

        # 存储实例
        self._adapters[name] = adapter
        logger.debug(f"Created adapter instance: {name}")

        return adapter

    def get_adapter(self, name: str) -> Optional[DataSourceAdapter]:
        """
        获取适配器实例

        Args:
            name: 适配器名称

        Returns:
            适配器实例，如果不存在返回 None
        """
        return self._adapters.get(name)

    def get_all_adapters(self) -> List[DataSourceAdapter]:
        """
        获取所有适配器实例

        Returns:
            适配器实例列表
        """
        return list(self._adapters.values())

    def get_adapter_names(self) -> List[str]:
        """
        获取所有已注册的适配器名称

        Returns:
            适配器名称列表
        """
        return list(self._adapter_classes.keys())
