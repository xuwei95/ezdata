"""沙箱只读护栏:包住注入沙箱的 handler,强制取数只读。

`run_datasource_query` 把 agent 手写的 Python 代码丢进沙箱 exec,代码里的
`handler.query("...")` 语句在工具层无法静态检查(SQL 串藏在代码内)。因此把只读
护栏下沉到**被注入的 handler** 这一唯一必经点:query 前跑 `assert_readonly_sql`,
写路径方法(write/extract/stream)直接拒绝。

作用范围仅限沙箱取数注入(pydata/pyextract),二者设计上都是只读;ETL 的写入/装载走
另一条路(runner 进程内 handler.write / _load),不经此代理,故不受影响。
"""

from typing import Any

from ezdata.utils.etl_util import assert_readonly_sql

# 写路径方法:沙箱取数场景一律禁用(写入/装载请走数据集成任务)
_BLOCKED_METHODS = frozenset({'write', 'extract', 'stream'})


class ReadOnlyHandler:
    """只读代理:query 强制只读 SQL 护栏、禁用写路径方法,其余透传给被包裹 handler。

    - query(statement, ...):先 `assert_readonly_sql(statement, family)`——SQL 族
      (rdbms/timeseries)拦截写入/DDL/多语句;非 SQL 族(akshare 函数名、ES/Mongo DSL)
      与非字符串语句天然放行,取数不受影响。
    - write / extract / stream:直接拒绝(沙箱取数只读)。
    - 其余(list_tables/get_columns/sample_query/aggregate/close/family/capabilities…)透传。
    """

    def __init__(self, handler: Any) -> None:
        object.__setattr__(self, '_h', handler)

    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> Any:
        assert_readonly_sql(statement, getattr(self._h, 'family', None))
        return self._h.query(statement, params, limit)

    def __getattr__(self, name: str) -> Any:
        # 类上未显式定义的属性才会走到这里(query/__init__ 已定义,不受影响)
        if name in _BLOCKED_METHODS:
            def _blocked(*_a: Any, **_k: Any) -> Any:
                raise PermissionError(f'沙箱取数为只读,禁止 {name}():写入/装载请用数据集成任务')

            return _blocked
        return getattr(self._h, name)


def read_only(handler: Any) -> ReadOnlyHandler:
    """把 handler 包成只读代理,供注入沙箱使用。"""
    return ReadOnlyHandler(handler)
