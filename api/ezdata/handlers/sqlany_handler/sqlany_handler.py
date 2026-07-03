"""SAP SQL Anywhere handler:复用 SqlConnector + sqlalchemy_sqlany。"""

from urllib.parse import quote_plus  # noqa: F401

from ezdata.handlers.sql_base import SqlConnector
from ezdata.handlers.sqlany_handler.connection_args import connection_args, connection_args_example


class SQLAnywhereHandler(SqlConnector):
    name = 'sqlany'
    title = 'SAP SQL Anywhere'
    driver = 'sqlalchemy_sqlany'
    default_port = 2638
    connection_args = connection_args
    connection_args_example = connection_args_example
