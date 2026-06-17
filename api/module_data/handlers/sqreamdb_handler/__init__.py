"""SQream 数据源 handler。"""

from module_data.handlers.sqreamdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.sqreamdb_handler.sqreamdb_handler import SQreamHandler as Handler

version = '0.0.1'
name = 'sqreamdb'
title = 'SQream'
description = 'SQream 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
