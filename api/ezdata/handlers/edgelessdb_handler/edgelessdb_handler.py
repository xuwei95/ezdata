"""EdgelessDB handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from ezdata.handlers.edgelessdb_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class EdgelessDBHandler(SqlConnector):
    name = 'edgelessdb'
    title = 'EdgelessDB'
    driver = 'mysql+pymysql'
    default_port = 3306
    connection_args = connection_args
    connection_args_example = connection_args_example
