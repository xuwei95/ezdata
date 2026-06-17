"""MariaDB handler:复用 SqlConnector + mysql+pymysql 方言。"""

from module_data.handlers.mariadb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class MariaDBHandler(SqlConnector):
    name = 'mariadb'
    title = 'MariaDB'
    driver = 'mysql+pymysql'
    default_port = 3306
    connection_args = connection_args
    connection_args_example = connection_args_example
