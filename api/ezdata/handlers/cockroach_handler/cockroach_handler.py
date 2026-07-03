"""CockroachDB handler:复用 SqlConnector + postgresql+psycopg2 方言。"""

from ezdata.handlers.cockroach_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class CockroachHandler(SqlConnector):
    name = 'cockroachdb'
    title = 'CockroachDB'
    driver = 'postgresql+psycopg2'
    default_port = 26257
    connection_args = connection_args
    connection_args_example = connection_args_example
