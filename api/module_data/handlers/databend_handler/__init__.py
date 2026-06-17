"""Databend 数据源 handler。"""

from module_data.handlers.databend_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.databend_handler.databend_handler import DatabendHandler as Handler

version = '0.0.1'
name = 'databend'
title = 'Databend'
description = 'Databend 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
