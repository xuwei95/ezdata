"""SQL Server 数据源 handler。"""

from module_data.handlers.mssql_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mssql_handler.mssql_handler import MSSQLHandler as Handler

version = '0.0.1'
name = 'mssql'
title = 'Microsoft SQL Server'
description = 'SQL Server 数据源(SQLAlchemy + dlt)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
