"""MatrixOne handler:复用 SqlConnector + mysql+pymysql 方言。"""

from ezdata.handlers.matrixone_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class MatrixOneHandler(SqlConnector):
    name = 'matrixone'
    title = 'MatrixOne'
    driver = 'mysql+pymysql'
    default_port = 6001
    connection_args = connection_args
    connection_args_example = connection_args_example
