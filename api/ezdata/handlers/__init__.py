"""
handler 注册表 + 自动发现(懒加载)。

约定:`handlers/` 下每个 `*_handler/` 子包的 __init__.py 暴露轻量元数据
(name/title/family/capabilities/description/connection_args)与 `load_handler()`——
后者才导入携带重依赖(驱动/ORM)的 Handler 类。

发现阶段只 import 这些轻量 __init__(不碰 sqlalchemy/dlt/驱动),把元数据登记为
HandlerMeta;真正需要类时(create_handler/get_handler_cls)才 load() 触发重导入并缓存,
失败则记入 import_error 并抛出可读错误(不再静默丢一个源)。
"""

import hashlib
import importlib
import json
import os
import pkgutil
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType

from ezdata.errors import DependencyError, UnknownSourceError
from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.const import to_json_schema


# ---------------------------------------------------------------------------
# 轻量元数据:发现阶段登记,不触发重依赖导入。load() 首次调用才导入 Handler 类并缓存。
# ---------------------------------------------------------------------------
@dataclass
class HandlerMeta:
    name: str
    title: str
    family: str
    capabilities: tuple[str, ...]  # 能力位名字(如 ('READ','WRITE',...))
    description: str
    directory: str  # 子包目录(取 icon.svg 用,免加载类)
    connection_args: 'OrderedDict[str, dict]'
    connection_args_example: 'OrderedDict[str, dict]'
    loader: Callable[[], type[Connector]]  # 懒加载 thunk
    _cls: type[Connector] | None = field(default=None, repr=False)
    import_error: Exception | None = field(default=None, repr=False)
    _load_lock: 'threading.Lock' = field(default_factory=threading.Lock, repr=False, compare=False)

    def load(self) -> type[Connector]:
        """首次调用触发重导入并缓存(线程安全);失败记入 import_error 并抛 DependencyError。"""
        if self._cls is not None:  # 快路径:已加载,无锁
            return self._cls
        with self._load_lock:
            if self._cls is None:  # double-check
                try:
                    self._cls = self.loader()
                except Exception as e:
                    self.import_error = e
                    raise DependencyError(
                        f'数据源 {self.name} 依赖未就绪(驱动/包缺失,可用 install_dependencies 安装): {e}',
                        source_type=self.name,
                    ) from e
            return self._cls


# name(source_type) -> HandlerMeta
_handlers: dict[str, HandlerMeta] = {}

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
    except Exception:
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


def _register_module(module: ModuleType) -> None:
    """把一个轻量 handler 子包(暴露 load_handler + 元数据常量)登记为 HandlerMeta。"""
    name = getattr(module, 'name', '')
    loader = getattr(module, 'load_handler', None)
    if not name or not callable(loader):
        return
    _handlers[name] = HandlerMeta(
        name=name,
        title=getattr(module, 'title', name),
        family=getattr(module, 'family', ''),
        capabilities=tuple(getattr(module, 'capabilities', ())),
        description=getattr(module, 'description', ''),
        directory=os.path.dirname(module.__file__),
        connection_args=getattr(module, 'connection_args', OrderedDict()),
        connection_args_example=getattr(module, 'connection_args_example', OrderedDict()),
        loader=loader,
    )


def register_handler(cls: type[Connector]) -> type[Connector]:
    """(兼容/逃生口)直接登记一个已导入的 Connector 子类。也可当装饰器用。

    正常路径走 _discover() 的懒加载登记;此函数用于测试或动态注册,登记即持有类(非懒)。
    """
    if cls.name:
        _handlers[cls.name] = HandlerMeta(
            name=cls.name,
            title=cls.title,
            family=cls.family,
            capabilities=tuple(c.name for c in Capability if c in cls.capabilities),
            description='',
            directory=os.path.dirname(__file__),
            connection_args=cls.connection_args,
            connection_args_example=cls.connection_args_example,
            loader=lambda c=cls: c,
            _cls=cls,
        )
    return cls


def _discover() -> None:
    """扫描 handlers/ 下的 *_handler 子包并 import 其轻量 __init__(不触发重依赖)。"""
    for mod in pkgutil.iter_modules(__path__):
        if not (mod.ispkg and mod.name.endswith('_handler')):
            continue
        try:
            module = importlib.import_module(f'{__name__}.{mod.name}')
        except Exception:
            continue
        _register_module(module)


def _meta(source_type: str) -> HandlerMeta:
    meta = _handlers.get(source_type)
    if meta is None:
        raise UnknownSourceError(f'未注册的数据源类型: {source_type}', source_type=source_type)
    return meta


