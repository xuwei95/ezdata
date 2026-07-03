"""Databend handler:复用 SqlConnector + databend 方言。"""

from ezdata.handlers.databend_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class DatabendHandler(SqlConnector):
    name = 'databend'
    title = 'Databend'
    driver = 'databend'
    default_port = 8000
    connection_args = connection_args
    connection_args_example = connection_args_example
