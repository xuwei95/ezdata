"""SQL Server handler:SqlConnector(pymssql 驱动,免装 ODBC)。"""

from module_data.handlers.mssql_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sql_base import SqlConnector


class MSSQLHandler(SqlConnector):
    name = 'mssql'
    title = 'Microsoft SQL Server'
    driver = 'mssql+pymssql'
    default_port = 1433
    connection_args = connection_args
    connection_args_example = connection_args_example
