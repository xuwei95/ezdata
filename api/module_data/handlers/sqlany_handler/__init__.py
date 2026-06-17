"""SAP SQL Anywhere 数据源 handler。"""

from module_data.handlers.sqlany_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sqlany_handler.sqlany_handler import SQLAnywhereHandler as Handler

version = '0.0.1'
name = 'sqlany'
title = 'SAP SQL Anywhere'
description = 'SAP SQL Anywhere 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
