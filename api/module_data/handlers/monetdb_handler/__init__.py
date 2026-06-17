"""MonetDB 数据源 handler。"""

from module_data.handlers.monetdb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.monetdb_handler.monetdb_handler import MonetDBHandler as Handler

version = '0.0.1'
name = 'monetdb'
title = 'MonetDB'
description = 'MonetDB 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
