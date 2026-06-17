"""Vertica 数据源 handler。"""

from module_data.handlers.vertica_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.vertica_handler.vertica_handler import VerticaHandler as Handler

version = '0.0.1'
name = 'vertica'
title = 'Vertica'
description = 'Vertica 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
