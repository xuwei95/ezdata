"""SQL Server handler:SqlConnector(pymssql 驱动,免装 ODBC)。"""

from ezdata.handlers.mssql_handler.connection_args import connection_args, connection_args_example
from ezdata.handlers.sql_base import SqlConnector


class MSSQLHandler(SqlConnector):
    name = 'mssql'
    title = 'Microsoft SQL Server'
    driver = 'mssql+pymssql'
    default_port = 1433
    connection_args = connection_args
    connection_args_example = connection_args_example
