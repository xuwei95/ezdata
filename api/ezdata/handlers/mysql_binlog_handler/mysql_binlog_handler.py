"""
MySQL Binlog handler:CDC 变更数据捕获(mysql-replication / pymysqlreplication)。

借鉴旧版 etl/data_models/mysql_binlog.py:BinLogStreamReader 读 insert/update/delete 行事件。
  - test_connection:校验连通 + binlog 是否开启;
  - query:有界预览(blocking=False,读最多 N 个变更);
  - stream:长驻 CDC,持续 yield 变更事件(供 worker);
  - extract:有界一批包成 dlt resource(微批装载)。
只读,无 WRITE 能力。

服务端前提:① log_bin=ON;② binlog_format=ROW;③ binlog_row_metadata=FULL(否则列名为 UNKNOWN_COLx);
账号需 REPLICATION SLAVE / REPLICATION CLIENT 权限。
"""

import random
from collections.abc import Iterator
from typing import Any

import pymysql

from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.mysql_binlog_handler.connection_args import connection_args, connection_args_example


class MySQLBinlogHandler(Connector):
    name = 'mysql_binlog'
    title = 'MySQL Binlog (CDC)'
    family = 'cdc'
    capabilities = Capability.EXTRACT | Capability.STREAM | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _conn_setting(self) -> dict:
        return {
            'host': self.arg('host', default='127.0.0.1'),
            'port': int(self.arg('port', default=3306)),
            'user': self.arg('user', 'username', default='root'),
            'passwd': str(self.arg('password', default='')),
        }

    def _only_events(self, events: list[str] | None) -> list | None:
        from pymysqlreplication.row_event import DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent

        mapping = {'insert': WriteRowsEvent, 'update': UpdateRowsEvent, 'delete': DeleteRowsEvent}
        if not events:
            return [WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent]
        return [mapping[e] for e in events if e in mapping]

    def _reader(
        self, *, blocking: bool, resume: bool, only_tables: list[str] | None, only_events: list[str] | None
    ) -> Any:
        from pymysqlreplication import BinLogStreamReader

        return BinLogStreamReader(
            connection_settings=self._conn_setting(),
            server_id=int(self.arg('server_id') or random.randint(10000, 99999)),
            freeze_schema=False,  # 查实时表结构以解析真实列名(否则 MINIMAL 元数据会得到 UNKNOWN_COL)
            resume_stream=resume,  # True=只接最新, False=从头
            blocking=blocking,
            only_schemas=[self.arg('database')] if self.arg('database') else None,
            only_tables=only_tables,
            only_events=self._only_events(only_events),
        )

    @staticmethod
    def _to_event(binlogevent: Any, row: dict) -> dict:
        from pymysqlreplication.row_event import DeleteRowsEvent, UpdateRowsEvent

        if isinstance(binlogevent, DeleteRowsEvent):
            action, data = 'delete', row['values']
        elif isinstance(binlogevent, UpdateRowsEvent):
            action, data = 'update', row['after_values']
        else:
            action, data = 'insert', row['values']
        return {'schema': binlogevent.schema, 'table': binlogevent.table, 'action': action, 'data': data}

    def test_connection(self) -> ConnectResult:
        try:
            conn = pymysql.connect(**{**self._conn_setting(), 'connect_timeout': 5})
            with conn.cursor() as cur:
                cur.execute("SHOW VARIABLES LIKE 'log_bin'")
                row = cur.fetchone()
            conn.close()
            if not row or str(row[1]).upper() not in ('ON', '1'):
                return ConnectResult(False, 'binlog 未开启(log_bin != ON)')
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def _db_conn(self) -> Any:
        return pymysql.connect(**{**self._conn_setting(), 'database': self.arg('database'), 'connect_timeout': 5})

    def list_tables(self) -> list[str]:
        """列出可监听的表(配置库内的表)。"""
        conn = self._db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute('SHOW TABLES')
                return [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

    def get_columns(self, table: str) -> list[Column]:
        conn = self._db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(f'SHOW FULL COLUMNS FROM `{table}`')
                rows = cur.fetchall()
            # 列序:Field, Type, Collation, Null, Key, Default, Extra, Privileges, Comment
            return [Column(name=r[0], type=r[1], nullable=(r[3] == 'YES'), comment=r[8] or '') for r in rows]
        finally:
            conn.close()

    def query(self, statement: dict | None = None, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """有界预览:从头读最多 N 个变更后返回(blocking=False)。"""
        statement = statement or {}
        n = limit or statement.get('max') or 20
        reader = self._reader(
            blocking=False,
            resume=False,
            only_tables=statement.get('only_tables'),
            only_events=statement.get('only_events'),
        )
        out = []
        try:
            for ev in reader:
                for row in ev.rows:
                    out.append(self._to_event(ev, row))
                    if len(out) >= n:
                        return out
        finally:
            reader.close()
        return out

    def stream(
        self,
        *,
        only_tables: list[str] | None = None,
        only_events: list[str] | None = None,
        from_beginning: bool = False,
        **kwargs: Any,
    ) -> Iterator[dict]:
        """长驻 CDC:持续 yield 变更事件(阻塞)。"""
        reader = self._reader(
            blocking=True, resume=not from_beginning, only_tables=only_tables, only_events=only_events
        )
        try:
            for ev in reader:
                for row in ev.rows:
                    yield self._to_event(ev, row)
        finally:
            reader.close()

    def extract(
        self, table: str | None = None, *, max_events: int = 10_000, only_events: list[str] | None = None, **kwargs: Any
    ) -> Any:
        """有界一批变更包成 dlt resource(blocking=False)。table 作为 only_tables 过滤。"""
        import dlt

        handler = self
        only_tables = [table] if table else None

        @dlt.resource(name=table or 'binlog', write_disposition='append')
        def _events() -> Any:
            reader = handler._reader(blocking=False, resume=False, only_tables=only_tables, only_events=only_events)
            n = 0
            try:
                for ev in reader:
                    for row in ev.rows:
                        yield handler._to_event(ev, row)
                        n += 1
                        if n >= max_events:
                            return
            finally:
                reader.close()

        return _events
