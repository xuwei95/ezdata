"""TimescaleDB handler:PostgreSQL 协议。"""

from module_data.handlers.sql_base import SqlConnector
from module_data.handlers.timescaledb_handler.connection_args import connection_args, connection_args_example


class TimescaleDBHandler(SqlConnector):
    name = 'timescaledb'
    title = 'TimescaleDB'
    driver = 'postgresql+psycopg2'
    default_port = 5432
    connection_args = connection_args
    connection_args_example = connection_args_example
