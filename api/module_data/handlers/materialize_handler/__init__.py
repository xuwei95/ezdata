"""Materialize 数据源 handler。"""

from module_data.handlers.materialize_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.materialize_handler.materialize_handler import MaterializeHandler as Handler

version = '0.0.1'
name = 'materialize'
title = 'Materialize'
description = 'Materialize 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
