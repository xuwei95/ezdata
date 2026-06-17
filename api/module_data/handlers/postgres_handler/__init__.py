"""PostgreSQL 数据源 handler。"""

from module_data.handlers.postgres_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.postgres_handler.postgres_handler import PostgresHandler as Handler

version = '0.0.1'
name = 'postgresql'
title = 'PostgreSQL'
description = 'PostgreSQL 数据源(SQLAlchemy + dlt)'

__all__ = [
           'Handler',
           'connection_args',
           'connection_args_example',
           'description',
           'name',
           'title',
           'version',
]
