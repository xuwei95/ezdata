"""GreptimeDB 数据源 handler。"""

from module_data.handlers.greptimedb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.greptimedb_handler.greptimedb_handler import GreptimeDBHandler as Handler

version = '0.0.1'
name = 'greptimedb'
title = 'GreptimeDB'
description = 'GreptimeDB 数据源(MySQL 协议,SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
