"""Cassandra handler:CQL 宽列存储(cassandra-driver),原生 client + dlt resource。"""

from typing import Any

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.cassandra_handler.connection_args import connection_args, connection_args_example


class CassandraHandler(Connector):
    name = 'cassandra'
    title = 'Apache Cassandra'
    family = 'wide_column'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example
    _driver_module = 'cassandra'        # scylla-driver 也用 cassandra.* 命名空间

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._session = None

    @property
    def keyspace(self) -> str | None:
        return self.arg('keyspace')

    @property
    def session(self) -> Any:
        if self._session is None:
            from cassandra.auth import PlainTextAuthProvider
            from cassandra.cluster import Cluster

            auth = None
            if self.arg('user'):
                auth = PlainTextAuthProvider(username=self.arg('user'), password=self.arg('password', default=''))
            hosts = [h.strip() for h in str(self.arg('host', default='127.0.0.1')).split(',')]
            cluster = Cluster(hosts, port=int(self.arg('port', default=9042)), auth_provider=auth)
            self._session = cluster.connect(self.keyspace) if self.keyspace else cluster.connect()
        return self._session

    def test_connection(self) -> ConnectResult:
        try:
            self.session.execute('SELECT now() FROM system.local')
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        rows = self.session.execute(
            'SELECT table_name FROM system_schema.tables WHERE keyspace_name=%s', (self.keyspace,))
        return [r.table_name for r in rows]

    def get_columns(self, table: str) -> list[Column]:
        rows = self.session.execute(
            'SELECT column_name, type FROM system_schema.columns WHERE keyspace_name=%s AND table_name=%s',
            (self.keyspace, table))
        return [Column(name=r.column_name, type=r.type) for r in rows]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        cql = statement
        if limit is not None and 'limit' not in cql.lower():
            cql = f'{cql.rstrip().rstrip(";")} LIMIT {int(limit)}'
        rows = self.session.execute(cql, params or None)
        return [dict(r._asdict()) for r in rows]

    def extract(self, table: str, *, chunk_size: int = 1000, **kwargs: Any) -> Any:
        import dlt

        session, ks = self.session, self.keyspace
        fq = f'{ks}.{table}' if ks else table

        @dlt.resource(name=table, write_disposition='append')
        def _rows() -> Any:
            stmt = session.prepare(f'SELECT * FROM {fq}')
            stmt.fetch_size = chunk_size
            for r in session.execute(stmt):
                yield dict(r._asdict())

        return _rows

    def write(self, data: Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        ks = self.keyspace
        fq = f'{ks}.{table}' if ks else table
        n = 0
        for rec in data:
            cols = ','.join(rec)
            ph = ','.join(['%s'] * len(rec))
            self.session.execute(f'INSERT INTO {fq} ({cols}) VALUES ({ph})', list(rec.values()))
            n += 1
        return {'written': n}
