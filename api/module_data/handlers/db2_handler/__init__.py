"""IBM Db2 数据源 handler。"""

from module_data.handlers.db2_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.db2_handler.db2_handler import Db2Handler as Handler

version = '0.0.1'
name = 'db2'
title = 'IBM Db2'
description = 'IBM Db2 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
