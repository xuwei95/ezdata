"""PostgreSQL handler:SqlConnector + postgresql 方言。"""

from ezdata.handlers.postgres_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class PostgresHandler(SqlConnector):
    name = 'postgresql'
    title = 'PostgreSQL'
    driver = 'postgresql+psycopg2'
    default_port = 5432
    connection_args = connection_args
    connection_args_example = connection_args_example