def get_handler_cls(source_type: str) -> type[Connector]:
    """取 handler 类(首次触发懒加载重导入;驱动缺失时抛可读错误)。"""
    return _meta(source_type).load()


def handler_icon(source_type: str) -> str | None:
    """返回该数据源类型的品牌图标 SVG 文本(子包目录下的 icon.svg);无则 None。

    走已登记的元数据目录,不加载 Handler 类(免驱动依赖)。source_type 未注册即 None。
    """
    meta = _handlers.get(source_type)
    if meta is None:
        return None
    icon_path = os.path.join(meta.directory, 'icon.svg')
    if not os.path.isfile(icon_path):
        return None
    try:
        with open(icon_path, encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def _read_requirements(path: str, seen: 'set[str] | None' = None) -> list[str]:
    """读 requirements.txt,递归展开 `-r other/requirements.txt` 引用,跳过其它 pip 选项行,去重保序。"""
    seen = seen if seen is not None else set()
    real = os.path.realpath(path)
    if real in seen or not os.path.isfile(path):
        return []
    seen.add(real)
    base = os.path.dirname(path)
    out: list[str] = []
    with open(path, encoding='utf-8') as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith('#'):
                continue
            if s.startswith(('-r ', '--requirement')):  # 递归引用:相对本文件目录解析
                inc = s.split(None, 1)[1].strip()
                out.extend(_read_requirements(os.path.join(base, inc), seen))
            elif s.startswith('-'):  # 其它 pip 选项(--extra-index-url 等)跳过
                continue
            else:
                out.append(s)
    dedup: list[str] = []
    for r in out:
        if r not in dedup:
            dedup.append(r)
    return dedup


def handler_requirements(source_type: str) -> list[str]:
    """该 handler 的依赖列表(展开 `-r` 引用后的实际包);无 requirements.txt 则空列表。"""
    meta = _meta(source_type)
    return _read_requirements(os.path.join(meta.directory, 'requirements.txt'))


def _req_dist_name(requirement: str) -> str:
    """从依赖行(如 'elasticsearch>=8.13,<9')取分发包名(pip/importlib.metadata 用名)。"""
    import re

    return re.split(r'[<>=!~;\[ ]', requirement, maxsplit=1)[0].strip()


def handler_dependencies(source_type: str) -> dict:
    """依赖诊断(只读、无副作用):按 requirements.txt 查各分发包是否已安装。

    注意:多数 handler 的驱动是方法内懒 import,故不能用「能否 load 类」判断就绪——
    这里按包名查 importlib.metadata,是与导入时机无关的准确判断。
    返回 {source_type, requirements, missing, ready}。
    """
    import importlib.metadata as md

    reqs = handler_requirements(source_type)
    missing: list[str] = []
    for r in reqs:
        name = _req_dist_name(r)
        if not name:
            continue
        try:
            md.version(name)
        except md.PackageNotFoundError:
            missing.append(r)
    return {'source_type': source_type, 'requirements': reqs, 'missing': missing, 'ready': not missing}


def create_handler(
    source_type: str, config: dict, secrets: str | dict | None = None, *, cache: bool = True
) -> Connector:
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
        if ent is not None:  # 并发下他人已建,丢弃本次、用已有
            ent[1] = now
            _handler_cache.move_to_end(key)
            _safe_close(handler)
            return ent[0]
        _handler_cache[key] = [handler, now]
        _evict_locked(now)
        return handler


def connection_schema(source_type: str) -> dict:
    """连接参数 → JSON Schema(前端表单)。走轻量元数据,不加载 Handler 类。"""
    meta = _meta(source_type)
    return to_json_schema(meta.connection_args, meta.connection_args_example)


def list_source_types() -> list[dict]:
    """列出已注册源类型 + 能力(给前端/权限可选项)。走轻量元数据,不加载任何 Handler 类。"""
    return [
        {
            'source_type': meta.name,
            'title': meta.title,
            'family': meta.family,
            'capabilities': list(meta.capabilities),
        }
        for _st, meta in sorted(_handlers.items())
    ]


_discover()

__all__ = [
    'Capability',
    'Column',
    'ConnectResult',
    'Connector',
    'HandlerMeta',
    'clear_handler_cache',
    'connection_schema',
    'create_handler',
    'get_handler_cls',
    'handler_cache_stats',
    'handler_dependencies',
    'handler_icon',
    'handler_requirements',
    'list_source_types',
    'register_handler',
]
