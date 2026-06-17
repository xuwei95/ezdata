"""CockroachDB 数据源 handler。"""

from module_data.handlers.cockroach_handler.cockroach_handler import CockroachHandler as Handler
from module_data.handlers.cockroach_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'cockroachdb'
title = 'CockroachDB'
description = 'CockroachDB 数据源(SQLAlchemy + dlt)'

__all__ = [
    'Handler',
    'connection_args',
    'connection_args_example',
    'description',
    'name',
    'title',
    'version',
]
