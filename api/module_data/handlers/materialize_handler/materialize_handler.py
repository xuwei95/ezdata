"""Materialize handler:复用 SqlConnector + postgresql+psycopg2。"""

from urllib.parse import quote_plus  # noqa: F401

from module_data.handlers.materialize_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class MaterializeHandler(SqlConnector):
    name = 'materialize'
    title = 'Materialize'
    driver = 'postgresql+psycopg2'
    default_port = 6875
    connection_args = connection_args
    connection_args_example = connection_args_example
