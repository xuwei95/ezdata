"""
handler 注册表 + 自动发现。

约定:`handlers/` 下每个 `*_handler/` 子包的 __init__.py 暴露 `Handler`(Connector 子类)。
本包导入时自动扫描所有 `*_handler` 子包并注册(新增源 = 加一个文件夹,零改动)。
"""

import hashlib
import importlib
import json
import os
import pkgutil
import threading
import time
from collections import OrderedDict

from module_data.handlers.base import Capability, Column, Connector, ConnectResult

# name(source_type) -> Connector 子类
_handlers: dict[str, type[Connector]] = {}

# ---------------------------------------------------------------------------
# handler 实例缓存(进程内):同一 (source_type, config, secrets) 复用实例 → 复用其
# engine 连接池 / client,避免每次 create_engine 重建池;并消除"无 dispose"泄漏。
# key = 内容哈希 → 改配置/密钥即换 key,自动失效。LRU + 空闲 TTL,淘汰时 close() 释放。
# 仅在长驻进程(backend/worker)有意义;sandbox 子进程用完即死,传 cache=False。
# ---------------------------------------------------------------------------
_CACHE_ENABLED = os.environ.get('HANDLER_CACHE_ENABLED', '1') not in ('0', 'false', 'False')
_CACHE_MAX = int(os.environ.get('HANDLER_CACHE_MAX', '64'))
_CACHE_TTL = float(os.environ.get('HANDLER_CACHE_TTL', '1800'))  # 空闲秒数
_handler_cache: 'OrderedDict[str, list]' = OrderedDict()  # key -> [handler, last_access_ts]
_cache_lock = threading.Lock()


def _cache_key(source_type: str, config: dict, secrets: 'str | dict | None') -> str:
    raw = json.dumps([source_type, config, secrets], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _safe_close(handler: Connector) -> None:
    try:
        handler.close()
    except Exception:  # noqa: BLE001
        pass


def _evict_locked(now: float) -> None:
    """淘汰:先清过期(从最久未用的队首起),再压到容量上限。需持锁调用。"""
    while _handler_cache:
        k = next(iter(_handler_cache))
        _h, ts = _handler_cache[k]
        if (now - ts) > _CACHE_TTL:
            _handler_cache.pop(k)
            _safe_close(_h)
        else:
            break
    while len(_handler_cache) > _CACHE_MAX:
        k, (h, _ts) = _handler_cache.popitem(last=False)
        _safe_close(h)


def clear_handler_cache() -> int:
    """清空缓存并释放所有连接,返回清掉的条数(测试/运维用)。"""
    with _cache_lock:
        n = len(_handler_cache)
        for _k, (h, _ts) in _handler_cache.items():
            _safe_close(h)
        _handler_cache.clear()
    return n


def handler_cache_stats() -> dict:
    """缓存观测(测试/运维用)。"""
    with _cache_lock:
        return {'size': len(_handler_cache), 'max': _CACHE_MAX, 'ttl': _CACHE_TTL, 'enabled': _CACHE_ENABLED}


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


def handler_icon(source_type: str) -> str | None:
    """返回该数据源类型的品牌图标 SVG 文本(取自其 handler 子包目录下的 icon.svg);无则 None。

    路径由已注册 handler 类自身所在目录推导(不假设目录命名),source_type 未注册即 None,天然防路径穿越。
    """
    import inspect  # noqa: PLC0415

    cls = _handlers.get(source_type)
    if cls is None:
        return None
    icon_path = os.path.join(os.path.dirname(inspect.getfile(cls)), 'icon.svg')
    if not os.path.isfile(icon_path):
        return None
    try:
        with open(icon_path, encoding='utf-8') as f:
            return f.read()
    except Exception:  # noqa: BLE001
        return None


def create_handler(source_type: str, config: dict, secrets: str | dict | None = None,
                   *, cache: bool = True) -> Connector:
    """从库记录构造 handler 实例。

    cache=True(默认):按 (source_type, config, secrets) 内容哈希复用进程内实例,
    复用其连接池/client。改配置/密钥即换 key 自动失效。
    cache=False:每次新建(sandbox 子进程、测试未保存配置、连通性测试等用)。
    """
    if not (cache and _CACHE_ENABLED):
        return get_handler_cls(source_type).from_record(config, secrets)

    key = _cache_key(source_type, config, secrets)
    now = time.monotonic()
    with _cache_lock:
        ent = _handler_cache.get(key)
        if ent is not None:
            ent[1] = now
            _handler_cache.move_to_end(key)
            return ent[0]
    # 未命中:在锁外构造(实例化轻、连接懒建),再登记
    handler = get_handler_cls(source_type).from_record(config, secrets)
    with _cache_lock:
        ent = _handler_cache.get(key)
        if ent is not None:            # 并发下他人已建,丢弃本次、用已有
            ent[1] = now
            _handler_cache.move_to_end(key)
            _safe_close(handler)
            return ent[0]
        _handler_cache[key] = [handler, now]
        _evict_locked(now)
        return handler


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
    'clear_handler_cache',
    'connection_schema',
    'create_handler',
    'get_handler_cls',
    'handler_cache_stats',
    'list_source_types',
    'register_handler',
]
