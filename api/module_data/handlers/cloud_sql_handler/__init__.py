"""Google Cloud SQL 数据源 handler。"""

from module_data.handlers.cloud_sql_handler.cloud_sql_handler import CloudSQLHandler as Handler
from module_data.handlers.cloud_sql_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'cloud_sql'
title = 'Google Cloud SQL'
description = 'Google Cloud SQL 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
