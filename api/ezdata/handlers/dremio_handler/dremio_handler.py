"""Dremio handler:数仓/OLAP 引擎,复用 SqlConnector + dremio+flight。"""

from urllib.parse import quote_plus

from ezdata.handlers.dremio_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class DremioHandler(SqlConnector):
    name = 'dremio'
    title = 'Dremio'
    driver = 'dremio+flight'
    default_port = 32010
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = self.arg('username', 'user', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        return f'dremio+flight://{user}:{pwd}@{host}:{port}/dremio'
