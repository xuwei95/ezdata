"""TiDB handler:复用 SqlConnector + mysql+pymysql 方言。"""

from ezdata.handlers.sql_base import SqlConnector
from ezdata.handlers.tidb_handler.connection_args import connection_args, connection_args_example


class TiDBHandler(SqlConnector):
    name = 'tidb'
    title = 'TiDB'
    driver = 'mysql+pymysql'
    default_port = 4000
    connection_args = connection_args
    connection_args_example = connection_args_example
