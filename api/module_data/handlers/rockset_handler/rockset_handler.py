"""Rockset handler:MySQL 协议,复用 SqlConnector + mysql+pymysql。"""

from module_data.handlers.rockset_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class RocksetHandler(SqlConnector):
    name = 'rockset'
    title = 'Rockset'
    driver = 'mysql+pymysql'
    default_port = 3306
    connection_args = connection_args
    connection_args_example = connection_args_example
