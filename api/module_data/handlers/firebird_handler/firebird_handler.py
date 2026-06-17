"""Firebird handler:复用 SqlConnector + firebird+fdb 方言。"""

from module_data.handlers.firebird_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class FirebirdHandler(SqlConnector):
    name = 'firebird'
    title = 'Firebird'
    driver = 'firebird+fdb'
    default_port = 3050
    connection_args = connection_args
    connection_args_example = connection_args_example
