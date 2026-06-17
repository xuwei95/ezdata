"""Dremio 数据源 handler。"""

from module_data.handlers.dremio_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.dremio_handler.dremio_handler import DremioHandler as Handler

version = '0.0.1'
name = 'dremio'
title = 'Dremio'
description = 'Dremio 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
