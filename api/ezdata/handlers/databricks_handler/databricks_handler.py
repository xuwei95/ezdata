"""Databricks handler:SqlConnector + databricks 方言(server_hostname/http_path/access_token)。"""

from urllib.parse import quote_plus, urlencode

from ezdata.handlers.databricks_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class DatabricksHandler(SqlConnector):
    name = 'databricks'
    title = 'Databricks'
    driver = 'databricks'
    default_port = 443
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        host = self.arg('server_hostname')
        token = quote_plus(str(self.arg('access_token', default='')))
        params = {
            k: v
            for k, v in {
                'http_path': self.arg('http_path'),
                'catalog': self.arg('catalog'),
                'schema': self.arg('schema'),
            }.items()
            if v
        }
        qs = f'?{urlencode(params)}' if params else ''
        return f'databricks://token:{token}@{host}:{self.default_port}{qs}'
