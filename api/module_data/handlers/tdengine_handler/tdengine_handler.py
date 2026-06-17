"""TDengine handler:时序库(taospy,REST 连接),TDengine SQL,原生 client + dlt resource。"""

from typing import Any

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.tdengine_handler.connection_args import connection_args, connection_args_example


class TDengineHandler(Connector):
    name = 'tdengine'
    title = 'TDengine'
    family = 'timeseries'
    capabilities = Capability.READ | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._conn = None

    @property
    def conn(self) -> Any:
        if self._conn is None:
            import taosrest

            self._conn = taosrest.connect(
                url=self.arg('url', default='http://127.0.0.1:6041'),
                token=self.arg('token') or None,
                user=self.arg('user', default='root'),
                password=self.arg('password', default='taosdata'),
                database=self.arg('database') or None)
        return self._conn

    def _rows(self, sql: str) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
        cur.close()
        return rows

    def test_connection(self) -> ConnectResult:
        try:
            self._rows('SELECT SERVER_VERSION()')
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return [next(iter(r.values())) for r in self._rows('SHOW TABLES')]

    def get_columns(self, table: str) -> list[Column]:
        return [Column(name=r.get('field') or r.get('Field'), type=r.get('type') or r.get('Type', ''))
                for r in self._rows(f'DESCRIBE {table}')]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        sql = statement
        if limit is not None and 'limit' not in sql.lower():
            sql = f'{sql.rstrip().rstrip(";")} LIMIT {int(limit)}'
        return self._rows(sql)

    def extract(self, table: str, **kwargs: Any) -> Any:
        import dlt

        handler = self

        @dlt.resource(name=table, write_disposition='append')
        def _rows() -> Any:
            yield from handler._rows(f'SELECT * FROM {table}')

        return _rows
