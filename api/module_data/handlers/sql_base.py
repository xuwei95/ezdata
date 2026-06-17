"""
SQL 族 handler 共享基类。

一个 SQLAlchemy Engine 串起 连接测试/反射/原生查询/dlt 取数/dlt 写数(已实测)。
各 SQL handler 只需:设 name/title、driver,必要时覆写 _build_url(方言专属参数)。
dlt 用同步驱动(pymysql 等),勿用 app 的 asyncmy。
"""

import time
from collections.abc import Iterable
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine, inspect, text

from module_data.handlers.base import Capability, Column, Connector, ConnectResult


class SqlConnector(Connector):
    family = 'rdbms'
    capabilities = (
        Capability.READ | Capability.WRITE | Capability.EXTRACT
        | Capability.SCHEMA | Capability.GEN_API
    )
    driver: str = ''            # SQLAlchemy driver 前缀,如 'mysql+pymysql'
    default_port: int | None = None

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._engine: Engine | None = None

    # 通用 URL 拼接;方言专属(sslmode/dsn/sid/server 等)由子类覆写
    def _build_url(self) -> str:
        url = self.arg('url')                       # 部分源(如 mysql)支持直接给完整 URL
        if url:
            return url
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        user = self.arg('user', 'username', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        database = self.arg('database', default='')
        return f'{self.driver}://{user}:{pwd}@{host}:{port}/{database}'

    def _engine_kwargs(self) -> dict:
        kw = self.arg('options', 'connection_parameters', default={}) or {}
        return dict(kw)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self._build_url(), pool_pre_ping=True, **self._engine_kwargs())
        return self._engine

    def test_connection(self) -> ConnectResult:
        t0 = time.perf_counter()
        try:
            with self.engine.connect() as c:
                c.execute(text('SELECT 1'))
            return ConnectResult(True, 'ok', (time.perf_counter() - t0) * 1000)
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return inspect(self.engine).get_table_names()

    def get_columns(self, table: str) -> list[Column]:
        cols = inspect(self.engine).get_columns(table)
        return [Column(name=c['name'], type=str(c['type']),
                       nullable=c.get('nullable', True), comment=c.get('comment') or '') for c in cols]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """参数化原生 SQL(绝不拼接);limit 作为强制上限兜底。"""
        sql = statement
        if limit is not None and 'limit' not in sql.lower():
            sql = f'SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}'
        with self.engine.connect() as c:
            return [dict(r) for r in c.execute(text(sql), params or {}).mappings()]

    def search(self, table: str, filters: list[dict] | None = None, page: int = 1,
               pagesize: int = 20, *, schema: str | None = None, **kwargs: Any) -> dict:
        """分页查询:SELECT ... LIMIT/OFFSET + COUNT(*)。"""
        from sqlalchemy import MetaData, Table, func, select

        from module_data.query import sqlalchemy_adapter

        t = Table(table, MetaData(), autoload_with=self.engine, schema=schema)
        stmt = select(t)
        if filters:
            stmt = sqlalchemy_adapter(filters)(stmt, t)
        with self.engine.connect() as c:
            total = c.execute(select(func.count()).select_from(stmt.order_by(None).subquery())).scalar()
            rows = c.execute(stmt.limit(pagesize).offset((page - 1) * pagesize)).mappings().all()
        return {'records': [dict(r) for r in rows], 'total': total, 'page': page, 'pagesize': pagesize}

    def extract(self, table: str, *, schema: str | None = None, backend: str = 'pyarrow',
                chunk_size: int = 50_000, incremental_key: str | None = None,
                filters: list[dict] | None = None, **kwargs: Any) -> Any:
        from dlt.sources.sql_database import sql_table

        # 统一过滤结构 -> query_adapter_callback(WHERE/ORDER BY)
        if filters and 'query_adapter_callback' not in kwargs:
            from module_data.query import sqlalchemy_adapter

            kwargs['query_adapter_callback'] = sqlalchemy_adapter(filters)
        incremental = None
        if incremental_key:
            import dlt

            incremental = dlt.sources.incremental(incremental_key)
        return sql_table(credentials=self.engine, table=table, schema=schema,
                         backend=backend, chunk_size=chunk_size, incremental=incremental, **kwargs)

    def write(self, data: Iterable[dict] | Any, table: str, mode: str = 'append',
              *, dataset: str = 'public', pipeline_name: str = 'data_write', **kwargs: Any) -> Any:
        import dlt

        dest = dlt.destinations.sqlalchemy(credentials=self.engine)
        pipe = dlt.pipeline(pipeline_name=pipeline_name, destination=dest, dataset_name=dataset)
        return pipe.run(data, table_name=table, write_disposition=mode, **kwargs)
