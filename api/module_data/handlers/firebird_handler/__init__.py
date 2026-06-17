"""Firebird 数据源 handler。"""

from module_data.handlers.firebird_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.firebird_handler.firebird_handler import FirebirdHandler as Handler

version = '0.0.1'
name = 'firebird'
title = 'Firebird'
description = 'Firebird 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
