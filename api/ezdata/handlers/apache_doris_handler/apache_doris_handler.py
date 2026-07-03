"""Apache Doris handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from ezdata.handlers.apache_doris_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class ApacheDorisHandler(SqlConnector):
    name = 'doris'
    title = 'Apache Doris'
    driver = 'mysql+pymysql'
    default_port = 9030
    connection_args = connection_args
    connection_args_example = connection_args_example
