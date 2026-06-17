"""ClickHouse handler:SqlConnector,按 protocol 选 native/http 驱动。"""

from urllib.parse import quote_plus

from module_data.handlers.clickhouse_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector

_PROTO_DRIVER = {'native': 'clickhouse+native', 'http': 'clickhouse+http', 'https': 'clickhouse+http'}


class ClickHouseHandler(SqlConnector):
    name = 'clickhouse'
    title = 'ClickHouse'
    driver = 'clickhouse+native'
    default_port = 9000
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        driver = _PROTO_DRIVER.get(self.arg('protocol', default='native'), 'clickhouse+native')
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        user = self.arg('user', 'username', default='default')
        pwd = quote_plus(str(self.arg('password', default='')))
        database = self.arg('database', default='default')
        return f'{driver}://{user}:{pwd}@{host}:{port}/{database}'
