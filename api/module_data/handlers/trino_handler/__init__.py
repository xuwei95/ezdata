"""Trino 数据源 handler。"""

from module_data.handlers.trino_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.trino_handler.trino_handler import TrinoHandler as Handler

version = '0.0.1'
name = 'trino'
title = 'Trino'
description = 'Trino 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
