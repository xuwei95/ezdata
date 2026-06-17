"""Amazon Aurora (MySQL) handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from module_data.handlers.aurora_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class AuroraHandler(SqlConnector):
    name = 'aurora'
    title = 'Amazon Aurora (MySQL)'
    driver = 'mysql+pymysql'
    default_port = 3306
    connection_args = connection_args
    connection_args_example = connection_args_example
