"""Apache Hive handler:数仓/OLAP 引擎,复用 SqlConnector + hive。"""

from urllib.parse import quote_plus

from ezdata.handlers.hive_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class HiveHandler(SqlConnector):
    name = 'hive'
    title = 'Apache Hive'
    driver = 'hive'
    default_port = 10000
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        user = self.arg('username', 'user', default='')
        pwd = quote_plus(str(self.arg('password', default='')))
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        database = self.arg('database', default='default')
        cred = f'{user}:{pwd}@' if pwd else (f'{user}@' if user else '')
        url = f'hive://{cred}{host}:{port}/{database}'
        auth = self.arg('auth')
        return f'{url}?auth={auth}' if auth else url
