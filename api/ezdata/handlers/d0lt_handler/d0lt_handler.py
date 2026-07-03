"""Dolt handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from ezdata.handlers.d0lt_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class DoltHandler(SqlConnector):
    name = 'dolt'
    title = 'Dolt'
    driver = 'mysql+pymysql'
    default_port = 3306
    connection_args = connection_args
    connection_args_example = connection_args_example
