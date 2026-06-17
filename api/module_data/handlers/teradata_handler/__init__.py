"""Teradata 数据源 handler。"""

from module_data.handlers.teradata_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.teradata_handler.teradata_handler import TeradataHandler as Handler

version = '0.0.1'
name = 'teradata'
title = 'Teradata'
description = 'Teradata 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
