"""Vertica handler:复用 SqlConnector + vertica+vertica_python 方言。"""

from ezdata.handlers.sql_base import SqlConnector
from ezdata.handlers.vertica_handler.connection_args import connection_args, connection_args_example


class VerticaHandler(SqlConnector):
    name = 'vertica'
    title = 'Vertica'
    driver = 'vertica+vertica_python'
    default_port = 5433
    connection_args = connection_args
    connection_args_example = connection_args_example
