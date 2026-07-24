"""沙箱只读护栏(ReadOnlyHandler)单测。

命题:注入沙箱的 handler 被 read_only() 包裹后,
- SQL 族(rdbms/timeseries)的写入/DDL/多语句 query 被拦截;
- 只读 SQL、非 SQL 族(akshare 函数名/ES·Mongo DSL)、非字符串语句放行;
- 写路径方法(write/extract/stream)一律拒绝;
- 其余属性/方法透传给被包裹 handler。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ezdata.errors import ReadOnlyViolation
from ezdata.handlers.sandbox_guard import read_only


class _FakeHandler:
    """最小假 handler:记录 query 收到的语句,声明 family。"""

    def __init__(self, family: str) -> None:
        self.family = family
        self.name = 'fake'
        self.last = None

    def query(self, statement, params=None, limit=None):
        self.last = (statement, params, limit)
        return [{'ok': 1}]

    def write(self, *a, **k):
        return 'WROTE'

    def extract(self, *a, **k):
        return 'EXTRACTED'

    def stream(self, *a, **k):
        return iter(())

    def list_tables(self):
        return ['t1', 't2']


# ---------------- SQL 族:拦截写入/DDL/多语句 ----------------

@pytest.mark.parametrize('bad_sql', [
    'DELETE FROM t WHERE 1=1',
    'DROP TABLE t',
    'UPDATE t SET a=1',
    'INSERT INTO t VALUES (1)',
    'TRUNCATE TABLE t',
    'ALTER TABLE t ADD c int',
    'SELECT 1; DROP TABLE t',            # 多语句堆叠
    'select * from t into outfile "/x"',  # 导出文件
])
def test_sql_family_blocks_writes(bad_sql):
    h = read_only(_FakeHandler('rdbms'))
    with pytest.raises(ReadOnlyViolation):
        h.query(bad_sql)


@pytest.mark.parametrize('good_sql', [
    'SELECT * FROM t',
    'select a, b from t where c > 0 limit 10',
    'WITH x AS (SELECT 1) SELECT * FROM x',
    'SHOW TABLES',
    'EXPLAIN SELECT 1',
])
def test_sql_family_allows_readonly(good_sql):
    inner = _FakeHandler('timeseries')
    h = read_only(inner)
    assert h.query(good_sql) == [{'ok': 1}]
    assert inner.last[0] == good_sql


# ---------------- 非 SQL 族 / 非字符串:天然放行 ----------------

def test_api_family_function_name_passthrough():
    """akshare/ccxt 用函数名取数,即便像危险词也不按 SQL 校验。"""
    inner = _FakeHandler('api')
    h = read_only(inner)
    # 函数名不是 SELECT 开头,若误判 SQL 会被拦;api 族应放行
    assert h.query('bond_zh_us_rate', {'start_date': '20130101'}) == [{'ok': 1}]


@pytest.mark.parametrize('family', ['search', 'document'])
def test_dsl_dict_passthrough(family):
    """ES DSL / Mongo pipeline 是 dict,非字符串,直接放行。"""
    h = read_only(_FakeHandler(family))
    assert h.query({'query': {'match_all': {}}}, None, 100) == [{'ok': 1}]


# ---------------- 写路径方法:一律拒绝 ----------------

@pytest.mark.parametrize('method', ['write', 'extract', 'stream'])
def test_write_path_methods_blocked(method):
    h = read_only(_FakeHandler('rdbms'))
    with pytest.raises(PermissionError):
        getattr(h, method)('data', 't')


# ---------------- 其余属性/方法透传 ----------------

def test_passthrough_read_methods_and_attrs():
    inner = _FakeHandler('rdbms')
    h = read_only(inner)
    assert h.list_tables() == ['t1', 't2']
    assert h.family == 'rdbms'
    assert h.name == 'fake'
