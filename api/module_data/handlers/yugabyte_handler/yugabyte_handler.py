"""YugabyteDB handler:复用 SqlConnector + postgresql+psycopg2。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.sql_base import SqlConnector
from module_data.handlers.yugabyte_handler.connection_args import connection_args, connection_args_example


class YugabyteHandler(SqlConnector):
    name = 'yugabyte'
    title = 'YugabyteDB'
    driver = 'postgresql+psycopg2'
    default_port = 5433
    connection_args = connection_args
    connection_args_example = connection_args_example
