"""
handler 注册表 + 自动发现。

约定:`handlers/` 下每个 `*_handler/` 子包的 __init__.py 暴露 `Handler`(Connector 子类)。
本包导入时自动扫描所有 `*_handler` 子包并注册(新增源 = 加一个文件夹,零改动)。
"""

import importlib
import pkgutil

from module_data.handlers.base import Capability, Column, Connector, ConnectResult

# name(source_type) -> Connector 子类
_handlers: dict[str, type[Connector]] = {}


def register_handler(cls: type[Connector]) -> type[Connector]:
    """注册一个 handler 类(按 cls.name)。也可当装饰器用。"""
    if cls.name:
        _handlers[cls.name] = cls
    return cls


def _discover() -> None:
    """扫描 handlers/ 下的 *_handler 子包并导入(触发各自 __init__ 注册)。"""
    for mod in pkgutil.iter_modules(__path__):
        if not (mod.ispkg and mod.name.endswith('_handler')):
            continue
        try:
            module = importlib.import_module(f'{__name__}.{mod.name}')
        except Exception:
            continue
        handler = getattr(module, 'Handler', None)
        if handler is not None and getattr(handler, 'name', ''):
            register_handler(handler)


def get_handler_cls(source_type: str) -> type[Connector]:
    cls = _handlers.get(source_type)
    if cls is None:
        raise ValueError(f'未注册的数据源类型: {source_type}')
    return cls


def create_handler(source_type: str, config: dict, secrets: str | dict | None = None) -> Connector:
    """从库记录构造 handler 实例。"""
    return get_handler_cls(source_type).from_record(config, secrets)


def connection_schema(source_type: str) -> dict:
    return get_handler_cls(source_type).connection_schema()


def list_source_types() -> list[dict]:
    """列出已注册源类型 + 能力(给前端/权限可选项)。"""
    return [{
        'source_type': st,
        'title': cls.title,
        'family': cls.family,
        'capabilities': [c.name for c in Capability if c in cls.capabilities],
    } for st, cls in sorted(_handlers.items())]


_discover()

__all__ = [
    'Capability',
    'Column',
    'ConnectResult',
    'Connector',
    'connection_schema',
    'create_handler',
    'get_handler_cls',
    'list_source_types',
    'register_handler',
]
