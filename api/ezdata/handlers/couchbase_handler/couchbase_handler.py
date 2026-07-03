"""Couchbase handler:文档库 N1QL(couchbase SDK 4.x),原生 client + dlt resource。"""

from typing import Any

from ezdata.handlers.base import Capability, Connector, ConnectResult
from ezdata.handlers.couchbase_handler.connection_args import connection_args, connection_args_example


class CouchbaseHandler(Connector):
    name = 'couchbase'
    title = 'Couchbase'
    family = 'document'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._cluster = None

    @property
    def bucket(self) -> str:
        return self.arg('bucket')

    @property
    def cluster(self) -> Any:
        def _make():
            from couchbase.auth import PasswordAuthenticator
            from couchbase.cluster import Cluster
            from couchbase.options import ClusterOptions
            opts = ClusterOptions(PasswordAuthenticator(self.arg('user', default=''), self.arg('password', default='')))
            cs = self.arg('connection_string') or f"couchbase://{self.arg('host', default='127.0.0.1')}"
            return Cluster(cs, opts)
        return self._lazy('_cluster', _make)

    def test_connection(self) -> ConnectResult:
        try:
            self.cluster.ping()
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        """列出 collection(N1QL system catalog)。"""
        rows = self.cluster.query('SELECT name FROM system:keyspaces')
        return [r['name'] for r in rows]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """N1QL 查询(命名参数走 SDK 的 named_parameters)。"""
        n1ql = statement
        if limit is not None and 'limit' not in n1ql.lower():
            n1ql = f'{n1ql.rstrip().rstrip(";")} LIMIT {int(limit)}'
        result = self.cluster.query(n1ql, **({'named_parameters': params} if params else {}))
        return list(result)

    def extract(self, table: str, **kwargs: Any) -> Any:
        """table 作为 collection/keyspace,抽取全部文档。"""
        import dlt

        cluster, scope, bucket = self.cluster, self.arg('scope', default='_default'), self.bucket

        @dlt.resource(name=table, write_disposition='append')
        def _docs() -> Any:
            yield from cluster.query(f'SELECT * FROM `{bucket}`.`{scope}`.`{table}`')

        return _docs

    def write(self, data: Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        """写入文档到 collection(需 _id 作为 key,否则自动生成)。"""
        import uuid

        coll = self.cluster.bucket(self.bucket).scope(self.arg('scope', default='_default')).collection(table)
        n = 0
        for rec in data:
            key = str(rec.get('_id') or uuid.uuid4().hex)
            coll.upsert(key, rec)
            n += 1
        return {'written': n}
