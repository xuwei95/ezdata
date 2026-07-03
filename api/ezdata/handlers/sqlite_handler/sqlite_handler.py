"""SQLite handler:复用 SqlConnector + sqlite。"""

from urllib.parse import quote_plus  # noqa: F401

from ezdata.handlers.sql_base import SqlConnector
from ezdata.handlers.sqlite_handler.connection_args import connection_args, connection_args_example


class SQLiteHandler(SqlConnector):
    name = 'sqlite'
    title = 'SQLite'
    driver = 'sqlite'
    default_port = 0
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        db = self.arg('db_file', 'database', default=':memory:')
        return f'sqlite:///{db}'
