"""
S3 / 对象存储 handler。

借鉴 MindsDB s3_handler 的核心做法:用 DuckDB + httpfs 把对象存储变成可 SQL 查询
(SELECT ... FROM 's3://bucket/path/*.parquet'),契合 plan「文件族 = DuckDB 读」。
  - query / get_columns:DuckDB httpfs 直接查 csv/parquet/json(endpoint_url 兼容 MinIO/OSS);
  - list_tables / write:boto3;
  - extract:dlt filesystem 源(批量装载)。
"""

from typing import Any
from urllib.parse import urlparse

from module_data.handlers.base import Capability, Column, Connector, ConnectResult
from module_data.handlers.s3_handler.connection_args import connection_args, connection_args_example


class S3Handler(Connector):
    name = 's3'
    title = 'S3 / 对象存储'
    family = 'file'
    capabilities = (
        Capability.READ | Capability.EXTRACT | Capability.WRITE
        | Capability.SCHEMA
    )
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None

    # ---------- boto3(连接测试 / 列举 / 上传)----------
    def _client_kwargs(self) -> dict:
        kw: dict = {
            'aws_access_key_id': self.arg('aws_access_key_id'),
            'aws_secret_access_key': self.arg('aws_secret_access_key'),
        }
        if self.arg('region_name'):
            kw['region_name'] = self.arg('region_name')
        if self.arg('aws_session_token'):
            kw['aws_session_token'] = self.arg('aws_session_token')
        if self.arg('endpoint_url'):
            kw['endpoint_url'] = self.arg('endpoint_url')
        return kw

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client('s3', **self._client_kwargs())
        return self._client

    @property
    def bucket(self) -> str:
        return self.arg('bucket')

    def test_connection(self) -> ConnectResult:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self, prefix: str = '') -> list[str]:
        """列对象 key(当作"表")。"""
        resp = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [o['Key'] for o in resp.get('Contents', [])]

    # ---------- DuckDB + httpfs(SQL 查询 / 结构)----------
    def _duckdb(self) -> Any:
        """建一个配好 httpfs + S3 凭据的内存 DuckDB 连接。"""
        import duckdb

        con = duckdb.connect(':memory:')
        try:
            con.execute('INSTALL httpfs')
        except Exception:
            con.execute('FORCE INSTALL httpfs')
        con.execute('LOAD httpfs')
        con.execute(f"SET s3_access_key_id='{self.arg('aws_access_key_id')}'")
        con.execute(f"SET s3_secret_access_key='{self.arg('aws_secret_access_key')}'")
        if self.arg('aws_session_token'):
            con.execute(f"SET s3_session_token='{self.arg('aws_session_token')}'")

        endpoint = self.arg('endpoint_url')
        if endpoint:                                   # MinIO/OSS 兼容
            u = urlparse(endpoint if '://' in endpoint else f'http://{endpoint}')
            con.execute(f"SET s3_endpoint='{u.netloc or u.path}'")
            con.execute("SET s3_url_style='path'")
            con.execute(f"SET s3_use_ssl={'true' if u.scheme == 'https' else 'false'}")
        else:
            con.execute(f"SET s3_region='{self.arg('region_name', default='us-east-1')}'")
        return con

    def _uri(self, table: str) -> str:
        """把 key/glob 拼成 s3:// URI(已是完整 URI 则原样)。"""
        return table if table.startswith('s3://') else f's3://{self.bucket}/{table}'

    def get_columns(self, table: str) -> list[Column]:
        """DuckDB 自动按扩展名识别 csv/parquet/json,DESCRIBE 推断字段。"""
        con = self._duckdb()
        rows = con.execute(f"DESCRIBE SELECT * FROM '{self._uri(table)}'").fetchall()
        con.close()
        # DESCRIBE 列: column_name, column_type, null, key, default, extra
        return [Column(name=r[0], type=str(r[1]), nullable=(r[2] != 'NO')) for r in rows]

    def sample_query(self, table: str, limit: int = 100) -> str:
        return f"SELECT * FROM 's3://{self.bucket}/{table}' LIMIT {limit}"

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """
        DuckDB SQL 查询。statement 可直接引用 's3://bucket/..' 文件;
        也支持把表名当文件:用 read('<table>') 占位会被替换成对应 URI。
        """
        sql = statement.replace("read('", f"'s3://{self.bucket}/").replace("')", "'") \
            if "read('" in statement else statement
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
        sql = statement.replace("read('", f"'s3://{self.bucket}/").replace("')", "'") \
            if "read('" in statement else statement
        con = self._duckdb()
        try:
            return con.execute(sql, params or {}).fetch_arrow_table()
        finally:
            con.close()

    # ---------- dlt(批量抽取)----------
    def extract(self, table: str, *, file_glob: str | None = None, **kwargs: Any) -> Any:
        """用 dlt filesystem 源读取桶内文件(table 作为前缀/glob)。"""
        from dlt.sources.filesystem import filesystem

        endpoint = self.arg('endpoint_url')
        creds = {
            'aws_access_key_id': self.arg('aws_access_key_id'),
            'aws_secret_access_key': self.arg('aws_secret_access_key'),
        }
        if endpoint:
            creds['endpoint_url'] = endpoint
        return filesystem(bucket_url=f's3://{self.bucket}', credentials=creds,
                          file_glob=file_glob or f'{table}*')

    def write(self, data: bytes | str, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        """简单上传:把 data 作为对象写到 key=table。"""
        body = data.encode() if isinstance(data, str) else data
        self.client.put_object(Bucket=self.bucket, Key=table, Body=body)
        return {'written_key': table}
