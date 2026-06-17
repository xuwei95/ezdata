"""Apache Impala handler:数仓/OLAP 引擎,复用 SqlConnector + impala。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.impala_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class ImpalaHandler(SqlConnector):
    name = 'impala'
    title = 'Apache Impala'
    driver = 'impala'
    default_port = 21050
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        host = self.arg('host', default='127.0.0.1')
        port = self.arg('port', default=self.default_port)
        database = self.arg('database', default='default')
        return f'impala://{host}:{port}/{database}'
