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

import hashlib
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

    def _default_server_id(self) -> int:
        """未配置 server_id 时按连接身份派生一个**稳定**从库标识。

        断点续读要求 server_id 稳定唯一(随机会让 MySQL 每次当成新 slave、无法续读且在 master 留孤儿 dump 线程);
        用 host/port/user/database 做确定性哈希映射到 [1, 2^32-1]。用户仍可在数据源配置里显式覆盖。
        """
        ident = f'{self.arg("host")}:{self.arg("port")}:{self.arg("user", "username")}:{self.arg("database")}'
        return int(hashlib.sha256(ident.encode('utf-8')).hexdigest(), 16) % 4_294_967_294 + 1

    def _reader(
        self,
        *,
        blocking: bool,
        resume: bool,
        only_tables: list[str] | None,
        only_events: list[str] | None,
        start_log_file: str | None = None,
        start_log_pos: int | None = None,
    ) -> Any:
        from pymysqlreplication import BinLogStreamReader

        # 传入起始位点(断点续读):从 (log_file, log_pos) 之后续读,resume_stream 必须为 True;
        # 无位点时维持调用方的 resume 语义(True=跳到当前只接最新, False=从最早处)。
        has_pos = bool(start_log_file) and start_log_pos is not None
        return BinLogStreamReader(
            connection_settings=self._conn_setting(),
            server_id=int(self.arg('server_id') or self._default_server_id()),
            freeze_schema=False,  # 查实时表结构以解析真实列名(否则 MINIMAL 元数据会得到 UNKNOWN_COL)
            resume_stream=True if has_pos else resume,  # True=只接最新, False=从头
            blocking=blocking,
            only_schemas=[self.arg('database')] if self.arg('database') else None,
            only_tables=only_tables,
            only_events=self._only_events(only_events),
            log_file=start_log_file if has_pos else None,
            log_pos=int(start_log_pos) if has_pos else None,
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

    @staticmethod
    def _with_pos(reader: Any, event: dict) -> dict:
        """给事件附当前 binlog 位点(reader 每读一个 event 后 .log_file/.log_pos 已更新)。

        调用方装载前应剔除 _log_file/_log_pos,避免污染目标表列;装载成功后据此提交位点。
        """
        event['_log_file'] = getattr(reader, 'log_file', None)
        event['_log_pos'] = getattr(reader, 'log_pos', None)
        return event

    def current_position(self) -> tuple[str, int] | None:
        """当前 binlog 位点 (File, Position)。

        供微批增量**首跑锚定起点**:先记下当前位点作 checkpoint,再从它往后读——这样即使某次运行
        读到 0 条也不会丢事件(下次从锚定点续读),避免每次新连接 from_current 跳过期间写入造成缺口。
        """
        conn = pymysql.connect(**{**self._conn_setting(), 'connect_timeout': 5})
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute('SHOW BINARY LOG STATUS')  # MySQL 8.4+
                except Exception:
                    cur.execute('SHOW MASTER STATUS')  # 旧版本
                row = cur.fetchone()
            if not row or not row[0]:
                return None
            return (row[0], int(row[1]))
        finally:
            conn.close()

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
        """有界读取:读最多 N 个变更后返回(blocking=False)。

        位点语义(供微批增量续读):
        - statement.start_log_file/start_log_pos 有值 → 从该位点之后续读;
        - 否则 statement.from_current=True → 从当前位点起(resume_stream=True,微批增量首跑,避免从头海量重读);
        - 否则 → 从最早处(默认,预览取样用)。
        每条事件附 _log_file/_log_pos(供调用方提交位点)。
        """
        statement = statement or {}
        n = limit or statement.get('max') or 20
        start_log_file = statement.get('start_log_file')
        start_log_pos = statement.get('start_log_pos')
        reader = self._reader(
            blocking=False,
            resume=bool(statement.get('from_current')),  # 无位点时:True=从当前, False=从头
            only_tables=statement.get('only_tables'),
            only_events=statement.get('only_events'),
            start_log_file=start_log_file,
            start_log_pos=start_log_pos,
        )
        out = []
        try:
            for ev in reader:
                for row in ev.rows:
                    out.append(self._with_pos(reader, self._to_event(ev, row)))
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
        start_log_file: str | None = None,
        start_log_pos: int | None = None,
        **kwargs: Any,
    ) -> Iterator[dict]:
        """长驻 CDC:持续 yield 变更事件(阻塞)。

        有 start_log_file/start_log_pos → 断点续读;否则 from_beginning 决定从最早处还是从当前位点起。
        每条事件附 _log_file/_log_pos(对标 kafka 的 _offset),供调用方装载成功后提交位点。
        """
        reader = self._reader(
            blocking=True,
            resume=not from_beginning,
            only_tables=only_tables,
            only_events=only_events,
            start_log_file=start_log_file,
            start_log_pos=start_log_pos,
        )
        try:
            for ev in reader:
                for row in ev.rows:
                    yield self._with_pos(reader, self._to_event(ev, row))
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
