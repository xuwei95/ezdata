"""OceanBase handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from ezdata.handlers.oceanbase_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class OceanBaseHandler(SqlConnector):
    name = 'oceanbase'
    title = 'OceanBase'
    driver = 'mysql+pymysql'
    default_port = 2881
    connection_args = connection_args
    connection_args_example = connection_args_example
