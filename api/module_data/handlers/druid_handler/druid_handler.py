"""Apache Druid handler:数仓/OLAP 引擎,复用 SqlConnector + druid。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.druid_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class DruidHandler(SqlConnector):
    name = 'druid'
    title = 'Apache Druid'
    driver = 'druid'
    default_port = 8082
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        path = self.arg('path', default='druid/v2/sql/')
        return f'druid://{host}:{port}/{path}'
