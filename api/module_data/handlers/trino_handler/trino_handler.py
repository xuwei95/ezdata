"""Trino handler:数仓/OLAP 引擎,复用 SqlConnector + trino。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.sql_base import SqlConnector
from module_data.handlers.trino_handler.connection_args import connection_args, connection_args_example


class TrinoHandler(SqlConnector):
    name = 'trino'
    title = 'Trino'
    driver = 'trino'
    default_port = 8080
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = self.arg('user', 'username', default='admin')
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        path = '/'.join(p for p in [self.arg('catalog'), self.arg('schema')] if p)
        return f'trino://{user}@{host}:{port}/{path}' if path else f'trino://{user}@{host}:{port}'
