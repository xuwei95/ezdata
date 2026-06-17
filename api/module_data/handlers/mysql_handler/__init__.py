"""MySQL 数据源 handler。"""

from module_data.handlers.mysql_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.mysql_handler.mysql_handler import MySQLHandler as Handler

version = '0.0.1'
name = 'mysql'
title = 'MySQL'
description = 'MySQL 数据源(SQLAlchemy + dlt)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
