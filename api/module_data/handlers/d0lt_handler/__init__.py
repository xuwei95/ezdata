"""Dolt 数据源 handler。"""

from module_data.handlers.d0lt_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.d0lt_handler.d0lt_handler import DoltHandler as Handler

version = '0.0.1'
name = 'dolt'
title = 'Dolt'
description = 'Dolt 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
