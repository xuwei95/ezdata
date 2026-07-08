"""ezdata 数据访问门面(无状态、无 db、无 web、无 config)。

入参是"数据源描述"(source_type + config + 明文 secrets dict),不认数据库/加密/租户。
- web 层:先查库拿配置 + 解密 secrets,再调用本模块;
- cli / mcp / skill:自行构造 config/secrets 直接调用。

handler 方法是同步阻塞的;async 场景(web)由调用方用 run_in_threadpool 包裹。
JSON 清洗(json_safe_rows)/序列化交由调用方按需处理(见 ezdata.utils.etl_util)。
"""

from typing import Any

from ezdata.errors import CapabilityError, EzDataError, QueryError
from ezdata.handlers import Capability, create_handler, handler_icon
from ezdata.handlers import connection_schema as _connection_schema
from ezdata.handlers import list_source_types as _list_source_types
from ezdata.utils.etl_util import assert_readonly_sql
from ezdata.utils.query import OPERATORS


def _require(handler: Any, cap: Capability) -> None:
    """能力校验:该源不支持则抛 CapabilityError(信息统一,便于上层/AI 识别)。"""
    if not handler.has(cap):
        raise CapabilityError(f'{handler.name} 不支持能力 {cap.name}', source_type=handler.name)


# ---------- 元信息(静态,不建连接) ----------
def list_source_types() -> list[dict]:
    """已注册数据源类型 + 能力(懒加载注册表,不触发驱动导入)。"""
    return _list_source_types()


def connection_schema(source_type: str) -> dict:
    """连接参数 JSON Schema(前端/CLI 表单)。"""
    return _connection_schema(source_type)


def source_type_icon(source_type: str) -> str | None:
    """数据源类型品牌图标 SVG;无则 None。"""
    return handler_icon(source_type)


def operators() -> list[dict]:
    """过滤操作符清单(条件查询用)。"""
    return OPERATORS


# ---------- 访问(建连接;内部走 create_handler 懒加载 + 实例缓存) ----------
def _handler(source_type: str, config: dict | None, secrets: dict | None, *, cache: bool = True) -> Any:
    return create_handler(source_type, config or {}, secrets or {}, cache=cache)


def test_connection(source_type: str, config: dict | None = None, secrets: dict | None = None) -> dict:
    """连通性测试。临时(未保存)配置不入实例缓存。"""
    r = _handler(source_type, config, secrets, cache=False).test_connection()
    return {'success': r.success, 'message': r.message, 'latencyMs': r.latency_ms}


def list_tables(source_type: str, config: dict | None = None, secrets: dict | None = None) -> list[str]:
    """列出表/集合/索引/接口(需 SCHEMA 能力)。"""
    h = _handler(source_type, config, secrets)
    _require(h, Capability.SCHEMA)
    try:
        return h.list_tables()
    except EzDataError:
        raise
    except Exception as e:
        raise QueryError(f'{source_type} 列表失败: {e}', source_type=source_type) from e


def get_columns(source_type: str, config: dict | None = None, secrets: dict | None = None, *, table: str) -> list[dict]:
    """读取字段结构,归一为 [{name,type,nullable,comment}]。"""
    h = _handler(source_type, config, secrets)
    _require(h, Capability.SCHEMA)
    try:
        cols = h.get_columns(table)
    except EzDataError:
        raise
    except Exception as e:
        raise QueryError(f'{source_type} 取字段结构失败: {e}', source_type=source_type, statement=table) from e
    return [{'name': c.name, 'type': c.type, 'nullable': c.nullable, 'comment': c.comment} for c in cols]


def query(
    source_type: str,
    config: dict | None = None,
    secrets: dict | None = None,
    *,
    statement: Any,
    limit: int | None = None,
    readonly: bool = True,
) -> list[dict]:
    """原生查询取数(读路径)。readonly=True 时对 SQL 文本族做只读护栏(拦 DML/DDL,抛 ReadOnlyViolation)。

    执行失败包成 QueryError 但**保留原始报错**(from e + statement),供 to_dict() 结构化带给 AI。
    """
    h = _handler(source_type, config, secrets)
    _require(h, Capability.READ)
    if readonly and isinstance(statement, str):
        assert_readonly_sql(statement, h.family)
    try:
        return h.query(statement, None, limit)
    except EzDataError:
        raise
    except Exception as e:
        raise QueryError(f'{source_type} 查询失败: {e}', source_type=source_type, statement=statement) from e


def write(
    source_type: str,
    config: dict | None = None,
    secrets: dict | None = None,
    *,
    records: Any,
    table: str,
    mode: str = 'append',
    **kwargs: Any,
) -> Any:
    """批量写入(写路径,需 WRITE 能力)。"""
    h = _handler(source_type, config, secrets)
    _require(h, Capability.WRITE)
    try:
        return h.write(records, table, mode=mode, **kwargs)
    except EzDataError:
        raise
    except Exception as e:
        raise QueryError(f'{source_type} 写入失败: {e}', source_type=source_type, statement=table) from e


def get_handler(
    source_type: str, config: dict | None = None, secrets: dict | None = None, *, cache: bool = True
) -> Any:
    """直接取一个 handler 实例(供需要多次调用/自定义方法的高级场景,如 cli/mcp 编排)。"""
    return _handler(source_type, config, secrets, cache=cache)
