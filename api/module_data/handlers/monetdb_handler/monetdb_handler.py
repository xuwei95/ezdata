"""MonetDB handler:复用 SqlConnector + monetdb 方言。"""

from module_data.handlers.monetdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class MonetDBHandler(SqlConnector):
    name = 'monetdb'
    title = 'MonetDB'
    driver = 'monetdb'
    default_port = 50000
    connection_args = connection_args
    connection_args_example = connection_args_example
