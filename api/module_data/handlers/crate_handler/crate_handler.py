"""CrateDB handler:复用 SqlConnector + crate 方言。"""

from module_data.handlers.crate_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class CrateHandler(SqlConnector):
    name = 'crate'
    title = 'CrateDB'
    driver = 'crate'
    default_port = 4200
    connection_args = connection_args
    connection_args_example = connection_args_example
