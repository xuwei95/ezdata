"""
GCS handler:仿 S3 —— fsspec(gcsfs)+ DuckDB register_filesystem 做 SQL 查询,dlt filesystem 抽取。
"""

import json
from typing import Any

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.gcs_handler.connection_args import connection_args, connection_args_example


class GCSHandler(Connector):
    name = 'gcs'
    title = 'Google Cloud Storage'
    family = 'file'
    capabilities = Capability.READ | Capability.EXTRACT | Capability.WRITE | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _token(self) -> Any:
        sa = self.arg('service_account_json') or self.arg('service_account_keys')
        if isinstance(sa, str) and sa.strip().startswith('{'):
            return json.loads(sa)
        return sa  # 路径 / None(走默认 ADC)

    def _fs(self) -> Any:
        import gcsfs

        return gcsfs.GCSFileSystem(token=self._token())

    @property
    def bucket(self) -> str:
        return self.arg('bucket')

    def _duckdb(self) -> Any:
        import duckdb

        con = duckdb.connect(':memory:')
        con.register_filesystem(self._fs())
        return con

    def _uri(self, table: str) -> str:
        return table if '://' in table else f'gcs://{self.bucket}/{table}'

    def test_connection(self) -> ConnectResult:
        try:
            self._fs().ls(self.bucket)
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self, prefix: str = '') -> list[str]:
        return self._fs().ls(f'{self.bucket}/{prefix}' if prefix else self.bucket)

    def get_columns(self, table: str) -> list[Column]:
        con = self._duckdb()
        rows = con.execute(f"DESCRIBE SELECT * FROM '{self._uri(table)}'").fetchall()
        con.close()
        return [Column(name=r[0], type=str(r[1]), nullable=(r[2] != 'NO')) for r in rows]

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        sql = statement
        if limit is not None and 'limit' not in sql.lower():
            sql = f'SELECT * FROM ({sql}) AS _q LIMIT {int(limit)}'
        con = self._duckdb()
        try:
            cur = con.execute(sql, params or {})
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]
        finally:
            con.close()

    def query_arrow(self, statement: str, params: dict | None = None) -> Any:
        """DuckDB 查询直接返回 pyarrow.Table(列式;供 dlt 高吞吐装载,ETL 快路用)。"""
        con = self._duckdb()
        try:
            return con.execute(statement, params or {}).fetch_arrow_table()
        finally:
            con.close()

    def extract(self, table: str, *, file_glob: str | None = None, **kwargs: Any) -> Any:
        from dlt.sources.filesystem import filesystem

        return filesystem(bucket_url=f'gs://{self.bucket}', credentials=self._token(),
                          file_glob=file_glob or f'{table}*')

    def write(self, data: bytes | str, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        body = data.encode() if isinstance(data, str) else data
        with self._fs().open(f'{self.bucket}/{table}', 'wb') as f:
            f.write(body)
        return {'written_key': table}
