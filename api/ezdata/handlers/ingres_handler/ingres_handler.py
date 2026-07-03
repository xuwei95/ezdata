"""Actian Ingres handler:复用 SqlConnector + ingres。"""

from urllib.parse import quote_plus

from ezdata.handlers.ingres_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class IngresHandler(SqlConnector):
    name = 'ingres'
    title = 'Actian Ingres'
    driver = 'ingres'
    default_port = 21064
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = self.arg('user', 'username', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        server = self.arg('server', 'host', default='(local)')
        db = self.arg('database', default='')
        return f'ingres://{user}:{pwd}@{server}/{db}'
