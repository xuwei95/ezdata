"""ETL 公共工具:目标族判断 / 记录序列化 / 错误信息截断。供数据服务与任务 runner 共用。"""

import csv
import io
import json
from typing import Any

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
