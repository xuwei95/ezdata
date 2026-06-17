"""OrioleDB handler:复用 SqlConnector + postgresql+psycopg2 方言。"""

from module_data.handlers.orioledb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class OrioleDBHandler(SqlConnector):
    name = 'orioledb'
    title = 'OrioleDB'
    driver = 'postgresql+psycopg2'
    default_port = 5432
    connection_args = connection_args
    connection_args_example = connection_args_example
