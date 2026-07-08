"""InfluxDB 3.x handler:时序库(influxdb3-python),支持 SQL 查询,原生 client + dlt resource。"""

from typing import Any

from ezdata.handlers.base import Capability, Connector, ConnectResult
from ezdata.handlers.influxdb_handler.connection_args import connection_args, connection_args_example


class InfluxDBHandler(Connector):
    name = 'influxdb'
    title = 'InfluxDB'
    family = 'timeseries'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None

    @property
    def client(self) -> Any:
        def _make():
            from influxdb_client_3 import InfluxDBClient3

            return InfluxDBClient3(
                host=self.arg('host', default='http://127.0.0.1:8181'),
                token=self.arg('token', default=''),
                database=self.arg('database', default=''),
                org=self.arg('org') or None,
            )

        return self._lazy('_client', _make)

    def _rows(self, sql: str) -> list[dict]:
        table = self.client.query(query=sql, language='sql')  # 返回 pyarrow.Table
        return table.to_pylist()

    def test_connection(self) -> ConnectResult:
        try:
            self._rows('SELECT 1')
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return [r.get('table_name') or r.get('name') for r in self._rows('SHOW TABLES')]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        sql = statement
        if limit is not None and 'limit' not in sql.lower():
            sql = f'SELECT * FROM ({sql}) LIMIT {int(limit)}'
        return self._rows(sql)

    def extract(self, table: str, **kwargs: Any) -> Any:
        import dlt

        handler = self

        @dlt.resource(name=table, write_disposition='append')
        def _measure() -> Any:
            yield from handler._rows(f'SELECT * FROM "{table}"')

        return _measure
