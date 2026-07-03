"""ETL 公共工具:目标族判断 / 记录序列化 / 错误信息截断 / 只读 SQL 校验。供数据服务与任务 runner 共用。"""

import csv
import io
import json
import re
from typing import Any

from ezdata.errors import ReadOnlyViolation


def json_safe(v: Any) -> Any:
    """把记录里的非 JSON 原生类型转成可序列化值(回前端/接口前用),否则 FastAPI 序列化会报
    'Object of type date is not JSON serializable'。处理 date/datetime/time→isoformat、Decimal→float、
    bytes→str、numpy·pandas 标量→原生、NaN/Inf→None,其余兜底 str()。"""
    import datetime as _dt
    import math as _math
    from decimal import Decimal as _Dec

    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, float):
        return None if (_math.isnan(v) or _math.isinf(v)) else v
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):  # pandas.Timestamp 也属 datetime
        return v.isoformat()
    if isinstance(v, _Dec):
        return float(v)
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).decode('utf-8', 'replace')
    if isinstance(v, dict):
        return {str(k): json_safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [json_safe(x) for x in v]
    if hasattr(v, 'item'):  # numpy / pandas 标量 → 原生
        try:
            return json_safe(v.item())
        except Exception:  # noqa: BLE001
            pass
    if hasattr(v, 'isoformat'):
        try:
            return v.isoformat()
        except Exception:  # noqa: BLE001
            pass
    return str(v)


def json_safe_rows(rows: Any) -> Any:
    """list[dict] 记录整体转 JSON 安全;非 list(如 None)原样返回。"""
    return [json_safe(r) for r in rows] if isinstance(rows, list) else rows

# 只读语句起始关键字白名单
_SQL_READONLY_START = re.compile(r'^\s*(select|with|show|explain|desc|describe)\b', re.IGNORECASE)
# 写入/DDL/危险关键字黑名单(以词边界匹配,避免误伤普通子串)
_SQL_DANGEROUS = re.compile(
    r'\b(insert|update|delete|drop|truncate|alter|create|replace|rename|grant|revoke|merge|call|exec|execute|'
    r'load\s+data|lock|unlock)\b|into\s+(out|dump)file',
    re.IGNORECASE,
)


# native 为 SQL 文本的数据源族,才做只读 SQL 护栏;api(akshare/ccxt 的函数名)、
# search/document(ES/Mongo 的 DSL)等族的 native 不是 SQL,各自 query 本就只读,无需且不能按 SQL 校验。
_SQL_NATIVE_FAMILIES = {'rdbms', 'timeseries'}


def assert_readonly_sql(statement: Any, family: str | None = None) -> None:
    """断言为「单条只读 SQL」,否则抛 ValueError。

    非字符串(如 ES/Mongo 的 DSL dict)直接放行——它们各自的 query 方法本就是只读检索。
    family 传入时:仅对 SQL 文本族(rdbms/timeseries)校验;其余族(如 api/akshare 的函数名)放行。
    """
    if not isinstance(statement, str):
        return
    if family is not None and family not in _SQL_NATIVE_FAMILIES:
        return
    s = statement.strip().rstrip(';').strip()
    if not s:
        return
    if ';' in s:  # 多语句(防堆叠注入)
        raise ReadOnlyViolation('查询仅允许单条只读语句(检测到多条语句)')
    if not _SQL_READONLY_START.match(s):
        raise ReadOnlyViolation('查询仅允许只读语句(SELECT / WITH / SHOW / EXPLAIN)')
    if _SQL_DANGEROUS.search(s):
        raise ReadOnlyViolation('检测到写入/DDL 关键字,已拦截(查询仅限只读,写入请用数据集成任务)')

# 目标为对象/文件存储时,写入路径是「整对象 bytes」,需先把记录序列化
FILE_FAMILIES = {'file', 'object', 'filesystem'}

# 错误信息最大长度(超过截断,避免前端 toast / 日志过长)
ERR_MAX = 400


def is_file_target(family: str | None) -> bool:
    return (family or '') in FILE_FAMILIES


def stream_statement(object_name: str | None) -> dict:
    """构造流式源有界读取(query)的 statement,兼容 binlog(only_tables)与 kafka(topic)。"""
    stmt: dict[str, Any] = {}
    if object_name:
        stmt['only_tables'] = [object_name]  # binlog 用
        stmt['topic'] = object_name          # kafka 用
    return stmt


def stream_kwargs(object_name: str | None) -> dict:
    """构造流式源长驻消费(stream)的 kwargs,兼容 binlog 与 kafka(各取所需,多余键被 **kwargs 吞掉)。"""
    kw: dict[str, Any] = {}
    if object_name:
        kw['only_tables'] = [object_name]  # binlog
        kw['topic'] = object_name          # kafka
    return kw


def serialize_records(records: list[dict], fmt: str = 'csv') -> str:
    """把记录列表序列化为文本(写入对象存储用)。支持 csv / json / jsonl。"""
    fmt = (fmt or 'csv').lower()
    if not records:
        return ''
    if fmt == 'json':
        return json.dumps(records, ensure_ascii=False, default=str)
    if fmt == 'jsonl':
        return '\n'.join(json.dumps(r, ensure_ascii=False, default=str) for r in records)
    # 默认 csv:并集列头,缺列留空
    headers: list[str] = []
    for r in records:
        for k in r:
            if k not in headers:
                headers.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction='ignore')
    w.writeheader()
    for r in records:
        w.writerow({k: ('' if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def short_err(e: Any, limit: int = ERR_MAX) -> str:
    """把异常信息压成一行并截断,保留首尾关键信息。"""
    msg = ' '.join(str(e).split())  # 折叠换行/多空格
    if len(msg) <= limit:
        return msg
    head = limit - 60
    return f'{msg[:head]} …(已截断,共 {len(msg)} 字)… {msg[-50:]}'
