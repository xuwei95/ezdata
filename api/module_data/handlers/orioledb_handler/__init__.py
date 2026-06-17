"""OrioleDB 数据源 handler。"""

from module_data.handlers.orioledb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.orioledb_handler.orioledb_handler import OrioleDBHandler as Handler

version = '0.0.1'
name = 'orioledb'
title = 'OrioleDB'
description = 'OrioleDB 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
