"""指标层 SQL 族下推 端到端对拍测试。

核心命题:handler.aggregate 下推结果 == 拉数 + pandas 兜底结果(_aggregate),口径一致。
SQL 族用 sqlite 真库端到端跑;并覆盖 metric_service._execute 的"下推优先 + 异常兜底"路由。
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ezdata.handlers.agg_spec import AggSpec
from ezdata.handlers.base import Capability
from ezdata.handlers.sqlite_handler.sqlite_handler import SQLiteHandler
from module_data.service import metric_service as M

# 财经样例:各板块金额分布,sum 互不相等(便于 top_n 无并列歧义)
_ROWS = [
    ('2024-01-01', '600519', 'baijiu', 100.0, 3),
    ('2024-01-02', '600519', 'baijiu', 150.0, 2),
    ('2024-01-02', '000001', 'bank', 200.0, 5),
    ('2024-02-01', '000001', 'bank', 60.0, 1),
    ('2024-02-01', '601318', 'insurance', 300.0, 4),
]


def _norm(rows):
    """归一为可比较集合:数值 round(4),其余转 str;忽略行序与列序。"""
    def cell(v):
        return round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else (None if v is None else str(v))

    return sorted(tuple(sorted((k, cell(v)) for k, v in r.items())) for r in rows)


@pytest.fixture()
def sqlite_handler():
    f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    f.close()
    import sqlite3

    con = sqlite3.connect(f.name)
    con.execute('CREATE TABLE trades(dt TEXT, symbol TEXT, sector TEXT, amount REAL, qty INTEGER)')
    con.executemany('INSERT INTO trades VALUES(?,?,?,?,?)', _ROWS)
    con.commit()
    con.close()
    h = SQLiteHandler({'db_file': f.name})
    yield h
    h.close()  # 释放 engine,否则 Windows 无法删临时库
    try:
        os.unlink(f.name)
    except OSError:
        pass


def _md(measure, dimensions=None, default_filters=None, time_field=None, unit='', caliber=''):
    """构造与 DataMetric 存储形态一致的 md(measure/dimensions/default_filters 为 JSON 串)。"""
    return {
        'measure': json.dumps(measure),
        'dimensions': json.dumps([{'field': d, 'name': d} for d in (dimensions or [])]),
        'default_filters': json.dumps(default_filters or {}),
        'time_field': time_field,
        'unit': unit,
        'caliber': caliber,
    }


# --------------------------------------------------------------------------- #
# SQL 族:下推 vs pandas 兜底 逐组合对拍(sqlite 真库)
# --------------------------------------------------------------------------- #
_SQL_CASES = [
    # (measure, group_by, filters, time_range, top_n)
    ({'agg': 'sum', 'field': 'amount'}, ['sector'], None, None, 0),
    ({'agg': 'avg', 'field': 'amount'}, ['sector'], None, None, 0),
    ({'agg': 'max', 'field': 'amount'}, ['sector'], None, None, 0),
    ({'agg': 'min', 'field': 'amount'}, ['sector'], None, None, 0),
    ({'agg': 'count', 'field': None}, ['sector'], None, None, 0),
    ({'agg': 'count_distinct', 'field': 'symbol'}, ['sector'], None, None, 0),
    ({'agg': 'sum', 'field': 'amount'}, [], None, None, 0),  # 总值
    ({'agg': 'avg', 'field': 'amount'}, [], None, None, 0),
    ({'agg': 'count', 'field': None}, [], None, None, 0),
    ({'agg': 'count_distinct', 'field': 'symbol'}, [], None, None, 0),
    ({'agg': 'sum', 'field': 'amount'}, ['sector'], {'sector': ['bank', 'baijiu']}, None, 0),  # IN 过滤
    ({'agg': 'sum', 'field': 'amount'}, ['sector'], {'sector': 'bank'}, None, 0),  # 等值过滤
    ({'agg': 'sum', 'field': 'amount'}, ['sector'], None, {'start': '2024-01-01', 'end': '2024-01-31'}, 0),  # 时间范围
    ({'agg': 'sum', 'field': 'amount'}, ['sector'], None, None, 2),  # top_n(sum 无并列)
    ({'agg': 'sum', 'field': 'amount'}, ['sector', 'symbol'], None, None, 0),  # 多维
]


@pytest.mark.parametrize('measure, group_by, filters, time_range, top_n', _SQL_CASES)
def test_sql_pushdown_matches_pandas(sqlite_handler, measure, group_by, filters, time_range, top_n):
    md = _md(measure, dimensions=group_by, time_field='dt')
    spec = AggSpec(
        table='trades', measure=measure, group_by=list(group_by),
        filters=filters or {}, time_field='dt', time_range=time_range, top_n=top_n,
    )
    pushed = M._shape('m', md, sqlite_handler.aggregate(spec))['rows']

    full = sqlite_handler.query('SELECT * FROM trades')
    fallback = M._aggregate('m', md, full, group_by or None, filters, time_range, top_n)['rows']

    assert _norm(pushed) == _norm(fallback), f'下推≠兜底\n下推={pushed}\n兜底={fallback}'
    if top_n:  # top_n 生效性
        assert len(pushed) <= top_n


def test_sql_pushdown_values_are_correct(sqlite_handler):
    """独立核验绝对值(不只对拍),防两路同错。"""
    spec = AggSpec(table='trades', measure={'agg': 'sum', 'field': 'amount'}, group_by=['sector'])
    got = {r['sector']: r['value'] for r in sqlite_handler.aggregate(spec)}
    assert got == {'baijiu': 250.0, 'bank': 260.0, 'insurance': 300.0}


# --------------------------------------------------------------------------- #
# metric_service._execute:下推优先 + 兜底路由,两路口径一致
# --------------------------------------------------------------------------- #
_EXPECT = [
    {'sector': 'baijiu', 'value': 250.0},
    {'sector': 'bank', 'value': 260.0},
    {'sector': 'insurance', 'value': 300.0},
]


def test_execute_uses_pushdown_and_matches_fallback(sqlite_handler):
    md = _md({'agg': 'sum', 'field': 'amount'}, dimensions=['sector'], time_field='dt')
    out = M._execute('m', md, sqlite_handler, 'trades', None, None, None, None)['rows']
    full = sqlite_handler.query('SELECT * FROM trades')
    fb = M._aggregate('m', md, full, None, None, None, None)['rows']
    assert _norm(out) == _norm(fb) == _norm(_EXPECT)


def test_execute_falls_back_when_no_aggregate_capability(sqlite_handler, monkeypatch):
    """源不具备 AGGREGATE 能力时,_execute 应回退拉数+pandas,结果不变。"""
    md = _md({'agg': 'sum', 'field': 'amount'}, dimensions=['sector'], time_field='dt')
    pushed = M._execute('m', md, sqlite_handler, 'trades', None, None, None, None)['rows']
    monkeypatch.setattr(sqlite_handler, 'capabilities', Capability.READ | Capability.SCHEMA, raising=False)
    fell_back = M._execute('m', md, sqlite_handler, 'trades', None, None, None, None)['rows']
    assert _norm(pushed) == _norm(fell_back)


def test_execute_falls_back_on_pushdown_exception(sqlite_handler, monkeypatch):
    """下推抛非 AggNotSupported 异常也应兜底(不让指标查询整体失败)。"""
    md = _md({'agg': 'sum', 'field': 'amount'}, dimensions=['sector'], time_field='dt')

    def boom(spec):
        raise RuntimeError('模拟方言/字段错误')

    monkeypatch.setattr(sqlite_handler, 'aggregate', boom)
    out = M._execute('m', md, sqlite_handler, 'trades', None, None, None, None)['rows']
    assert _norm(out) == _norm(_EXPECT)
