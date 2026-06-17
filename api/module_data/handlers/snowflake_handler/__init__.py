"""Snowflake 数据源 handler。"""

from module_data.handlers.snowflake_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.snowflake_handler.snowflake_handler import SnowflakeHandler as Handler

version = '0.0.1'
name = 'snowflake'
title = 'Snowflake'
description = 'Snowflake 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
