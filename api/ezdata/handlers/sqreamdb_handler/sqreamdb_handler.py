"""SQream handler:复用 SqlConnector + sqream 方言。"""

from ezdata.handlers.sql_base import SqlConnector
from ezdata.handlers.sqreamdb_handler.connection_args import connection_args, connection_args_example


class SQreamHandler(SqlConnector):
    name = 'sqreamdb'
    title = 'SQream'
    driver = 'sqream'
    default_port = 5000
    connection_args = connection_args
    connection_args_example = connection_args_example
