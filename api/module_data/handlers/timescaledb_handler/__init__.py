"""TimescaleDB 数据源 handler。"""

from module_data.handlers.timescaledb_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.timescaledb_handler.timescaledb_handler import TimescaleDBHandler as Handler

version = '0.0.1'
name = 'timescaledb'
title = 'TimescaleDB'
description = 'TimescaleDB 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
