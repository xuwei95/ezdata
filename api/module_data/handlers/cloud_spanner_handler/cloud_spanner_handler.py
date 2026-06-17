"""Google Cloud Spanner handler:复用 SqlConnector + spanner+spanner。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.cloud_spanner_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class CloudSpannerHandler(SqlConnector):
    name = 'cloud_spanner'
    title = 'Google Cloud Spanner'
    driver = 'spanner+spanner'
    default_port = 0
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        p = self.arg('project')
        i = self.arg('instance_id')
        d = self.arg('database_id')
        return f'spanner+spanner:///projects/{p}/instances/{i}/databases/{d}'
