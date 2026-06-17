"""Apache Hive 数据源 handler。"""

from module_data.handlers.hive_handler.connection_args import connection_args, connection_args_example
from module_data.handlers.hive_handler.hive_handler import HiveHandler as Handler

version = '0.0.1'
name = 'hive'
title = 'Apache Hive'
description = 'Apache Hive 数据源(SQLAlchemy + dlt)'

__all__ = ['Handler', 'connection_args', 'connection_args_example', 'description', 'name', 'title', 'version']
