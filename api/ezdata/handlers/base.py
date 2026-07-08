"""
连接器(handler)抽象基类 + 能力声明。

结构扳自 MindsDB handler:每个 handler 用类属性声明 name/title/family/connection_args,
__init__ 收一份 connection_data(dict)。在此基础上加了两样 MindsDB 没有的:
  - capabilities:能力位(可读/可写/可抽取/结构/流式/可生成接口),= 权限上界;
  - extract()/write():用 dlt 做批量取数/写数(读路径 query 仍走原生)。
不依赖 mindsdb 包(只借结构与 connection_args 写法)。
"""

import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Flag, auto
from typing import Any

from ezdata.handlers.const import secret_fields, to_json_schema


class Capability(Flag):
    """连接器能力位(可组合)。"""

    READ = auto()  # 原生查询(读路径)
    WRITE = auto()  # 写入/更新/删除
    EXTRACT = auto()  # 批量抽取(dlt 写路径)
    SCHEMA = auto()  # 读取数据结构
    STREAM = auto()  # 流式消费(Kafka / binlog)
    GEN_API = auto()  # 可生成数据服务接口
    VECTOR = auto()  # 向量相似度检索


@dataclass
class ConnectResult:
    success: bool
    message: str = ''
    latency_ms: float | None = None


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    comment: str = ''


class Connector(ABC):
    """所有数据源 handler 的基类。"""

    # —— 身份/元信息(子类覆盖)——
    name: str = ''  # 'mysql' / 'elasticsearch' ...
    title: str = ''  # 'MySQL'
    family: str = ''  # 'rdbms' / 'search' / 'document' / 'file' ...
    capabilities: Capability = Capability(0)
    connection_args: 'OrderedDict[str, dict]' = OrderedDict()
    connection_args_example: 'OrderedDict[str, dict]' = OrderedDict()

    def __init__(self, connection_data: dict[str, Any]) -> None:
        self.connection_data: dict[str, Any] = connection_data or {}
        self._lock = threading.RLock()  # 保护共享句柄(engine/client/driver)的懒建

    def _lazy(self, attr: str, factory: 'Any') -> Any:
        """线程安全懒建共享句柄:建好后并发使用安全(池/client 本身线程安全),只锁创建那一刻。

        实例缓存会让同一 handler 被多线程共享,故 engine/client/driver 的首次创建必须串行,
        否则会建出多个连接池、泄漏其一。
        """
        val = getattr(self, attr, None)
        if val is not None:  # 快路径:已建,无锁
            return val
        with self._lock:
            val = getattr(self, attr, None)  # double-check
            if val is None:
                val = factory()
                setattr(self, attr, val)
            return val

    # ---------- 构造 / 元信息 ----------
    @classmethod
    def from_record(cls, config: dict[str, Any], secrets: str | dict | None = None) -> 'Connector':
        """从库记录构造:config(非密钥) + secrets(AES 密文串或已解密 dict)。

        secrets 为密文串时,用宿主注入的解密器(见 ezdata.services.secrets)解密;未注入则报错——
        纯数据 SDK 不内置加密体系,cli/mcp 等请注入解密器或直接传明文 dict。
        """
        merged = dict(config or {})
        if isinstance(secrets, str) and secrets:
            import json

            from ezdata.services.secrets import get_decryptor

            decrypt = get_decryptor()
            if decrypt is None:
                raise RuntimeError(
                    '收到密文形式的 secrets,但未注入解密器:请改传明文 dict,'
                    '或调用 ezdata.services.secrets.set_decryptor(...) 注入。'
                )
            merged.update(json.loads(decrypt(secrets)))
        elif isinstance(secrets, dict):
            merged.update(secrets)
        return cls(merged)

    @classmethod
    def connection_schema(cls) -> dict:
        """connection_args → JSON Schema(前端表单,带 example 默认值)。"""
        return to_json_schema(cls.connection_args, cls.connection_args_example)

    @classmethod
    def secret_fields(cls) -> list[str]:
        """密钥字段名(入库时单独 AES 加密)。"""
        return secret_fields(cls.connection_args)

    def arg(self, *keys: str, default: Any = None) -> Any:
        """按多个候选键取连接参数(兼容 user/username 等别名)。"""
        for k in keys:
            if self.connection_data.get(k) not in (None, ''):
                return self.connection_data[k]
        return default

    # ---------- 生命周期 ----------
    def close(self) -> None:
        """释放底层连接(供缓存淘汰/手动回收)。基类尽力释放已知句柄,各源可覆写。

        覆盖常见持有方式:_engine(SQLAlchemy 池)、_client(pymongo/es/boto3)、_driver(neo4j)。
        无连接(如文件源每次开/关 :memory: DuckDB)则全为 None,安全跳过。
        """
        eng = getattr(self, '_engine', None)
        if eng is not None and hasattr(eng, 'dispose'):
            try:
                eng.dispose()
            except Exception:
                pass
        for attr in ('_client', '_driver'):
            obj = getattr(self, attr, None)
            if obj is None:
                continue
            for m in ('close', 'disconnect'):
                fn = getattr(obj, m, None)
                if callable(fn):
                    try:
                        fn()
                    except Exception:
                        pass
                    break

    # ---------- 能力 ----------
    def has(self, cap: Capability) -> bool:
        return cap in self.capabilities

    def _require(self, cap: Capability) -> None:
        if not self.has(cap):
            raise NotImplementedError(f'{self.name} 不支持能力: {cap.name}')

    @abstractmethod
    def test_connection(self) -> ConnectResult:
        """连接测试。"""

    def list_tables(self) -> list[str]:
        self._require(Capability.SCHEMA)
        raise NotImplementedError

    def get_columns(self, table: str) -> list[Column]:
        self._require(Capability.SCHEMA)
        raise NotImplementedError

    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """原生查询取数(读路径)。statement 形态由各源决定:SQL 串 / DSL dict / Cypher。"""
        self._require(Capability.READ)
        raise NotImplementedError

    def sample_query(self, table: str, limit: int = 100) -> Any:
        """原生查询默认示例(前端预填)。基类给通用 SQL,各异构源覆盖为对应方言/DSL。"""
        return f'SELECT * FROM {table} LIMIT {limit}'

    def extract(self, table: str, **kwargs: Any) -> Any:
        """返回 dlt source/resource,供 Celery 批跑装载(写路径)。"""
        self._require(Capability.EXTRACT)
        raise NotImplementedError

    def write(self, data: Iterable[dict] | Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        self._require(Capability.WRITE)
        raise NotImplementedError

    def stream(self, **kwargs: Any) -> Iterator[dict]:
        """流式消费(长驻):持续 yield 记录(Kafka 消息 / binlog 变更事件)。供长驻 worker 调用。"""
        self._require(Capability.STREAM)
        raise NotImplementedError

    def similarity_search(
        self, query: str, collection: str, limit: int = 10, filters: dict | None = None, **kwargs: Any
    ) -> list[dict]:
        """向量相似度检索:对 collection 按 query 文本检索最相近的 limit 条。"""
        self._require(Capability.VECTOR)
        raise NotImplementedError

    def search(
        self, table: str, filters: list[dict] | None = None, page: int = 1, pagesize: int = 20, **kwargs: Any
    ) -> dict:
        """分页查询(数据接口用):返回 {records, total, page, pagesize}。
        仅支持 offset/页码分页的源实现并保留 GEN_API 能力。"""
        self._require(Capability.GEN_API)
        raise NotImplementedError
