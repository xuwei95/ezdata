"""Apache Pinot handler:数仓/OLAP 引擎,复用 SqlConnector + pinot。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.pinot_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class PinotHandler(SqlConnector):
    name = 'pinot'
    title = 'Apache Pinot'
    driver = 'pinot'
    default_port = 8000
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        host = self.arg('host', default='127.0.0.1')
        broker = self.arg('broker_port', default=self.default_port)
        controller = self.arg('controller_port', default=9000)
        scheme = self.arg('scheme', default='http')
        return f'pinot://{host}:{broker}/query/sql?controller={scheme}://{host}:{controller}/'
