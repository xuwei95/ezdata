"""StarRocks handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from module_data.handlers.sql_base import SqlConnector
from module_data.handlers.starrocks_handler.connection_args import connection_args, connection_args_example


class StarRocksHandler(SqlConnector):
    name = 'starrocks'
    title = 'StarRocks'
    driver = 'mysql+pymysql'
    default_port = 9030
    connection_args = connection_args
    connection_args_example = connection_args_example
