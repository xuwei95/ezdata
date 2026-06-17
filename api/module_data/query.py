"""
统一查询条件结构 + 按源翻译器(参考旧版 extract_rules / parse_extract_rules)。

统一结构(前端只产这一种,后端按源翻译):
    rules = [
        {"field": "start_time", "op": "lt",  "value": "2026-06-17"},
        {"field": "status",     "op": "eq",  "value": "SUCCESS"},
        {"field": "name",       "op": "contains", "value": "task"},
        {"field": "start_time", "op": "sort_desc"},
    ]
兼容旧字段名:`op` 亦可写 `rule`。

翻译器:
    sqlalchemy_adapter(rules) -> query_adapter_callback   # SQL 族(dlt sql_table / select)
    to_es(rules)              -> (query_dsl, sort_list)    # Elasticsearch
    to_mongo(rules)           -> (filter, sort_list)       # MongoDB
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import and_

# 操作符目录(供前端渲染条件构造器:name + 中文 + 适用维度)
OPERATORS = [
    {'op': 'eq', 'label': '等于'}, {'op': 'neq', 'label': '不等于'},
    {'op': 'gt', 'label': '大于'}, {'op': 'gte', 'label': '大于等于'},
    {'op': 'lt', 'label': '小于'}, {'op': 'lte', 'label': '小于等于'},
    {'op': 'in', 'label': '在列表中'}, {'op': 'nin', 'label': '不在列表中'},
    {'op': 'contains', 'label': '包含'}, {'op': 'ncontains', 'label': '不包含'},
    {'op': 'between', 'label': '区间'}, {'op': 'isnull', 'label': '为空'}, {'op': 'notnull', 'label': '非空'},
    {'op': 'sort_asc', 'label': '升序'}, {'op': 'sort_desc', 'label': '降序'},
]
SORT_OPS = {'sort_asc', 'sort_desc'}


def _parts(rule: dict) -> tuple[str, str, Any]:
    return rule.get('field'), (rule.get('op') or rule.get('rule')), rule.get('value')


# ---------- SQL(SQLAlchemy)----------
# op -> (col, value) 构造条件;dispatch 表避免长 if/elif
_SQL_OPS: dict[str, Callable] = {
    'eq': lambda c, v: c == v, 'neq': lambda c, v: c != v,
    'gt': lambda c, v: c > v, 'gte': lambda c, v: c >= v,
    'lt': lambda c, v: c < v, 'lte': lambda c, v: c <= v,
    'in': lambda c, v: c.in_(v), 'nin': lambda c, v: ~c.in_(v),
    'contains': lambda c, v: c.like(f'%{v}%'), 'ncontains': lambda c, v: ~c.like(f'%{v}%'),
    'between': lambda c, v: c.between(v[0], v[1]),
    'isnull': lambda c, v: c.is_(None), 'notnull': lambda c, v: c.isnot(None),
}


def sqlalchemy_adapter(rules: list[dict]) -> Callable:
    """返回 dlt sql_table 的 query_adapter_callback(也可直接用于 select)。"""

    def adapter(query: Any, table: Any) -> Any:
        conds, orders = [], []
        for r in rules or []:
            field, op, value = _parts(r)
            if not field or not op:
                continue
            col = table.c[field]
            if op in SORT_OPS:
                orders.append(col.asc() if op == 'sort_asc' else col.desc())
            elif op in _SQL_OPS:
                conds.append(_SQL_OPS[op](col, value))
        if conds:
            query = query.where(and_(*conds))
        if orders:
            query = query.order_by(*orders)
        return query

    return adapter


# ---------- Elasticsearch DSL ----------
def to_es(rules: list[dict]) -> tuple[dict, list]:  # noqa: PLR0912  逐操作符翻译,分支即操作符表
    bool_q: dict = {'must': [], 'must_not': []}
    sort_list: list = []
    for r in rules or []:
        field, op, value = _parts(r)
        if not field or not op:
            continue
        if op in SORT_OPS:
            sort_list.append({field: {'order': 'asc' if op == 'sort_asc' else 'desc'}})
        elif op == 'eq':
            bool_q['must'].append({'term': {field: value}})
        elif op == 'neq':
            bool_q['must_not'].append({'term': {field: value}})
        elif op in ('gt', 'gte', 'lt', 'lte'):
            bool_q['must'].append({'range': {field: {op: value}}})
        elif op == 'in':
            bool_q['must'].append({'terms': {field: value}})
        elif op == 'nin':
            bool_q['must_not'].append({'terms': {field: value}})
        elif op == 'contains':
            bool_q['must'].append({'wildcard': {field: f'*{value}*'}})
        elif op == 'ncontains':
            bool_q['must_not'].append({'wildcard': {field: f'*{value}*'}})
        elif op == 'between':
            bool_q['must'].append({'range': {field: {'gte': value[0], 'lte': value[1]}}})
        elif op == 'notnull':
            bool_q['must'].append({'exists': {'field': field}})
        elif op == 'isnull':
            bool_q['must_not'].append({'exists': {'field': field}})
    if not bool_q['must'] and not bool_q['must_not']:
        return {'match_all': {}}, sort_list
    return {'bool': {k: v for k, v in bool_q.items() if v}}, sort_list


# ---------- MongoDB ----------
def to_mongo(rules: list[dict]) -> tuple[dict, list]:
    mops = {'gt': '$gt', 'gte': '$gte', 'lt': '$lt', 'lte': '$lte', 'neq': '$ne', 'in': '$in', 'nin': '$nin'}
    flt: dict = {}
    sort_list: list = []
    for r in rules or []:
        field, op, value = _parts(r)
        if not field or not op:
            continue
        if op in SORT_OPS:
            sort_list.append((field, 1 if op == 'sort_asc' else -1))
        elif op == 'eq':
            flt[field] = value
        elif op in mops:
            flt.setdefault(field, {})[mops[op]] = value
        elif op == 'contains':
            flt[field] = {'$regex': value}
        elif op == 'ncontains':
            flt[field] = {'$not': {'$regex': value}}
        elif op == 'between':
            flt[field] = {'$gte': value[0], '$lte': value[1]}
        elif op == 'isnull':
            flt[field] = None
        elif op == 'notnull':
            flt[field] = {'$ne': None}
    return flt, sort_list
