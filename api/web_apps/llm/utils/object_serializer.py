# encoding: utf-8
"""
对象序列化工具类
复刻 ToolsAgentExecutor 的序列化/反序列化逻辑
用于处理非 JSON 序列化对象和超长字符串
"""
import json
import types
from typing import Any, Dict
from collections.abc import Iterator
from utils.common_utils import gen_uuid


class ObjectSerializer:
    """
    对象序列化管理器
    将不可序列化的对象或超长字符串转换为引用字符串，并维护对象映射表
    """

    def __init__(self, max_token: int = 2000):
        """
        初始化序列化器

        Args:
            max_token: 字符串最大长度阈值，超过此长度将被序列化为引用
        """
        self.max_token = max_token
        self.object_map: Dict[str, Any] = {}

    def serialize_value(self, value: Any) -> Any:
        """
        将值序列化为 JSON 兼容格式或引用字符串

        对于字典，递归处理每个键值对
        对于可 JSON 序列化的值：
            - 长度 <= max_token: 直接返回
            - 长度 > max_token: 创建引用字符串
        对于不可 JSON 序列化的值：创建引用字符串

        Args:
            value: 待序列化的值

        Returns:
            序列化后的值或引用字符串
        """
        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}

        # 特殊处理：迭代器和生成器（直接序列化为引用）
        if isinstance(value, (types.GeneratorType, Iterator)):
            ref_key = f"object({type(value).__name__}):{gen_uuid('base')[:16]}"
            self.object_map[ref_key] = value
            return ref_key

        try:
            # 尝试 JSON 序列化
            json.dumps(value)
            if len(str(value)) > self.max_token:
                # 超长字符串，创建引用
                ref_key = f"object({type(value).__name__}):{str(value)[:100]}"
                self.object_map[ref_key] = value
                return ref_key
            return value
        except (TypeError, ValueError):
            # 不可序列化对象，创建引用
            ref_key = f"object({type(value).__name__}):{gen_uuid('base')[:16]}"
            self.object_map[ref_key] = value
            return ref_key

    def de_serialize_value(self, value: Any) -> Any:
        """
        将引用字符串还原为原始对象

        对于字典，递归处理每个键值对
        对于字符串，尝试从 object_map 查找对应对象
        如果找不到，返回原值

        Args:
            value: 待反序列化的值或引用字符串

        Returns:
            反序列化后的原始对象
        """
        if isinstance(value, dict):
            return {k: self.de_serialize_value(v) for k, v in value.items()}

        # 尝试查找引用对象
        return self.object_map.get(str(value), value)

    def clear(self):
        """清理对象映射表，释放内存"""
        self.object_map.clear()

    def __len__(self):
        """返回当前存储的对象数量"""
        return len(self.object_map)
