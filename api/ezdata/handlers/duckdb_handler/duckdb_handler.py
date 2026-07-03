"""DuckDB handler:复用 SqlConnector + duckdb。"""

from urllib.parse import quote_plus  # noqa: F401

from ezdata.handlers.duckdb_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class DuckDBHandler(SqlConnector):
    name = 'duckdb'
    title = 'DuckDB'
    driver = 'duckdb'
    default_port = 0
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _build_url(self) -> str:
        db = self.arg('database', default=':memory:')
        return f'duckdb:///{db}'
